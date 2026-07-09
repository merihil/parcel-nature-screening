-- Column types match what geopandas/pandas already inferred and created in existing
-- deployments (verified against a live database on 2026-07-07). Kept as-is here so a
-- fresh install ends up structurally identical to an existing one.
CREATE TABLE IF NOT EXISTS core.forest_stand_features (
    id SERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    feature_type TEXT NOT NULL,
    source_identifier TEXT,
    stand_number BIGINT,
    special_feature DOUBLE PRECISION,
    standclass BIGINT,
    development_class TEXT,
    mean_age BIGINT,
    fertility_class BIGINT,
    drainage_state BIGINT,
    soil_type BIGINT,
    cutting_restriction DOUBLE PRECISION,
    silviculture_restriction DOUBLE PRECISION,
    cutting_proposal_year DOUBLE PRECISION,
    geom geometry(MultiPolygon, 3067),
    created_at TIMESTAMP DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS forest_stand_features_source_identifier_idx
ON core.forest_stand_features (source_name, source_identifier);

DROP INDEX IF EXISTS core.idx_forest_stand_features_geom;

CREATE INDEX IF NOT EXISTS forest_stand_features_geom_idx
ON core.forest_stand_features
USING GIST (geom);
