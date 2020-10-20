from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.event import listen
from .sqlalchemy_add_columns import create_and_upgrade
from sqlalchemy.sql import text
import collections
import copy
import logging
import os

logger = logging.getLogger(__name__)


def load_spatialite(con, connection_record):
    """Load spatialite extension as described in
    https://geoalchemy-2.readthedocs.io/en/latest/spatialite_tutorial.html"""
    import sqlite3

    con.enable_load_extension(True)
    cur = con.cursor()
    libs = [
        # SpatiaLite >= 4.2 and Sqlite >= 3.7.17, should work on all platforms
        ("mod_spatialite", "sqlite3_modspatialite_init"),
        # SpatiaLite >= 4.2 and Sqlite < 3.7.17 (Travis)
        ("mod_spatialite.so", "sqlite3_modspatialite_init"),
        # SpatiaLite < 4.2 (linux)
        ("libspatialite.so", "sqlite3_extension_init"),
    ]
    found = False
    for lib, entry_point in libs:
        try:
            cur.execute("select load_extension('{}', '{}')".format(lib, entry_point))
        except sqlite3.OperationalError:
            logger.exception(
                "Loading extension %s from %s failed, trying the next", entry_point, lib
            )
            continue
        else:
            logger.info("Successfully loaded extension %s from %s.", entry_point, lib)
            found = True
            break
    if not found:
        raise RuntimeError("Cannot find any suitable spatialite module")
    cur.close()
    con.enable_load_extension(False)

class ViewTriggers(object):
    def __init__(self, connection_settings, db_type="spatialite", echo=False):
        """

        :param connection_settings:
        db_type (str choice): database type. 'sqlite' and 'postgresql' are
                              supported
        """
        self.settings = connection_settings
        # make sure within the ThreediDatabase object we always use 'sqlite'
        # as the db_type identifier
        self.db_type = db_type
        self.echo = echo

        self._engine = None
        self._combined_base = None  # TODO: unused?
        self._base = None  # TODO: unused?
        self._base_metadata = None

    def create_and_check_fields(self):

        # engine = self.get_engine()
        create_and_upgrade(self.engine, self.get_metadata())
        # self.metadata(engine=engine, force_refresh=True)

    def create_db(self, overwrite=False):
        if self.db_type == "spatialite":

            if overwrite and os.path.isfile(self.settings["db_file"]):
                os.remove(self.settings["db_file"])

            drv = ogr.GetDriverByName("SQLite")
            drv.CreateDataSource(self.settings["db_file"], ["SPATIALITE=YES"])
            Base.metadata.bind = self.engine
            Base.metadata.create_all(self.engine)

            # todo: add settings to improve database creation speed for older
            # versions of gdal

    @property
    def engine(self):
        # TODO: can this become a cached_property? Depends on the following method.
        return self.get_engine()

    def get_engine(self, get_seperate_engine=False):

        if self._engine is None or get_seperate_engine:
            if self.db_type == "spatialite":
                engine = create_engine(
                    "sqlite:///{0}".format(self.settings["db_path"]), echo=self.echo
                )
                listen(engine, "connect", load_spatialite)
                if get_seperate_engine:
                    return engine
                else:
                    self._engine = engine

            elif self.db_type == "postgres":
                con = (
                    "postgresql://{username}:{password}@{host}:"
                    "{port}/{database}".format(**self.settings)
                )

                engine = create_engine(con, echo=self.echo)
                if get_seperate_engine:
                    return engine
                else:
                    self._engine = engine

        return self._engine

    def get_metadata(self, including_existing_tables=True, engine=None):

        if including_existing_tables:
            metadata = copy.deepcopy(Base.metadata)
            if engine is None:
                engine = self.engine

            metadata.bind = engine
            metadata.reflect(extend_existing=True)
            return metadata
        else:
            if self._base_metadata is None:
                self._base_metadata = copy.deepcopy(Base.metadata)
            return self._base_metadata

    def get_session(self):
        return sessionmaker(bind=self.engine)()

    def add_triggers(self):
        conn = self.get_session()

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_manhole_insert;
        """)

        conn.execute(
            """
        CREATE TRIGGER v2_manhole_insert 
        INSTEAD OF INSERT 
        ON v2_manhole_view 
        BEGIN 
        INSERT INTO v2_connection_nodes(storage_area, initial_waterlevel, 
        the_geom, the_geom_linestring, code) 
        SELECT NEW.node_storage_area, NEW.node_initial_waterlevel, 
        NEW.the_geom, NEW.node_the_geom_linestring, NEW.node_code 
        WHERE not exists(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = NEW.the_geom); 

        INSERT INTO v2_manhole( display_name, code, connection_node_id, shape, 
        width, length, manhole_indicator, calculation_type, bottom_level, 
        surface_level, drain_level, sediment_level, zoom_category) 
        SELECT NEW.manh_display_name, NEW.manh_code, a.id, NEW.manh_shape,
        NEW.manh_width, NEW.manh_length, NEW.manh_manhole_indicator,
        NEW.manh_calculation_type, NEW.manh_bottom_level, 
        NEW.manh_surface_level, NEW.manh_drain_level, NEW.manh_sediment_level,
        NEW.manh_zoom_category 
        FROM v2_connection_nodes a 
        WHERE MbrTouches(a.the_geom,NEW.the_geom)=1 
        ; 
        END; 
        """)
        
        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_manhole_update;
        """)
        
        conn.execute(
        """
        CREATE TRIGGER v2_manhole_update
        INSTEAD OF UPDATE 
        ON v2_manhole_view
        BEGIN
        UPDATE v2_manhole
        SET id = NEW.manh_id, display_name = NEW.manh_display_name, code = 
        NEW.manh_code, connection_node_id = NEW.manh_connection_node_id,
        shape = NEW.manh_shape, width = NEW.manh_width, length= NEW.manh_length,
        manhole_indicator = NEW.manh_manhole_indicator, calculation_type = 
        NEW.manh_calculation_type, bottom_level = NEW.manh_bottom_level,
        surface_level = NEW.manh_surface_level, drain_level =
        NEW.manh_drain_level, sediment_level = NEW.manh_sediment_level,
        zoom_category = NEW.manh_zoom_category
        WHERE "id" = OLD."manh_id";

        UPDATE v2_connection_nodes  
        SET id = NEW.node_id, storage_area = NEW.node_storage_area,
        initial_waterlevel  = NEW.node_initial_waterlevel, the_geom_linestring = 
        NEW.node_the_geom_linestring, code = NEW.node_code, the_geom =
        NEW.the_geom
        WHERE "id" = OLD."node_id"
        ;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_manhole_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_manhole_delete
        INSTEAD OF DELETE
        ON v2_manhole_view
        BEGIN
        DELETE FROM v2_manhole
        WHERE "id" = OLD."manh_id";
        
        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND 
        id not in (select connection_node_end_id from v2_pumpstation 
               where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND 
        id not in (select connection_node_end_id from v2_channel) AND 
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pipe_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pipe_insert 
        INSTEAD OF INSERT 
        ON v2_pipe_view 
        BEGIN 
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.pipe_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.pipe_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        INSERT INTO v2_pipe(
        id, display_name, code, profile_num, sewerage_type, calculation_type, 
        invert_level_start_point, invert_level_end_point, 
        cross_section_definition_id, friction_value, friction_type, 
        dist_calc_points, material, original_length, 
        zoom_category, connection_node_start_id, connection_node_end_id)
        SELECT NEW.pipe_id, NEW.pipe_display_name, NEW.pipe_code, 
        NEW.pipe_profile_num, NEW.pipe_sewerage_type, NEW.pipe_calculation_type,
        NEW.pipe_invert_level_start_point, NEW.pipe_invert_level_end_point,
        NEW.pipe_cross_section_definition_id, NEW.pipe_friction_value, 
        NEW.pipe_friction_type, NEW.pipe_dist_calc_points, NEW.pipe_material, 
        NEW.pipe_original_length, NEW.pipe_zoom_category, 
        a.id, b.id
        FROM v2_connection_nodes a, v2_connection_nodes b
        WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
        MbrTouches(ST_endpoint(New.the_geom),b.the_geom) =1;
        END;
        """)


        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pipe_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pipe_update
        INSTEAD OF UPDATE
        ON v2_pipe_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.pipe_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.pipe_code
        WHERE NOT EXISTS(
        SELECT * from v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_pipe
        SET "id" = NEW."pipe_id", "display_name" = NEW."pipe_display_name",
        "code" = NEW."pipe_code", "profile_num" = NEW."pipe_profile_num",
        "sewerage_type" = NEW."pipe_sewerage_type","calculation_type" = 
        NEW."pipe_calculation_type", "connection_node_start_id" = (select 
        a.id FROM v2_connection_nodes a WHERE MbrTouches(
        ST_startpoint(NEW.the_geom),a.the_geom) =1), "connection_node_end_id" = 
        (select a.id FROM v2_connection_nodes a WHERE MbrTouches(
        ST_endpoint(NEW.the_geom),a.the_geom) =1), "invert_level_start_point" = 
        NEW."pipe_invert_level_start_point", "invert_level_end_point" = 
        NEW."pipe_invert_level_end_point", "cross_section_definition_id" = 
        New."pipe_cross_section_definition_id", "friction_type" = 
        NEW."pipe_friction_type", "friction_value" = NEW."pipe_friction_value", 
        "dist_calc_points" = NEW."pipe_dist_calc_points", "material" = 
        NEW."pipe_material", 
        "original_length" = NEW."pipe_original_length", "zoom_category" = 
        NEW."pipe_zoom_category"
        WHERE "id" = OLD."pipe_id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pipe_delete;
        """)


        conn.execute(
        """
        CREATE TRIGGER v2_pipe_delete
        INSTEAD OF DELETE
        ON v2_pipe_view
        BEGIN
        DELETE FROM v2_pipe
        WHERE "id" = OLD."pipe_id";

        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        drop trigger if exists v2_weir_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_weir_insert 
        INSTEAD OF INSERT
        ON v2_weir_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.weir_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.weir_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        INSERT INTO v2_weir(
        display_name, code, crest_level, crest_type, 
        cross_section_definition_id, sewerage, discharge_coefficient_positive, 
        discharge_coefficient_negative, external, zoom_category, friction_value,
        friction_type, connection_node_start_id, connection_node_end_id)
        SELECT 
        NEW.weir_display_name, NEW.weir_code, NEW.weir_crest_level,
        NEW.weir_crest_type, NEW.weir_cross_section_definition_id,
        NEW.weir_sewerage, NEW.weir_discharge_coefficient_positive, 
        NEW.weir_discharge_coefficient_negative,NEW.weir_external, 
        NEW.weir_zoom_category, NEW.weir_friction_value,NEW.weir_friction_type,
        a.id,b.id
        FROM 
        v2_connection_nodes a, 
        v2_connection_nodes b
        WHERE MbrTouches(a.the_geom,ST_Startpoint(NEW.the_geom))=1 AND 
        MbrTouches(b.the_geom,ST_endpoint(NEW.the_geom))=1
        ;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_weir_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_weir_update
        INSTEAD OF UPDATE
        ON v2_weir_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.weir_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.weir_code
        WHERE NOT EXISTS(
        SELECT * from v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_weir
        SET id = NEW.weir_id, display_name = NEW.weir_display_name, code = 
        NEW.weir_code, crest_level = NEW.weir_crest_level, crest_type = 
        NEW.weir_crest_type, cross_section_definition_id = 
        New.weir_cross_section_definition_id, sewerage = NEW.weir_sewerage,
        discharge_coefficient_positive = NEW.weir_discharge_coefficient_positive,
        discharge_coefficient_negative = NEW.weir_discharge_coefficient_negative,
        external = NEW.weir_external, zoom_category = NEW.weir_zoom_category,
        friction_value = NEW.weir_friction_value, friction_type = 
        NEW.weir_friction_type, connection_node_start_id = (SELECT a.id 
            FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id = (SELECT b.id FROM v2_connection_nodes b 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),b.the_geom) =1)
        WHERE v2_weir."id" = OLD."weir_id" ;
        END;
        """)

        conn.execute(
        """
        drop trigger if exists v2_weir_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_weir_delete
        INSTEAD OF DELETE
        ON v2_weir_view
        BEGIN
        DELETE FROM v2_weir
        WHERE "id" = OLD."weir_id";

        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        
        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_orifice_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_orifice_insert
        INSTEAD OF INSERT
        ON v2_orifice_view
        BEGIN
        INSERT INTO v2_connection_nodes(storage_area, the_geom, code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.orf_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.orf_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        INSERT INTO v2_orifice(
        display_name, code, crest_level, 	sewerage, 
        cross_section_definition_id, friction_value, friction_type, 
        discharge_coefficient_positive, discharge_coefficient_negative,
        zoom_category, crest_type, connection_node_start_id, 
        connection_node_end_id)
        SELECT 
        NEW.orf_display_name, NEW.orf_code,  
        NEW.orf_crest_level, NEW.orf_sewerage, 
        NEW.orf_cross_section_definition_id, NEW.orf_friction_value,
        NEW.orf_friction_type, NEW.orf_discharge_coefficient_positive, 
        NEW.orf_discharge_coefficient_negative, NEW.orf_zoom_category, 
        NEW.orf_crest_type, a.id, b.id
        FROM 
        v2_connection_nodes a, v2_connection_nodes b
        WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
        MbrTouches(ST_endpoint(New.the_geom),b.the_geom)=1;
        END;
        """)
        
        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_orifice_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_orifice_update
        INSTEAD OF UPDATE
        ON v2_orifice_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.orf_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.orf_code
        WHERE NOT EXISTS(
        SELECT * from v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_orifice
        SET id = NEW.orf_id, display_name = NEW.orf_display_name, code = 
        NEW.orf_code,crest_level = 
        NEW.orf_crest_level, sewerage = NEW.orf_sewerage,
        cross_section_definition_id = NEW.orf_cross_section_definition_id,
        friction_value = NEW.orf_friction_value,discharge_coefficient_positive =
        NEW.orf_discharge_coefficient_positive,discharge_coefficient_negative =
        NEW.orf_discharge_coefficient_negative, zoom_category = 
        NEW.orf_zoom_category, crest_type = NEW.orf_crest_type,
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE v2_orifice."id" = OLD."orf_id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_orifice_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_orifice_delete
        INSTEAD OF DELETE
        ON v2_orifice_view
        BEGIN
        DELETE FROM v2_orifice 
        WHERE "id" = OLD."orf_id";

        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)
        
        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_view_insert;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_culvert_view_insert 
        INSTEAD OF INSERT
        ON v2_culvert_view 
        BEGIN 
        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom, code) 
        SELECT 
        0.1, 
        ST_startpoint(NEW.the_geom), NEW.cul_code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom)); 

        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.cul_code
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom)); 

        INSERT INTO v2_culvert( 
        display_name, code, calculation_type, friction_value, friction_type,
        dist_calc_points, zoom_category, cross_section_definition_id, 
        discharge_coefficient_positive, discharge_coefficient_negative, 
        invert_level_start_point, invert_level_end_point, the_geom, 
        connection_node_start_id, connection_node_end_id) 
        SELECT 
        NEW.cul_display_name, NEW.cul_code, NEW.cul_calculation_type, 
        NEW.cul_friction_value,NEW.cul_friction_type,NEW.cul_dist_calc_points,
        NEW.cul_zoom_category,NEW.cul_cross_section_definition_id,
        NEW.cul_discharge_coefficient_positive,
        NEW.cul_discharge_coefficient_negative,NEW.cul_invert_level_start_point,
        NEW.cul_invert_level_end_point,NEW.the_geom, a.id, b.id 
        FROM 
        v2_connection_nodes a, v2_connection_nodes b 
        WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
        MbrTouches(ST_endpoint(New.the_geom),b.the_geom)=1 ; 
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_view_update;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_culvert_view_update
        INSTEAD OF UPDATE 
        ON v2_culvert_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.cul_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.cul_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_culvert 
        set id = NEW.cul_id, display_name = NEW.cul_display_name,code = 
        NEW.cul_code, calculation_type = NEW.cul_calculation_type,friction_value
        = NEW.cul_friction_value, friction_type = NEW.cul_friction_type,
        dist_calc_points = NEW.cul_dist_calc_points, zoom_category = 
        NEW.cul_zoom_category, cross_section_definition_id = 
        NEW.cul_cross_section_definition_id,invert_level_start_point =
        NEW.cul_invert_level_start_point,discharge_coefficient_negative = 
        NEW.cul_discharge_coefficient_negative,discharge_coefficient_positive = 
        NEW.cul_discharge_coefficient_positive,invert_level_end_point = 
        NEW.cul_invert_level_end_point, the_geom = NEW.the_geom,
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE v2_culvert."id"               = OLD."cul_id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_view_delete;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_culvert_view_delete
        INSTEAD OF DELETE
        ON v2_culvert_view
        BEGIN
        DELETE FROM v2_culvert
        WHERE "id" = OLD."cul_id";

        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_insert_bef;
        """)
        
        conn.execute(
        """
        CREATE TRIGGER v2_culvert_insert_bef
        BEFORE INSERT
        ON v2_culvert
        BEGIN 
        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom)); 

        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * from v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom)); 
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_insert_aft;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_culvert_insert_aft
        AFTER INSERT
        ON v2_culvert
        BEGIN 
        UPDATE v2_culvert 
        SET 
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id =(SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE connection_node_start_id is NULL OR connection_node_end_id is NULL;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_update_bef;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_culvert_update_bef
        BEFORE UPDATE
        ON v2_culvert
        BEGIN 
        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom)); 

        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom, code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_culvert
        SET 
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id =(SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE id = NEW.id;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_culvert_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_culvert_delete
        AFTER DELETE
        ON v2_culvert
        BEGIN
        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_channel_insert_bef;
        """)
        
        conn.execute(
        """
        CREATE TRIGGER v2_channel_insert_bef
        BEFORE INSERT 
        ON v2_channel
        BEGIN 
        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom)); 

        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom)); 
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_channel_insert_aft;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_channel_insert_aft
        AFTER INSERT
        ON v2_channel
        BEGIN 
        UPDATE v2_channel 
        SET 
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id =(SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE connection_node_start_id is NULL OR connection_node_end_id is NULL;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_channel_update_bef;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_channel_update_bef
        BEFORE UPDATE
        ON v2_channel
        BEGIN 
        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_Startpoint(NEW.the_geom)); 

        INSERT INTO v2_connection_nodes( 
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.code 
        WHERE NOT EXISTS( 
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_channel
        SET 
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id =(SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE id = NEW.id;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_channel_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_channel_delete
        AFTER DELETE
        ON v2_channel
        BEGIN
        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pumpstation_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pumpstation_insert 
        INSTEAD OF INSERT
        ON v2_pumpstation_view 
        BEGIN 
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.pump_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.pump_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        INSERT INTO v2_pumpstation(
        display_name, code, classification, type, sewerage, start_level,
        lower_stop_level, upper_stop_level, capacity, zoom_category,
        connection_node_start_id, connection_node_end_id)
        SELECT 
        NEW.pump_display_name, NEW.pump_code, NEW.pump_classification,
        NEW.pump_type,NEW.pump_sewerage, NEW.pump_start_level, 
        NEW.pump_lower_stop_level, NEW.pump_upper_stop_level, NEW.pump_capacity,
        NEW.pump_zoom_category,a.id,b.id
        FROM 
        v2_connection_nodes a, 
        v2_connection_nodes b
        WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom)=1 AND 
	      MbrTouches(ST_endpoint(New.the_geom),b.the_geom)=1 
        ;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pumpstation_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pumpstation_update
        INSTEAD OF UPDATE 
        ON v2_pumpstation_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_startpoint(NEW.the_geom), NEW.pump_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_startpoint(NEW.the_geom));

        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        0.1, ST_endpoint(NEW.the_geom), NEW.pump_code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = ST_endpoint(NEW.the_geom));

        UPDATE v2_pumpstation
        SET id = NEW.pump_id, display_name = NEW.pump_display_name, code = 
        NEW.pump_code, classification = NEW.pump_classification,sewerage = 
        NEW.pump_sewerage, start_level = NEW.pump_start_level, lower_stop_level=
        NEW.pump_lower_stop_level, upper_stop_level = NEW.pump_upper_stop_level,
        capacity = NEW.pump_capacity, zoom_category = NEW.pump_zoom_category,
        connection_node_start_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_startpoint(NEW.the_geom),a.the_geom) =1),
        connection_node_end_id = (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(ST_endpoint(NEW.the_geom),a.the_geom) =1)
        WHERE v2_pumpstation."id" = OLD."pump_id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pumpstation_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pumpstation_delete
        INSTEAD OF DELETE
        ON v2_pumpstation_view
        BEGIN
        DELETE FROM v2_pumpstation 
        WHERE "id" = OLD."pump_id";

        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pumpstation_point_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pumpstation_point_insert 
        INSTEAD OF INSERT
        ON v2_pumpstation_point_view 
        BEGIN 
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        CASE WHEN NEW.storage_area is not NULL THEN NEW.storage_area
        ELSE 0.1 END, NEW.the_geom, NEW.code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = NEW.the_geom);

        INSERT INTO v2_pumpstation(
        display_name, code, classification, type, sewerage, start_level,
        lower_stop_level, upper_stop_level, capacity, zoom_category,
        connection_node_start_id)
        SELECT 
        NEW.display_name, NEW.code, NEW.classification, NEW.type,NEW.sewerage, 
        NEW.start_level, NEW.lower_stop_level, NEW.upper_stop_level, 
        NEW.capacity, NEW.zoom_category,a.id
        FROM 
        v2_connection_nodes a
        WHERE MbrTouches(NEW.the_geom,a.the_geom)=1
        ;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pumpstation_point_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pumpstation_point_update
        INSTEAD OF UPDATE 
        ON v2_pumpstation_point_view
        BEGIN
        INSERT INTO v2_connection_nodes(
        storage_area, the_geom,code) 
        SELECT 
        CASE WHEN NEW.storage_area is not NULL THEN NEW.storage_area
        ELSE 0.1 END, NEW.the_geom, NEW.code
        WHERE NOT EXISTS(
        SELECT * FROM v2_connection_nodes 
        WHERE the_geom = NEW.the_geom);

        UPDATE v2_pumpstation
        SET id = NEW.pump_id, display_name = NEW.display_name, code = 
        NEW.code, classification = NEW.classification,sewerage = NEW.sewerage, 
        start_level = NEW.start_level, lower_stop_level=NEW.lower_stop_level, 
        upper_stop_level = NEW.upper_stop_level, capacity = NEW.capacity, 
        zoom_category = NEW.zoom_category,connection_node_start_id = 
        (SELECT a.id FROM v2_connection_nodes a 
            WHERE MbrTouches(NEW.the_geom,a.the_geom) =1)
        WHERE v2_pumpstation."id" = OLD."pump_id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_pumpstation_point_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_pumpstation_point_delete
        INSTEAD OF DELETE
        ON v2_pumpstation_point_view
        BEGIN
        DELETE FROM v2_pumpstation 
        WHERE "id" = OLD."pump_id";

        DELETE FROM v2_connection_nodes where 
        id not in (select connection_node_id from v2_manhole) AND 
        id not in (select connection_node_start_id from v2_pipe) AND 
        id not in (select connection_node_end_id from v2_pipe) AND 
        id not in (select connection_node_start_id from v2_weir) AND 
        id not in (select connection_node_end_id from v2_weir) AND 
        id not in (select connection_node_start_id from v2_pumpstation) AND
        id not in (select connection_node_end_id from v2_pumpstation
                   where connection_node_end_id is not null) AND 
        id not in (select connection_node_start_id from v2_channel) AND
        id not in (select connection_node_end_id from v2_channel) AND
        id not in (select connection_node_start_id from v2_culvert) AND 
        id not in (select connection_node_end_id from v2_culvert) AND 
        id not in (select connection_node_start_id from v2_orifice) AND 
        id not in (select connection_node_end_id from v2_orifice);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_1d_boundary_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_1d_boundary_insert
        INSTEAD OF INSERT
        ON v2_1d_boundary_conditions_view 
        BEGIN 
        INSERT INTO v2_1d_boundary_conditions( 
        boundary_type, connection_node_id,timeseries)
        SELECT 
        NEW.boundary_type, a.id, NEW.timeseries
        FROM v2_connection_nodes a 
        WHERE MbrTouches(a.the_geom,NEW.the_geom)=1;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_1d_boundary_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_1d_boundary_update
        INSTEAD OF UPDATE
        ON v2_1d_boundary_conditions_view
        BEGIN
        UPDATE v2_1d_boundary_conditions
        SET id = NEW.id, connection_node_id  = (SELECT 
        a.id FROM v2_connection_nodes a 
        WHERE MbrTouches(NEW.the_geom,a.the_geom) =1),
        boundary_type = NEW.boundary_type, timeseries = 
        NEW.timeseries
        WHERE "id" = OLD."id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_1d_boundary_delete;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_1d_boundary_delete
        INSTEAD OF DELETE
        ON v2_1d_boundary_conditions_view
        BEGIN
        DELETE FROM v2_1d_boundary_conditions
        WHERE "id" = OLD."id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_1d_lateral_insert;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_1d_lateral_insert
        INSTEAD OF INSERT
        ON v2_1d_lateral_view 
        BEGIN 
        INSERT INTO v2_1d_lateral( 
        connection_node_id,timeseries)
        SELECT 
        a.id, NEW.timeseries
        FROM v2_connection_nodes a 
        WHERE MbrTouches(a.the_geom,NEW.the_geom)=1;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_lateral_update;
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_lateral_update
        INSTEAD OF UPDATE
        ON v2_1d_lateral_view
        BEGIN
        UPDATE v2_1d_lateral
        SET id = NEW.id, connection_node_id  = (SELECT 
        a.id FROM v2_connection_nodes a 
        WHERE MbrTouches(NEW.the_geom,a.the_geom) =1),
        timeseries = NEW.timeseries
        WHERE "id" = OLD."id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_1d_lateral_delete
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_1d_lateral_delete
        INSTEAD OF DELETE
        ON v2_1d_lateral_view
        BEGIN
        DELETE FROM v2_1d_lateral
        WHERE "id" = OLD."id";
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_cross_section_location_view_insert
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_cross_section_location_view_insert
        INSTEAD OF INSERT
        ON v2_cross_section_location_view 
        BEGIN 
        INSERT INTO v2_cross_section_location( 
        reference_level, definition_id,channel_id,code,friction_type,
        friction_value,bank_level,id,the_geom)
        VALUES(NEW.loc_reference_level,NEW.loc_definition_id,NEW.loc_channel_id,
        NEW.loc_code, NEW.loc_friction_type, NEW.loc_friction_value,
        NEW.loc_bank_level,NEW.loc_id,NEW.the_geom);
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_cross_section_location_view_update
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_cross_section_location_view_update
        INSTEAD OF UPDATE
        ON v2_cross_section_location_view 
        BEGIN 
        UPDATE v2_cross_section_location
        SET reference_level =NEW.loc_reference_level, definition_id = 
        NEW.loc_definition_id, channel_id =NEW.loc_channel_id, code = 
        NEW.loc_code, friction_type = NEW.loc_friction_type, friction_value = 
        NEW.loc_friction_value, bank_level = NEW.loc_bank_level, id = NEW.loc_id,
        the_geom = NEW.the_geom
        WHERE id = OLD.loc_id;
        END;
        """)

        conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_cross_section_location_view_delete
        """)

        conn.execute(
        """
        CREATE TRIGGER v2_cross_section_location_view_delete
        INSTEAD OF DELETE
        ON v2_cross_section_location_view
        BEGIN
        DELETE FROM v2_cross_section_location
        WHERE "id" = old.loc_id;
        END;
        """)

       conn.execute(
        """
        DROP TRIGGER IF EXISTS v2_impervious_surface_delete;
        """)

        conn.execute(
            """
        CREATE TRIGGER v2_impervious_surface_delete 
        AFTER DELETE 
        ON v2_impervious_surface 
        BEGIN 
        DELETE FROM v2_impervious_surface_map
        WHERE impervious_surface_id not in (SELECT id FROM v2_impervious_surface)
        ;
        END; 
        """)

        conn.commit()
        conn.close()