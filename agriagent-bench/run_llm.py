"""AgriAgent-Bench 大模型实测：让 LLM 在同一套环境里跑完整生长季。

与基线共用 env.py / 评分器，仅智能体实现不同，因此分数可直接与
随机 / 只收不管 / 农技规则 / 规则+预报 / 全知 五条基线同轴比较。

用法：
    export AGRIBENCH_BASE_URL="https://xxx/v1"
    export AGRIBENCH_API_KEY="sk-..."
    export AGRIBENCH_MODEL="deepseek-flash"
    python run_llm.py                    # 3 站点 × 3 年，每格 1 局
    python run_llm.py --workers 3        # 并发 3 路（按站点分组）
    python run_llm.py --sites huzhou_nanxun --years 2024

输出：
    results/llm_results_<model>.jsonl   逐局追加，可断点续跑
    results/llm_summary_<model>.json    汇总
"""

import argparse
import json
import os
import statistics as st
import sys
import time
from multiprocessing import Pool

from agents import LLMAgent
from env import PaddyEnv

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

SITES = ["huzhou_nanxun", "jiaxing_tongxiang", "hangzhou_yuhang"]
YEARS = [2024, 2025, 2026]


def one_episode(job):
    """跑一局完整生长季。job = (site, year, seed, forecast_days, tag)"""
    site, year, seed, fd, tag = job
    wpath = os.path.join(DATA, f"weather_{site}_{year}.json")
    fpath = os.path.join(DATA, f"forecast_{site}_{year}.json")
    if not os.path.exists(wpath):
        return {"error": f"缺气象 {wpath}"}

    env = PaddyEnv(wpath, forecast_path=fpath, seed=seed, forecast_days=fd)
    agent = LLMAgent()
    agent.reset()

    t0 = time.time()
    steps = 0
    while not env.state.done and steps < 260:
        obs = env.get_observation()
        action, amount, reason = agent.act(obs, env)
        env.step(action, amount, reason)
        steps += 1
    score = env.score()

    return {
        "site": site, "year": year, "seed": seed, "tag": tag,
        "model": agent.name, "forecast_days": fd,
        "steps": steps, "elapsed_s": round(time.time() - t0, 1),
        "api_calls": agent.calls, "parse_fail_or_err": agent.failures,
        "score": score,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", nargs="*", default=SITES)
    ap.add_argument("--years", nargs="*", type=int, default=YEARS)
    ap.add_argument("--seeds", nargs="*", type=int, default=[0])
    ap.add_argument("--forecast-days", type=int, default=7)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--tag", default="main")
    args = ap.parse_args()

    model = os.environ.get("AGRIBENCH_MODEL", "")
    if not model:
        sys.exit("请先设置 AGRIBENCH_MODEL / AGRIBENCH_BASE_URL / AGRIBENCH_API_KEY")
    safe = model.replace("/", "_").replace(":", "_")
    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, f"llm_results_{safe}.jsonl")
    sum_path = os.path.join(OUT, f"llm_summary_{safe}.json")

    # 年优先排序：先跑完一个年份的全部站点，便于中途出阶段性结论
    jobs = [(s, y, seed, args.forecast_days, args.tag)
            for y in args.years for s in args.sites for seed in args.seeds]

    done = set()
    rows = []
    if os.path.exists(out_path):
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                rows.append(r)
                done.add((r["site"], r["year"], r["seed"], r.get("tag")))
    todo = [j for j in jobs if (j[0], j[1], j[2], j[4]) not in done]
    print(f"模型 {model}｜计划 {len(jobs)} 局，已完成 {len(jobs) - len(todo)}，待跑 {len(todo)}",
          flush=True)

    if todo:
        with open(out_path, "a", encoding="utf-8") as fout, Pool(args.workers) as pool:
            for r in pool.imap_unordered(one_episode, todo):
                if "error" in r:
                    print("[skip]", r["error"], flush=True)
                    continue
                rows.append(r)
                fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                fout.flush()
                s = r["score"]
                print(f"{r['site']:20s} {r['year']} seed{r['seed']} "
                      f"产{s['yield_kg_mu']:6.1f} 净{s['net_profit']:8.1f} "
                      f"总分{s['score_total']:5.1f} 违规{s['violations']} "
                      f"{r['elapsed_s']:6.0f}s", flush=True)

    rows = [r for r in rows if "error" not in r]
    if not rows:
        print("无有效结果")
        return

    def avg(k):
        return round(st.mean(r["score"][k] for r in rows), 2)

    summary = {
        "model": model,
        "forecast_days": args.forecast_days,
        "n_runs": len(rows),
        "sites": sorted({r["site"] for r in rows}),
        "years": sorted({r["year"] for r in rows}),
        "yield_kg_mu": avg("yield_kg_mu"),
        "net_profit": avg("net_profit"),
        "cost": avg("cost"),
        "violations": avg("violations"),
        "pest_peak": avg("pest_peak"),
        "score_profit": avg("score_profit"),
        "score_yield": avg("score_yield"),
        "score_rule": avg("score_rule"),
        "score_process": avg("score_process"),
        "score_total": avg("score_total"),
        "score_std": round(st.pstdev([r["score"]["score_total"] for r in rows]), 2),
        "score_min": round(min(r["score"]["score_total"] for r in rows), 1),
        "score_max": round(max(r["score"]["score_total"] for r in rows), 1),
        "action_dist": {},
        "per_run": [{"site": r["site"], "year": r["year"], "seed": r["seed"],
                     "total": r["score"]["score_total"],
                     "yield": r["score"]["yield_kg_mu"],
                     "net": r["score"]["net_profit"]} for r in rows],
    }
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n=== 汇总 ===")
    print(f"产量 {summary['yield_kg_mu']:.1f} kg/亩 | 净收益 {summary['net_profit']:+.1f} 元/亩 | "
          f"成本 {summary['cost']:.1f} | 违规 {summary['violations']:.2f}")
    print(f"总分 {summary['score_total']:.1f}（{summary['score_min']:.1f}–{summary['score_max']:.1f}，"
          f"σ={summary['score_std']:.1f}）")
    print(f"写入 {out_path}")


if __name__ == "__main__":
    main()
