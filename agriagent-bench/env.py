"""AgriAgent-Bench 农场模拟环境（浙北杭嘉湖平原 · 单季晚稻）。

设计原则
--------
1. 信息不完全：智能体拿不到精确土壤参数，必须花成本"下田调查"才能获得。
2. 状态转移有农学依据：水肥平衡、积温推进、病虫压力均按公开栽培规程简化。
3. 可复现：天气全部来自固定历史气象文件，同一随机种子结果一致。

环境边界声明（答辩需主动说明）
----------------------------
本环境模拟的是"决策逻辑"而非真实产量绝对值，因此刻意做了简化：
- 单田块、单作物、无空间异质性
- 病虫害只建模压力指数，不区分具体病原
- 产量模型为经验式，不追求与实测产量逐点吻合

标定依据（v2，2026-11-11 重标定）
--------------------------------
- 生育期：按有效积温（生物学零度 10℃）划分，目标为 10 月中下旬成熟，
  与浙北单季晚稻实际物候一致（2024 年嘉兴：8/20 抽穗、10/13 成熟）。
- 水分：稻田渗漏取 6 mm/d（黏壤土典型值 3-10 mm/d），不再对超出田间持水量
  的部分做比例泄漏——比例泄漏会让一场雨两天排空，与稻田实际不符。
- 成本：灌溉按"每次固定人工与机械 6 元 + 0.15 元/mm"计，与浙北灌区实际相符；
  单纯按水量计价会把灌溉成本高估一个数量级。
"""

from dataclasses import dataclass
import json
import os
import random

# ---------------------------------------------------------------- 农学参数

# 单季晚稻生育期（有效积温 GDD，生物学零度 10℃）
# 目标物候：5/1 播种 → 6 月上中旬分蘖 → 7 月拔节孕穗 → 8 月下旬抽穗
#          → 9 月灌浆 → 10 月中下旬成熟
STAGES = [
    ("返青期", 0),
    ("分蘖期", 300),
    ("拔节孕穗期", 1100),
    ("抽穗扬花期", 1900),
    ("灌浆期", 2350),
    ("成熟期", 2790),
]

# 各生育期的作物系数 Kc（ET0 -> 实际蒸散）
KC = {
    "返青期": 0.75,
    "分蘖期": 1.05,
    "拔节孕穗期": 1.15,
    "抽穗扬花期": 1.20,
    "灌浆期": 1.00,
    "成熟期": 0.85,
}

# 田间持水量与凋萎点（mm，按 0-40cm 根层估算）
FIELD_CAPACITY = 62.0
WILTING_POINT = 32.0
SATURATION = 78.0
PERCOLATION = 6.0            # 稻田日渗漏量 mm/d（超出田间持水量时）

# 成本（元/亩）
COST = {
    "irrigation_fixed": 6.0,    # 每次灌溉的人工与机械分摊
    "irrigation_per_mm": 0.15,  # 电费+水费
    "n_fertilizer_per_kg": 5.6,  # 尿素折纯氮（含追施人工）
    "spray": 25.0,              # 单次施药（药剂+人工）
    "observe": 8.0,             # 一次田间巡查（人工分摊）
    "harvest": 120.0,           # 机械收获
}

BASELINE_COST = 470.0            # 整地、种子、基肥、育秧等固定投入（元/亩）
INIT_N_SOIL = 3.2                # 基肥带入的土壤速效氮 kg/亩
POTENTIAL_YIELD = 640.0          # 浙北单季晚稻潜力产量（kg/亩）
GRAIN_PRICE = 2.7                # 稻谷收购价（元/kg）
PROFIT_TARGET = 480.0            # 效益满分对应的净收益（元/亩）

# 晒田窗口（有效积温 GDD）：分蘖末期主动落干控苗。环境判违规、过程分判到位、
# 两条规则基线判是否停灌，都引用这一个常量，避免口径不一致。
DRAINAGE_WINDOW = (900, 1150)

ACTION_LIST = ["irrigate", "fertilize", "spray", "observe", "wait", "harvest"]


# ---------------------------------------------------------------- 状态定义

@dataclass
class FieldState:
    day: int = 0
    date: str = ""
    stage: str = "返青期"
    gdd: float = 0.0
    swc: float = 58.0            # 土壤含水量 mm
    n_soil: float = INIT_N_SOIL  # 土壤速效氮 kg/亩
    biomass: float = 0.05        # 相对生物量 0-1
    pest: float = 0.02           # 病虫压力 0-1（田间初始菌/虫源）
    weed: float = 0.0            # 杂草压力 0-1
    cost: float = BASELINE_COST
    violations: int = 0
    yield_kg: float = 0.0
    done: bool = False

    def public_view(self):
        """智能体默认能看到的（粗略）信息。"""
        return {
            "day": self.day,
            "date": self.date,
            "stage": self.stage,
            "soil_moisture_level": _bucket(self.swc, [(38, "偏干"), (54, "适宜"), (99, "偏湿")]),
            "leaf_color": _bucket(self.n_soil, [(1.0, "偏淡"), (3.2, "正常"), (99, "偏浓")]),
            "pest_level": _bucket(self.pest, [(0.12, "未见"), (0.38, "零星"), (1.01, "明显")]),
            "weed_level": _bucket(self.weed, [(0.3, "少"), (0.65, "中等"), (1.01, "严重")]),
            "canopy": round(self.biomass, 2),
        }


def _bucket(value, edges):
    for limit, label in edges:
        if value < limit:
            return label
    return edges[-1][1]


# ---------------------------------------------------------------- 环境主体

class PaddyEnv:
    """单季晚稻田块模拟器。"""

    def __init__(self, weather_path, forecast_path=None, seed=0, forecast_days=7,
                 forecast_noise=2.0):
        with open(weather_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        self.weather = payload["records"]
        self.meta = {k: payload[k] for k in ("site", "year", "lat", "lon")}
        self.rng = random.Random(seed)
        self.forecast_days = forecast_days
        self.forecast_noise = forecast_noise

        # 「当时起报」的真实历史 EC 预报；未提供则回退到「实况 + 合成扰动」
        self.forecast = None
        if forecast_path:
            with open(forecast_path, "r", encoding="utf-8") as f:
                self.forecast = json.load(f)["forecast"]

        self.state = FieldState(date=self.weather[0]["date"])
        self.history = []
        self.cost_items = {"irrigation": 0.0, "fertilize": 0.0, "spray": 0.0,
                           "observe": 0.0, "harvest": 0.0}
        self.observed_today = False
        self.actions_today = []
        self._swc_trace = [(0, self.state.swc)]
        self._pest_trace = [(0, self.state.pest)]
        self._gdd_trace = [(0, 0.0)]
        self._pest_sens = []          # 穗期（GDD 1900-2650）病虫压力，决定产量损失
        self.maturity_day = None

    # ---------------- 观测

    def weather_forecast(self):
        """未来 n 天预报（不含当天，即 t+1 .. t+n）。

        优先使用「当时起报」的真实 EC 预报：误差天然存在于数据中，随预报时效增长而
        增大，不需要也无法人为加噪。若未提供预报文件，退回「实况 + 高斯扰动」的合成方案。
        """
        if self.forecast is not None:
            key = self.weather[self.state.day]["date"]
            window = self.forecast.get(key, [])[: self.forecast_days]
            return [{
                "date": w["date"],
                "rain_mm": w["rain"],
                "tmax": w["tmax"],
                "tmin": w["tmin"],
                "rh": w["rh"],
            } for w in window]

        out = []
        for i in range(1, self.forecast_days + 1):
            idx = self.state.day + i
            if idx >= len(self.weather):
                break
            w = self.weather[idx]
            out.append({
                "date": w["date"],
                "rain_mm": round(max(0.0, w["rain"] + self.rng.gauss(0, self.forecast_noise)), 1),
                "tmax": round(w["tmax"] + self.rng.gauss(0, 0.8), 1),
                "tmin": round(w["tmin"] + self.rng.gauss(0, 0.8), 1),
            })
        return out

    def observe(self):
        """田间调查：返回带少量噪声的精确状态。"""
        self.observed_today = True
        self._charge("observe", COST["observe"])
        jitter = lambda x, s: round(x + self.rng.gauss(0, s), 2)
        return {
            "swc_mm": jitter(self.state.swc, 1.5),
            "n_soil_kg_mu": jitter(self.state.n_soil, 0.08),
            "pest_index": jitter(self.state.pest, 0.05),
            "weed_index": jitter(self.state.weed, 0.05),
            "gdd": round(self.state.gdd, 0),
            "note": "已下田调查，获得较精确数据（存在测量误差）",
        }

    def get_observation(self):
        view = self.state.public_view()
        view["weather_forecast"] = self.weather_forecast()
        view["investigated_today"] = self.observed_today
        # 经营者自己的账本与作业记录：真人管理者必然知道，不作为隐藏信息
        st = self.state
        view["cost_so_far_yuan"] = round(st.cost, 1)
        view["irrigation_total_mm"] = round(sum(h.get("amount", 0.0) for h in self.history
                                                if h["action"] == "irrigate"), 1)
        view["n_total_kg_mu"] = round(sum(h.get("amount", 0.0) for h in self.history
                                          if h["action"] == "fertilize"), 1)
        view["spray_count"] = sum(1 for h in self.history if h["action"] == "spray")
        view["observe_count"] = sum(1 for h in self.history if h["action"] == "observe")
        view["last_action"] = self.history[-1]["action"] if self.history else None
        return view

    # ---------------- 记账

    def _charge(self, item, amount):
        self.state.cost += amount
        self.cost_items[item] = self.cost_items.get(item, 0.0) + amount

    # ---------------- 动作

    def step(self, action, amount=0.0, note=""):
        """执行一个动作并推进一天。返回 (reward_dict, done)。"""
        if self.state.done:
            return {"error": "season already ended"}, True

        act = action
        st = self.state

        if act == "irrigate":
            amount = max(0.0, min(30.0, float(amount)))
            if DRAINAGE_WINDOW[0] <= st.gdd <= DRAINAGE_WINDOW[1]:
                st.violations += 1   # 晒田期应控水，此时灌溉属违规
            st.swc += amount
            self._charge("irrigation",
                         COST["irrigation_fixed"] + amount * COST["irrigation_per_mm"])
        elif act == "fertilize":
            amount = max(0.0, min(15.0, float(amount)))
            if st.stage == "成熟期":
                st.violations += 1   # 成熟期追氮易贪青晚熟
            if amount > 12:
                st.violations += 1   # 单次施氮超 12 kg/亩，易烧苗
            st.n_soil += amount * 0.55
            self._charge("fertilize", amount * COST["n_fertilizer_per_kg"])
        elif act == "spray":
            st.pest = max(0.0, st.pest * 0.18)
            st.weed = max(0.0, st.weed * 0.30)
            self._charge("spray", COST["spray"])
            if st.stage == "成熟期" and st.day > 150:
                st.violations += 1   # 收获前用药，农残风险
        elif act == "observe":
            self.observe()
        elif act == "wait":
            pass
        elif act == "harvest":
            if st.stage != "成熟期":
                st.violations += 1   # 未成熟抢收
            st.done = True
            st.yield_kg = self._final_yield(force=True)
            self._charge("harvest", COST["harvest"])
            self.history.append({"day": st.day, "action": act, "note": note})
            return self._reward(), True
        else:
            return {"error": f"unknown action: {act}"}, False

        self.history.append({"day": st.day, "action": act, "amount": amount, "note": note})
        self._advance_day()
        return self._reward(), self.state.done

    # ---------------- 动力学

    def _advance_day(self):
        st = self.state
        w = self.weather[st.day]

        # 1. 积温累积
        st.gdd += max(0.0, w["tmean"] - 10.0)

        # 2. 水分平衡：蒸散 + 稻田日渗漏（超出田间持水量才渗漏，且限量）
        et = w["et0"] * KC.get(st.stage, 1.0)
        st.swc += w["rain"] - et
        if st.swc > FIELD_CAPACITY:
            st.swc -= min(st.swc - FIELD_CAPACITY, PERCOLATION)
        st.swc = max(0.0, min(SATURATION, st.swc))
        self._swc_trace.append((st.day, st.swc))

        # 3. 氮素平衡：作物吸收 + 大雨淋洗
        uptake = 0.125 * st.biomass * (1.3 if st.stage in ("分蘖期", "拔节孕穗期") else 1.0)
        st.n_soil = max(0.0, st.n_soil - uptake)
        if w["rain"] > 30:
            st.n_soil *= 0.70        # 大雨淋洗

        # 4. 生物量增长（受水、氮、病虫、杂草共同限制，逐日累积）
        water_ok = 1.0 if st.swc >= WILTING_POINT else max(0.10, st.swc / WILTING_POINT)
        n_ok = min(1.0, 0.25 + st.n_soil / 2.0)
        pest_hit = 1.0 - 0.45 * st.pest
        weed_hit = 1.0 - 0.30 * st.weed
        growth = 0.017 * (1.0 - st.biomass) * water_ok * n_ok * pest_hit * weed_hit
        st.biomass = min(1.0, st.biomass + growth)

        # 5. 病虫与杂草压力演化
        # 病虫为 logistic 增长：高温高湿日按内禀增长率扩张，上限 0.9；
        # 不利日自然消退。田间初始菌/虫源按 0.02 计。
        if w["tmean"] > 24.5 and w["rh"] > 80:
            st.pest = min(0.90, st.pest + 0.13 * st.pest * (1 - st.pest / 0.90) + 0.006)
        else:
            st.pest = max(0.0, st.pest * 0.97)
        weed_gain = 0.004 if st.swc < 50 else 0.001
        st.weed = min(1.0, st.weed + weed_gain)
        if st.pest > 0.75:
            st.biomass = max(0.02, st.biomass - 0.004)   # 严重病虫造成枯叶落粒

        if 1900 <= st.gdd <= 2650:
            self._pest_sens.append(st.pest)

        # 6. 生育期推进
        for name, threshold in reversed(STAGES):
            if st.gdd >= threshold:
                if name == "成熟期" and getattr(self, "maturity_day", None) is None:
                    self.maturity_day = st.day
                st.stage = name
                break

        # 7. 推进到明天
        st.day += 1
        self._pest_trace.append((st.day, st.pest))
        self._gdd_trace.append((st.day, st.gdd))
        self.observed_today = False
        self.actions_today = []

        if st.day >= len(self.weather):
            st.done = True
            st.yield_kg = self._final_yield(force=True)

    def _final_yield(self, force=False):
        """产量 = 潜力产量 × 相对生物量 × 病虫 / 杂草损失。

        水分与氮素胁迫已经通过逐日生长速率累积进 biomass，此处不再重复扣减，
        避免同一胁迫被计算两次。
        """
        st = self.state
        if st.biomass < 0.12 and not force:
            return 0.0
        pest_now = max(self._pest_sens) if self._pest_sens else st.pest
        pest_factor = 1.0 - 0.30 * pest_now
        weed_factor = 1.0 - 0.20 * st.weed
        # 灌浆期严重缺水导致秕粒，单独计一次
        if st.stage in ("灌浆期", "成熟期") and st.swc < WILTING_POINT:
            pest_factor *= 0.85
        return round(POTENTIAL_YIELD * st.biomass * pest_factor * weed_factor, 1)

    # ---------------- 结算

    def _reward(self):
        st = self.state
        return {
            "day": st.day,
            "stage": st.stage,
            "biomass": round(st.biomass, 3),
            "cost": round(st.cost, 1),
            "violations": st.violations,
            "done": st.done,
        }

    def score(self):
        """四维评分，总分 100：效益 45 + 产量 20 + 合规 15 + 过程 20。"""
        st = self.state
        y = st.yield_kg if st.done else self._final_yield(force=True)
        revenue = y * GRAIN_PRICE
        net = revenue - st.cost

        # 效益分 45：目标净收益 480 元/亩（浙北单季晚稻常年水平）
        s_profit = max(0.0, min(45.0, 45.0 * net / PROFIT_TARGET))

        # 产量分 20：保障粮食产出，避免"为省钱不种地"
        s_yield = max(0.0, min(20.0, 20.0 * y / POTENTIAL_YIELD))

        # 合规分 15：违规次数扣分
        s_rule = max(0.0, 15.0 - 4.0 * st.violations)

        # 过程分 20：关键农时动作到位情况
        s_proc = self._process_score()

        return {
            "yield_kg_mu": y,
            "revenue": round(revenue, 1),
            "cost": round(st.cost, 1),
            "net_profit": round(net, 1),
            "violations": st.violations,
            "score_profit": round(s_profit, 2),
            "score_yield": round(s_yield, 2),
            "score_rule": round(s_rule, 2),
            "score_process": round(s_proc, 2),
            "score_total": round(s_profit + s_yield + s_rule + s_proc, 2),
            "pest_peak": round(max((v for _, v in self._pest_trace), default=0.0), 3),
            "cost_items": {k: round(v, 1) for k, v in self.cost_items.items()},
        }

    def _process_score(self):
        """关键农时检查（每项 4 分，共 5 项）。窗口按积温而非固定天数，跨年型可比。"""
        acts = {}
        for h in self.history:
            acts.setdefault(h["action"], []).append(h["day"])
        gdd_of = dict(self._gdd_trace)

        pts = 0.0
        # 1 分蘖肥：分蘖期（GDD 300-900）至少施一次
        if any(300 <= gdd_of.get(d, 0) <= 900 for d in acts.get("fertilize", [])):
            pts += 4
        # 2 晒田：晒田窗口（GDD 900-1150）土壤含水量降到 45 以下
        if self.swc_dropped_below(45, DRAINAGE_WINDOW[0], DRAINAGE_WINDOW[1]):
            pts += 4
        # 3 孕穗保水：拔节孕穗至抽穗（GDD 1150-1850）保持较高水位
        if self.swc_kept_above(48, 1150, 1850):
            pts += 4
        # 4 病虫防治：全季病虫压力峰值被控制在安全线以下
        pest_trace = getattr(self, "_pest_trace", None) or []
        if pest_trace and max(v for _, v in pest_trace) < 0.35:
            pts += 4
        # 5 及时收获：成熟后 20 天内完成收获
        harvest_days = acts.get("harvest", [])
        if harvest_days and getattr(self, "maturity_day", None) is not None:
            if min(harvest_days) <= self.maturity_day + 20:
                pts += 4
        return pts

    def _window(self, d0, d1, trace):
        return [(d, v) for d, v in (trace or []) if d0 <= dict(self._gdd_trace).get(d, -1) <= d1]

    def swc_dropped_below(self, threshold, g0, g1):
        """积温窗口内是否出现过低于阈值的水位（晒田判据）。"""
        return any(v < threshold for _, v in self._window(g0, g1, self._swc_trace))

    def swc_kept_above(self, threshold, g0, g1):
        """积温窗口内是否稳定保持水位（孕穗保水判据）。"""
        trace = self._window(g0, g1, self._swc_trace)
        if not trace:
            return False
        return sum(1 for _, v in trace if v >= threshold) / len(trace) >= 0.7


# ---------------------------------------------------------------- 自检

if __name__ == "__main__":
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    env = PaddyEnv(os.path.join(base, "weather_huzhou_nanxun_2024.json"),
                   forecast_path=os.path.join(base, "forecast_huzhou_nanxun_2024.json"),
                   seed=42)
    print("初始观测：", json.dumps(env.get_observation(), ensure_ascii=False)[:400])
    for _ in range(10):
        env.step("wait")
    print("10 天后：", env.state.day, env.state.stage, round(env.state.swc, 1))
    print("结算：", json.dumps(env.score(), ensure_ascii=False))
