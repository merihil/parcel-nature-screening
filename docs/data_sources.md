# Data Sources

What external datasets this project uses, where they come from, and what they contain.

## Cadastral parcels

**Source:** National Land Survey of Finland / MML  
**Use in project:** User input and main analysis unit  
**Target table:** `core.parcels`  
**Key fields:**
- `property_id`
- `municipality_code`
- `area_m2`
- `geom`

**Why included:**
The application evaluates biodiversity potential at property level, so parcel geometries are the core spatial unit.

## Natura 2000 areas

**Source:** SYKE WFS  
**Use in project:** Conservation context and proximity analysis  
**Geometry type:** Polygon / MultiPolygon  
**Target table:** `core.nature_features`  
**Key fields:**
- `feature_subtype`: SAC / SCI / SPA
- `source_identifier`: Natura site code
- `name`: site name
- `geom`: geometry

**Why included:**
Natura areas indicate existing conservation value and ecological context. The application uses them to calculate overlap and nearest-distance indicators.

## Forest stands

**Source:** Finnish Forest Centre (Metsäkeskus) WFS  
**Use in project:** Forest structure and habitat potential indicators  
**Target table:** `core.forest_stand_features`  
**Key fields:**
- `development_class`
- `fertility_class`
- `drainage_state`
- `special_feature`
- `mean_age`
- `source_identifier`
- `geom`

**Why included:**
Forest stand attributes can indicate old forest, fertile habitats, peatlands and potential biodiversity value.

**More data sources will be added as the project evolves.**