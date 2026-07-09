CREATE INDEX IF NOT EXISTS parcels_geom_idx
ON core.parcels
USING GIST (geom);

CREATE INDEX IF NOT EXISTS parcels_property_id_idx
ON core.parcels (property_id);

CREATE INDEX IF NOT EXISTS nature_features_geom_idx
ON core.nature_features
USING GIST (geom);

CREATE INDEX IF NOT EXISTS forest_stands_geom_idx
ON core.forest_stands
USING GIST (geom);