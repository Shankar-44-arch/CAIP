import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { KARNATAKA_STATE_CENTER, KARNATAKA_DISTRICT_CENTROIDS } from '@/services/karnatakaGeo';

interface DistrictRankingItem {
  district_code: string;
  district_name: string;
  total_ipc_crimes: number;
  z_score_vs_state_mean: number;
  elevated: boolean;
}

interface Props {
  ranking: DistrictRankingItem[];
}

/**
 * KarnatakaChoroplethMap
 * ------------------------
 * Renders Karnataka districts as a CHOROPLETH (color-shaded district
 * areas), NOT a point-based heatmap. This is a deliberate, honest
 * design choice: our data is annual district-TOTAL crime counts, not
 * geocoded individual incidents, so a point heatmap (which implies
 * "this exact spot had a crime") would misrepresent the data's actual
 * grain.
 *
 * If frontend/public/karnataka_districts.geojson exists (fetched via
 * scripts/fetch_karnataka_boundaries.py), district polygons are shaded
 * by crime_rate. If not, falls back to circle markers at district HQ
 * centroids sized/colored by crime total — still honest, just less
 * visually rich.
 */
export default function KarnatakaChoroplethMap({ ranking }: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const [geoJsonAvailable, setGeoJsonAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    if (!mapRef.current || mapInstance.current) return;
    const map = L.map(mapRef.current).setView(KARNATAKA_STATE_CENTER, 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 12,
      minZoom: 6,
    }).addTo(map);
    mapInstance.current = map;
    return () => { map.remove(); mapInstance.current = null; };
  }, []);

  useEffect(() => {
    const map = mapInstance.current;
    if (!map || ranking.length === 0) return;

    const byCode = new Map(ranking.map((r) => [r.district_code, r]));
    const maxCrime = Math.max(...ranking.map((r) => r.total_ipc_crimes));

    const colorFor = (count: number) => {
      const intensity = count / maxCrime;
      if (intensity > 0.75) return '#B91C1C';
      if (intensity > 0.5) return '#EA580C';
      if (intensity > 0.25) return '#D97706';
      return '#16A34A';
    };

    let cleanupFns: (() => void)[] = [];

    fetch('/karnataka_districts.geojson')
      .then((res) => {
        if (!res.ok) throw new Error('geojson not found');
        return res.json();
      })
      .then((geojson) => {
        setGeoJsonAvailable(true);
        const layer = L.geoJSON(geojson, {
          style: (feature) => {
            const match = byCode.get(feature?.properties?.district_code);
            return {
              fillColor: match ? colorFor(match.total_ipc_crimes) : '#374151',
              fillOpacity: 0.65,
              color: '#1F2937',
              weight: 1,
            };
          },
          onEachFeature: (feature, lyr) => {
            const match = byCode.get(feature?.properties?.district_code);
            if (match) {
              lyr.bindPopup(
                `<strong>${match.district_name}</strong><br/>` +
                `Total IPC crimes: ${match.total_ipc_crimes}<br/>` +
                `Z-score vs state mean: ${match.z_score_vs_state_mean}` +
                (match.elevated ? '<br/><span style="color:#B91C1C">⚠ Statistically elevated</span>' : '')
              );
            }
          },
        }).addTo(map);
        cleanupFns.push(() => layer.remove());
      })
      .catch(() => {
        // Honest fallback — centroid markers, not fabricated polygons
        setGeoJsonAvailable(false);
        const markers: L.CircleMarker[] = [];
        ranking.forEach((r) => {
          const centroid = KARNATAKA_DISTRICT_CENTROIDS[r.district_code];
          if (!centroid) return;
          const [lat, lng] = centroid;
          // Guards against GRP (Government Railway Police) and any
          // other non-geographic jurisdiction, whose centroid is
          // intentionally [null, null, ...] — see
          // data/karnataka_geo_reference.py for why.
          if (lat === null || lng === null) return;
          const marker = L.circleMarker([lat, lng], {
            radius: 8 + 12 * (r.total_ipc_crimes / maxCrime),
            color: colorFor(r.total_ipc_crimes),
            fillColor: colorFor(r.total_ipc_crimes),
            fillOpacity: 0.6,
            weight: 2,
          }).bindPopup(
            `<strong>${r.district_name}</strong><br/>Total IPC crimes: ${r.total_ipc_crimes}`
          );
          marker.addTo(map);
          markers.push(marker);
        });
        cleanupFns.push(() => markers.forEach((m) => m.remove()));
      });

    return () => cleanupFns.forEach((fn) => fn());
  }, [ranking]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapRef} style={{ width: '100%', height: '100%', borderRadius: 6 }} />
      {geoJsonAvailable === false && (
        <div style={{
          position: 'absolute', bottom: 8, left: 8, right: 8,
          background: 'rgba(17,24,39,0.85)', color: '#E5E7EB',
          fontSize: 12, padding: '6px 10px', borderRadius: 4,
        }}>
          District boundary polygons unavailable — showing district HQ markers
          instead. Run <code>scripts/fetch_karnataka_boundaries.py</code> to
          enable full choropleth shading.
        </div>
      )}
    </div>
  );
}
