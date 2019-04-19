DELETE FROM v2_numerical_settings;

INSERT INTO v2_numerical_settings(
    id, 
    convergence_eps,
    integration_method,
    max_degree,
    max_nonlin_iterations,
    use_of_cg,
    use_of_nested_newton) 
values(
    1,
    0.00001,
    0,
    5,
    20,
    20,
    0);

DELETE FROM v2_global_settings;

INSERT INTO v2_global_settings(
    id, 
    advection_1d,
    advection_2d,
    dem_file,
    dem_obstacle_detection,
    dist_calc_points,
    epsg_code,
    flooding_threshold,
    frict_avg,
    frict_coef,
    frict_coef_file,
    grid_space,
    initial_waterlevel,
    kmax,
    name,
    nr_timesteps,
    numerical_settings_id,
    output_time_step,
    sim_time_step,
    simple_infiltration_settings_id,
    start_date,
    start_time,
    table_step_size,
    timestep_plus,
    use_0d_inflow,
    use_1d_flow,
    use_2d_flow,
    use_2d_rain)
values(
    1,
    0,
    1,
    'rasters/dem.tif',
    0,
    50,
    28992,
    0.02,
    0,
    0.02,
    'rasters/friction.tif',
    10,
    -10,
    3,
    'default',
    240,
    1,
    300,
    30,
    1,
    '2017-01-01',
    '2017-01-01 00:00:00',
    0.01,
    1,
    0,
    0,
    1,
    1);

DELETE FROM v2_simple_infiltration;

insert into v2_simple_infiltration(
    id,
    infiltration_rate,
    infiltration_rate_file)
values(
    1,
    0,
    'rasters/infiltration.tif');