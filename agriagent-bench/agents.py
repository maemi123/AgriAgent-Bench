"""AgriAgent-Bench 的智能体实现。

包含四条基线（用于校准评测台的上下界）和一个 LLM 通用接口：

    RandomAgent  随机乱动          —— 下界，用来确认"乱来会受罚"
    NaiveAgent   只收不管          —— 对照，代表"靠天吃饭"
    RuleAgent    农技规则专家      —— 实用参照，代表"老农水平"
    ForecastRuleAgent 规则+预报    —— 与 RuleAgent 单点差异，用于测量预报信息的价值
    OracleAgent  全知专家          —— 上界，代表"信息完备时的天花板"
    LLMAgent     通用大模型接口    —— 需自行配置 API

所有规则型基线的农时判断都以**有效积温 GDD** 为准，而非固定天数，
这样不同年型（冷暖、早晚）之间的动作窗口才可比。

LLM 接口通过环境变量配置，不写死密钥：
    AGRIBENCH_BASE_URL   例：https://api.deepseek.com/v1
    AGRIBENCH_API_KEY
    AGRIBENCH_MODEL      例：deepseek-chat
"""

import json
import os
import random
import re
import subprocess
import urllib.request

from env import DRAINAGE_WINDOW


# ---------------------------------------------------------------- 基类

class BaseAgent:
    name = "base"

    def reset(self):
        pass

    def act(self, observation, env):
        """返回 (action, amount, reason)。"""
        raise NotImplementedError


# ---------------------------------------------------------------- 下界

class RandomAgent(BaseAgent):
    name = "随机乱动"

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def act(self, observation, env):
        if env.state.stage == "成熟期" and self.rng.random() < 0.3:
            return "harvest", 0, "随机收获"
        choice = self.rng.choices(
            ["wait", "irrigate", "fertilize", "spray", "observe"],
            weights=[40, 20, 15, 15, 10],
        )[0]
        amount = {"irrigate": self.rng.uniform(5, 30), "fertilize": self.rng.uniform(1, 12)}.get(choice, 0)
        return choice, amount, "随机动作"


class NaiveAgent(BaseAgent):
    """只等成熟就收，不做任何管理。"""
    name = "只收不管"

    def act(self, observation, env):
        if env.state.stage == "成熟期":
            return "harvest", 0, "成熟即收"
        return "wait", 0, "不干预"


# ---------------------------------------------------------------- 规则基线

class RuleAgent(BaseAgent):
    """按浙北单季晚稻栽培规程写的规则策略（不看预报）。"""

    name = "农技规则"

    # 追肥计划：分蘖肥 / 穗肥 / 粒肥（GDD 区间, 施氮量 kg/亩）
    FERT_PLAN = [(300, 520, 6.0), (1100, 1300, 6.0), (1700, 1900, 3.0)]

    def __init__(self):
        self.fert_done = []
        self.last_spray_day = -99
        self.last_obs_day = -99
        self.maturity_seen = None

    def act(self, observation, env):
        st = env.state
        d = st.day
        g = st.gdd

        # 成熟后适期收获
        if st.stage == "成熟期":
            if self.maturity_seen is None:
                self.maturity_seen = d
            if d - self.maturity_seen >= 8:
                return "harvest", 0, "成熟后适期收获"

        # 病虫：见零星即打，间隔不少于 12 天
        if observation["pest_level"] in ("明显", "零星") and d - self.last_spray_day >= 12:
            self.last_spray_day = d
            return "spray", 0, "按病虫发生情况施药"

        # 灌溉
        reason = self._irrigate_decision(observation, env)
        if reason:
            return "irrigate", 22, reason

        # 追肥：按 GDD 窗口，每段只施一次
        for i, (g0, g1, amount) in enumerate(self.FERT_PLAN):
            if i not in self.fert_done and g0 <= g <= g1:
                if observation["leaf_color"] != "偏浓":
                    self.fert_done.append(i)
                    return "fertilize", amount, "按生育期追肥"

        # 每 12 天田调一次
        if d - self.last_obs_day >= 12:
            self.last_obs_day = d
            return "observe", 0, "定期巡田"

        return "wait", 0, "维持现状"

    def _irrigate_decision(self, observation, env):
        """灌溉判定：返回理由字符串，None 表示不灌溉。子类只覆盖这一个点。"""
        st = env.state
        if DRAINAGE_WINDOW[0] <= st.gdd <= DRAINAGE_WINDOW[1]:   # 晒田期
            return None
        if observation["soil_moisture_level"] != "偏干":
            return None
        return "墒情偏干，补水"


class ForecastRuleAgent(RuleAgent):
    """会看预报的规则策略。

    与 RuleAgent 的唯一差别在灌溉判定：若预报未来 N 天累计降水超过阈值，即使墒情
    偏干也暂缓灌溉。因此两者得分之差，就是「预报信息」本身的边际价值。
    预报本身有误差，所以「等雨」有时会落空——这正是要测量的代价。
    """

    name = "规则+预报"

    def __init__(self, rain_threshold=15.0, lead=7):
        super().__init__()
        self.rain_threshold = rain_threshold
        self.lead = lead

    def _irrigate_decision(self, observation, env):
        reason = super()._irrigate_decision(observation, env)
        if not reason:
            return None
        fc = observation.get("weather_forecast") or []
        rain = sum(w["rain_mm"] for w in fc[: self.lead])
        if rain >= self.rain_threshold:
            return None
        return f"{reason}（预报未来{self.lead}天仅 {rain:.0f}mm 降水）"


# ---------------------------------------------------------------- 上界

class OracleAgent(BaseAgent):
    """全知专家：直接读真实状态、知道完整天气，代表信息完备上界。

    策略按浙北高产栽培规程设定：水位维持在适宜区间、晒田期主动落干、
    三次追肥、病虫压到安全线以下、成熟后适期收获。
    """

    name = "全知上界"

    SLACK = 0.15        # 病虫防治阈值（远低于"明显"的 0.38，留出安全余量）
    BAND_LOW = 52       # 适宜水位下限
    BAND_TOP = 64       # 灌溉目标水位

    def __init__(self):
        self.maturity_seen = None
        self.fert_done = []
        self.last_spray_day = -99

    def act(self, observation, env):
        st = env.state
        d = st.day
        g = st.gdd

        if st.stage == "成熟期":
            if self.maturity_seen is None:
                self.maturity_seen = d
            if d - self.maturity_seen >= 5:
                return "harvest", 0, "成熟后适期收获"

        # 病虫：主动压到安全线以下，收获前 20 天停药
        if st.pest > self.SLACK and d - self.last_spray_day >= 10 and st.stage != "成熟期":
            self.last_spray_day = d
            return "spray", 0, "病虫指数超阈值"

        # 水分
        drainage = DRAINAGE_WINDOW[0] <= g <= DRAINAGE_WINDOW[1]
        if drainage:
            pass          # 晒田期严格停灌，靠降水与蒸散自然落干
        elif st.stage != "成熟期":
            next_rain = sum(w["rain"] for w in env.weather[st.day: st.day + 3])
            if st.swc < self.BAND_LOW and next_rain < 6:
                return "irrigate", min(30, self.BAND_TOP - st.swc), "水位低于适宜区间且近期无雨"

        # 追肥：三次计划 + 缺氮补救
        for i, (g0, g1, amount) in enumerate(RuleAgent.FERT_PLAN):
            if i not in self.fert_done and g0 <= g <= g1:
                self.fert_done.append(i)
                return "fertilize", amount, "按生育期追肥"
        if st.n_soil < 1.2 and st.stage in ("分蘖期", "拔节孕穗期", "抽穗扬花期"):
            return "fertilize", 5, "氮素偏低，追肥"

        return "wait", 0, "状态良好"


# ---------------------------------------------------------------- LLM 接口

SYSTEM_PROMPT = """你是浙北杭嘉湖平原的水稻种植决策助手，负责管理一块单季晚稻田（约 1 亩）。

你每天做一次决策，动作当天生效，然后环境推进一天。你只能看到粗略的等级信息；
若需要精确数据，可以执行 observe（花费 8 元），当天即可拿到带测量误差的精确值。

关键农事（按有效积温 GDD 判断，不是按固定日期）：
- 分蘖期（GDD 300-1100）：需追分蘖肥；分蘖末期（GDD 950-1150）要晒田控苗，此时灌溉属违规
- 拔节孕穗至抽穗（GDD 1100-1900）：需保持水层，缺水会显著减产
- 成熟期：及时收获，过晚掉粒
- 单次施氮超过 12 kg/亩属违规；成熟期追氮属违规；收获前用药有农残风险
- 肥料会被大雨淋洗，暴雨后可能需要补施

可选动作（action）：
- irrigate: 灌溉，amount 为毫米（0-30）
- fertilize: 施氮肥，amount 为 kg/亩（0-15）
- spray: 施药，防治病虫杂草
- observe: 下田调查，获取精确数据
- wait: 不做处理
- harvest: 收获（仅成熟期）

只输出一行 JSON，不要解释：
{"action":"wait","amount":0,"reason":"简短理由"}"""


class LLMAgent(BaseAgent):
    def __init__(self, model=None, base_url=None, api_key=None, temperature=0.2, timeout=60):
        self.model = model or os.environ.get("AGRIBENCH_MODEL", "")
        self.base_url = (base_url or os.environ.get("AGRIBENCH_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("AGRIBENCH_API_KEY", "")
        self.temperature = temperature
        self.timeout = timeout
        self.name = self.model or "LLM"
        self.calls = 0
        self.failures = 0
        if not (self.model and self.base_url and self.api_key):
            raise ValueError(
                "缺少 LLM 配置。请设置环境变量 AGRIBENCH_BASE_URL / AGRIBENCH_API_KEY / AGRIBENCH_MODEL"
            )

    def _chat(self, messages):
        import time as _time
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 320,
        }
        body = json.dumps(payload, ensure_ascii=False)
        url = self.base_url + "/chat/completions"

        last = None
        for attempt in range(6):
            try:
                req = urllib.request.Request(
                    url,
                    data=body.encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer " + self.api_key,
                    },
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception:
                # 本机 CA 链可能过期/缺失，退回 curl
                out = subprocess.check_output(
                    ["curl", "-s", "--max-time", str(self.timeout), "-X", "POST", url,
                     "-H", "Content-Type: application/json",
                     "-H", "Authorization: Bearer " + self.api_key,
                     "--data-binary", "@-"],
                    input=body.encode("utf-8"),
                )
                data = json.loads(out.decode("utf-8"))

            if "error" not in data:
                return data["choices"][0]["message"]["content"]

            err = data["error"]
            last = RuntimeError(f"{err.get('type')}: {err.get('message')}")
            blob = (str(err.get("type", "")) + str(err.get("code", ""))
                    + str(err.get("message", ""))).lower()
            if "concurrency" in blob or "rate" in blob:
                _time.sleep(min(60, 6 * (attempt + 1)))   # 限流退避
                continue
            raise last
        raise last

    def act(self, observation, env):
        self.calls += 1
        prompt = "当前田块观测：\n" + json.dumps(observation, ensure_ascii=False)
        try:
            raw = self._chat([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
            return self._parse(raw)
        except Exception as exc:
            self.failures += 1
            return "wait", 0, f"调用失败：{type(exc).__name__}"

    @staticmethod
    def _parse(raw):
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                obj = json.loads(text[start:end + 1])
                action = str(obj.get("action", "wait")).strip().lower()
                amount = float(obj.get("amount", 0) or 0)
                if action not in ("irrigate", "fertilize", "spray", "observe", "wait", "harvest"):
                    return "wait", 0, "动作非法，退回等待"
                return action, amount, str(obj.get("reason", ""))[:80]
            except Exception:
                pass
        # 兜底：正则抓动作名与数字
        m = re.search(r'"action"\s*:\s*"(\w+)"', text)
        if m and m.group(1).lower() in ("irrigate", "fertilize", "spray", "observe",
                                        "wait", "harvest"):
            a = re.search(r'"amount"\s*:\s*([\d.]+)', text)
            return m.group(1).lower(), float(a.group(1)) if a else 0, "正则兜底解析"
        if os.environ.get("AGRIBENCH_DEBUG"):
            print("[raw]", repr(raw[:300]), flush=True)
        return "wait", 0, "解析失败，退回等待"


# ---------------------------------------------------------------- 工厂

def build_agent(kind, **kwargs):
    table = {
        "random": RandomAgent,
        "naive": NaiveAgent,
        "rule": RuleAgent,
        "rule_forecast": ForecastRuleAgent,
        "oracle": OracleAgent,
        "llm": LLMAgent,
    }
    if kind not in table:
        raise ValueError(f"unknown agent kind: {kind}")
    return table[kind](**kwargs)
