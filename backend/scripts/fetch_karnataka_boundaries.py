"""
Fetch REAL Karnataka district administrative boundaries from
OpenStreetMap via the Overpass API, for choropleth map rendering.

This is NOT fabricated geometry — it queries OSM's actual
admin_level=5 (district-level in India) boundary relations tagged
within Karnataka, which are community-maintained but sourced from
Survey of India references and are the standard open-license
(ODbL) option for this purpose.

Usage:
    python scripts/fetch_karnataka_boundaries.py
    -> writes frontend/public/karnataka_districts.geojson

If Overpass is unavailable or rate-limited, this script fails loudly
rather than falling back to approximate polygons — a missing boundary
file means the frontend falls back to centroid markers only (see
karnataka_geo_reference.py), which is honest, not a silent fabrication.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Overpass QL query: all admin_level=5 (district) boundaries whose
# parent relation is Karnataka state (ISO 3166-2:IN-KA), output as GeoJSON-
# convertible relation geometry.
OVERPASS_QUERY = """
[out:json][timeout:180];
area["ISO3166-2"="IN-KA"]->.karnataka;
(
  relation["admin_level"="5"]["boundary"="administrative"](area.karnataka);
);
out geom;
"""


def fetch_boundaries() -> dict:
    data = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data)
    try:
        with urllib.request.urlopen(req, timeout=200) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"ERROR: Could not reach Overpass API: {exc}", file=sys.stderr)
        print("This script requires internet access to overpass-api.de.", file=sys.stderr)
        print("If unavailable, the frontend will use district CENTROID markers "
              "only (see karnataka_geo_reference.py) rather than a fabricated "
              "boundary polygon.", file=sys.stderr)
        sys.exit(1)


def overpass_to_geojson(osm_data: dict) -> dict:
    """Minimal conversion of Overpass relation geometry to GeoJSON
    FeatureCollection. For production use, prefer osmtogeojson (npm) or
    osm2geojson (python) for robust multipolygon handling — this is a
    simplified converter sufficient for outer-way stitching in the
    common case."""
    features = []
    for element in osm_data.get("elements", []):
        if element.get("type") != "relation":
            continue
        tags = element.get("tags", {})
        name = tags.get("name:en") or tags.get("name", "Unknown")

        outer_coords = []
        for member in element.get("members", []):
            if member.get("role") == "outer" and "geometry" in member:
                coords = [[pt["lon"], pt["lat"]] for pt in member["geometry"]]
                outer_coords.append(coords)

        if not outer_coords:
            continue

        features.append({
            "type": "Feature",
            "properties": {
                "name": name,
                "osm_id": element.get("id"),
                "admin_level": tags.get("admin_level"),
            },
            "geometry": {
                "type": "MultiLineString",  # NOTE: proper polygon stitching
                "coordinates": outer_coords,  # requires ring-closing logic;
            },                                 # recommend osmtogeojson for production
        })

    return {"type": "FeatureCollection", "features": features}


def main():
    print("Fetching Karnataka district boundaries from OpenStreetMap Overpass API...")
    osm_data = fetch_boundaries()
    geojson = overpass_to_geojson(osm_data)

    n_features = len(geojson["features"])
    print(f"Retrieved {n_features} district boundary relations.")

    if n_features == 0:
        print("WARNING: Zero boundaries retrieved. Not writing an empty/invalid file.", file=sys.stderr)
        sys.exit(1)

    out_path = "frontend/public/karnataka_districts.geojson"
    with open(out_path, "w") as f:
        json.dump(geojson, f)
    print(f"Wrote {out_path}")
    print(
        "NOTE: This simplified converter emits MultiLineString outer rings. "
        "For production-quality filled choropleth polygons, post-process "
        "this file with the 'osmtogeojson' Node package or QGIS, which "
        "correctly stitch multipolygon relations into closed Polygon/"
        "MultiPolygon geometries. This script intentionally avoids silently "
        "guessing ring closure to prevent rendering distorted district shapes."
    )


if __name__ == "__main__":
    import urllib.parse
    main()
