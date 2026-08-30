DROP INDEX IF EXISTS core.parcels_property_id_idx;

CREATE UNIQUE INDEX IF NOT EXISTS parcels_property_id_unique_idx
ON core.parcels (property_id);