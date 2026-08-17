"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";

type HealthStatus = "checking" | "online" | "offline";
type BoundaryStatus = "loading" | "loaded" | "offline";

const LAGOS_CENTER: [number, number] = [3.3792, 6.5244];

// Add the study-area boundary layers (state, LGAs, neighborhoods) to a
// loaded map. Returns the number of features per layer for the legend.
function addBoundaryLayers(map: maplibregl.Map, data: {
  city: unknown;
  lgas: unknown;
  neighborhoods: unknown;
}): { lgas: number; neighborhoods: number } {
  const city = data.city as maplibregl.GeoJSONSourceSpecification["data"];
  const lgas = data.lgas as maplibregl.GeoJSONSourceSpecification["data"];
  const neighborhoods = data.neighborhoods as maplibregl.GeoJSONSourceSpecification["data"];

  map.addSource("city", { type: "geojson", data: city });
  map.addLayer({
    id: "city-fill",
    type: "fill",
    source: "city",
    paint: {
      "fill-color": "#f59e0b",
      "fill-opacity": 0.15,
    },
  });
  map.addLayer({
    id: "city-outline",
    type: "line",
    source: "city",
    paint: {
      "line-color": "#b45309",
      "line-width": 2,
    },
  });

  map.addSource("lgas", { type: "geojson", data: lgas });
  map.addLayer({
    id: "lga-outline",
    type: "line",
    source: "lgas",
    paint: {
      "line-color": "#6366f1",
      "line-width": 1,
      "line-opacity": 0.8,
    },
  });

  // Neighborhoods: points render as circles, the few polygon boundaries
  // render as a light fill + outline. No-op layers for the other geometry
  // type are fine — MapLibre skips them.
  map.addSource("neighborhoods", { type: "geojson", data: neighborhoods });
  map.addLayer({
    id: "neighborhood-fill",
    type: "fill",
    source: "neighborhoods",
    paint: {
      "fill-color": "#0d9488",
      "fill-opacity": 0.2,
    },
  });
  map.addLayer({
    id: "neighborhood-outline",
    type: "line",
    source: "neighborhoods",
    paint: {
      "line-color": "#0f766e",
      "line-width": 1,
    },
  });
  map.addLayer({
    id: "neighborhood-points",
    type: "circle",
    source: "neighborhoods",
    paint: {
      "circle-radius": 4,
      "circle-color": "#14b8a6",
      "circle-stroke-color": "#ffffff",
      "circle-stroke-width": 1,
    },
  });

  const lgaCount = (lgas as { features?: unknown[] }).features?.length ?? 0;
  const neighborhoodCount =
    (neighborhoods as { features?: unknown[] }).features?.length ?? 0;
  return { lgas: lgaCount, neighborhoods: neighborhoodCount };
}

// Expand the map bounds to cover the state boundary geometry.
function stateBounds(featureCollection: unknown): maplibregl.LngLatBounds {
  const bounds = new maplibregl.LngLatBounds();
  const features = (featureCollection as { features?: unknown[] }).features ?? [];
  const pushRing = (ring: number[][]) => {
    for (const position of ring) {
      if (position.length >= 2) bounds.extend([position[0], position[1]]);
    }
  };
  for (const feature of features) {
    const geometry = (feature as { geometry?: { type?: string; coordinates?: unknown } })
      .geometry;
    if (!geometry) continue;
    if (geometry.type === "Polygon") {
      for (const ring of geometry.coordinates as number[][][]) {
        pushRing(ring);
      }
    } else if (geometry.type === "MultiPolygon") {
      for (const polygon of geometry.coordinates as number[][][][]) {
        for (const ring of polygon) {
          pushRing(ring);
        }
      }
    }
  }
  return bounds;
}

export default function Home() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [health, setHealth] = useState<HealthStatus>("checking");
  const [boundaryStatus, setBoundaryStatus] = useState<BoundaryStatus>("loading");
  const [lgaCount, setLgaCount] = useState<number | null>(null);
  const [neighborhoodCount, setNeighborhoodCount] = useState<number | null>(null);
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "© OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm",
            type: "raster",
            source: "osm",
          },
        ],
      },
      center: LAGOS_CENTER,
      zoom: 10,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;
    map.on("load", () => setMapReady(true));

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    fetch("/api/v1/health")
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"));
  }, []);

  // Load the study-area boundaries once the map is ready.
  useEffect(() => {
    if (!mapReady) return;
    const map = mapRef.current;
    if (!map) return;

    const onLoad = async () => {
      try {
        const [cityRes, lgasRes, neighborhoodsRes] = await Promise.all([
          fetch("/api/v1/boundaries/city"),
          fetch("/api/v1/boundaries/lgas"),
          fetch("/api/v1/boundaries/neighborhoods"),
        ]);
        if (!cityRes.ok || !lgasRes.ok || !neighborhoodsRes.ok) {
          throw new Error("boundary fetch failed");
        }
        const [city, lgas, neighborhoods] = await Promise.all([
          cityRes.json(),
          lgasRes.json(),
          neighborhoodsRes.json(),
        ]);

        const counts = addBoundaryLayers(map, { city, lgas, neighborhoods });
        setLgaCount(counts.lgas);
        setNeighborhoodCount(counts.neighborhoods);
        setBoundaryStatus("loaded");

        map.fitBounds(stateBounds(city), { padding: 40 });
      } catch {
        setBoundaryStatus("offline");
      }
    };

    void onLoad();
  }, [mapReady]);

  return (
    <div className="relative flex flex-1 flex-col">
      <header className="z-10 flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3">
        <div>
          <h1 className="text-lg font-semibold text-zinc-900">
            Urban Heat Intelligence
          </h1>
          <p className="text-xs text-zinc-500">
            Urban Heat Island mapping — Lagos, Nigeria
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`h-2 w-2 rounded-full ${
              health === "online"
                ? "bg-emerald-500"
                : health === "offline"
                  ? "bg-red-500"
                  : "bg-amber-400"
            }`}
          />
          <span className="text-zinc-600">
            API {health === "checking" ? "checking…" : health}
          </span>
        </div>
      </header>

      <main className="relative flex-1">
        {/* Inline styles: MapLibre adds its own class to this container and
            its stylesheet `position: relative` would override Tailwind's
            utilities (unlayered CSS beats @layer). Inline wins over all. */}
        <div
          ref={mapContainer}
          className="bg-white"
          style={{ position: "absolute", inset: 0 }}
        />
        <div className="pointer-events-none absolute bottom-4 left-4 z-10 max-w-xs rounded-lg bg-white/90 p-3 text-xs text-zinc-700 shadow">
          <p className="font-medium text-zinc-900">Study area</p>
          <p className="mt-1">
            Lagos State, Nigeria. Landsat 8/9 scenes will be processed here to
            derive NDVI, Land Surface Temperature and built-up indicators.
          </p>
          <div className="mt-2 space-y-1 border-t border-zinc-200 pt-2">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-sm bg-amber-500/40 ring-1 ring-amber-700" />
              <span>State boundary</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-0.5 w-2.5 bg-indigo-500" />
              <span>
                LGA boundaries{" "}
                {boundaryStatus === "loaded" && lgaCount !== null
                  ? `(${lgaCount})`
                  : boundaryStatus === "offline"
                    ? "(unavailable)"
                    : "(loading…)"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-teal-500 ring-1 ring-teal-700" />
              <span>
                Neighborhoods{" "}
                {boundaryStatus === "loaded" && neighborhoodCount !== null
                  ? `(${neighborhoodCount})`
                  : boundaryStatus === "offline"
                    ? "(unavailable)"
                    : "(loading…)"}
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
