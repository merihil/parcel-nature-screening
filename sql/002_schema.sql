CREATE TABLE IF NOT EXISTS core.parcels (
    id SERIAL PRIMARY KEY,
    property_id TEXT NOT NULL,
    municipality_code TEXT,
    area_m2 DOUBLE PRECISION,
    source_name TEXT,
    geom geometry(MultiPolygon, 3067),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.nature_features (
    id SERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    feature_type TEXT NOT NULL,
    feature_subtype TEXT,
    name TEXT,
    legal_status TEXT,
    geom geometry(MultiPolygon, 3067),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS core.forest_stands (
    id SERIAL PRIMARY KEY,
    stand_id TEXT,
    main_tree_species TEXT,
    development_class TEXT,
    site_type TEXT,
    mean_age DOUBLE PRECISION,
    mean_height DOUBLE PRECISION,
    volume_m3_ha DOUBLE PRECISION,
    geom geometry(MultiPolygon, 3067),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analysis.parcel_scores (
    id SERIAL PRIMARY KEY,
    property_id TEXT NOT NULL,
    score_total DOUBLE PRECISION,
    score_class TEXT,
    details JSONB,
    calculated_at TIMESTAMP DEFAULT now()
);