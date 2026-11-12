"""抓取浙北地区历史气象数据（ERA5-Land 再分析，经 Open-Meteo 分发）。

输出：data/weather_<site>_<year>.json
用途：作为 AgriAgent-Bench 农场模拟环境的外生天气驱动。
"""

import json
import os
import time
import urllib.request
import urllib.parse

# 浙北杭嘉湖平原三个代表点位（水稻主产区）
SITES = {
    "huzhou_nanxun": (30.87, 120.09),   # 湖州南浔：杭嘉湖平原东部
    "jiaxing_tongxiang": (30.63, 120.56),  # 嘉兴桐乡：浙北平原中部
    "hangzhou_yuhang": (30.42, 120.30),   # 杭州余杭：杭州北部
}

# 三个生长季：与历史 EC 预报存档窗口（2024-03 起）对齐
YEARS = [2024, 2025, 2026]

# 实况源固定为 ERA5（0.25°）。
# 注意：ERA5-Land 的降水在本数据源已不再提供 2024 年及以后的值（返回 None），
# 为保证三年同源可比，统一改用 ERA5。
MODEL = "era5"

DAILY_VARS = ",".join([
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "relative_humidity_2m_mean",
    "wind_speed_10m_max",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
])

BASE = "https://archive-api.open-meteo.com/v1/archive"


def http_get(url):
    """优先用标准库，SSL 证书异常时回退到 curl（跨机器可复现）。"""
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        import subprocess
        out = subprocess.check_output(["curl", "-s", "--max-time", "60", url])
        return out.decode("utf-8")


def fetch(lat, lon, start, end, model=None):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": DAILY_VARS,
        "models": model or MODEL,
        "timezone": "Asia/Shanghai",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    return json.loads(http_get(url))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int, default=YEARS)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--sites", nargs="*", default=list(SITES))
    args = ap.parse_args()

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(out_dir, exist_ok=True)
    sites = {k: v for k, v in SITES.items() if k in args.sites}

    for site, (lat, lon) in sites.items():
        for year in args.years:
            # 单季晚稻生长季：5 月 1 日 — 10 月 31 日
            start, end = f"{year}-05-01", f"{year}-10-31"
            payload = fetch(lat, lon, start, end, model=args.model)
            daily = payload["daily"]

            records = []
            for i, date in enumerate(daily["time"]):
                records.append({
                    "date": date,
                    "tmax": daily["temperature_2m_max"][i],
                    "tmin": daily["temperature_2m_min"][i],
                    "tmean": daily["temperature_2m_mean"][i],
                    "rain": daily["precipitation_sum"][i],
                    "rh": daily["relative_humidity_2m_mean"][i],
                    "wind": daily["wind_speed_10m_max"][i],
                    "rad": daily["shortwave_radiation_sum"][i],
                    "et0": daily["et0_fao_evapotranspiration"][i],
                })

            tag = f"_{args.suffix}" if args.suffix else ""
            path = os.path.join(out_dir, f"weather{tag}_{site}_{year}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "site": site,
                    "lat": payload["latitude"],
                    "lon": payload["longitude"],
                    "elevation": payload["elevation"],
                    "year": year,
                    "source": f"{(args.model or MODEL).upper()} via Open-Meteo Archive API",
                    "records": records,
                }, f, ensure_ascii=False, indent=2)

            total_rain = sum(r["rain"] for r in records)
            print(f"{site} {year}: {len(records)} days, rain={total_rain:.0f}mm -> {path}")
            time.sleep(0.4)


if __name__ == "__main__":
    main()
