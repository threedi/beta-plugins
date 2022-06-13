drop schema hydrobasins;
create schema hydrobasins;
select count(*) FROM hydrobasins.level_12;

DROP TABLE IF EXISTS hydrobasins.similar_sized_hydrobasins;
CREATE TABLE hydrobasins.similar_sized_hydrobasins (
    id serial PRIMARY KEY,
    hybas_id numeric(11,0),
    next_down numeric(11,0),
    next_sink numeric(11,0),
    main_bas numeric(11,0),
    dist_sink numeric(10,1),
    dist_main numeric(10,1),
    sub_area numeric(10,1),
    up_area numeric(10,1),
    pfaf_id numeric(13,0),
    endo numeric(6,0),
    coast numeric(6,0),
    "order" numeric(6,0),
    sort numeric(11,0),
    geom geometry(MultiPolygon,4326)
)
;

-- Find parent
ALTER TABLE hydrobasins.level_01 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_02 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_03 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_04 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_05 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_06 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_07 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_08 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_09 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_10 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_11 ADD COLUMN pos geometry(Point, 4326);
ALTER TABLE hydrobasins.level_12 ADD COLUMN pos geometry(Point, 4326);

UPDATE hydrobasins.level_01 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_02 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_03 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_04 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_05 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_06 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_07 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_08 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_09 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_10 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_11 SET wkb_geometry = ST_MakeValid(wkb_geometry);
UPDATE hydrobasins.level_12 SET wkb_geometry = ST_MakeValid(wkb_geometry);

UPDATE hydrobasins.level_01 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_02 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_03 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_04 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_05 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_06 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_07 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_08 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_09 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_10 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_11 SET pos = ST_PointOnSurface(wkb_geometry);
UPDATE hydrobasins.level_12 SET pos = ST_PointOnSurface(wkb_geometry);

ALTER TABLE hydrobasins.level_02 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_03 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_04 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_05 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_06 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_07 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_08 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_09 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_10 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_11 ADD COLUMN parent numeric(11,0);
ALTER TABLE hydrobasins.level_12 ADD COLUMN parent numeric(11,0);

UPDATE hydrobasins.level_02 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_01 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_03 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_02 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_04 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_03 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_05 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_04 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_06 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_05 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_07 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_06 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_08 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_07 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_09 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_08 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_10 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_09 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_11 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_10 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);
UPDATE hydrobasins.level_12 AS tgt SET parent = src.hybas_id FROM hydrobasins.level_11 AS src WHERE ST_Intersects(tgt.pos, src.wkb_geometry);



-- RESET
DELETE FROM hydrobasins.similar_sized_hydrobasins;

-- Level 01
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_01
WHERE	sub_area < 100  -- Units = km2 (= million m2)
;

-- Level 02
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_02
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;

-- Level 03
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_03
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;

-- Level 04
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_04
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


-- Level 05
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_05
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


-- Level 06
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_06
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


-- Level 07
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_07
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


-- Level 08
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_08
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


-- Level 09
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_09
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


-- Level 10
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_10
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;

-- Level 11
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_11
WHERE	sub_area < 100 AND parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;

-- Level 12
INSERT INTO hydrobasins.similar_sized_hydrobasins(
	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, geom
)
SELECT 	hybas_id, next_down, next_sink, main_bas, dist_sink, dist_main, sub_area, up_area, pfaf_id, endo, coast, "order", sort, wkb_geometry
FROM 	hydrobasins.level_12
WHERE	parent NOT IN (SELECT hybas_id FROM hydrobasins.similar_sized_hydrobasins)  -- Units = km2 (= million m2)
;


SELECT max(sub_area) FROM hydrobasins.similar_sized_hydrobasins;
