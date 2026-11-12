"""AgriAgent-Bench 初步实验（pilot）：五条基线 × 三站点 × 三个生长季。

用法：
    python run_pilot.py                      # 默认 7 天预报时效
    python run_pilot.py --forecast-days 3    # 信息量消融
    python run_pilot.py --no-forecast        # 退回合成扰动（仅作对照）
    python run_pilot.py --llm <模型名>       # 追加一个 LLM（需配置环境变量）

输出：
    results/pilot_results_lead<N>.json   原始结果
    results/pilot_summary_lead<N>.json   汇总指标
"""

import argparse
import json
import os
import statistics
import sys

from env import PaddyEnv
from agents import build_agent

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "results")

SITES = ["huzhou_nanxun", "jiaxing_tongxiang", "hangzhou_yuhang"]
# 与历史 EC 预报存档窗口（2024-03 起）对齐
YEARS = [2024, 2025, 2026]
AGENTS = ["naive", "random", "rule", "rule_forecast", "oracle"]
SEEDS = [0, 1, 2]
MAX_STEPS = 400


def run_episode(agent, weather_path, seed, forecast_path=None, forecast_days=7):
    env = PaddyEnv(weather_path, forecast_path=forecast_path, seed=seed,
                   forecast_days=forecast_days)
    agent.reset()
    trace = []
    steps = 0
    while not env.state.done and steps < MAX_STEPS:
        obs = env.get_observation()
        action, amount, reason = agent.act(obs, env)
        _, done = env.step(action, amount, reason)
        trace.append({
            "day": env.state.day,
            "gdd": round(env.state.gdd),
            "stage": env.state.stage,
            "swc": round(env.state.swc, 1),
            "n_soil": round(env.state.n_soil, 2),
            "biomass": round(env.state.biomass, 3),
            "pest": round(env.state.pest, 3),
            "cost": round(env.state.cost, 1),
            "action": action,
            "amount": round(float(amount or 0), 1),
            "reason": str(reason)[:40],
        })
        steps += 1
    return env.score(), trace


def summarize(runs):
    """按 agent 聚合。"""
    table = {}
    for r in runs:
        table.setdefault(r["agent"], []).append(r)

    out = {}
    for agent, items in table.items():
        def avg(key):
            return round(statistics.mean(i["score"][key] for i in items), 2)

        actions = {}
        for i in items:
            for t in i["trace"]:
                actions[t["action"]] = actions.get(t["action"], 0) + 1
        total_actions = sum(actions.values()) or 1

        n_irr = sum(1 for i in items for t in i["trace"] if t["action"] == "irrigate")
        n_spray = sum(1 for i in items for t in i["trace"] if t["action"] == "spray")
        n_obs = sum(1 for i in items for t in i["trace"] if t["action"] == "observe")
        n_fert = sum(1 for i in items for t in i["trace"] if t["action"] == "fertilize")
        out[agent] = {
            "n_runs": len(items),
            "yield_kg_mu": avg("yield_kg_mu"),
            "net_profit": avg("net_profit"),
            "cost": avg("cost"),
            "violations": avg("violations"),
            "pest_peak": avg("pest_peak"),
            "score_yield": avg("score_yield"),
            "score_profit": avg("score_profit"),
            "score_rule": avg("score_rule"),
            "score_process": avg("score_process"),
            "score_total": avg("score_total"),
            "action_dist": {k: round(v / total_actions, 3) for k, v in sorted(actions.items())},
            "per_run": {"irrigate": round(n_irr / len(items), 1),
                        "fertilize": round(n_fert / len(items), 1),
                        "spray": round(n_spray / len(items), 1),
                        "observe": round(n_obs / len(items), 1)},
        }
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", default=None, help="额外跑一个 LLM，传入模型名")
    parser.add_argument("--forecast-days", type=int, default=7,
                        help="预报时效（3/5/7），用于信息量消融实验")
    parser.add_argument("--no-forecast", action="store_true",
                        help="不使用真实历史预报，退回合成扰动（仅作对照）")
    args = parser.parse_args()

    os.makedirs(OUT, exist_ok=True)
    agent_kinds = list(AGENTS)
    if args.llm:
        agent_kinds.append("llm")

    runs = []
    for site in SITES:
        for year in YEARS:
            path = os.path.join(DATA, f"weather_{site}_{year}.json")
            if not os.path.exists(path):
                print(f"[skip] 缺气象文件 {path}", file=sys.stderr)
                continue
            fpath = os.path.join(DATA, f"forecast_{site}_{year}.json")
            if args.no_forecast or not os.path.exists(fpath):
                fpath = None
            for kind in agent_kinds:
                for seed in SEEDS:
                    kwargs = {}
                    if kind == "random":
                        kwargs["seed"] = seed
                    elif kind == "llm":
                        kwargs["model"] = args.llm
                    elif kind == "rule_forecast":
                        kwargs["lead"] = args.forecast_days
                    agent = build_agent(kind, **kwargs)
                    score, trace = run_episode(agent, path, seed, fpath,
                                               args.forecast_days)
                    runs.append({
                        "site": site, "year": year,
                        "agent": kind, "agent_name": agent.name,
                        "seed": seed, "score": score, "trace": trace,
                        "forecast_days": args.forecast_days,
                        "real_forecast": fpath is not None,
                    })
                    print(f"{site:22s} {year} {kind:7s} seed={seed} "
                          f"产量={score['yield_kg_mu']:6.1f} 总分={score['score_total']:5.1f} "
                          f"违规={score['violations']}")

    summary = summarize(runs)
    used_real_forecast = any(r["real_forecast"] for r in runs)
    suffix = f"_lead{args.forecast_days}" + ("" if used_real_forecast else "_noforecast")
    with open(os.path.join(OUT, f"pilot_results{suffix}.json"), "w", encoding="utf-8") as f:
        json.dump({"sites": SITES, "years": YEARS, "seeds": SEEDS,
                   "forecast_days": args.forecast_days, "runs": runs}, f,
                  ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, f"pilot_summary{suffix}.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n=== 汇总（三站点三年型三随机种子平均；预报时效 {args.forecast_days} 天） ===")
    header = f"{'策略':<10}{'产量':>8}{'净收益':>9}{'成本':>8}{'违规':>6}{'结果':>7}{'效益':>7}{'合规':>7}{'过程':>7}{'总分':>7}"
    print(header)
    for agent, s in summary.items():
        print(f"{s['n_runs']:>2}次 {agent:<8}"
              f"{s['yield_kg_mu']:>8.1f}{s['net_profit']:>9.1f}{s['cost']:>8.1f}"
              f"{s['violations']:>6.1f}{s['score_yield']:>7.1f}{s['score_profit']:>7.1f}"
              f"{s['score_rule']:>7.1f}{s['score_process']:>7.1f}{s['score_total']:>7.1f}")
    print(f"\n结果已写入 results/pilot_results{suffix}.json 与 pilot_summary{suffix}.json")


if __name__ == "__main__":
    main()
