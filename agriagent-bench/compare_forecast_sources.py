"""对比不同预报源（EC / JMA）在同一批年份上的技巧与基线表现。

用法：
    python compare_forecast_sources.py            # 默认比 2022（仅 JMA 有）
"""

import json
import os
import statistics as st

from agents import build_agent
from env import PaddyEnv

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SITES = ["huzhou_nanxun", "jiaxing_tongxiang", "hangzhou_yuhang"]


def skill(site, year, tag):
    """预报各时效的降水相关系数 / MAE（对 ERA5 实况）。"""
    wpath = os.path.join(DATA, f"weather_era5_{site}_{year}.json")
    if not os.path.exists(wpath):
        wpath = os.path.join(DATA, f"weather_{site}_{year}.json")
    fname = f"forecast_{tag}_{site}_{year}.json" if tag else f"forecast_{site}_{year}.json"
    fpath = os.path.join(DATA, fname)
    if not (os.path.exists(wpath) and os.path.exists(fpath)):
        return None
    obs = {r["date"]: r for r in json.load(open(wpath, encoding="utf-8"))["records"]}
    fc = json.load(open(fpath, encoding="utf-8"))["forecast"]
    out = {}
    for k in range(1, 8):
        fo, ob = [], []
        for t, win in fc.items():
            if len(win) < k:
                continue
            d = win[k - 1]["date"]
            o = obs.get(d)
            if not o or o["rain"] is None:
                continue
            fo.append(win[k - 1]["rain"])
            ob.append(o["rain"])
        if len(fo) < 30:
            continue
        mae = st.mean(abs(a - b) for a, b in zip(fo, ob))
        try:
            r = st.correlation(fo, ob)
        except Exception:
            r = float("nan")
        out[k] = (mae, r)
    return out


def baselines(site, year, tag):
    wpath = os.path.join(DATA, f"weather_era5_{site}_{year}.json")
    if not os.path.exists(wpath):
        wpath = os.path.join(DATA, f"weather_{site}_{year}.json")
    fpath = os.path.join(DATA, f"forecast_{tag}_{site}_{year}.json") if tag else None
    if not os.path.exists(fpath or ""):
        fpath = None
    rows = {}
    for kind in ["oracle", "rule_forecast", "rule", "naive", "random"]:
        a = build_agent(kind, **({"seed": 0} if kind == "random" else {}))
        env = PaddyEnv(wpath, forecast_path=fpath, seed=0, forecast_days=7)
        a.reset()
        while not env.state.done:
            act, amt, rs = a.act(env.get_observation(), env)
            env.step(act, amt, rs)
        rows[kind] = env.score()
    return rows


if __name__ == "__main__":
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2022
    tags = sys.argv[2:] or ["jma", ""]

    print(f"=== {year} 年：预报技巧对比（对 ERA5 实况，三站点平均）===")
    print(f"{'预报源':<12}{'1天 r':>9}{'3天 r':>9}{'5天 r':>9}{'7天 r':>9}{'7天 MAE':>10}")
    for tag in tags:
        per = [skill(s, year, tag) for s in SITES]
        per = [p for p in per if p]
        if not per:
            print(f"{(tag or 'ecmwf'):<12} 数据缺失")
            continue
        def rr(k):
            vals = [p[k][1] for p in per if k in p]
            return st.mean(vals) if vals else float("nan")
        def mm(k):
            vals = [p[k][0] for p in per if k in p]
            return st.mean(vals) if vals else float("nan")
        print(f"{(tag or 'ecmwf'):<12}{rr(1):>9.3f}{rr(3):>9.3f}{rr(5):>9.3f}{rr(7):>9.3f}{mm(7):>10.2f}")

    print(f"\n=== {year} 年：五条基线（三站点，单种子）===")
    print(f"{'预报源':<10}{'策略':<14}{'产量':>8}{'净收益':>10}{'成本':>9}{'违规':>7}{'总分':>8}")
    for tag in tags:
        for s in SITES:
            try:
                rows = baselines(s, year, tag)
            except Exception as exc:
                print(f"{(tag or 'ecmwf'):<10}{s:<14} ERR {exc}")
                continue
            for k in ["oracle", "rule_forecast", "rule", "naive", "random"]:
                r = rows[k]
                print(f"{(tag or 'ecmwf'):<10}{s[:12]:<14}{r['yield_kg_mu']:>8.1f}"
                      f"{r['net_profit']:>10.1f}{r['cost']:>9.1f}{r['violations']:>7.1f}"
                      f"{r['score_total']:>8.1f}")
