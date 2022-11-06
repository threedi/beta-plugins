from main import create_threedimodel

create_threedimodel(
    threedi_api_key = "fill_in",
    lizard_api_key = "fill_in",
    local_dir=r"C:\Temp\3Di Global",
    schematisation_name="Dnipro",
    extent_filename=r"C:\Temp\3Di Global\test_shapefile_dnipro.shp",
    pixel_size=10,
    nr_cells=50000,
    dem_raster_uuid="eae92c48-cd68-4820-9d82-f86f763b4186"
)