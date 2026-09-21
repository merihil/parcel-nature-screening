-- import_forest_stands.py / import_special_habitats.py used to write pandas'
-- NaN straight through for missing numeric WFS fields, landing as a literal
-- float NaN in Postgres instead of NULL. `x IS NOT NULL` is true for NaN, so
-- this silently broke every "does this stand have X" check (scoring's
-- special_feature bonus, map_layers' popups). The ETL now normalizes NaN to
-- None before writing (see optional_column() in both files); this backfills
-- rows written before that fix.
UPDATE core.forest_stand_features
SET
    special_feature = NULLIF(special_feature, 'NaN'::float8),
    cutting_restriction = NULLIF(cutting_restriction, 'NaN'::float8),
    silviculture_restriction = NULLIF(silviculture_restriction, 'NaN'::float8),
    cutting_proposal_year = NULLIF(cutting_proposal_year, 'NaN'::float8)
WHERE special_feature = 'NaN'::float8
OR cutting_restriction = 'NaN'::float8
OR silviculture_restriction = 'NaN'::float8
OR cutting_proposal_year = 'NaN'::float8;

UPDATE core.special_habitat_features
SET
    special_feature = NULLIF(special_feature, 'NaN'::float8),
    cutting_restriction = NULLIF(cutting_restriction, 'NaN'::float8),
    silviculture_restriction = NULLIF(silviculture_restriction, 'NaN'::float8),
    cutting_proposal_year = NULLIF(cutting_proposal_year, 'NaN'::float8)
WHERE special_feature = 'NaN'::float8
OR cutting_restriction = 'NaN'::float8
OR silviculture_restriction = 'NaN'::float8
OR cutting_proposal_year = 'NaN'::float8;
