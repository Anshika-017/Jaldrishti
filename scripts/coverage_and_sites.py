"""Coverage of Delhi within R km of stations (clipped to the boundary) and greedy new-station sites.
Usage: python scripts/coverage_and_sites.py path/to/delhi.geojson"""
import sys, json, numpy as np, pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely import contains_xy
LO0, LA0, KX, KY = 76.83, 28.89, 97.7, 111.2        # same local km frame as the dashboard
xy = lambda lo, la: ((lo - LO0) * KX, (LA0 - la) * KY)
g = json.load(open(sys.argv[1])); geo = g["features"][0]["geometry"] if g["type"] == "FeatureCollection" else g.get("geometry", g)
polys = geo["coordinates"] if geo["type"] == "MultiPolygon" else [geo["coordinates"]]
D = unary_union([Polygon([xy(x, y) for x, y, *_ in p[0]]) for p in polys])
gx, gy = np.meshgrid(np.arange(0.25, 60, 0.5), np.arange(0.25, 60, 0.5)); gx, gy = gx.ravel(), gy.ravel()
m = contains_xy(D, gx, gy); gx, gy = gx[m], gy[m]
F = pd.read_csv("data/stations_final.csv")
def cov(df, R):
    c = np.zeros(len(gx), bool)
    for lo, la in zip(df.lon, df.lat):
        a, b = xy(lo, la); c |= (gx - a) ** 2 + (gy - b) ** 2 <= R ** 2
    return c
O = F[F.source.str.startswith("Delhi")]; rel = F.tier == "reliable"
print("radius_km | orig9 reliable | expanded reliable | orig9 all | expanded all   (share of Delhi area)")
for R in (3, 5, 8):
    print(R, *["%.1f%%" % (cov(s, R).mean() * 100) for s in (O[O.tier == "reliable"], F[rel], O, F)])
cur = cov(F[rel], 5); cx, cy = np.meshgrid(np.arange(0.5, 60, 1.0), np.arange(0.5, 60, 1.0)); cx, cy = cx.ravel(), cy.ravel()
ok = contains_xy(D, cx, cy); cx, cy = cx[ok], cy[ok]; out = []
for k in range(5):
    gains = [((~cur) & ((gx - a) ** 2 + (gy - b) ** 2 <= 25)).sum() for a, b in zip(cx, cy)]
    i = int(np.argmax(gains)); a, b = cx[i], cy[i]; cur |= (gx - a) ** 2 + (gy - b) ** 2 <= 25
    out.append((k + 1, round(LA0 - b / KY, 4), round(LO0 + a / KX, 4), round(gains[i] * 0.25), round(cur.mean() * 100, 1)))
P = pd.DataFrame(out, columns=["rank", "lat", "lon", "new_km2", "coverage_after_pct"]); P.to_csv("data/recommended_sites_computed.csv", index=False); print(P.to_string(index=False))
