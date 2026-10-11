# JalDrishti: how much of Delhi does groundwater monitoring actually cover?

Built for **Environmental Hacks, Bharat Builds Tour** (Heat and Water track).
Live demo (AWS Lambda Function URL): https://rkwrwlztdmr6ncc2by4pnmvan40wimio.lambda-url.ap-southeast-2.on.aws/

JalDrishti is a decision-support map. It shows where Delhi's groundwater telemetry stations are, how much of the city lies within a chosen distance of one, where there is no monitoring data, and where new stations would add the most coverage. It does **not** predict water shortage or tanker demand.

## Findings (all computed by the scripts in `scripts/`)
- Two government telemetry datasets were cleaned and combined into **38 stations**, each tiered **reliable (24)** or **caution (14)**.
- Within 5 km of a station (clipped to the boundary used here): the original 9 stations cover **22.8%** of Delhi (reliable only); the expanded reliable network covers **57.3%**. Counting caution stations too: 29.4% to 70.4%.
- Five suggested new station positions, chosen to cover the most uncovered area, would raise reliable coverage from 57.3% to **82.0%**. These are map positions only, not checked for feasibility.
- Leave-one-out check on 24 reliable stations: a station's nearest neighbour differs in median depth by about **3 m within 5 km** and about **7.5 m at 5 to 10 km** (the trend is not statistically significant, n = 24). "Covered" means a station is nearby, not that conditions at that spot are known.
- 2026 monsoon: of 18 stations with data before and after, **12 rose** (shallower), 4 fell, 2 were unchanged. The three deepest-water stations (Pusa, Vivek Vihar, Kabulline, 25 to 29 m) showed no recovery; the reason is unexplained.
- 2026 seasonal pattern: regional groundwater depth was deepest in July and recovered by September, after a hot, dry April to June (NASA POWER). This is a seasonal pattern, **not** evidence that heat caused it: heat, missing rain and pumping coincide.
- 16 of 50 May-2022 water-quality samples that exceed a report threshold lie more than 5 km from any reliable station. Poor-quality samples were not more likely than others to fall in monitoring gaps.

## Data cleaning (what was wrong with the raw files)
- Older file (173,132 rows): about 65% zeros, 999 missing-value codes, negative values to -847, corrupted longitudes (decimal point lost), unreliable district labels. About 11% of rows survived basic filtering.
- 2026 CGWB file: the value 26.844 repeated 1,269 times from May 2026 (a stuck reading); one station constant at 26.840. These were removed before computing daily medians.
- Rules: keep 0 < level < 100; daily median per station; drop days more than 3 m from a 15-day rolling median; tier by days of data, flat readings and repeated values.

## Architecture (AWS)
- **S3** (private bucket): `stations_final.json` and `dashboard.html`.
- **Lambda** (`aws/lambda_function.py`, Python): with no parameters it serves the dashboard from S3; with `?lat=&lon=&radius=` it returns the nearest station, distance, tier and whether the point is covered.
- **Lambda Function URL** (public, no auth): the single endpoint for page and lookup.
- Environment variable `BUCKET` names the bucket. The function role needs read access to it.

## Limitations
- The Delhi boundary (117 vertices) came from a third-party GitHub compilation; its source, date and licence are unverified. Treat coverage percentages as provisional.
- Depth units are probably metres below ground (water level rose after the monsoon at 12 of 18 stations) but are not confirmed against CGWB documentation.
- The original 9 stations cover 2024 to 2025; the CGWB stations cover Jan to Oct 2026. Absolute depths across the two datasets are not compared and the time series are not merged.
- The 5 km radius is an assumption (adjustable on the page). Most stations have one to two years of data, so no multi-year trend can be claimed.
- Water-quality points are May 2022 samples, not current quality.
- NASA POWER is a gridded model estimate at one point, not a station; days at or above 40 C is a simple threshold, not the IMD heatwave definition.
- A coverage gap does not mean no groundwater or no water access.

## Reproduce
```
pip install -r requirements.txt
python scripts/build_stations.py   data/raw/gwl_tel_6_hourly_cgwb_dl_2026_2030.csv
python scripts/coverage_and_sites.py data/raw/delhi.geojson
python scripts/quality_samples.py  data/raw/17091922641670497393file.pdf   # needs poppler (pdftotext)
python scripts/fetch_heat.py
```
Raw inputs are not included. Sources: National Water Data Portal groundwater telemetry (Delhi, CGWB 2026 to 2030 and Delhi SW/GW 2021 to 2025); CGWB, "Ground Water Quality in Shallow Aquifers of NCT of Delhi (AAP 2023-24)"; NASA POWER daily API.
The older Delhi SW/GW file was cleaned with the same rules; its nine selected stations are listed in `scripts/build_stations.py`.

## Files
- `aws/` Lambda function and dashboard page
- `data/` station inventory, 2022 quality samples, recommended sites, cleaned daily 2026 readings
- `scripts/` cleaning, coverage and site selection, PDF extraction, heat download
