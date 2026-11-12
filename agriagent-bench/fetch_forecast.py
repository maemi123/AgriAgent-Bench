#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_forecast.py —— 抓取「当时真实起报」的 EC 预报，构造无未来泄漏的滚动预报。

数据源：Open-Meteo Previous Runs API
  - 变量后缀 _previous_dayK = 「有效期前 K 天发布的预报」，K = 1..7
  - 因此「t 日发布的 7 天预报」= 对有效期 d = t+1..t+7 分别取 _previous_day(K=d-t)
  - 一次请求即可拿到整季全部时效，无需逐日起报

模型：ecmwf_ifs025（ECMWF IFS 0.25°），存档自 2024-03 起
输出：data/forecast_<site>_<year>.json
"""

import json
import os
import subprocess
import urllib.parse

BASE = "https://previous-runs-api.open-meteo.com/v1/forecast"
MODEL = "ecmwf_ifs025"
LEADS = 7

SITES = {
    "huzhou_nanxun": (30.87, 120.09),
    "jiaxing_tongxiang": (30.63, 120.56),
    "hangzhou_yuhang": (30.42, 120.30),
}
YEARS = [2024, 2025, 2026]
SEASON = ("05-01", "10-31")
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# 基础变量 -> 聚合方式（辐射/ET0 仅 EC 有；JMA 只提供前三项，够环境用）
VARS_FULL = ["precipitation", "temperature_2m", "relative_humidity_2m",
             "shortwave_radiation", "et0_fao_evapotranspiration"]
VARS_BASIC = ["precipitation", "temperature_2m", "relative_humidity_2m"]
VARS = VARS_FULL


def http_get(url, timeout=300):
    """优先 urllib，失败回退 curl（本机 Python CA 证书过期）。"""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read().decode("utf-8")
    except Exception:
        out = subprocess.check_output(["curl", "-s", "--max-time", str(timeout), url])
        return out.decode("utf-8")


def build_url(lat, lon, start, end):
    params = []
    for v in VARS:
        for k in range(1, LEADS + 1):
            params.append(f"{v}_previous_day{k}")
    q = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": ",".join(params),
        "models": MODEL,
        "timezone": "Asia/Shanghai",
    }
    return BASE + "?" + urllib.parse.urlencode(q)


def shift_date(iso, days):
    import datetime
    d = datetime.date.fromisoformat(iso) + datetime.timedelta(days=days)
    return d.isoformat()


def aggregate(payload):
    """把逐时 × 7 时效聚合成 {lead: {date: {rain,tmax,tmin,rh,rad,et0}}}"""
    h = payload["hourly"]
    times = h["time"]
    # 按本地日期分桶
    day_idx = {}
    for i, ts in enumerate(times):
        d = ts[:10]
        day_idx.setdefault(d, []).append(i)

    out = {}
    for k in range(1, LEADS + 1):
        per_day = {}
        for d, idxs in day_idx.items():
            def vals(name):
                key = f"{name}_previous_day{k}"
                arr = h.get(key)
                if arr is None:
                    return []
                return [arr[i] for i in idxs if arr[i] is not None]

            rain = vals("precipitation")
            temp = vals("temperature_2m")
            rh = vals("relative_humidity_2m")
            rad = vals("shortwave_radiation")
            et0 = vals("et0_fao_evapotranspiration")

            if len(rain) < 12:      # 该日数据不足，视为缺失
                continue
            per_day[d] = {
                "rain": round(sum(rain), 1),
                "tmax": round(max(temp), 1) if temp else None,
                "tmin": round(min(temp), 1) if temp else None,
                "rh": round(sum(rh) / len(rh)) if rh else None,
                "rad": round(sum(rad) * 3600 / 1e6, 2) if rad else None,
                "et0": round(sum(et0), 2) if et0 else None,
            }
        out[k] = per_day
    return out


def main():
    global MODEL, YEARS, VARS, LEADS
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--years", nargs="*", type=int, default=YEARS)
    ap.add_argument("--suffix", default="", help="文件名后缀，如 jma → forecast_jma_<site>_<year>.json")
    ap.add_argument("--sites", nargs="*", default=list(SITES))
    ap.add_argument("--leads", type=int, default=LEADS)
    args = ap.parse_args()
    MODEL, YEARS, LEADS = args.model, args.years, args.leads
    VARS = VARS_FULL if MODEL.startswith("ecmwf") else VARS_BASIC
    sites = {k: v for k, v in SITES.items() if k in args.sites}

    os.makedirs(OUT_DIR, exist_ok=True)
    for site, (lat, lon) in sites.items():
        for year in YEARS:
            s = f"{year}-{SEASON[0]}"
            e = shift_date(f"{year}-{SEASON[1]}", LEADS + 2)
            # 为保证 season 第一天也有 lead-7 数据，向前多取 7 天
            fetch_s = shift_date(s, -LEADS)
            url = build_url(lat, lon, fetch_s, e)
            print(f"[{site} {year}] fetching {fetch_s} -> {e} ...", flush=True)
            raw = http_get(url, timeout=900)
            payload = json.loads(raw)
            if payload.get("error"):
                print("  ERROR:", payload.get("reason"))
                continue

            leads = aggregate(payload)

            days = []
            d = s
            while d <= f"{year}-{SEASON[1]}":
                days.append(d)
                d = shift_date(d, 1)

            forecast = {}
            for t in days:
                window = []
                for k in range(1, LEADS + 1):
                    d = shift_date(t, k)
                    rec = leads[k].get(d)
                    if rec:
                        window.append({"date": d, **rec})
                if len(window) == LEADS:
                    forecast[t] = window

            doc = {
                "site": site,
                "lat": lat,
                "lon": lon,
                "year": year,
                "model": MODEL,
                "source": f"{MODEL} via Open-Meteo Previous Runs API",
                "leads": LEADS,
                "issued_at": "00 UTC (= 08:00 Asia/Shanghai) on decision day",
                "window": f"lead {LEADS}: valid dates t+1 .. t+{LEADS}",
                "n_days": len(forecast),
                "forecast": forecast,
            }
            tag = f"_{args.suffix}" if args.suffix else ""
            path = os.path.join(OUT_DIR, f"forecast{tag}_{site}_{year}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(doc, f, ensure_ascii=False)
            print(f"  -> {os.path.basename(path)}  ({len(forecast)} 天有完整 7 天预报)")


if __name__ == "__main__":
    main()
