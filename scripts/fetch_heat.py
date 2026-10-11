"""Daily Delhi weather from NASA POWER (gridded estimate at one point, not a station). Usage: python scripts/fetch_heat.py"""
import requests, pandas as pd
r = requests.get("https://power.larc.nasa.gov/api/temporal/daily/point", timeout=180,
    params=dict(parameters="T2M,T2M_MAX,RH2M,PRECTOTCORR", community="RE", longitude=77.21, latitude=28.61,
                start="20190101", end="20261005", format="JSON"))
r.raise_for_status()
df = pd.DataFrame(r.json()["properties"]["parameter"]); df.index = pd.to_datetime(df.index, format="%Y%m%d"); df = df.mask(df == -999)
m = df.resample("MS").agg({"T2M": "mean", "T2M_MAX": "mean", "RH2M": "mean", "PRECTOTCORR": "sum"})
m["days_max_ge_40C"] = (df["T2M_MAX"] >= 40).resample("MS").sum()   # simple threshold, not the IMD heatwave definition
df.to_csv("data/delhi_heat_daily.csv"); m.to_csv("data/delhi_heat_monthly.csv"); print(m.tail(12).round(1))
