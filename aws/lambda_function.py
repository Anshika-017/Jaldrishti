import json, math, os, boto3

BUCKET = os.environ.get("BUCKET", "YOUR-BUCKET-NAME")
KEY = os.environ.get("KEY", "stations_final.json")
PAGE = os.environ.get("PAGE", "dashboard.html")
_cache = {}

def s3get(key):
    return boto3.client("s3").get_object(Bucket=BUCKET, Key=key)["Body"].read()

def stations():
    if "s" not in _cache:
        _cache["s"] = json.loads(s3get(KEY))
    return _cache["s"]

def km(la1, lo1, la2, lo2):
    r = math.pi / 180
    return math.hypot((lo2 - lo1) * r * 6371 * math.cos(la1 * r), (la2 - la1) * r * 6371)

def lambda_handler(event, context):
    q = event.get("queryStringParameters") or {}
    if not q:  # no parameters: serve the dashboard page from S3
        return {"statusCode": 200, "headers": {"Content-Type": "text/html; charset=utf-8"},
                "body": s3get(PAGE).decode("utf-8")}
    try:
        lat, lon = float(q["lat"]), float(q["lon"])
        radius = float(q.get("radius", 5))
    except (KeyError, ValueError):
        return resp(400, {"error": "need numeric lat and lon, optional radius (km)"})
    if not (28.3 < lat < 29.0 and 76.7 < lon < 77.5):
        return resp(400, {"error": "point is outside the Delhi area"})
    rows = sorted(((km(lat, lon, s["lat"], s["lon"]), s) for s in stations()), key=lambda x: x[0])
    d, s = rows[0]
    rel = [(dd, ss) for dd, ss in rows if ss["tier"] == "reliable"][0]
    return resp(200, {
        "nearest_station": s["name"], "distance_km": round(d, 2),
        "median_depth_m": s["median_m"], "tier": s["tier"], "note": s["note"],
        "source": s["source"], "radius_km": radius, "covered": d <= radius,
        "nearest_reliable": rel[1]["name"], "nearest_reliable_km": round(rel[0], 2),
        "covered_by_reliable": rel[0] <= radius,
    })

def resp(code, body):
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(body)}
