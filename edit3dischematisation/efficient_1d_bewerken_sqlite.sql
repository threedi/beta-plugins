/*
Script to effectively edit the 1D components of a 3Di model.
The script adds triggers to the 1D view tables to make 
insertion, updating and deletion of view possible for easy
modifications. Also the geometry of the views is treated as an 
actual geometry which can be used to snap line elements to 
connection nodes. 

The script is currently a Beta version and thus bugs might occur.
Also no responsibility is taken for wrong assumptions or corrupted 
data. 

Created by: Ivar Lokhorst, Nelen & Schuurmans
Last edit:  19-01-2019
*/

update geometry_columns
set spatial_index_enabled = 0;

----------------------------------------------------------------------------------------
--------------------------------- V2 Manhole edits -------------------------------------
----------------------------------------------------------------------------------------
drop view if exists v2_manhole_view;

create view v2_manhole_view as
SELECT 
    manh.rowid                    AS ROWID,
    node.id                       AS node_id,
    manh.bottom_level             AS manh_bottom_level,
    manh.surface_level            AS manh_surface_level,
    manh.display_name             AS manh_display_name,
    manh.shape                    AS manh_shape,
    manh.width                    AS manh_width,
    manh.length                   AS manh_length,
    manh.manhole_indicator        AS manh_manhole_indicator,
    manh.calculation_type         AS manh_calculation_type,
    manh.drain_level              AS manh_drain_level,
    manh.zoom_category            AS manh_zoom_category,
    node.initial_waterlevel       AS node_initial_waterlevel,   
    manh.id                       AS manh_id,
    manh.connection_node_id       AS manh_connection_node_id,
    node.storage_area             AS node_storage_area,
    manh.code                     AS manh_code,
    node.code                     AS node_code,
    node.the_geom,
    node.the_geom_linestring      AS node_the_geom_linestring,
    manh.sediment_level           AS manh_sediment_level 
FROM 
    v2_manhole manh,
    v2_connection_nodes node
WHERE manh.connection_node_id = node.id;

delete from views_geometry_columns 
where view_name = 'v2_manhole_view';

insert into views_geometry_columns(
    view_name,
	view_geometry,
	view_rowid,
    f_table_name,
	f_geometry_column)
values(
    'v2_manhole_view',
    'the_geom',
	'ROWID',
	'v2_connection_nodes',
	'the_geom');

drop trigger if exists v2_manhole_insert;

create trigger v2_manhole_insert 
    instead of insert 
    on v2_manhole_view 
    BEGIN 
    INSERT INTO v2_connection_nodes( 
        storage_area, 
    	initial_waterlevel, 
    	the_geom, 
	    the_geom_linestring, 
        code) 
    SELECT 
        NEW.node_storage_area, 
        NEW.node_initial_waterlevel, 
	    NEW.the_geom, 
	    NEW.node_the_geom_linestring, 
        NEW.node_code 
    where not exists(
        select * from v2_connection_nodes 
	    where the_geom = NEW.the_geom); 

    INSERT INTO v2_manhole( 
        display_name,
	    code, 
	    connection_node_id, 
	    shape, 
	    width, 
	    length, 
        manhole_indicator, 
	    calculation_type, 
	    bottom_level, 
	    surface_level, 
        drain_level, 
	    sediment_level, 
	    zoom_category) 
    SELECT 
        NEW.manh_display_name,
	    NEW.manh_code,
	    a.id,
    	NEW.manh_shape,
    	NEW.manh_width,
        NEW.manh_length, 
        NEW.manh_manhole_indicator,
	    NEW.manh_calculation_type,
        NEW.manh_bottom_level,
	    NEW.manh_surface_level, 
        NEW.manh_drain_level,
        NEW.manh_sediment_level,
	    NEW.manh_zoom_category 
    FROM 
	    v2_connection_nodes a 
    WHERE MbrTouches(a.the_geom,NEW.the_geom)=1 
    ; 
    END; 

drop trigger if exists v2_manhole_update;

create trigger v2_manhole_update
	instead of update 
	on v2_manhole_view
	BEGIN
	UPDATE v2_manhole         
	SET id                 = NEW.manh_id,
	    display_name       = NEW.manh_display_name,
        code               = NEW.manh_code,
        connection_node_id = NEW.manh_connection_node_id,
        shape              = NEW.manh_shape,
        width              = NEW.manh_width,
        length             = NEW.manh_length,
        manhole_indicator  = NEW.manh_manhole_indicator,
        calculation_type   = NEW.manh_calculation_type,
        bottom_level       = NEW.manh_bottom_level,
        surface_level      = NEW.manh_surface_level,
        drain_level        = NEW.manh_drain_level,
        sediment_level     = NEW.manh_sediment_level,
        zoom_category      = NEW.manh_zoom_category
    WHERE "id" = OLD."manh_id";
		
    UPDATE v2_connection_nodes  
    set id                    = NEW.node_id,
        storage_area          = NEW.node_storage_area,
        initial_waterlevel    = NEW.node_initial_waterlevel,
        the_geom_linestring   = NEW.node_the_geom_linestring,
        code                  = NEW.node_code,
        the_geom              = NEW.the_geom
    where "id" = OLD."node_id"
    ;
    END;
 
drop trigger if exists v2_manhole_delete;

create trigger v2_manhole_delete
    instead of delete
    on v2_manhole_view
    BEGIN
    DELETE FROM v2_manhole
	WHERE "id" = OLD."manh_id";
        
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;

----------------------------------------------------------------------------------------
---------------------------------- V2 pipe edits ---------------------------------------
----------------------------------------------------------------------------------------

drop trigger if exists v2_pipe_insert;

create trigger v2_pipe_insert 
    instead of insert 
    on v2_pipe_view 
    BEGIN 
	INSERT INTO v2_pipe(
        display_name, 
		code, 
		profile_num, 
		sewerage_type, 
		calculation_type, 
        invert_level_start_point, 
		invert_level_end_point, 
		cross_section_definition_id, 
        friction_value, 
		friction_type, 
		dist_calc_points, 
		material, 
		pipe_quality, 
        original_length, 
		zoom_category, 
		connection_node_start_id, 
		connection_node_end_id)
	SELECT 
	    NEW.pipe_display_name, 
		NEW.pipe_code, 
		NEW.pipe_profile_num, 
		NEW.pipe_sewerage_type, 
		NEW.pipe_calculation_type, 
        COALESCE(NEW.pipe_invert_level_start_point,a.manh_bottom_level), 
		COALESCE(NEW.pipe_invert_level_end_point,b.manh_bottom_level), 
        NEW.pipe_cross_section_definition_id,
        NEW.pipe_friction_value, 
        NEW.pipe_friction_type, 
		NEW.pipe_dist_calc_points, 
		NEW.pipe_material, 
		NEW.pipe_pipe_quality, 
        NEW.pipe_original_length, 
		NEW.pipe_zoom_category, 
		a.node_id, 
		b.node_id
    FROM v2_manhole_view a, 
	     v2_manhole_view b
    WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
	      MbrTouches(ST_endpoint(New.the_geom),b.the_geom) =1;
    end;

drop trigger if exists v2_pipe_update;

create trigger v2_pipe_update
	instead of update 
	on v2_pipe_view
    BEGIN        
    UPDATE v2_pipe
    	SET "id"                          = NEW."pipe_id",
            "display_name"                = NEW."pipe_display_name",
            "code"                        = NEW."pipe_code",
	        "profile_num"                 = NEW."pipe_profile_num",
            "sewerage_type"               = NEW."pipe_sewerage_type",
            "calculation_type"            = NEW."pipe_calculation_type" ,
            "connection_node_start_id"    = (select 
			                                     a.id 
										     from v2_connection_nodes a 
										     where MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
            "connection_node_end_id"      = (select 
			                                     a.id 
										     from v2_connection_nodes a 
										     where MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1),
            "invert_level_start_point"    = NEW."pipe_invert_level_start_point",
            "invert_level_end_point"      = NEW."pipe_invert_level_end_point",
            "cross_section_definition_id" = New."pipe_cross_section_definition_id",
            "friction_type"               = NEW."pipe_friction_type",
            "friction_value"              = NEW."pipe_friction_value", 
            "dist_calc_points"            = NEW."pipe_dist_calc_points",
            "material"                    = NEW."pipe_material",
            "pipe_quality"                = NEW."pipe_pipe_quality",
            "original_length"             = NEW."pipe_original_length",
            "zoom_category"               = NEW."pipe_zoom_category"
	    WHERE "id" = OLD."pipe_id";
    end;

drop trigger if exists v2_pipe_delete;

create trigger v2_pipe_delete
    instead of delete
    on v2_pipe_view
    BEGIN
    DELETE FROM v2_pipe        
	WHERE "id" = OLD."pipe_id";
        
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;

----------------------------------------------------------------------------------------
---------------------------------- V2 weir edits ---------------------------------------
----------------------------------------------------------------------------------------

drop trigger if exists v2_weir_insert;

create trigger v2_weir_insert 
	instead of insert 
	on v2_weir_view
	BEGIN
	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.weir_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom));

	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.weir_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

    INSERT INTO v2_weir(
        display_name, 
		code, 
		crest_level, 
		crest_type, 
		cross_section_definition_id,
        sewerage, 
		discharge_coefficient_positive, 
		discharge_coefficient_negative, 
        external, 
		zoom_category, 
		friction_value, 
		friction_type, 
        connection_node_start_id, 
		connection_node_end_id)
	SELECT 
	    NEW.weir_display_name, 
		NEW.weir_code, 
		NEW.weir_crest_level,
	    NEW.weir_crest_type, 
		NEW.weir_cross_section_definition_id,
		NEW.weir_sewerage, 
		NEW.weir_discharge_coefficient_positive, 
		NEW.weir_discharge_coefficient_negative,
	    NEW.weir_external, 
		NEW.weir_zoom_category,
		NEW.weir_friction_value,
		NEW.weir_friction_type,
	    a.id,
		b.id
    FROM 
	    v2_connection_nodes a, 
		v2_connection_nodes b
    where MbrTouches(a.the_geom,ST_Startpoint(NEW.the_geom))=1 AND 
	      MbrTouches(b.the_geom,ST_endpoint(NEW.the_geom))=1
    ;
    END;

drop trigger if exists v2_weir_update;

create trigger v2_weir_update
	instead of update 
	on v2_weir_view
	BEGIN
    INSERT INTO v2_connection_nodes(
  	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.weir_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom));

	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.weir_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

    UPDATE v2_weir
	SET id                             = NEW.weir_id,
	    display_name                   = NEW.weir_display_name,
	    code                           = NEW.weir_code,
	    crest_level                    = NEW.weir_crest_level,
	    crest_type                     = NEW.weir_crest_type,
	    cross_section_definition_id    = New.weir_cross_section_definition_id,
	    sewerage                       = NEW.weir_sewerage,
	    discharge_coefficient_positive = NEW.weir_discharge_coefficient_positive,
	    discharge_coefficient_negative = NEW.weir_discharge_coefficient_negative,
	    external                       = NEW.weir_external,
	    zoom_category                  = NEW.weir_zoom_category,
	    friction_value                 = NEW.weir_friction_value,
	    friction_type                  = NEW.weir_friction_type,
	    connection_node_start_id       = (select 
		                                      a.id 
										  from v2_connection_nodes a 
										  where MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
	    connection_node_end_id         = (select 
		                                      b.id 
										  from v2_connection_nodes b 
										  where MbrTouches(ST_endpoint(NEW.the_geom),b.the_geom) =1)
	    WHERE v2_weir."id"             = OLD."weir_id" ;
    END;

drop trigger if exists v2_weir_delete;

create trigger v2_weir_delete
    instead of delete
    on v2_weir_view
    BEGIN
    DELETE FROM v2_weir        
    WHERE "id" = OLD."weir_id";
        
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;

----------------------------------------------------------------------------------------
--------------------------------- V2 Orifice edits -------------------------------------
----------------------------------------------------------------------------------------
drop trigger if exists v2_orifice_insert;

create trigger v2_orifice_insert
    instead of insert
    on v2_orifice_view
    BEGIN
	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.orf_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom));

	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.orf_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

	INSERT INTO v2_orifice(
        display_name, 
		code, 
		max_capacity, 
		crest_level, 
		sewerage, 
		cross_section_definition_id,
        friction_value, 
		friction_type, 
		discharge_coefficient_positive, 
		discharge_coefficient_negative,
        zoom_category, 
		crest_type, 
		connection_node_start_id, 
		connection_node_end_id)
	SELECT 
	    NEW.orf_display_name, 
		NEW.orf_code, 
	    NEW.orf_max_capacity, 
		NEW.orf_crest_level, 
		NEW.orf_sewerage, 
		NEW.orf_cross_section_definition_id, 
		NEW.orf_friction_value,
	    NEW.orf_friction_type, 
		NEW.orf_discharge_coefficient_positive, 
		NEW.orf_discharge_coefficient_negative,
	    NEW.orf_zoom_category, 
		NEW.orf_crest_type, 
		a.id, 
        b.id
    FROM 
	    v2_connection_nodes a, 
		v2_connection_nodes b
    WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
	      MbrTouches(ST_endpoint(New.the_geom),b.the_geom)=1
	;
	END;

drop trigger if exists v2_orifice_update;

create trigger v2_orifice_update
	instead of update 
	on v2_orifice_view
	BEGIN
    INSERT INTO v2_connection_nodes(
	    storage_area, 
	    the_geom,
	    code) 
	SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.orf_code
    where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom));

	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.orf_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

    UPDATE v2_orifice
	    SET id                             = NEW.orf_id,
            display_name                   = NEW.orf_display_name,
            code                           = NEW.orf_code,
            max_capacity                   = NEW.orf_max_capacity,
            crest_level                    = NEW.orf_crest_level,
            sewerage                       = NEW.orf_sewerage,
            cross_section_definition_id    = NEW.orf_cross_section_definition_id,
            friction_value                 = NEW.orf_friction_value,
            discharge_coefficient_positive = NEW.orf_discharge_coefficient_positive,
            discharge_coefficient_negative = NEW.orf_discharge_coefficient_negative,
            zoom_category                  = NEW.orf_zoom_category,
            crest_type                     = NEW.orf_crest_type,
            connection_node_start_id       = (select 
			                                      a.id 
										      from v2_connection_nodes a 
											  where MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
            connection_node_end_id         = (select 
			                                      a.id 
											  from v2_connection_nodes a 
											  where MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
	WHERE v2_orifice."id"                  = OLD."orf_id";
    END;

drop trigger if exists v2_orifice_delete;

create trigger v2_orifice_delete
    instead of delete
    on v2_orifice_view
    BEGIN
    DELETE FROM v2_orifice        
    WHERE "id" = OLD."orf_id";
        
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;

----------------------------------------------------------------------------------------
--------------------------------- V2 Culvert edits -------------------------------------
----------------------------------------------------------------------------------------
drop trigger if exists v2_culvert_insert;

create trigger v2_culvert_insert 
    instead of insert 
    on v2_culvert_view 
    BEGIN 
    INSERT INTO v2_connection_nodes( 
        storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.cul_code 
    where not exists( 
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom)); 

    INSERT INTO v2_connection_nodes( 
        storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.cul_code
    where not exists( 
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom)); 

    INSERT INTO v2_culvert( 
        display_name, 
		code, 
		calculation_type, 
		friction_value, 
		friction_type,
		dist_calc_points, 
        zoom_category, 
		cross_section_definition_id, 
		discharge_coefficient_positive, 
		discharge_coefficient_negative, 
        invert_level_start_point, 
		invert_level_end_point, 
		the_geom, 
		connection_node_start_id, 
		connection_node_end_id) 
    SELECT 
	    NEW.cul_display_name, 
		NEW.cul_code, 
		NEW.cul_calculation_type, 
        NEW.cul_friction_value,
		NEW.cul_friction_type,
		NEW.cul_dist_calc_points,
		NEW.cul_zoom_category,
        NEW.cul_cross_section_definition_id,
        NEW.cul_discharge_coefficient_positive,
		NEW.cul_discharge_coefficient_negative,
		NEW.cul_invert_level_start_point,
		NEW.cul_invert_level_end_point,
		NEW.the_geom, 
        a.id, 
		b.id 
    FROM 
	    v2_connection_nodes a, 
		v2_connection_nodes b 
    WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
	      MbrTouches(ST_endpoint(New.the_geom),b.the_geom)=1 
    ; 
    END;

drop trigger if exists v2_culvert_update;

create trigger v2_culvert_update
	instead of update 
	on v2_culvert_view
	BEGIN
	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.cul_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom));

	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.cul_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

    update v2_culvert 
	set id                             = NEW.cul_id,
        display_name                   = NEW.cul_display_name,
        code                           = NEW.cul_code,
        calculation_type               = NEW.cul_calculation_type,
        friction_value                 = NEW.cul_friction_value,
        friction_type                  = NEW.cul_friction_type,
        dist_calc_points               = NEW.cul_dist_calc_points,
		zoom_category                  = NEW.cul_zoom_category,
		cross_section_definition_id    = NEW.cul_cross_section_definition_id,
        invert_level_start_point       = NEW.cul_invert_level_start_point,
		discharge_coefficient_negative = NEW.cul_discharge_coefficient_negative,
		discharge_coefficient_positive = NEW.cul_discharge_coefficient_positive,
        invert_level_end_point         = NEW.cul_invert_level_end_point,
        the_geom                       = NEW.the_geom,
        connection_node_start_id       = (select 
		                                      a.id 
								          from v2_connection_nodes a 
									      where MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id         = (select 
		                                      a.id 
									      from v2_connection_nodes a 
									      where MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
    WHERE v2_culvert."id"               = OLD."cul_id";
    END;

drop trigger if exists v2_culvert_delete;

create trigger v2_culvert_delete
    instead of delete
    on v2_culvert_view
    BEGIN
    DELETE FROM v2_culvert        
	WHERE "id" = OLD."cul_id";
        
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;

----------------------------------------------------------------------------------------
--------------------------------- V2 Channel edits -------------------------------------
----------------------------------------------------------------------------------------
drop trigger if exists v2_channel_insert_bef;

create trigger v2_channel_insert_bef
    before insert 
    on v2_channel
    BEGIN 
    INSERT INTO v2_connection_nodes( 
        storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.code 
    where not exists( 
        select * from v2_connection_nodes 
		where the_geom = ST_Startpoint(NEW.the_geom)); 

    INSERT INTO v2_connection_nodes( 
        storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.code 
    where not exists( 
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom)); 
    END;
drop trigger if exists v2_channel_insert_aft;

create trigger v2_channel_insert_aft
    after insert
    on v2_channel
    BEGIN 
    update v2_channel 
    set 
    connection_node_start_id = (select 
	                                a.id 
								from v2_connection_nodes a 
								where MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
    connection_node_end_id =(select 
	                             a.id 
							 from v2_connection_nodes a 
							 where MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
    where connection_node_start_id is NULL AND connection_node_end_id is NULL;
    END;

drop trigger if exists v2_channel_delete;

create trigger v2_channel_delete
    after delete
    on v2_channel
    BEGIN
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;


----------------------------------------------------------------------------------------
------------------------------- V2 Pumpstation edits -----------------------------------
----------------------------------------------------------------------------------------
drop trigger if exists v2_pumpstation_insert;

create trigger v2_pumpstation_insert 
    instead of insert 
    on v2_pumpstation_view 
    BEGIN 
    INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.pump_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_startpoint(NEW.the_geom));

    INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.pump_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

	INSERT INTO v2_pumpstation(
        display_name, 
		code, 
		classification, 
		type, 
		sewerage, 
		start_level,
        lower_stop_level, 
		upper_stop_level, 
		capacity, 
		zoom_category,
        connection_node_start_id, 
		connection_node_end_id)
	SELECT 
	    NEW.pump_display_name, 
		NEW.pump_code, 
		NEW.pump_classification,
	    NEW.pump_type,
		NEW.pump_sewerage, 
		NEW.pump_start_level, 
		NEW.pump_lower_stop_level, 
		NEW.pump_upper_stop_level, 
		NEW.pump_capacity,
		NEW.pump_zoom_category,
	    a.id,
		b.id
    FROM 
	    v2_connection_nodes a, 
		v2_connection_nodes b
    WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
	      MbrTouches(ST_endpoint(New.the_geom),b.the_geom)=1 
    ;
    END;

drop trigger if exists v2_pumpstation_update;

create trigger v2_pumpstation_update
	instead of update 
	on v2_pumpstation_view
	begin
    INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_startpoint(NEW.the_geom), 
		NEW.pump_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_startpoint(NEW.the_geom));

    INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
    SELECT 
	    0.1, 
		ST_endpoint(NEW.the_geom), 
		NEW.pump_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = ST_endpoint(NEW.the_geom));

    UPDATE v2_pumpstation
	    SET id                       = NEW.pump_id,
	        display_name             = NEW.pump_display_name,
	        code                     = NEW.pump_code,
	        classification           = NEW.pump_classification,
	        sewerage                 = NEW.pump_sewerage,
	        start_level              = NEW.pump_start_level,
	        lower_stop_level         = NEW.pump_lower_stop_level,
	        upper_stop_level         = NEW.pump_upper_stop_level,
	        capacity                 = NEW.pump_capacity,
	        zoom_category            = NEW.pump_zoom_category,
	        connection_node_start_id = (select 
			                                a.id 
									    from v2_connection_nodes a 
										where MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
	    connection_node_end_id       = (select 
		                                    a.id
										from v2_connection_nodes a 
										where MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
	WHERE v2_pumpstation."id" = OLD."pump_id";
	END;

drop trigger if exists v2_pumpstation_delete;

create trigger v2_pumpstation_delete
    instead of delete
    on v2_pumpstation_view
    BEGIN
    DELETE FROM v2_pumpstation        
    WHERE "id" = OLD."pump_id";
        
    DELETE FROM v2_connection_nodes where 
	id not in (select connection_node_id       from v2_manhole)     AND 
	id not in (select connection_node_start_id from v2_pipe)        AND 
	id not in (select connection_node_end_id   from v2_pipe)        AND 
	id not in (select connection_node_start_id from v2_weir)        AND 
	id not in (select connection_node_end_id   from v2_weir)        AND 
	id not in (select connection_node_start_id from v2_pumpstation) AND 
	id not in (select connection_node_end_id   from v2_pumpstation 
	           where connection_node_end_id is not null)            AND 
	id not in (select connection_node_start_id from v2_channel)     AND 
	id not in (select connection_node_end_id   from v2_channel)     AND 
	id not in (select connection_node_start_id from v2_culvert)     AND 
	id not in (select connection_node_end_id   from v2_culvert)     AND 
	id not in (select connection_node_start_id from v2_orifice)     AND 
	id not in (select connection_node_end_id from v2_orifice);
    end;

----------------------------------------------------------------------------------------
------------------------------- V2 1d boundary edits -----------------------------------
----------------------------------------------------------------------------------------
drop view if exists v2_1d_boundary_view;

create view v2_1d_boundary_view as
SELECT 
    bound.rowid               AS ROWID,
    bound.id                  AS bound_id,
    bound.connection_node_id  AS bound_connection_node_id,
    bound.boundary_type       AS bound_boundary_type,
    bound.timeseries          AS bound_timeseries,
    node.code                 AS node_code,
    node.initial_waterlevel   AS node_initial_waterlevel,
    node.storage_area         AS node_storage_area,
    node.the_geom,
    node.the_geom_linestring  AS node_the_geom_linestring
FROM 
    v2_1d_boundary_conditions bound,
    v2_connection_nodes node
WHERE bound.connection_node_id = node.id;

delete from views_geometry_columns 
where view_name = 'v2_1d_boundary_view';

insert into views_geometry_columns(
    view_name,
	view_geometry,
	view_rowid,
	f_table_name,
	f_geometry_column)
values(
    'v2_1d_boundary_view',
	'the_geom',
	'ROWID',
	'v2_connection_nodes',
	'the_geom');

drop trigger if exists v2_1d_boundary_insert;

create trigger v2_1d_boundary_insert
    instead of insert 
    on v2_1d_boundary_view 
    BEGIN 
    INSERT INTO v2_connection_nodes( 
        storage_area, 
		initial_waterlevel, 
		the_geom, 
		the_geom_linestring, 
		code)
    SELECT 
	    NEW.node_storage_area, 
		NEW.node_initial_waterlevel, 
		NEW.the_geom, 
		NEW.node_the_geom_linestring, 
        NEW.node_code 
    where not exists( 
        select * from v2_connection_nodes 
		where the_geom = NEW.the_geom); 

    INSERT INTO v2_1d_boundary_conditions( 
        boundary_type, 
		connection_node_id,
		timeseries)
    SELECT 
	    NEW.bound_boundary_type, 
		a.id,
		NEW.bound_timeseries
    FROM v2_connection_nodes a 
    WHERE MbrTouches(a.the_geom,NEW.the_geom)=1;
    END;

drop trigger if exists v2_1d_boundary_update;

create trigger v2_1d_boundary_update
    instead of update 
	on v2_1d_boundary_view
	BEGIN
	INSERT INTO v2_connection_nodes(
	    storage_area, 
		the_geom,
		code) 
	SELECT 
	    NEW.node_storage_area,
		NEW.the_geom, 
		NEW.node_code
	where not exists(
        select * from v2_connection_nodes 
		where the_geom = NEW.the_geom);
        
	UPDATE v2_1d_boundary_conditions
	    SET id                  = NEW.bound_id,
	        connection_node_id  = (select 
			                           a.id 
								   from v2_connection_nodes a 
								   where MbrTouches(NEW.the_geom,a.the_geom) =1),
	        boundary_type       = NEW.bound_boundary_type,
	        timeseries          = NEW.bound_timeseries
	    WHERE "id"              = OLD."bound_id";
    END;

drop trigger if exists v2_1d_boundary_delete;

create trigger v2_1d_boundary_delete
    instead of delete
    on v2_1d_boundary_view
    BEGIN
    DELETE FROM v2_1d_boundary_conditions
	WHERE "id" = OLD."bound_id";
end;
