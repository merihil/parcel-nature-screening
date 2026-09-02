CREATE TABLE IF NOT EXISTS core.special_habitat_features (
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

CREATE UNIQUE INDEX IF NOT EXISTS special_habitat_features_source_identifier_idx
ON core.special_habitat_features (source_name, source_identifier);

DROP INDEX IF EXISTS core.idx_special_habitat_features_geom;

CREATE INDEX IF NOT EXISTS special_habitat_features_geom_idx
ON core.special_habitat_features
USING GIST (geom);
