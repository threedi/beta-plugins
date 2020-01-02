--
-- PostgreSQL database dump
--

-- Dumped from database version 9.3.24
-- Dumped by pg_dump version 9.5.3

-- Started on 2018-12-21 09:47:20

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

SET default_with_oids = false;

-- Function: public.count_node(anyarray, integer)

-- DROP FUNCTION public.count_node(anyarray, integer);

CREATE OR REPLACE FUNCTION public.count_node(
    anyarray,
    node_id integer)
  RETURNS integer AS
$BODY$
                DECLARE
                  table_name text;
                  sel_count integer;
                  counter integer;
                BEGIN
                counter := 0;
                FOREACH table_name IN ARRAY $1
                LOOP
                  RAISE NOTICE 'processing table %',table_name;
                  EXECUTE format('
                 SELECT COUNT(*) FROM %I AS x
                    WHERE x.connection_node_start_id = %L
                    OR x.connection_node_end_id = %L'
                      , table_name, $2, $2)
                     INTO sel_count;
                  RAISE NOTICE 'counted % appearences of
                     connection_node_id % ', sel_count, $2;
                  counter := counter + sel_count;
                  IF counter > 1 THEN
                 EXIT;
                  END IF;
                END LOOP;
                RETURN counter;
                END
                $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.count_node(anyarray, integer)
  OWNER TO postgres;
  
-- Function: public.intersects_connection_node(geometry, integer, integer)

-- DROP FUNCTION public.intersects_connection_node(geometry, integer, integer);

CREATE OR REPLACE FUNCTION public.intersects_connection_node(
    channel_geom geometry,
    channel_start_id integer,
    channel_end_id integer)
  RETURNS integer AS
$BODY$
                SELECT COUNT(*)::integer FROM v2_connection_nodes AS c
                  WHERE
                    ($2 = c.id OR $3 = c.id)
                  AND
                    (ST_Intersects(c.the_geom, ST_StartPoint($1))
                      OR
                     ST_Intersects(c.the_geom, ST_EndPoint($1)))
              $BODY$
  LANGUAGE sql STABLE
  COST 100;
ALTER FUNCTION public.intersects_connection_node(geometry, integer, integer)
  OWNER TO postgres;
  
-- Function: public.intersects_channel(geometry, integer)

-- DROP FUNCTION public.intersects_channel(geometry, integer);

CREATE OR REPLACE FUNCTION public.intersects_channel(
    x_sec_geom geometry,
    x_sec_channel_id integer)
  RETURNS integer AS
$BODY$
        DECLARE
          result integer;
        BEGIN
            SELECT COUNT(*)::integer FROM v2_channel AS c
            WHERE ($2 = c.id)
            AND
            (ST_Intersects(c.the_geom, $1))
            INTO result;
            IF result > 0 THEN
               UPDATE
                  v2_channel
               SET
                  the_geom = ST_LineMerge(
                     ST_Union(
                        ST_Line_Substring(v2_channel.the_geom, 0, ST_Line_Locate_Point(v2_channel.the_geom, $1)),
                        ST_Line_Substring(v2_channel.the_geom, ST_Line_Locate_Point(v2_channel.the_geom, $1), 1)
                     ))
                WHERE ($2 = v2_channel.id);
            END IF;
            return result;
        END
        $BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION public.intersects_channel(geometry, integer)
  OWNER TO postgres;

-- Function: public.on_channel(integer, geometry)

-- DROP FUNCTION public.on_channel(integer, geometry);

CREATE OR REPLACE FUNCTION public.on_channel(
    channel_pk integer,
    pnt_geom geometry)
  RETURNS integer AS
$BODY$
           SELECT COUNT(*)::integer FROM v2_channel AS c
           WHERE  c.id = $1
           AND ST_Intersects(c.the_geom, $2);
           $BODY$
  LANGUAGE sql STABLE
  COST 100;
ALTER FUNCTION public.on_channel(integer, geometry)
  OWNER TO postgres;

  
--
-- TOC entry 230 (class 1259 OID 12491347)
-- Name: v2_1d_boundary_conditions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_1d_boundary_conditions (
    id integer NOT NULL,
    connection_node_id integer NOT NULL,
    boundary_type integer,
    timeseries text,
    CONSTRAINT boundary_must_have_only_one_connection CHECK ((count_node(ARRAY['v2_channel'::text, 'v2_weir'::text, 'v2_orifice'::text, 'v2_culvert'::text, 'v2_pipe'::text, 'v2_pumpstation'::text], connection_node_id) = 1))
);


--
-- TOC entry 229 (class 1259 OID 12491345)
-- Name: v2_1d_boundary_conditions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_1d_boundary_conditions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3961 (class 0 OID 0)
-- Dependencies: 229
-- Name: v2_1d_boundary_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_1d_boundary_conditions_id_seq OWNED BY v2_1d_boundary_conditions.id;


--
-- TOC entry 240 (class 1259 OID 12491438)
-- Name: v2_1d_lateral; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_1d_lateral (
    id integer NOT NULL,
    connection_node_id integer NOT NULL,
    timeseries text
);


--
-- TOC entry 239 (class 1259 OID 12491436)
-- Name: v2_1d_lateral_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_1d_lateral_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3962 (class 0 OID 0)
-- Dependencies: 239
-- Name: v2_1d_lateral_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_1d_lateral_id_seq OWNED BY v2_1d_lateral.id;


--
-- TOC entry 266 (class 1259 OID 12491696)
-- Name: v2_2d_boundary_conditions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_2d_boundary_conditions (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    timeseries text,
    boundary_type integer,
    the_geom geometry(LineString,28992)
);


--
-- TOC entry 265 (class 1259 OID 12491694)
-- Name: v2_2d_boundary_conditions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_2d_boundary_conditions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3963 (class 0 OID 0)
-- Dependencies: 265
-- Name: v2_2d_boundary_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_2d_boundary_conditions_id_seq OWNED BY v2_2d_boundary_conditions.id;


--
-- TOC entry 254 (class 1259 OID 12491611)
-- Name: v2_2d_lateral; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_2d_lateral (
    id integer NOT NULL,
    type integer,
    the_geom geometry(Point,28992),
    timeseries text
);


--
-- TOC entry 253 (class 1259 OID 12491609)
-- Name: v2_2d_lateral_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_2d_lateral_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3964 (class 0 OID 0)
-- Dependencies: 253
-- Name: v2_2d_lateral_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_2d_lateral_id_seq OWNED BY v2_2d_lateral.id;


--
-- TOC entry 276 (class 1259 OID 12491797)
-- Name: v2_aggregation_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_aggregation_settings (
    id integer NOT NULL,
    global_settings_id integer,
    var_name character varying(100) NOT NULL,
    flow_variable character varying(100),
    aggregation_method character varying(100) NOT NULL,
    aggregation_in_space boolean NOT NULL,
    timestep integer NOT NULL,
    CONSTRAINT aggregate_var CHECK ((((flow_variable)::text = ANY ((ARRAY['max_timestep'::character varying, 'vol_2D_groundwater_sum'::character varying, 'vol_2D_rain'::character varying, 'min_timestep'::character varying, 'vol_2D_lateral'::character varying, 'infiltration'::character varying, 'flow_velocity'::character varying, 'max_surface_grid'::character varying, 'vol_pumps_drained'::character varying, 'vol_2D_sum'::character varying, 'vol_1D_lateral'::character varying, 'vol_inflow_bounds'::character varying, 'init_2D_volume'::character varying, 'wet_cross-section'::character varying, 'pump_discharge'::character varying, 'rain'::character varying, 'volume'::character varying, 'vol_1D_rain'::character varying, 'init_1D_volume'::character varying, 'discharge'::character varying, 'sum_2D_infil'::character varying, 'lateral_discharge'::character varying, 'waterlevel'::character varying, 'vol_1D_sum'::character varying, 'wet_surface'::character varying, 'vol_outflow_bounds'::character varying])::text[])) OR (((flow_variable IS NULL) OR ((flow_variable)::text = ''::text)) AND ((var_name)::text = ANY ((ARRAY['max_timestep'::character varying, 'vol_2D_groundwater_sum'::character varying, 'vol_2D_rain'::character varying, 'min_timestep'::character varying, 'vol_2D_lateral'::character varying, 'infiltration'::character varying, 'flow_velocity'::character varying, 'max_surface_grid'::character varying, 'vol_pumps_drained'::character varying, 'vol_2D_sum'::character varying, 'vol_1D_lateral'::character varying, 'vol_inflow_bounds'::character varying, 'init_2D_volume'::character varying, 'wet_cross-section'::character varying, 'pump_discharge'::character varying, 'rain'::character varying, 'volume'::character varying, 'vol_1D_rain'::character varying, 'init_1D_volume'::character varying, 'discharge'::character varying, 'sum_2D_infil'::character varying, 'lateral_discharge'::character varying, 'waterlevel'::character varying, 'vol_1D_sum'::character varying, 'wet_surface'::character varying, 'vol_outflow_bounds'::character varying])::text[])))))
);


--
-- TOC entry 275 (class 1259 OID 12491795)
-- Name: v2_aggregation_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_aggregation_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3965 (class 0 OID 0)
-- Dependencies: 275
-- Name: v2_aggregation_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_aggregation_settings_id_seq OWNED BY v2_aggregation_settings.id;


--
-- TOC entry 278 (class 1259 OID 12491820)
-- Name: v2_calculation_point; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_calculation_point (
    id integer NOT NULL,
    content_type_id integer NOT NULL,
    user_ref character varying(80) NOT NULL,
    calc_type integer NOT NULL,
    the_geom geometry(Point,28992) NOT NULL
);


--
-- TOC entry 277 (class 1259 OID 12491818)
-- Name: v2_calculation_point_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_calculation_point_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3966 (class 0 OID 0)
-- Dependencies: 277
-- Name: v2_calculation_point_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_calculation_point_id_seq OWNED BY v2_calculation_point.id;


--
-- TOC entry 234 (class 1259 OID 12491379)
-- Name: v2_channel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_channel (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    calculation_type integer,
    dist_calc_points double precision,
    zoom_category integer,
    the_geom geometry(LineString,28992) NOT NULL,
    connection_node_start_id integer,
    connection_node_end_id integer,
    CONSTRAINT has_two_connection_nodes CHECK ((intersects_connection_node(the_geom, connection_node_start_id, connection_node_end_id) = 2))
);


--
-- TOC entry 233 (class 1259 OID 12491377)
-- Name: v2_channel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_channel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3967 (class 0 OID 0)
-- Dependencies: 233
-- Name: v2_channel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_channel_id_seq OWNED BY v2_channel.id;


--
-- TOC entry 280 (class 1259 OID 12491832)
-- Name: v2_connected_pnt; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_connected_pnt (
    id integer NOT NULL,
    exchange_level double precision,
    calculation_pnt_id integer NOT NULL,
    levee_id integer,
    the_geom geometry(Point,28992) NOT NULL
);


--
-- TOC entry 279 (class 1259 OID 12491830)
-- Name: v2_connected_pnt_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_connected_pnt_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3968 (class 0 OID 0)
-- Dependencies: 279
-- Name: v2_connected_pnt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_connected_pnt_id_seq OWNED BY v2_connected_pnt.id;


--
-- TOC entry 228 (class 1259 OID 12491334)
-- Name: v2_connection_nodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_connection_nodes (
    id integer NOT NULL,
    storage_area double precision,
    initial_waterlevel double precision,
    the_geom geometry(Point,28992) NOT NULL,
    the_geom_linestring geometry(LineString,28992),
    code character varying(100) NOT NULL
);


--
-- TOC entry 227 (class 1259 OID 12491332)
-- Name: v2_connection_nodes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_connection_nodes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3969 (class 0 OID 0)
-- Dependencies: 227
-- Name: v2_connection_nodes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_connection_nodes_id_seq OWNED BY v2_connection_nodes.id;


--
-- TOC entry 290 (class 1259 OID 12492141)
-- Name: v2_control; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control (
    id integer NOT NULL,
    control_group_id integer,
    control_type character varying(15),
    control_id integer,
    measure_group_id integer,
    start character varying(50),
    "end" character varying(50),
    measure_frequency integer
);


--
-- TOC entry 298 (class 1259 OID 12492191)
-- Name: v2_control_delta; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_delta (
    id integer NOT NULL,
    measure_variable character varying(50),
    measure_delta double precision,
    measure_dt double precision,
    action_type character varying(50),
    action_value character varying(50),
    action_time double precision,
    target_type character varying(100),
    target_id integer
);


--
-- TOC entry 297 (class 1259 OID 12492189)
-- Name: v2_control_delta_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_delta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3970 (class 0 OID 0)
-- Dependencies: 297
-- Name: v2_control_delta_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_delta_id_seq OWNED BY v2_control_delta.id;


--
-- TOC entry 282 (class 1259 OID 12491937)
-- Name: v2_control_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_group (
    id integer NOT NULL,
    name character varying(100),
    description text
);


--
-- TOC entry 281 (class 1259 OID 12491935)
-- Name: v2_control_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3971 (class 0 OID 0)
-- Dependencies: 281
-- Name: v2_control_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_group_id_seq OWNED BY v2_control_group.id;


--
-- TOC entry 289 (class 1259 OID 12492139)
-- Name: v2_control_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3972 (class 0 OID 0)
-- Dependencies: 289
-- Name: v2_control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_id_seq OWNED BY v2_control.id;


--
-- TOC entry 288 (class 1259 OID 12492098)
-- Name: v2_control_measure_group; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_measure_group (
    id integer NOT NULL
);


--
-- TOC entry 287 (class 1259 OID 12492096)
-- Name: v2_control_measure_group_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_measure_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3973 (class 0 OID 0)
-- Dependencies: 287
-- Name: v2_control_measure_group_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_measure_group_id_seq OWNED BY v2_control_measure_group.id;


--
-- TOC entry 292 (class 1259 OID 12492161)
-- Name: v2_control_measure_map; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_measure_map (
    id integer NOT NULL,
    measure_group_id integer,
    object_type character varying(100),
    object_id integer,
    weight numeric(3,2)
);


--
-- TOC entry 291 (class 1259 OID 12492159)
-- Name: v2_control_measure_map_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_measure_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3974 (class 0 OID 0)
-- Dependencies: 291
-- Name: v2_control_measure_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_measure_map_id_seq OWNED BY v2_control_measure_map.id;


--
-- TOC entry 294 (class 1259 OID 12492175)
-- Name: v2_control_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_memory (
    id integer NOT NULL,
    measure_variable character varying(50),
    upper_threshold double precision,
    lower_threshold double precision,
    action_type character varying(50),
    action_value character varying(50),
    target_type character varying(100),
    target_id integer,
    is_active boolean NOT NULL,
    is_inverse boolean NOT NULL
);


--
-- TOC entry 293 (class 1259 OID 12492173)
-- Name: v2_control_memory_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_memory_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3975 (class 0 OID 0)
-- Dependencies: 293
-- Name: v2_control_memory_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_memory_id_seq OWNED BY v2_control_memory.id;


--
-- TOC entry 296 (class 1259 OID 12492183)
-- Name: v2_control_pid; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_pid (
    id integer NOT NULL,
    measure_variable character varying(50),
    setpoint double precision,
    kp double precision,
    ki double precision,
    kd double precision,
    action_type character varying(50),
    target_type character varying(100),
    target_id integer,
    target_upper_limit character varying(50),
    target_lower_limit character varying(50)
);


--
-- TOC entry 295 (class 1259 OID 12492181)
-- Name: v2_control_pid_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_pid_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3976 (class 0 OID 0)
-- Dependencies: 295
-- Name: v2_control_pid_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_pid_id_seq OWNED BY v2_control_pid.id;


--
-- TOC entry 286 (class 1259 OID 12492081)
-- Name: v2_control_table; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_table (
    id integer NOT NULL,
    action_table text,
    action_type character varying(50),
    measure_variable character varying(50),
    measure_operator character varying(2),
    target_type character varying(100),
    target_id integer
);


--
-- TOC entry 285 (class 1259 OID 12492079)
-- Name: v2_control_table_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_table_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3977 (class 0 OID 0)
-- Dependencies: 285
-- Name: v2_control_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_table_id_seq OWNED BY v2_control_table.id;


--
-- TOC entry 300 (class 1259 OID 12492199)
-- Name: v2_control_timed; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_control_timed (
    id integer NOT NULL,
    action_type character varying(50),
    action_table text,
    target_type character varying(100),
    target_id integer
);


--
-- TOC entry 299 (class 1259 OID 12492197)
-- Name: v2_control_timed_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_control_timed_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3978 (class 0 OID 0)
-- Dependencies: 299
-- Name: v2_control_timed_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_control_timed_id_seq OWNED BY v2_control_timed.id;


--
-- TOC entry 236 (class 1259 OID 12491403)
-- Name: v2_cross_section_definition; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_cross_section_definition (
    id integer NOT NULL,
    shape integer,
    width character varying(255),
    height character varying(255),
    code character varying(100) NOT NULL
);


--
-- TOC entry 235 (class 1259 OID 12491401)
-- Name: v2_cross_section_definition_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_cross_section_definition_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3979 (class 0 OID 0)
-- Dependencies: 235
-- Name: v2_cross_section_definition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_cross_section_definition_id_seq OWNED BY v2_cross_section_definition.id;


--
-- TOC entry 238 (class 1259 OID 12491414)
-- Name: v2_cross_section_location; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_cross_section_location (
    id integer NOT NULL,
    channel_id integer,
    definition_id integer,
    reference_level double precision,
    friction_type integer,
    friction_value double precision,
    bank_level double precision,
    the_geom geometry(Point,28992),
    code character varying(100) NOT NULL,
    CONSTRAINT lies_on_channel_vertex CHECK ((intersects_channel(the_geom, channel_id) = 1))
);


--
-- TOC entry 237 (class 1259 OID 12491412)
-- Name: v2_cross_section_location_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_cross_section_location_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3980 (class 0 OID 0)
-- Dependencies: 237
-- Name: v2_cross_section_location_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_cross_section_location_id_seq OWNED BY v2_cross_section_location.id;


--
-- TOC entry 252 (class 1259 OID 12491563)
-- Name: v2_culvert; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_culvert (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    calculation_type integer,
    friction_value double precision,
    friction_type integer,
    dist_calc_points double precision,
    zoom_category integer,
    cross_section_definition_id integer,
    discharge_coefficient_positive double precision NOT NULL,
    discharge_coefficient_negative double precision NOT NULL,
    invert_level_start_point double precision,
    invert_level_end_point double precision,
    the_geom geometry(LineString,28992) NOT NULL,
    connection_node_start_id integer,
    connection_node_end_id integer,
    CONSTRAINT has_two_connection_nodes CHECK ((intersects_connection_node(the_geom, connection_node_start_id, connection_node_end_id) = 2))
);


--
-- TOC entry 251 (class 1259 OID 12491561)
-- Name: v2_culvert_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_culvert_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3981 (class 0 OID 0)
-- Dependencies: 251
-- Name: v2_culvert_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_culvert_id_seq OWNED BY v2_culvert.id;


--
-- TOC entry 284 (class 1259 OID 12492069)
-- Name: v2_dem_average_area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_dem_average_area (
    id integer NOT NULL,
    the_geom geometry(Polygon,28992)
);


--
-- TOC entry 283 (class 1259 OID 12492067)
-- Name: v2_dem_average_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_dem_average_area_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3982 (class 0 OID 0)
-- Dependencies: 283
-- Name: v2_dem_average_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_dem_average_area_id_seq OWNED BY v2_dem_average_area.id;


--
-- TOC entry 262 (class 1259 OID 12491658)
-- Name: v2_floodfill; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_floodfill (
    id integer NOT NULL,
    waterlevel double precision,
    the_geom geometry(Point,28992)
);


--
-- TOC entry 261 (class 1259 OID 12491656)
-- Name: v2_floodfill_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_floodfill_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3983 (class 0 OID 0)
-- Dependencies: 261
-- Name: v2_floodfill_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_floodfill_id_seq OWNED BY v2_floodfill.id;


--
-- TOC entry 258 (class 1259 OID 12491635)
-- Name: v2_global_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_global_settings (
    id integer NOT NULL,
    use_2d_flow boolean NOT NULL,
    use_1d_flow boolean NOT NULL,
    manhole_storage_area double precision,
    name character varying(128),
    sim_time_step double precision NOT NULL,
    output_time_step double precision,
    nr_timesteps integer NOT NULL,
    start_time timestamp with time zone,
    start_date date NOT NULL,
    grid_space double precision NOT NULL,
    dist_calc_points double precision NOT NULL,
    kmax integer NOT NULL,
    guess_dams integer,
    table_step_size double precision NOT NULL,
    flooding_threshold double precision NOT NULL,
    advection_1d integer NOT NULL,
    advection_2d integer NOT NULL,
    dem_file character varying(255),
    frict_type integer,
    frict_coef double precision NOT NULL,
    frict_coef_file character varying(255),
    water_level_ini_type integer,
    initial_waterlevel double precision NOT NULL,
    initial_waterlevel_file character varying(255),
    interception_global double precision,
    interception_file character varying(255),
    dem_obstacle_detection boolean NOT NULL,
    dem_obstacle_height double precision,
    embedded_cutoff_threshold double precision,
    epsg_code integer,
    timestep_plus boolean NOT NULL,
    max_angle_1d_advection double precision,
    minimum_sim_time_step double precision,
    maximum_sim_time_step double precision,
    frict_avg integer NOT NULL,
    wind_shielding_file character varying(255),
    control_group_id integer,
    numerical_settings_id integer NOT NULL,
    use_0d_inflow integer NOT NULL,
    table_step_size_1d double precision,
    table_step_size_volume_2d double precision,
    use_2d_rain integer NOT NULL,
    initial_groundwater_level double precision,
    initial_groundwater_level_file character varying(255),
    initial_groundwater_level_type integer,
    groundwater_settings_id integer,
    simple_infiltration_settings_id integer,
    interflow_settings_id integer
);


--
-- TOC entry 257 (class 1259 OID 12491633)
-- Name: v2_global_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_global_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3984 (class 0 OID 0)
-- Dependencies: 257
-- Name: v2_global_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_global_settings_id_seq OWNED BY v2_global_settings.id;


--
-- TOC entry 260 (class 1259 OID 12491646)
-- Name: v2_grid_refinement; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_grid_refinement (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    refinement_level integer,
    the_geom geometry(LineString,28992),
    code character varying(100) NOT NULL
);


--
-- TOC entry 310 (class 1259 OID 12492303)
-- Name: v2_grid_refinement_area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_grid_refinement_area (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    refinement_level integer,
    code character varying(100) NOT NULL,
    the_geom geometry(Polygon,28992)
);


--
-- TOC entry 309 (class 1259 OID 12492301)
-- Name: v2_grid_refinement_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_grid_refinement_area_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3985 (class 0 OID 0)
-- Dependencies: 309
-- Name: v2_grid_refinement_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_grid_refinement_area_id_seq OWNED BY v2_grid_refinement_area.id;


--
-- TOC entry 259 (class 1259 OID 12491644)
-- Name: v2_grid_refinement_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_grid_refinement_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3986 (class 0 OID 0)
-- Dependencies: 259
-- Name: v2_grid_refinement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_grid_refinement_id_seq OWNED BY v2_grid_refinement.id;


--
-- TOC entry 312 (class 1259 OID 12492315)
-- Name: v2_groundwater; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_groundwater (
    id integer NOT NULL,
    groundwater_impervious_layer_level double precision,
    groundwater_impervious_layer_level_file character varying(255),
    groundwater_impervious_layer_level_type integer,
    phreatic_storage_capacity double precision,
    phreatic_storage_capacity_file character varying(255),
    phreatic_storage_capacity_type integer,
    equilibrium_infiltration_rate double precision,
    equilibrium_infiltration_rate_file character varying(255),
    equilibrium_infiltration_rate_type integer,
    initial_infiltration_rate double precision,
    initial_infiltration_rate_file character varying(255),
    initial_infiltration_rate_type integer,
    infiltration_decay_period double precision,
    infiltration_decay_period_file character varying(255),
    infiltration_decay_period_type integer,
    groundwater_hydro_connectivity double precision,
    groundwater_hydro_connectivity_file character varying(255),
    groundwater_hydro_connectivity_type integer,
    display_name character varying(255),
    leakage double precision,
    leakage_file character varying(255)
);


--
-- TOC entry 311 (class 1259 OID 12492313)
-- Name: v2_groundwater_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_groundwater_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3987 (class 0 OID 0)
-- Dependencies: 311
-- Name: v2_groundwater_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_groundwater_id_seq OWNED BY v2_groundwater.id;


--
-- TOC entry 244 (class 1259 OID 12491481)
-- Name: v2_impervious_surface; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_impervious_surface (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    surface_class character varying(128) NOT NULL,
    surface_sub_class character varying(128),
    surface_inclination character varying(64) NOT NULL,
    zoom_category integer,
    nr_of_inhabitants double precision,
    dry_weather_flow double precision,
    function character varying(64),
    area double precision,
    the_geom geometry(Polygon,28992)
);


--
-- TOC entry 274 (class 1259 OID 12491758)
-- Name: v2_impervious_surface_map; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_impervious_surface_map (
    id integer NOT NULL,
    impervious_surface_id integer,
    connection_node_id integer NOT NULL,
    percentage double precision
);


--
-- TOC entry 243 (class 1259 OID 12491479)
-- Name: v2_impervious_surface_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_impervious_surface_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3988 (class 0 OID 0)
-- Dependencies: 243
-- Name: v2_impervious_surface_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_impervious_surface_id_seq OWNED BY v2_impervious_surface.id;


--
-- TOC entry 273 (class 1259 OID 12491756)
-- Name: v2_impervious_surface_map_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_impervious_surface_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3989 (class 0 OID 0)
-- Dependencies: 273
-- Name: v2_impervious_surface_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_impervious_surface_map_id_seq OWNED BY v2_impervious_surface_map.id;


--
-- TOC entry 256 (class 1259 OID 12491623)
-- Name: v2_initial_waterlevel; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_initial_waterlevel (
    id integer NOT NULL,
    waterlevel_summer double precision,
    waterlevel_winter double precision,
    waterlevel double precision,
    the_geom geometry(Polygon,28992)
);


--
-- TOC entry 255 (class 1259 OID 12491621)
-- Name: v2_initial_waterlevel_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_initial_waterlevel_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3990 (class 0 OID 0)
-- Dependencies: 255
-- Name: v2_initial_waterlevel_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_initial_waterlevel_id_seq OWNED BY v2_initial_waterlevel.id;


--
-- TOC entry 316 (class 1259 OID 12492337)
-- Name: v2_interflow; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_interflow (
    id integer NOT NULL,
    interflow_type integer NOT NULL,
    porosity double precision,
    porosity_file character varying(255),
    porosity_layer_thickness double precision,
    impervious_layer_elevation double precision,
    hydraulic_conductivity double precision,
    hydraulic_conductivity_file character varying(255),
    display_name character varying(255)
);


--
-- TOC entry 315 (class 1259 OID 12492335)
-- Name: v2_interflow_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_interflow_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3991 (class 0 OID 0)
-- Dependencies: 315
-- Name: v2_interflow_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_interflow_id_seq OWNED BY v2_interflow.id;


--
-- TOC entry 270 (class 1259 OID 12491734)
-- Name: v2_levee; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_levee (
    id integer NOT NULL,
    crest_level double precision,
    the_geom geometry(LineString,28992),
    material integer,
    max_breach_depth double precision,
    code character varying(100) NOT NULL
);


--
-- TOC entry 269 (class 1259 OID 12491732)
-- Name: v2_levee_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_levee_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3992 (class 0 OID 0)
-- Dependencies: 269
-- Name: v2_levee_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_levee_id_seq OWNED BY v2_levee.id;


--
-- TOC entry 232 (class 1259 OID 12491365)
-- Name: v2_manhole; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_manhole (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    connection_node_id integer NOT NULL,
    shape character varying(4),
    width double precision,
    length double precision,
    manhole_indicator integer,
    calculation_type integer,
    bottom_level double precision,
    surface_level double precision,
    drain_level double precision,
    sediment_level double precision,
    zoom_category integer
);


--
-- TOC entry 231 (class 1259 OID 12491363)
-- Name: v2_manhole_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_manhole_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3993 (class 0 OID 0)
-- Dependencies: 231
-- Name: v2_manhole_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_manhole_id_seq OWNED BY v2_manhole.id;


--
-- TOC entry 302 (class 1259 OID 12492211)
-- Name: v2_numerical_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_numerical_settings (
    id integer NOT NULL,
    cfl_strictness_factor_1d double precision,
    cfl_strictness_factor_2d double precision,
    convergence_cg double precision,
    convergence_eps double precision,
    flow_direction_threshold double precision,
    frict_shallow_water_correction integer,
    general_numerical_threshold double precision,
    integration_method integer,
    limiter_grad_1d integer,
    limiter_grad_2d integer,
    limiter_slope_crossectional_area_2d integer,
    limiter_slope_friction_2d integer,
    max_nonlin_iterations integer,
    max_degree integer NOT NULL,
    minimum_friction_velocity double precision,
    minimum_surface_area double precision,
    precon_cg integer,
    preissmann_slot double precision,
    pump_implicit_ratio double precision,
    thin_water_layer_definition double precision,
    use_of_cg integer NOT NULL,
    use_of_nested_newton integer NOT NULL
);


--
-- TOC entry 301 (class 1259 OID 12492209)
-- Name: v2_numerical_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_numerical_settings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3994 (class 0 OID 0)
-- Dependencies: 301
-- Name: v2_numerical_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_numerical_settings_id_seq OWNED BY v2_numerical_settings.id;


--
-- TOC entry 272 (class 1259 OID 12491746)
-- Name: v2_obstacle; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_obstacle (
    id integer NOT NULL,
    crest_level double precision,
    the_geom geometry(LineString,28992),
    code character varying(100) NOT NULL
);


--
-- TOC entry 271 (class 1259 OID 12491744)
-- Name: v2_obstacle_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_obstacle_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3995 (class 0 OID 0)
-- Dependencies: 271
-- Name: v2_obstacle_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_obstacle_id_seq OWNED BY v2_obstacle.id;


--
-- TOC entry 246 (class 1259 OID 12491505)
-- Name: v2_orifice; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_orifice (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    max_capacity double precision,
    crest_level double precision,
    sewerage boolean NOT NULL,
    cross_section_definition_id integer,
    friction_value double precision,
    friction_type integer,
    discharge_coefficient_positive double precision,
    discharge_coefficient_negative double precision,
    zoom_category integer,
    crest_type integer,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- TOC entry 245 (class 1259 OID 12491503)
-- Name: v2_orifice_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_orifice_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3996 (class 0 OID 0)
-- Dependencies: 245
-- Name: v2_orifice_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_orifice_id_seq OWNED BY v2_orifice.id;


--
-- TOC entry 242 (class 1259 OID 12491455)
-- Name: v2_pipe; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_pipe (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    profile_num integer,
    sewerage_type integer,
    calculation_type integer,
    invert_level_start_point double precision,
    invert_level_end_point double precision,
    cross_section_definition_id integer,
    friction_value double precision,
    friction_type integer,
    dist_calc_points double precision,
    material integer,
    pipe_quality double precision,
    original_length double precision,
    zoom_category integer,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- TOC entry 241 (class 1259 OID 12491453)
-- Name: v2_pipe_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_pipe_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3997 (class 0 OID 0)
-- Dependencies: 241
-- Name: v2_pipe_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_pipe_id_seq OWNED BY v2_pipe.id;


--
-- TOC entry 250 (class 1259 OID 12491551)
-- Name: v2_pumped_drainage_area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_pumped_drainage_area (
    id integer NOT NULL,
    name character varying(64) NOT NULL,
    code character varying(100) NOT NULL,
    the_geom geometry(Polygon,28992) NOT NULL
);


--
-- TOC entry 249 (class 1259 OID 12491549)
-- Name: v2_pumped_drainage_area_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_pumped_drainage_area_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3998 (class 0 OID 0)
-- Dependencies: 249
-- Name: v2_pumped_drainage_area_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_pumped_drainage_area_id_seq OWNED BY v2_pumped_drainage_area.id;


--
-- TOC entry 248 (class 1259 OID 12491531)
-- Name: v2_pumpstation; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_pumpstation (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    classification integer,
    sewerage boolean NOT NULL,
    start_level double precision,
    lower_stop_level double precision,
    upper_stop_level double precision,
    capacity double precision,
    zoom_category integer,
    connection_node_start_id integer,
    connection_node_end_id integer,
    type integer
);


--
-- TOC entry 247 (class 1259 OID 12491529)
-- Name: v2_pumpstation_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_pumpstation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 3999 (class 0 OID 0)
-- Dependencies: 247
-- Name: v2_pumpstation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_pumpstation_id_seq OWNED BY v2_pumpstation.id;


--
-- TOC entry 314 (class 1259 OID 12492326)
-- Name: v2_simple_infiltration; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_simple_infiltration (
    id integer NOT NULL,
    infiltration_rate double precision NOT NULL,
    infiltration_rate_file character varying(255),
    infiltration_surface_option integer,
    max_infiltration_capacity_file text,
    display_name character varying(255)
);


--
-- TOC entry 313 (class 1259 OID 12492324)
-- Name: v2_simple_infiltration_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_simple_infiltration_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4000 (class 0 OID 0)
-- Dependencies: 313
-- Name: v2_simple_infiltration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_simple_infiltration_id_seq OWNED BY v2_simple_infiltration.id;


--
-- TOC entry 306 (class 1259 OID 12492249)
-- Name: v2_surface; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_surface (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    zoom_category integer,
    nr_of_inhabitants double precision,
    dry_weather_flow double precision,
    function character varying(64),
    area double precision,
    surface_parameters_id integer,
    the_geom geometry(Polygon,28992)
);


--
-- TOC entry 305 (class 1259 OID 12492247)
-- Name: v2_surface_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_surface_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4001 (class 0 OID 0)
-- Dependencies: 305
-- Name: v2_surface_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_surface_id_seq OWNED BY v2_surface.id;


--
-- TOC entry 308 (class 1259 OID 12492260)
-- Name: v2_surface_map; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_surface_map (
    id integer NOT NULL,
    surface_type character varying(40),
    surface_id integer,
    connection_node_id integer NOT NULL,
    percentage double precision
);


--
-- TOC entry 307 (class 1259 OID 12492258)
-- Name: v2_surface_map_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_surface_map_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4002 (class 0 OID 0)
-- Dependencies: 307
-- Name: v2_surface_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_surface_map_id_seq OWNED BY v2_surface_map.id;


--
-- TOC entry 304 (class 1259 OID 12492241)
-- Name: v2_surface_parameters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_surface_parameters (
    id integer NOT NULL,
    outflow_delay double precision NOT NULL,
    surface_layer_thickness double precision NOT NULL,
    infiltration boolean NOT NULL,
    max_infiltration_capacity double precision NOT NULL,
    min_infiltration_capacity double precision NOT NULL,
    infiltration_decay_constant double precision NOT NULL,
    infiltration_recovery_constant double precision NOT NULL
);


--
-- TOC entry 303 (class 1259 OID 12492239)
-- Name: v2_surface_parameters_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_surface_parameters_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4003 (class 0 OID 0)
-- Dependencies: 303
-- Name: v2_surface_parameters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_surface_parameters_id_seq OWNED BY v2_surface_parameters.id;


--
-- TOC entry 264 (class 1259 OID 12491670)
-- Name: v2_weir; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_weir (
    id integer NOT NULL,
    display_name character varying(255) NOT NULL,
    code character varying(100) NOT NULL,
    crest_level double precision,
    crest_type integer,
    cross_section_definition_id integer,
    sewerage boolean NOT NULL,
    discharge_coefficient_positive double precision,
    discharge_coefficient_negative double precision,
    external boolean,
    zoom_category integer,
    friction_value double precision,
    friction_type integer,
    connection_node_start_id integer,
    connection_node_end_id integer
);


--
-- TOC entry 263 (class 1259 OID 12491668)
-- Name: v2_weir_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_weir_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4004 (class 0 OID 0)
-- Dependencies: 263
-- Name: v2_weir_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_weir_id_seq OWNED BY v2_weir.id;


--
-- TOC entry 268 (class 1259 OID 12491716)
-- Name: v2_windshielding; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE v2_windshielding (
    id integer NOT NULL,
    channel_id integer,
    north double precision,
    northeast double precision,
    east double precision,
    southeast double precision,
    south double precision,
    southwest double precision,
    west double precision,
    northwest double precision,
    the_geom geometry(Point,28992),
    CONSTRAINT must_be_on_channel CHECK ((on_channel(channel_id, the_geom) = 1))
);


--
-- TOC entry 267 (class 1259 OID 12491714)
-- Name: v2_windshielding_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE v2_windshielding_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- TOC entry 4005 (class 0 OID 0)
-- Dependencies: 267
-- Name: v2_windshielding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE v2_windshielding_id_seq OWNED BY v2_windshielding.id;


--
-- TOC entry 3573 (class 2604 OID 12491350)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_boundary_conditions ALTER COLUMN id SET DEFAULT nextval('v2_1d_boundary_conditions_id_seq'::regclass);


--
-- TOC entry 3581 (class 2604 OID 12491441)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_lateral ALTER COLUMN id SET DEFAULT nextval('v2_1d_lateral_id_seq'::regclass);


--
-- TOC entry 3595 (class 2604 OID 12491699)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_2d_boundary_conditions ALTER COLUMN id SET DEFAULT nextval('v2_2d_boundary_conditions_id_seq'::regclass);


--
-- TOC entry 3589 (class 2604 OID 12491614)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_2d_lateral ALTER COLUMN id SET DEFAULT nextval('v2_2d_lateral_id_seq'::regclass);


--
-- TOC entry 3601 (class 2604 OID 12491800)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_aggregation_settings ALTER COLUMN id SET DEFAULT nextval('v2_aggregation_settings_id_seq'::regclass);


--
-- TOC entry 3603 (class 2604 OID 12491823)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_calculation_point ALTER COLUMN id SET DEFAULT nextval('v2_calculation_point_id_seq'::regclass);


--
-- TOC entry 3576 (class 2604 OID 12491382)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_channel ALTER COLUMN id SET DEFAULT nextval('v2_channel_id_seq'::regclass);


--
-- TOC entry 3604 (class 2604 OID 12491835)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_connected_pnt ALTER COLUMN id SET DEFAULT nextval('v2_connected_pnt_id_seq'::regclass);


--
-- TOC entry 3572 (class 2604 OID 12491337)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_connection_nodes ALTER COLUMN id SET DEFAULT nextval('v2_connection_nodes_id_seq'::regclass);


--
-- TOC entry 3609 (class 2604 OID 12492144)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control ALTER COLUMN id SET DEFAULT nextval('v2_control_id_seq'::regclass);


--
-- TOC entry 3613 (class 2604 OID 12492194)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_delta ALTER COLUMN id SET DEFAULT nextval('v2_control_delta_id_seq'::regclass);


--
-- TOC entry 3605 (class 2604 OID 12491940)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_group ALTER COLUMN id SET DEFAULT nextval('v2_control_group_id_seq'::regclass);


--
-- TOC entry 3608 (class 2604 OID 12492101)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_measure_group ALTER COLUMN id SET DEFAULT nextval('v2_control_measure_group_id_seq'::regclass);


--
-- TOC entry 3610 (class 2604 OID 12492164)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_measure_map ALTER COLUMN id SET DEFAULT nextval('v2_control_measure_map_id_seq'::regclass);


--
-- TOC entry 3611 (class 2604 OID 12492178)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_memory ALTER COLUMN id SET DEFAULT nextval('v2_control_memory_id_seq'::regclass);


--
-- TOC entry 3612 (class 2604 OID 12492186)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_pid ALTER COLUMN id SET DEFAULT nextval('v2_control_pid_id_seq'::regclass);


--
-- TOC entry 3607 (class 2604 OID 12492084)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_table ALTER COLUMN id SET DEFAULT nextval('v2_control_table_id_seq'::regclass);


--
-- TOC entry 3614 (class 2604 OID 12492202)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_timed ALTER COLUMN id SET DEFAULT nextval('v2_control_timed_id_seq'::regclass);


--
-- TOC entry 3578 (class 2604 OID 12491406)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_cross_section_definition ALTER COLUMN id SET DEFAULT nextval('v2_cross_section_definition_id_seq'::regclass);


--
-- TOC entry 3579 (class 2604 OID 12491417)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_cross_section_location ALTER COLUMN id SET DEFAULT nextval('v2_cross_section_location_id_seq'::regclass);


--
-- TOC entry 3587 (class 2604 OID 12491566)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_culvert ALTER COLUMN id SET DEFAULT nextval('v2_culvert_id_seq'::regclass);


--
-- TOC entry 3606 (class 2604 OID 12492072)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_dem_average_area ALTER COLUMN id SET DEFAULT nextval('v2_dem_average_area_id_seq'::regclass);


--
-- TOC entry 3593 (class 2604 OID 12491661)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_floodfill ALTER COLUMN id SET DEFAULT nextval('v2_floodfill_id_seq'::regclass);


--
-- TOC entry 3591 (class 2604 OID 12491638)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings ALTER COLUMN id SET DEFAULT nextval('v2_global_settings_id_seq'::regclass);


--
-- TOC entry 3592 (class 2604 OID 12491649)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_grid_refinement ALTER COLUMN id SET DEFAULT nextval('v2_grid_refinement_id_seq'::regclass);


--
-- TOC entry 3619 (class 2604 OID 12492306)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_grid_refinement_area ALTER COLUMN id SET DEFAULT nextval('v2_grid_refinement_area_id_seq'::regclass);


--
-- TOC entry 3620 (class 2604 OID 12492318)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_groundwater ALTER COLUMN id SET DEFAULT nextval('v2_groundwater_id_seq'::regclass);


--
-- TOC entry 3583 (class 2604 OID 12491484)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_impervious_surface ALTER COLUMN id SET DEFAULT nextval('v2_impervious_surface_id_seq'::regclass);


--
-- TOC entry 3600 (class 2604 OID 12491761)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_impervious_surface_map ALTER COLUMN id SET DEFAULT nextval('v2_impervious_surface_map_id_seq'::regclass);


--
-- TOC entry 3590 (class 2604 OID 12491626)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_initial_waterlevel ALTER COLUMN id SET DEFAULT nextval('v2_initial_waterlevel_id_seq'::regclass);


--
-- TOC entry 3622 (class 2604 OID 12492340)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_interflow ALTER COLUMN id SET DEFAULT nextval('v2_interflow_id_seq'::regclass);


--
-- TOC entry 3598 (class 2604 OID 12491737)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_levee ALTER COLUMN id SET DEFAULT nextval('v2_levee_id_seq'::regclass);


--
-- TOC entry 3575 (class 2604 OID 12491368)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_manhole ALTER COLUMN id SET DEFAULT nextval('v2_manhole_id_seq'::regclass);


--
-- TOC entry 3615 (class 2604 OID 12492214)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_numerical_settings ALTER COLUMN id SET DEFAULT nextval('v2_numerical_settings_id_seq'::regclass);


--
-- TOC entry 3599 (class 2604 OID 12491749)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_obstacle ALTER COLUMN id SET DEFAULT nextval('v2_obstacle_id_seq'::regclass);


--
-- TOC entry 3584 (class 2604 OID 12491508)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_orifice ALTER COLUMN id SET DEFAULT nextval('v2_orifice_id_seq'::regclass);


--
-- TOC entry 3582 (class 2604 OID 12491458)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pipe ALTER COLUMN id SET DEFAULT nextval('v2_pipe_id_seq'::regclass);


--
-- TOC entry 3586 (class 2604 OID 12491554)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pumped_drainage_area ALTER COLUMN id SET DEFAULT nextval('v2_pumped_drainage_area_id_seq'::regclass);


--
-- TOC entry 3585 (class 2604 OID 12491534)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pumpstation ALTER COLUMN id SET DEFAULT nextval('v2_pumpstation_id_seq'::regclass);


--
-- TOC entry 3621 (class 2604 OID 12492329)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_simple_infiltration ALTER COLUMN id SET DEFAULT nextval('v2_simple_infiltration_id_seq'::regclass);


--
-- TOC entry 3617 (class 2604 OID 12492252)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface ALTER COLUMN id SET DEFAULT nextval('v2_surface_id_seq'::regclass);


--
-- TOC entry 3618 (class 2604 OID 12492263)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface_map ALTER COLUMN id SET DEFAULT nextval('v2_surface_map_id_seq'::regclass);


--
-- TOC entry 3616 (class 2604 OID 12492244)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface_parameters ALTER COLUMN id SET DEFAULT nextval('v2_surface_parameters_id_seq'::regclass);


--
-- TOC entry 3594 (class 2604 OID 12491673)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_weir ALTER COLUMN id SET DEFAULT nextval('v2_weir_id_seq'::regclass);


--
-- TOC entry 3596 (class 2604 OID 12491719)
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_windshielding ALTER COLUMN id SET DEFAULT nextval('v2_windshielding_id_seq'::regclass);


--
-- TOC entry 3628 (class 2606 OID 12492370)
-- Name: unique_connection_node; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_boundary_conditions
    ADD CONSTRAINT unique_connection_node UNIQUE (connection_node_id);


--
-- TOC entry 3630 (class 2606 OID 12491357)
-- Name: v2_1d_boundary_conditions_connection_node_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_boundary_conditions
    ADD CONSTRAINT v2_1d_boundary_conditions_connection_node_id_key UNIQUE (connection_node_id);


--
-- TOC entry 3632 (class 2606 OID 12491355)
-- Name: v2_1d_boundary_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_boundary_conditions
    ADD CONSTRAINT v2_1d_boundary_conditions_pkey PRIMARY KEY (id);


--
-- TOC entry 3652 (class 2606 OID 12491446)
-- Name: v2_1d_lateral_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_lateral
    ADD CONSTRAINT v2_1d_lateral_pkey PRIMARY KEY (id);


--
-- TOC entry 3706 (class 2606 OID 12491704)
-- Name: v2_2d_boundary_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_2d_boundary_conditions
    ADD CONSTRAINT v2_2d_boundary_conditions_pkey PRIMARY KEY (id);


--
-- TOC entry 3680 (class 2606 OID 12491619)
-- Name: v2_2d_lateral_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_2d_lateral
    ADD CONSTRAINT v2_2d_lateral_pkey PRIMARY KEY (id);


--
-- TOC entry 3724 (class 2606 OID 12491802)
-- Name: v2_aggregation_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_aggregation_settings
    ADD CONSTRAINT v2_aggregation_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3726 (class 2606 OID 12491828)
-- Name: v2_calculation_point_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_calculation_point
    ADD CONSTRAINT v2_calculation_point_pkey PRIMARY KEY (id);


--
-- TOC entry 3641 (class 2606 OID 12491387)
-- Name: v2_channel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_channel
    ADD CONSTRAINT v2_channel_pkey PRIMARY KEY (id);


--
-- TOC entry 3731 (class 2606 OID 12491840)
-- Name: v2_connected_pnt_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_connected_pnt
    ADD CONSTRAINT v2_connected_pnt_pkey PRIMARY KEY (id);


--
-- TOC entry 3624 (class 2606 OID 12491342)
-- Name: v2_connection_nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_connection_nodes
    ADD CONSTRAINT v2_connection_nodes_pkey PRIMARY KEY (id);


--
-- TOC entry 3754 (class 2606 OID 12492196)
-- Name: v2_control_delta_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_delta
    ADD CONSTRAINT v2_control_delta_pkey PRIMARY KEY (id);


--
-- TOC entry 3734 (class 2606 OID 12491942)
-- Name: v2_control_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_group
    ADD CONSTRAINT v2_control_group_pkey PRIMARY KEY (id);


--
-- TOC entry 3741 (class 2606 OID 12492103)
-- Name: v2_control_measure_group_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_measure_group
    ADD CONSTRAINT v2_control_measure_group_pkey PRIMARY KEY (id);


--
-- TOC entry 3748 (class 2606 OID 12492166)
-- Name: v2_control_measure_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_measure_map
    ADD CONSTRAINT v2_control_measure_map_pkey PRIMARY KEY (id);


--
-- TOC entry 3750 (class 2606 OID 12492180)
-- Name: v2_control_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_memory
    ADD CONSTRAINT v2_control_memory_pkey PRIMARY KEY (id);


--
-- TOC entry 3752 (class 2606 OID 12492188)
-- Name: v2_control_pid_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_pid
    ADD CONSTRAINT v2_control_pid_pkey PRIMARY KEY (id);


--
-- TOC entry 3745 (class 2606 OID 12492146)
-- Name: v2_control_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control
    ADD CONSTRAINT v2_control_pkey PRIMARY KEY (id);


--
-- TOC entry 3739 (class 2606 OID 12492089)
-- Name: v2_control_table_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_table
    ADD CONSTRAINT v2_control_table_pkey PRIMARY KEY (id);


--
-- TOC entry 3756 (class 2606 OID 12492207)
-- Name: v2_control_timed_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_timed
    ADD CONSTRAINT v2_control_timed_pkey PRIMARY KEY (id);


--
-- TOC entry 3644 (class 2606 OID 12491411)
-- Name: v2_cross_section_definition_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_cross_section_definition
    ADD CONSTRAINT v2_cross_section_definition_pkey PRIMARY KEY (id);


--
-- TOC entry 3648 (class 2606 OID 12491422)
-- Name: v2_cross_section_location_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_cross_section_location
    ADD CONSTRAINT v2_cross_section_location_pkey PRIMARY KEY (id);


--
-- TOC entry 3677 (class 2606 OID 12491571)
-- Name: v2_culvert_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_culvert
    ADD CONSTRAINT v2_culvert_pkey PRIMARY KEY (id);


--
-- TOC entry 3736 (class 2606 OID 12492077)
-- Name: v2_dem_average_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_dem_average_area
    ADD CONSTRAINT v2_dem_average_area_pkey PRIMARY KEY (id);


--
-- TOC entry 3698 (class 2606 OID 12491666)
-- Name: v2_floodfill_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_floodfill
    ADD CONSTRAINT v2_floodfill_pkey PRIMARY KEY (id);


--
-- TOC entry 3689 (class 2606 OID 12491785)
-- Name: v2_global_settings_name_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT v2_global_settings_name_uniq UNIQUE (name);


--
-- TOC entry 3692 (class 2606 OID 12491643)
-- Name: v2_global_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT v2_global_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3769 (class 2606 OID 12492311)
-- Name: v2_grid_refinement_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_grid_refinement_area
    ADD CONSTRAINT v2_grid_refinement_area_pkey PRIMARY KEY (id);


--
-- TOC entry 3695 (class 2606 OID 12491654)
-- Name: v2_grid_refinement_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_grid_refinement
    ADD CONSTRAINT v2_grid_refinement_pkey PRIMARY KEY (id);


--
-- TOC entry 3772 (class 2606 OID 12492323)
-- Name: v2_groundwater_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_groundwater
    ADD CONSTRAINT v2_groundwater_pkey PRIMARY KEY (id);


--
-- TOC entry 3721 (class 2606 OID 12491763)
-- Name: v2_impervious_surface_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_impervious_surface_map
    ADD CONSTRAINT v2_impervious_surface_map_pkey PRIMARY KEY (id);


--
-- TOC entry 3659 (class 2606 OID 12491489)
-- Name: v2_impervious_surface_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_impervious_surface
    ADD CONSTRAINT v2_impervious_surface_pkey PRIMARY KEY (id);


--
-- TOC entry 3683 (class 2606 OID 12491631)
-- Name: v2_initial_waterlevel_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_initial_waterlevel
    ADD CONSTRAINT v2_initial_waterlevel_pkey PRIMARY KEY (id);


--
-- TOC entry 3776 (class 2606 OID 12492345)
-- Name: v2_interflow_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_interflow
    ADD CONSTRAINT v2_interflow_pkey PRIMARY KEY (id);


--
-- TOC entry 3713 (class 2606 OID 12491742)
-- Name: v2_levee_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_levee
    ADD CONSTRAINT v2_levee_pkey PRIMARY KEY (id);


--
-- TOC entry 3635 (class 2606 OID 12491918)
-- Name: v2_manhole_connection_node_id_uniq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_manhole
    ADD CONSTRAINT v2_manhole_connection_node_id_uniq UNIQUE (connection_node_id);


--
-- TOC entry 3637 (class 2606 OID 12491370)
-- Name: v2_manhole_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_manhole
    ADD CONSTRAINT v2_manhole_pkey PRIMARY KEY (id);


--
-- TOC entry 3758 (class 2606 OID 12492216)
-- Name: v2_numerical_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_numerical_settings
    ADD CONSTRAINT v2_numerical_settings_pkey PRIMARY KEY (id);


--
-- TOC entry 3716 (class 2606 OID 12491754)
-- Name: v2_obstacle_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_obstacle
    ADD CONSTRAINT v2_obstacle_pkey PRIMARY KEY (id);


--
-- TOC entry 3665 (class 2606 OID 12491510)
-- Name: v2_orifice_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_orifice
    ADD CONSTRAINT v2_orifice_pkey PRIMARY KEY (id);


--
-- TOC entry 3657 (class 2606 OID 12491460)
-- Name: v2_pipe_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pipe
    ADD CONSTRAINT v2_pipe_pkey PRIMARY KEY (id);


--
-- TOC entry 3671 (class 2606 OID 12491559)
-- Name: v2_pumped_drainage_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pumped_drainage_area
    ADD CONSTRAINT v2_pumped_drainage_area_pkey PRIMARY KEY (id);


--
-- TOC entry 3669 (class 2606 OID 12491536)
-- Name: v2_pumpstation_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pumpstation
    ADD CONSTRAINT v2_pumpstation_pkey PRIMARY KEY (id);


--
-- TOC entry 3774 (class 2606 OID 12492334)
-- Name: v2_simple_infiltration_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_simple_infiltration
    ADD CONSTRAINT v2_simple_infiltration_pkey PRIMARY KEY (id);


--
-- TOC entry 3767 (class 2606 OID 12492265)
-- Name: v2_surface_map_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface_map
    ADD CONSTRAINT v2_surface_map_pkey PRIMARY KEY (id);


--
-- TOC entry 3760 (class 2606 OID 12492246)
-- Name: v2_surface_parameters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface_parameters
    ADD CONSTRAINT v2_surface_parameters_pkey PRIMARY KEY (id);


--
-- TOC entry 3762 (class 2606 OID 12492257)
-- Name: v2_surface_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface
    ADD CONSTRAINT v2_surface_pkey PRIMARY KEY (id);


--
-- TOC entry 3704 (class 2606 OID 12491675)
-- Name: v2_weir_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_weir
    ADD CONSTRAINT v2_weir_pkey PRIMARY KEY (id);


--
-- TOC entry 3710 (class 2606 OID 12491724)
-- Name: v2_windshielding_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_windshielding
    ADD CONSTRAINT v2_windshielding_pkey PRIMARY KEY (id);


--
-- TOC entry 3650 (class 1259 OID 12491452)
-- Name: v2_1d_lateral_connection_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_1d_lateral_connection_node_id ON public.v2_1d_lateral USING btree (connection_node_id);


--
-- TOC entry 3707 (class 1259 OID 12491705)
-- Name: v2_2d_boundary_conditions_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_2d_boundary_conditions_the_geom_id ON public.v2_2d_boundary_conditions USING gist (the_geom);


--
-- TOC entry 3681 (class 1259 OID 12491620)
-- Name: v2_2d_lateral_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_2d_lateral_the_geom_id ON public.v2_2d_lateral USING gist (the_geom);


--
-- TOC entry 3722 (class 1259 OID 12491808)
-- Name: v2_aggregation_settings_global_settings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_aggregation_settings_global_settings_id ON public.v2_aggregation_settings USING btree (global_settings_id);


--
-- TOC entry 3727 (class 1259 OID 12491829)
-- Name: v2_calculation_point_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_calculation_point_the_geom_id ON public.v2_calculation_point USING gist (the_geom);


--
-- TOC entry 3638 (class 1259 OID 12491400)
-- Name: v2_channel_connection_node_end_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_channel_connection_node_end_id ON public.v2_channel USING btree (connection_node_end_id);


--
-- TOC entry 3639 (class 1259 OID 12491394)
-- Name: v2_channel_connection_node_start_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_channel_connection_node_start_id ON public.v2_channel USING btree (connection_node_start_id);


--
-- TOC entry 3642 (class 1259 OID 12491388)
-- Name: v2_channel_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_channel_the_geom_id ON public.v2_channel USING gist (the_geom);


--
-- TOC entry 3728 (class 1259 OID 12491846)
-- Name: v2_connected_pnt_calculation_pnt_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_connected_pnt_calculation_pnt_id ON public.v2_connected_pnt USING btree (calculation_pnt_id);


--
-- TOC entry 3729 (class 1259 OID 12491852)
-- Name: v2_connected_pnt_levee_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_connected_pnt_levee_id ON public.v2_connected_pnt USING btree (levee_id);


--
-- TOC entry 3732 (class 1259 OID 12491853)
-- Name: v2_connected_pnt_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_connected_pnt_the_geom_id ON public.v2_connected_pnt USING gist (the_geom);


--
-- TOC entry 3625 (class 1259 OID 12491343)
-- Name: v2_connection_nodes_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_connection_nodes_the_geom_id ON public.v2_connection_nodes USING gist (the_geom);


--
-- TOC entry 3626 (class 1259 OID 12491344)
-- Name: v2_connection_nodes_the_geom_linestring_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_connection_nodes_the_geom_linestring_id ON public.v2_connection_nodes USING gist (the_geom_linestring);


--
-- TOC entry 3742 (class 1259 OID 12492152)
-- Name: v2_control_control_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_control_control_group_id ON public.v2_control USING btree (control_group_id);


--
-- TOC entry 3743 (class 1259 OID 12492158)
-- Name: v2_control_measure_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_control_measure_group_id ON public.v2_control USING btree (measure_group_id);


--
-- TOC entry 3746 (class 1259 OID 12492172)
-- Name: v2_control_measure_map_measure_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_control_measure_map_measure_group_id ON public.v2_control_measure_map USING btree (measure_group_id);


--
-- TOC entry 3645 (class 1259 OID 12491428)
-- Name: v2_cross_section_location_channel_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_cross_section_location_channel_id ON public.v2_cross_section_location USING btree (channel_id);


--
-- TOC entry 3646 (class 1259 OID 12491434)
-- Name: v2_cross_section_location_definition_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_cross_section_location_definition_id ON public.v2_cross_section_location USING btree (definition_id);


--
-- TOC entry 3649 (class 1259 OID 12491435)
-- Name: v2_cross_section_location_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_cross_section_location_the_geom_id ON public.v2_cross_section_location USING gist (the_geom);


--
-- TOC entry 3673 (class 1259 OID 12491590)
-- Name: v2_culvert_connection_node_end_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_culvert_connection_node_end_id ON public.v2_culvert USING btree (connection_node_end_id);


--
-- TOC entry 3674 (class 1259 OID 12491584)
-- Name: v2_culvert_connection_node_start_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_culvert_connection_node_start_id ON public.v2_culvert USING btree (connection_node_start_id);


--
-- TOC entry 3675 (class 1259 OID 12491577)
-- Name: v2_culvert_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_culvert_cross_section_definition_id ON public.v2_culvert USING btree (cross_section_definition_id);


--
-- TOC entry 3678 (class 1259 OID 12491578)
-- Name: v2_culvert_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_culvert_the_geom_id ON public.v2_culvert USING gist (the_geom);


--
-- TOC entry 3737 (class 1259 OID 12492078)
-- Name: v2_dem_average_area_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_dem_average_area_the_geom_id ON public.v2_dem_average_area USING gist (the_geom);


--
-- TOC entry 3699 (class 1259 OID 12491667)
-- Name: v2_floodfill_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_floodfill_the_geom_id ON public.v2_floodfill USING gist (the_geom);


--
-- TOC entry 3685 (class 1259 OID 12492135)
-- Name: v2_global_settings_control_group_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_global_settings_control_group_id ON public.v2_global_settings USING btree (control_group_id);


--
-- TOC entry 3686 (class 1259 OID 12492351)
-- Name: v2_global_settings_groundwater_settings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_global_settings_groundwater_settings_id ON public.v2_global_settings USING btree (groundwater_settings_id);


--
-- TOC entry 3687 (class 1259 OID 12492363)
-- Name: v2_global_settings_interflow_settings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_global_settings_interflow_settings_id ON public.v2_global_settings USING btree (interflow_settings_id);


--
-- TOC entry 3690 (class 1259 OID 12492223)
-- Name: v2_global_settings_numerical_settings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_global_settings_numerical_settings_id ON public.v2_global_settings USING btree (numerical_settings_id);


--
-- TOC entry 3693 (class 1259 OID 12492357)
-- Name: v2_global_settings_simple_infiltration_settings_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_global_settings_simple_infiltration_settings_id ON public.v2_global_settings USING btree (simple_infiltration_settings_id);


--
-- TOC entry 3770 (class 1259 OID 12492312)
-- Name: v2_grid_refinement_area_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_grid_refinement_area_the_geom_id ON public.v2_grid_refinement_area USING gist (the_geom);


--
-- TOC entry 3696 (class 1259 OID 12491655)
-- Name: v2_grid_refinement_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_grid_refinement_the_geom_id ON public.v2_grid_refinement USING gist (the_geom);


--
-- TOC entry 3718 (class 1259 OID 12491775)
-- Name: v2_impervious_surface_map_connection_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_impervious_surface_map_connection_node_id ON public.v2_impervious_surface_map USING btree (connection_node_id);


--
-- TOC entry 3719 (class 1259 OID 12491769)
-- Name: v2_impervious_surface_map_impervious_surface_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_impervious_surface_map_impervious_surface_id ON public.v2_impervious_surface_map USING btree (impervious_surface_id);


--
-- TOC entry 3660 (class 1259 OID 12491502)
-- Name: v2_impervious_surface_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_impervious_surface_the_geom_id ON public.v2_impervious_surface USING gist (the_geom);


--
-- TOC entry 3684 (class 1259 OID 12491632)
-- Name: v2_initial_waterlevel_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_initial_waterlevel_the_geom_id ON public.v2_initial_waterlevel USING gist (the_geom);


--
-- TOC entry 3714 (class 1259 OID 12491743)
-- Name: v2_levee_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_levee_the_geom_id ON public.v2_levee USING gist (the_geom);


--
-- TOC entry 3633 (class 1259 OID 12491376)
-- Name: v2_manhole_connection_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_manhole_connection_node_id ON public.v2_manhole USING btree (connection_node_id);


--
-- TOC entry 3717 (class 1259 OID 12491755)
-- Name: v2_obstacle_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_obstacle_the_geom_id ON public.v2_obstacle USING gist (the_geom);


--
-- TOC entry 3661 (class 1259 OID 12491528)
-- Name: v2_orifice_connection_node_end_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_orifice_connection_node_end_id ON public.v2_orifice USING btree (connection_node_end_id);


--
-- TOC entry 3662 (class 1259 OID 12491522)
-- Name: v2_orifice_connection_node_start_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_orifice_connection_node_start_id ON public.v2_orifice USING btree (connection_node_start_id);


--
-- TOC entry 3663 (class 1259 OID 12491516)
-- Name: v2_orifice_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_orifice_cross_section_definition_id ON public.v2_orifice USING btree (cross_section_definition_id);


--
-- TOC entry 3653 (class 1259 OID 12491478)
-- Name: v2_pipe_connection_node_end_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_pipe_connection_node_end_id ON public.v2_pipe USING btree (connection_node_end_id);


--
-- TOC entry 3654 (class 1259 OID 12491472)
-- Name: v2_pipe_connection_node_start_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_pipe_connection_node_start_id ON public.v2_pipe USING btree (connection_node_start_id);


--
-- TOC entry 3655 (class 1259 OID 12491466)
-- Name: v2_pipe_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_pipe_cross_section_definition_id ON public.v2_pipe USING btree (cross_section_definition_id);


--
-- TOC entry 3672 (class 1259 OID 12491560)
-- Name: v2_pumped_drainage_area_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_pumped_drainage_area_the_geom_id ON public.v2_pumped_drainage_area USING gist (the_geom);


--
-- TOC entry 3666 (class 1259 OID 12491548)
-- Name: v2_pumpstation_connection_node_end_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_pumpstation_connection_node_end_id ON public.v2_pumpstation USING btree (connection_node_end_id);


--
-- TOC entry 3667 (class 1259 OID 12491542)
-- Name: v2_pumpstation_connection_node_start_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_pumpstation_connection_node_start_id ON public.v2_pumpstation USING btree (connection_node_start_id);


--
-- TOC entry 3765 (class 1259 OID 12492278)
-- Name: v2_surface_map_connection_node_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_surface_map_connection_node_id ON public.v2_surface_map USING btree (connection_node_id);


--
-- TOC entry 3763 (class 1259 OID 12492271)
-- Name: v2_surface_surface_parameters_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_surface_surface_parameters_id ON public.v2_surface USING btree (surface_parameters_id);


--
-- TOC entry 3764 (class 1259 OID 12492272)
-- Name: v2_surface_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_surface_the_geom_id ON public.v2_surface USING gist (the_geom);


--
-- TOC entry 3700 (class 1259 OID 12491693)
-- Name: v2_weir_connection_node_end_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_weir_connection_node_end_id ON public.v2_weir USING btree (connection_node_end_id);


--
-- TOC entry 3701 (class 1259 OID 12491687)
-- Name: v2_weir_connection_node_start_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_weir_connection_node_start_id ON public.v2_weir USING btree (connection_node_start_id);


--
-- TOC entry 3702 (class 1259 OID 12491681)
-- Name: v2_weir_cross_section_definition_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_weir_cross_section_definition_id ON public.v2_weir USING btree (cross_section_definition_id);


--
-- TOC entry 3708 (class 1259 OID 12491730)
-- Name: v2_windshielding_channel_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_windshielding_channel_id ON public.v2_windshielding USING btree (channel_id);


--
-- TOC entry 3711 (class 1259 OID 12491731)
-- Name: v2_windshielding_the_geom_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX v2_windshielding_the_geom_id ON public.v2_windshielding USING gist (the_geom);


--
-- TOC entry 3822 (class 2620 OID 12492438)
-- Name: format_input_str; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER format_input_str BEFORE INSERT OR UPDATE ON public.v2_global_settings FOR EACH ROW EXECUTE PROCEDURE format_input_str();


--
-- TOC entry 3819 (class 2620 OID 12492418)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_culvert FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3821 (class 2620 OID 12492419)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_initial_waterlevel FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3825 (class 2620 OID 12492420)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_2d_boundary_conditions FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3824 (class 2620 OID 12492421)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_floodfill FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3817 (class 2620 OID 12492422)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_impervious_surface FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3828 (class 2620 OID 12492423)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_obstacle FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3831 (class 2620 OID 12492424)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_dem_average_area FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3818 (class 2620 OID 12492425)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_pumped_drainage_area FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3829 (class 2620 OID 12492426)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_calculation_point FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3826 (class 2620 OID 12492427)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_windshielding FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3814 (class 2620 OID 12492428)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_connection_nodes FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3832 (class 2620 OID 12492429)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_surface FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3830 (class 2620 OID 12492430)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_connected_pnt FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3815 (class 2620 OID 12492431)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_channel FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3833 (class 2620 OID 12492432)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_grid_refinement_area FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3823 (class 2620 OID 12492433)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_grid_refinement FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3816 (class 2620 OID 12492434)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_cross_section_location FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3820 (class 2620 OID 12492435)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_2d_lateral FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3827 (class 2620 OID 12492436)
-- Name: geom_to_grid; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER geom_to_grid BEFORE INSERT OR UPDATE ON public.v2_levee FOR EACH ROW EXECUTE PROCEDURE geom_to_grid();


--
-- TOC entry 3807 (class 2606 OID 12491841)
-- Name: calculation_pnt_id_refs_id_3a23ca39; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_connected_pnt
    ADD CONSTRAINT calculation_pnt_id_refs_id_3a23ca39 FOREIGN KEY (calculation_pnt_id) REFERENCES v2_calculation_point(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3781 (class 2606 OID 12491423)
-- Name: channel_id_refs_id_0941f88e; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_cross_section_location
    ADD CONSTRAINT channel_id_refs_id_0941f88e FOREIGN KEY (channel_id) REFERENCES v2_channel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3803 (class 2606 OID 12491725)
-- Name: channel_id_refs_id_79d66cdb; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_windshielding
    ADD CONSTRAINT channel_id_refs_id_79d66cdb FOREIGN KEY (channel_id) REFERENCES v2_channel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3789 (class 2606 OID 12491523)
-- Name: connection_node_end_id_refs_id_014ee229; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_orifice
    ADD CONSTRAINT connection_node_end_id_refs_id_014ee229 FOREIGN KEY (connection_node_end_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3792 (class 2606 OID 12491585)
-- Name: connection_node_end_id_refs_id_35ee1270; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_culvert
    ADD CONSTRAINT connection_node_end_id_refs_id_35ee1270 FOREIGN KEY (connection_node_end_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3780 (class 2606 OID 12491395)
-- Name: connection_node_end_id_refs_id_395a4016; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_channel
    ADD CONSTRAINT connection_node_end_id_refs_id_395a4016 FOREIGN KEY (connection_node_end_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3786 (class 2606 OID 12491473)
-- Name: connection_node_end_id_refs_id_a9965429; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pipe
    ADD CONSTRAINT connection_node_end_id_refs_id_a9965429 FOREIGN KEY (connection_node_end_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3791 (class 2606 OID 12491543)
-- Name: connection_node_end_id_refs_id_b2beccef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pumpstation
    ADD CONSTRAINT connection_node_end_id_refs_id_b2beccef FOREIGN KEY (connection_node_end_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3802 (class 2606 OID 12491688)
-- Name: connection_node_end_id_refs_id_f40dbf77; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_weir
    ADD CONSTRAINT connection_node_end_id_refs_id_f40dbf77 FOREIGN KEY (connection_node_end_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3777 (class 2606 OID 12491358)
-- Name: connection_node_id_refs_id_0a6435e0; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_boundary_conditions
    ADD CONSTRAINT connection_node_id_refs_id_0a6435e0 FOREIGN KEY (connection_node_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3813 (class 2606 OID 12492273)
-- Name: connection_node_id_refs_id_114a184b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface_map
    ADD CONSTRAINT connection_node_id_refs_id_114a184b FOREIGN KEY (connection_node_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3778 (class 2606 OID 12491371)
-- Name: connection_node_id_refs_id_4f81516d; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_manhole
    ADD CONSTRAINT connection_node_id_refs_id_4f81516d FOREIGN KEY (connection_node_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3783 (class 2606 OID 12491447)
-- Name: connection_node_id_refs_id_55d2df40; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_1d_lateral
    ADD CONSTRAINT connection_node_id_refs_id_55d2df40 FOREIGN KEY (connection_node_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3805 (class 2606 OID 12491770)
-- Name: connection_node_id_refs_id_c500d603; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_impervious_surface_map
    ADD CONSTRAINT connection_node_id_refs_id_c500d603 FOREIGN KEY (connection_node_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3788 (class 2606 OID 12491517)
-- Name: connection_node_start_id_refs_id_014ee229; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_orifice
    ADD CONSTRAINT connection_node_start_id_refs_id_014ee229 FOREIGN KEY (connection_node_start_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3794 (class 2606 OID 12491579)
-- Name: connection_node_start_id_refs_id_35ee1270; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_culvert
    ADD CONSTRAINT connection_node_start_id_refs_id_35ee1270 FOREIGN KEY (connection_node_start_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3779 (class 2606 OID 12491389)
-- Name: connection_node_start_id_refs_id_395a4016; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_channel
    ADD CONSTRAINT connection_node_start_id_refs_id_395a4016 FOREIGN KEY (connection_node_start_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3785 (class 2606 OID 12491467)
-- Name: connection_node_start_id_refs_id_a9965429; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pipe
    ADD CONSTRAINT connection_node_start_id_refs_id_a9965429 FOREIGN KEY (connection_node_start_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3790 (class 2606 OID 12491537)
-- Name: connection_node_start_id_refs_id_b2beccef; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pumpstation
    ADD CONSTRAINT connection_node_start_id_refs_id_b2beccef FOREIGN KEY (connection_node_start_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3801 (class 2606 OID 12491682)
-- Name: connection_node_start_id_refs_id_f40dbf77; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_weir
    ADD CONSTRAINT connection_node_start_id_refs_id_f40dbf77 FOREIGN KEY (connection_node_start_id) REFERENCES v2_connection_nodes(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3799 (class 2606 OID 12492130)
-- Name: control_group_id_refs_id_d0f4e2d1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT control_group_id_refs_id_d0f4e2d1 FOREIGN KEY (control_group_id) REFERENCES v2_control_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3809 (class 2606 OID 12492147)
-- Name: control_group_id_refs_id_d891225c; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control
    ADD CONSTRAINT control_group_id_refs_id_d891225c FOREIGN KEY (control_group_id) REFERENCES v2_control_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3787 (class 2606 OID 12491511)
-- Name: cross_section_definition_id_refs_id_10f5522f; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_orifice
    ADD CONSTRAINT cross_section_definition_id_refs_id_10f5522f FOREIGN KEY (cross_section_definition_id) REFERENCES v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3784 (class 2606 OID 12491461)
-- Name: cross_section_definition_id_refs_id_3168ade8; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_pipe
    ADD CONSTRAINT cross_section_definition_id_refs_id_3168ade8 FOREIGN KEY (cross_section_definition_id) REFERENCES v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3800 (class 2606 OID 12491676)
-- Name: cross_section_definition_id_refs_id_52de4c23; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_weir
    ADD CONSTRAINT cross_section_definition_id_refs_id_52de4c23 FOREIGN KEY (cross_section_definition_id) REFERENCES v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3793 (class 2606 OID 12491572)
-- Name: cross_section_definition_id_refs_id_8e4efefc; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_culvert
    ADD CONSTRAINT cross_section_definition_id_refs_id_8e4efefc FOREIGN KEY (cross_section_definition_id) REFERENCES v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3782 (class 2606 OID 12491429)
-- Name: definition_id_refs_id_a1746ea0; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_cross_section_location
    ADD CONSTRAINT definition_id_refs_id_a1746ea0 FOREIGN KEY (definition_id) REFERENCES v2_cross_section_definition(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3806 (class 2606 OID 12491803)
-- Name: global_settings_id_refs_id_295daf41; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_aggregation_settings
    ADD CONSTRAINT global_settings_id_refs_id_295daf41 FOREIGN KEY (global_settings_id) REFERENCES v2_global_settings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3796 (class 2606 OID 12492346)
-- Name: groundwater_settings_id_refs_id_300ed996; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT groundwater_settings_id_refs_id_300ed996 FOREIGN KEY (groundwater_settings_id) REFERENCES v2_groundwater(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3804 (class 2606 OID 12491764)
-- Name: impervious_surface_id_refs_id_001c234b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_impervious_surface_map
    ADD CONSTRAINT impervious_surface_id_refs_id_001c234b FOREIGN KEY (impervious_surface_id) REFERENCES v2_impervious_surface(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3798 (class 2606 OID 12492358)
-- Name: interflow_settings_id_refs_id_79a59d6a; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT interflow_settings_id_refs_id_79a59d6a FOREIGN KEY (interflow_settings_id) REFERENCES v2_interflow(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3808 (class 2606 OID 12491847)
-- Name: levee_id_refs_id_2e565295; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_connected_pnt
    ADD CONSTRAINT levee_id_refs_id_2e565295 FOREIGN KEY (levee_id) REFERENCES v2_levee(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3810 (class 2606 OID 12492153)
-- Name: measure_group_id_refs_id_36a28871; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control
    ADD CONSTRAINT measure_group_id_refs_id_36a28871 FOREIGN KEY (measure_group_id) REFERENCES v2_control_measure_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3811 (class 2606 OID 12492167)
-- Name: measure_group_id_refs_id_7deb88a7; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_control_measure_map
    ADD CONSTRAINT measure_group_id_refs_id_7deb88a7 FOREIGN KEY (measure_group_id) REFERENCES v2_control_measure_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3795 (class 2606 OID 12492224)
-- Name: numerical_settings_id_refs_id_4154bad2; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT numerical_settings_id_refs_id_4154bad2 FOREIGN KEY (numerical_settings_id) REFERENCES v2_numerical_settings(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3797 (class 2606 OID 12492352)
-- Name: simple_infiltration_settings_id_refs_id_ac3bb32b; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_global_settings
    ADD CONSTRAINT simple_infiltration_settings_id_refs_id_ac3bb32b FOREIGN KEY (simple_infiltration_settings_id) REFERENCES v2_simple_infiltration(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3812 (class 2606 OID 12492266)
-- Name: surface_parameters_id_refs_id_d2471b65; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY v2_surface
    ADD CONSTRAINT surface_parameters_id_refs_id_d2471b65 FOREIGN KEY (surface_parameters_id) REFERENCES v2_surface_parameters(id) DEFERRABLE INITIALLY DEFERRED;


-- Completed on 2018-12-21 09:47:24

--
-- PostgreSQL database dump complete
--

