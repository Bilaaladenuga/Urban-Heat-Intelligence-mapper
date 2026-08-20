"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import * as maplibregl from "maplibre-gl";

type HealthStatus = "checking" | "online" | "offline";
type BoundaryStatus = "loading" | "loaded" | "offline";

const LAGOS_CENTER: [number, number] = [3.3792, 6.5244];

interface SceneInfo {
  scene_id: string;
  bands: number;
  crs: string;
  width: number;
  height: number;
  bounds: { west: number; south: number; east: number; north: number };
  nodata: number | null;
  type?: string;
}

const BAND_LABELS: Record<number, string> = {
  1: "SR_B4 (Red)",
  2: "SR_B5 (NIR)",
  3: "SR_B6 (SWIR1)",
  4: "SR_B7 (SWIR2)",
  5: "ST_B10 (Temp)",
  6: "QA_PIXEL",
};

const COLORMAP_OPTIONS = [
  { value: "", label: "Grayscale" },
  { value: "thermal", label: "Thermal" },
  { value: "ndvi", label: "NDVI colormap" },
];

const NDVI_COLORMAP_OPTIONS = [
  { value: "ndvi", label: "NDVI (brown → green)" },
  { value: "", label: "Grayscale" },
];

// Add the study-area boundary layers to a loaded map.
function addBoundaryLayers(
  map: maplibregl.Map,
  data: { city: unknown; lgas: unknown; neighborhoods: unknown }
): { lgas: number; neighborhoods: number } {
  const city = data.city as maplibregl.GeoJSONSourceSpecification["data"];
  const lgas = data.lgas as maplibregl.GeoJSONSourceSpecification["data"];
  const neighborhoods = data.neighborhoods as maplibregl.GeoJSONSourceSpecification["data"];

  map.addSource("city", { type: "geojson", data: city });
  map.addLayer({
    id: "city-fill",
    type: "fill",
    source: "city",
    paint: { "fill-color": "#f59e0b", "fill-opacity": 0.15 },
  });
  map.addLayer({
    id: "city-outline",
    type: "line",
    source: "city",
    paint: { "line-color": "#b45309", "line-width": 2 },
  });

  map.addSource("lgas", { type: "geojson", data: lgas });
  map.addLayer({
    id: "lga-outline",
    type: "line",
    source: "lgas",
    paint: { "line-color": "#6366f1", "line-width": 1, "line-opacity": 0.8 },
  });

  map.addSource("neighborhoods", { type: "geojson", data: neighborhoods });
  map.addLayer({
    id: "neighborhood-fill",
    type: "fill",
    source: "neighborhoods",
    paint: { "fill-color": "#0d9488", "fill-opacity": 0.2 },
  });
  map.addLayer({
    id: "neighborhood-outline",
    type: "line",
    source: "neighborhoods",
    paint: { "line-color": "#0f766e", "line-width": 1 },
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

function stateBounds(featureCollection: unknown): maplibregl.LngLatBounds {
  const bounds = new maplibregl.LngLatBounds();
  const features = (
    featureCollection as { features?: unknown[] }
  ).features ?? [];
  const pushRing = (ring: number[][]) => {
    for (const position of ring) {
      if (position.length >= 2) bounds.extend([position[0], position[1]]);
    }
  };
  for (const feature of features) {
    const geometry = (
      feature as { geometry?: { type?: string; coordinates?: unknown } }
    ).geometry;
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

// Build the tile URL for a raster layer.
function tileUrl(sceneId: string, band: number, colormap: string): string {
  const params = new URLSearchParams();
  params.set("band", String(band));
  if (colormap) params.set("colormap", colormap);
  return `/api/v1/rasters/${sceneId}/tiles/{z}/{x}/{y}.png?${params.toString()}`;
}

// Get the effective band number for a scene type.
function effectiveBand(scene: SceneInfo | null, band: number): number {
  if (!scene) return band;
  if (scene.type === "ndvi") return 1;
  return band;
}

export default function Home() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [health, setHealth] = useState<HealthStatus>("checking");
  const [boundaryStatus, setBoundaryStatus] = useState<BoundaryStatus>("loading");
  const [lgaCount, setLgaCount] = useState<number | null>(null);
  const [neighborhoodCount, setNeighborhoodCount] = useState<number | null>(null);
  const [mapReady, setMapReady] = useState(false);

  // Raster layer state.
  const [scenes, setScenes] = useState<SceneInfo[]>([]);
  const [selectedScene, setSelectedScene] = useState<string>("");
  const [selectedBand, setSelectedBand] = useState<number>(1);
  const [colormap, setColormap] = useState<string>("");
  const [opacity, setOpacity] = useState<number>(0.7);
  const [rasterVisible, setRasterVisible] = useState<boolean>(false);
  const [rasterStatus, setRasterStatus] = useState<string>("idle");

  // Derived: the currently selected scene object.
  const activeScene = scenes.find((s) => s.scene_id === selectedScene) ?? null;

  // Use refs to avoid stale closures in the raster update effect.
  const rasterStateRef = useRef({ rasterVisible, selectedScene, selectedBand, colormap, opacity, activeScene });
  rasterStateRef.current = { rasterVisible, selectedScene, selectedBand, colormap, opacity, activeScene };

  // Initialize map.
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
        layers: [{ id: "osm", type: "raster", source: "osm" }],
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

  // Health check.
  useEffect(() => {
    fetch("/api/v1/health")
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"));
  }, []);

  // Fetch available scenes.
  useEffect(() => {
    fetch("/api/v1/rasters")
      .then((res) => (res.ok ? res.json() : Promise.reject()))
      .then((data: { scenes: SceneInfo[] }) => {
        setScenes(data.scenes);
        if (data.scenes.length > 0) {
          setSelectedScene(data.scenes[0].scene_id);
        }
      })
      .catch(() => setScenes([]));
  }, []);

  // Load boundaries.
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

  // Single effect to update the raster layer whenever any raster param changes.
  // Uses refs to avoid stale-closure bugs.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) return;

    const { rasterVisible: vis, selectedScene: scene, selectedBand: band, colormap: cm, opacity: op, activeScene: aScene } = rasterStateRef.current;

    const rasterLayerId = "raster-layer";
    const rasterSourceId = "raster-source";

    // Always clean up first.
    try {
      if (map.getLayer(rasterLayerId)) map.removeLayer(rasterLayerId);
    } catch { /* layer might not exist */ }
    try {
      if (map.getSource(rasterSourceId)) map.removeSource(rasterSourceId);
    } catch { /* source might still be loading */ }

    if (!vis || !scene) {
      setRasterStatus(!vis ? "hidden" : "no scene selected");
      return;
    }

    // Small delay to ensure previous source is fully removed.
    setTimeout(() => {
      try {
        const effBand = effectiveBand(aScene, band);
        const url = tileUrl(scene, effBand, cm);
        map.addSource(rasterSourceId, {
          type: "raster",
          tiles: [url],
          tileSize: 256,
          maxzoom: 18,
        });
        map.addLayer({
          id: rasterLayerId,
          type: "raster",
          source: rasterSourceId,
          paint: { "raster-opacity": op },
        });
        setRasterStatus(`showing ${scene} (band ${effBand}${cm ? ", " + cm : ""})`);
      } catch (err) {
        setRasterStatus(`error: ${String(err)}`);
      }
    }, 100);
  }, [rasterVisible, selectedScene, selectedBand, colormap, opacity, mapReady]);

  return (
    <div className="relative flex flex-1 flex-col">
      <header className="z-20 flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-3">
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
        {/* Map container — must be the lowest layer */}
        <div
          ref={mapContainer}
          className="bg-white"
          style={{ position: "absolute", inset: 0 }}
        />

        {/* Legend panel — pointer-events-none lets map drag/scroll through */}
        <div className="pointer-events-none absolute bottom-4 left-4 z-10 max-w-xs rounded-lg bg-white/90 p-3 text-xs text-zinc-700 shadow">
          <p className="font-medium text-zinc-900">Study area</p>
          <p className="mt-1">
            Lagos State, Nigeria. Landsat 8/9 scenes processed for NDVI,
            LST and built-up indicators.
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

        {/* Raster controls — SEPARATE panel, NOT inside pointer-events-none */}
        <div className="absolute bottom-4 right-4 z-10 w-64 rounded-lg bg-white p-3 text-xs text-zinc-700 shadow-lg border border-zinc-200">
          <p className="font-medium text-zinc-900">Raster layers</p>
          {scenes.length === 0 ? (
            <p className="mt-1 text-zinc-400">Loading layers…</p>
          ) : (
            <>
              <label className="mt-2 flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rasterVisible}
                  onChange={(e) => setRasterVisible(e.target.checked)}
                  className="h-4 w-4 cursor-pointer"
                />
                <span className="font-medium">Show raster overlay</span>
              </label>

              {rasterVisible && (
                <div className="mt-3 space-y-3">
                  {/* Layer selector */}
                  <div>
                    <label className="text-zinc-600 font-medium">Layer</label>
                    <select
                      value={selectedScene}
                      onChange={(e) => setSelectedScene(e.target.value)}
                      className="mt-1 block w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-xs"
                    >
                      {scenes.map((s) => (
                        <option key={s.scene_id} value={s.scene_id}>
                          {s.scene_id.replace(/_/g, " ")}{" "}
                          {s.type === "ndvi" ? "[NDVI]" : "[RGB]"}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Band selector — hidden for NDVI */}
                  {activeScene?.type !== "ndvi" && (
                    <div>
                      <label className="text-zinc-600 font-medium">Band</label>
                      <select
                        value={selectedBand}
                        onChange={(e) => setSelectedBand(Number(e.target.value))}
                        className="mt-1 block w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-xs"
                      >
                        {Array.from({ length: 6 }, (_, i) => i + 1).map((b) => (
                          <option key={b} value={b}>
                            {BAND_LABELS[b]}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Colormap */}
                  <div>
                    <label className="text-zinc-600 font-medium">Colormap</label>
                    <select
                      value={colormap}
                      onChange={(e) => setColormap(e.target.value)}
                      className="mt-1 block w-full rounded border border-zinc-300 bg-white px-2 py-1.5 text-xs"
                    >
                      {(activeScene?.type === "ndvi"
                        ? NDVI_COLORMAP_OPTIONS
                        : COLORMAP_OPTIONS
                      ).map((c) => (
                        <option key={c.value} value={c.value}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Opacity slider */}
                  <div>
                    <label className="text-zinc-600 font-medium">
                      Opacity: {Math.round(opacity * 100)}%
                    </label>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.05}
                      value={opacity}
                      onChange={(e) => setOpacity(Number(e.target.value))}
                      className="mt-1 w-full"
                    />
                  </div>

                  {/* Status line */}
                  <p className="text-zinc-400 italic">{rasterStatus}</p>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
