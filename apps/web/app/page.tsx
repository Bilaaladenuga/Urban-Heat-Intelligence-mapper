"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";

type HealthStatus = "checking" | "online" | "offline";
type BoundaryStatus = "loading" | "loaded" | "offline";

const LAGOS_CENTER: [number, number] = [3.3792, 6.5244];

export default function Home() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [health, setHealth] = useState<HealthStatus>("checking");
  const [boundaryStatus, setBoundaryStatus] = useState<BoundaryStatus>("loading");
  const [lgaCount, setLgaCount] = useState<number | null>(null);

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

  // Load study-area boundaries once the map is ready.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const onLoad = async () => {
      try {
        const [cityRes, lgasRes] = await Promise.all([
          fetch("/api/v1/boundaries/city"),
          fetch("/api/v1/boundaries/lgas"),
        ]);
        if (!cityRes.ok || !lgasRes.ok) throw new Error("boundary fetch failed");
        const city = await cityRes.json();
        const lgas = await lgasRes.json();

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

        setLgaCount(lgas.features.length);
        setBoundaryStatus("loaded");

        // Fit the map to the state boundary.
        const bounds = new maplibregl.LngLatBounds();
        city.features.forEach((feature: any) => {
          if (feature.geometry.type === "Polygon") {
            feature.geometry.coordinates[0].forEach((coord: number[]) =>
              bounds.extend(coord as [number, number]),
            );
          } else if (feature.geometry.type === "MultiPolygon") {
            feature.geometry.coordinates.forEach((poly: number[][][]) =>
              poly[0].forEach((coord: number[]) =>
                bounds.extend(coord as [number, number]),
              ),
            );
          }
        });
        map.fitBounds(bounds, { padding: 40 });
      } catch {
        setBoundaryStatus("offline");
      }
    };

    if (map.loaded()) {
      void onLoad();
    } else {
      map.once("load", onLoad);
    }
  }, [mapRef.current]); // eslint-disable-line react-hooks/exhaustive-deps

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
        <div ref={mapContainer} className="absolute inset-0" />
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
          </div>
        </div>
      </main>
    </div>
  );
}
