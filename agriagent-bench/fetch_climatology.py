#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_climatology.py —— 抓取 2016-2025 十年实况（ERA5），用于「环境层年际稳健性校验」。

定位说明：
  真实历史 EC 预报的公开存档只到 2024-03，因此 LLM 主实验无法覆盖十年。
  但实况（ERA5）可回溯到 1940 年，成本极低，可用来回答：
  「评分体系在不同年型下是否稳定？会不会某一年所有策略都被判死/判活？」

输出：data/clim/weather_<site>_<year>.json
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_weather import SITES, fetch  # noqa: E402

YEARS = list(range(2016, 2026))   # 2016–2025，十年
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "clim")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = []
    for site, (lat, lon) in SITES.items():
        for year in YEARS:
            start, end = f"{year}-05-01", f"{year}-10-31"
            payload = fetch(lat, lon, start, end)
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
            path = os.path.join(OUT_DIR, f"weather_{site}_{year}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"site": site, "lat": payload["latitude"], "lon": payload["longitude"],
                           "elevation": payload["elevation"], "year": year,
                           "source": "ERA5 via Open-Meteo Archive API",
                           "records": records}, f, ensure_ascii=False, indent=2)
            rain = sum(r["rain"] or 0 for r in records)
            et0 = sum(r["et0"] or 0 for r in records)
            tmean = sum(r["tmean"] or 0 for r in records) / len(records)
            summary.append({"site": site, "year": year, "rain_mm": round(rain),
                            "et0_mm": round(et0), "tmean": round(tmean, 1)})
            print(f"{site} {year}: rain={rain:.0f} et0={et0:.0f} tmean={tmean:.1f}", flush=True)
            time.sleep(0.3)

    path = os.path.join(OUT_DIR, "season_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n-> {path}")


if __name__ == "__main__":
    main()
