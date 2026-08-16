# Task 0.1 — Research Question

**Status:** Complete (Phase 0 — Research Design)

## Primary research question

> **Which areas of Lagos, Nigeria experience greater land surface heat, and how is that related to vegetation (NDVI) and urban development (built-up intensity)?**

## Supporting questions

1. **Spatial pattern:** Where are the highest and lowest land surface temperatures (LST) in Lagos, and how are they distributed across the city?
2. **Vegetation relationship:** How is vegetation cover (NDVI) associated with land surface temperature?
3. **Built-up relationship:** How is built-up intensity associated with land surface temperature?
4. **Combined effect:** Do the hottest areas coincide with low vegetation **and** high built-up intensity?
5. **Temporal dimension:** How do LST, vegetation, and built-up indicators change between available Landsat acquisition dates?

## Objectives

1. Build a **reproducible Landsat processing pipeline** (acquisition → preprocessing → NDVI → LST → built-up indicators) for Lagos.
2. **Quantify the spatial relationship** between LST, NDVI, and built-up density using spatial statistics.
3. Deliver an **interactive Web GIS** to explore the derived layers, legends, and temporal comparisons.
4. Produce a **clearly-labeled analytical indicator** of areas that combine high heat, low vegetation, and high built-up intensity for further investigation/planning.

## Hypotheses

- **H1 (vegetation):** There is a statistically significant **negative** association between NDVI and LST — areas with more vegetation tend to be cooler.
- **H2 (built-up):** There is a statistically significant **positive** association between built-up intensity and LST — denser built-up areas tend to be hotter.
- **H0 (null):** No statistically significant association exists between NDVI/built-up intensity and LST in the study area.

## Scope note

The project measures **surface** heat (LST from thermal infrared), not air temperature, and does not claim health-risk classification — hotspot categories are analytical indicators only, per `PROJECT_SPEC.md` Phase 9.
