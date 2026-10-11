"""Clean the 2026 CGWB telemetry and merge it with the original 9 stations.
Usage: python scripts/build_stations.py path/to/gwl_tel_6_hourly_cgwb_dl_2026_2030.csv"""
import sys, json, pandas as pd
RAW = sys.argv[1]
STUCK = 26.844  # repeated 1,269 times from May 2026: a stuck/default reading, not groundwater
a = pd.read_csv(RAW)
col = [c for c in a.columns if c.startswith("Groundwater Level")][0]
a = a.rename(columns={col: "level"})
a["time"] = pd.to_datetime(a["Data Acquisition Time"], format="%d-%m-%Y %H:%M")
bad = (a.level.round(3) == STUCK) | (a.Station == "Qatlupur_2") | (a.level <= 0) | (a.level >= 100)
v = a[~bad]
d = v.set_index("time").groupby("Station")["level"].resample("D").median().dropna().reset_index()
d["roll"] = d.groupby("Station")["level"].transform(lambda s: s.rolling(15, center=True, min_periods=5).median())
d = d[(d.level - d.roll).abs() < 3].drop(columns="roll")          # drop >3 m jumps from a 15-day rolling median
g = d.groupby("Station").agg(days=("level", "size"), med=("level", "median"),
        p10=("level", lambda x: x.quantile(.1)), p90=("level", lambda x: x.quantile(.9)))
g = g.join(v.groupby("Station")[["Latitude", "Longitude"]].median())
g["spread"] = g.p90 - g.p10
g["modal_share"] = v.groupby("Station")["level"].agg(lambda x: x.round(3).value_counts().iloc[0] / len(x))
def tier(r):
    why = []
    if r.days < 30: return "exclude", "fewer than 30 valid days"
    if r.days < 100: why.append("short record (%d d)" % r.days)
    if r.spread < 0.16: why.append("near-flat readings")
    if r.modal_share > 0.2 and r.days >= 100: why.append("repeated identical value (%d%% of readings)" % round(r.modal_share * 100))
    return ("caution", "; ".join(why)) if why else ("reliable", "")
g[["tier", "note"]] = g.apply(lambda r: pd.Series(tier(r)), axis=1)
# original 9 stations: older Delhi SW GW telemetry, cleaned the same way (see README)
orig = [("Alipur_4",28.799,77.137,9.325,425,"reliable",""),("Burari_2",28.756,77.196,4.630,434,"reliable",""),
 ("Khera Kalan_1",28.771,77.112,12.675,426,"reliable",""),("Sannoth Lake",28.835,77.049,9.566,327,"reliable",""),
 ("Singhola_2",28.845,77.121,17.922,427,"caution","10 m p10-p90 range"),("Tagore Garden_1",28.65757,77.120175,17.708,424,"reliable","longitude recovered"),
 ("Daurala",28.510715,76.894526,25.2,709,"reliable",""),("Mundella Kalan",28.610835,76.894722,24.75,401,"caution","near-flat readings"),
 ("Salahpur",28.516111,77.060838,25.6,399,"caution","near-flat readings")]
rows = [dict(name=n, lat=la, lon=lo, median_m=m, days=dd, tier=t, note=nt, source="Delhi SW GW telemetry 2024-25") for n, la, lo, m, dd, t, nt in orig]
for s, r in g[g.tier != "exclude"].iterrows():
    rows.append(dict(name=s, lat=round(r.Latitude, 6), lon=round(r.Longitude, 6), median_m=round(r.med, 3), days=int(r.days),
                     tier=r.tier, note=r.note, source="CGWB telemetry 2026 (Jan-Oct 7)"))
F = pd.DataFrame(rows)
F.to_csv("data/stations_final.csv", index=False)
json.dump(F.to_dict("records"), open("data/stations_final.json", "w"), indent=1)
d.to_csv("data/cgwb2026_daily_clean.csv", index=False)
print(len(F), "stations:", F.tier.value_counts().to_dict())
