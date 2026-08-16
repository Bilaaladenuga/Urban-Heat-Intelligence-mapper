"use client";

import { useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";

type HealthStatus = "checking" | "online" | "offline";

const LAGOS_CENTER: [number, number] = [3.3792, 6.5244];

export default function Home() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [health, setHealth] = useState<HealthStatus>("checking");

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
        </div>
      </main>
    </div>
  );
}
