from osgeo import ogr

from main import create_threedimodel
from epsg import transform_layer
from threedi_api.constants import ORGANISATION_UUID

def test_transform_layer():
    fn = r"C:\Temp\3Di Global\test_shapefile_dnipro.shp"
    ds = ogr.Open(fn)
    layer = ds.GetLayer(0)
    driver = ogr.GetDriverByName("GPKG")
    source_epsg = layer.GetSpatialRef().GetAuthorityCode(None)
    dest_epsg = 32638
    transformed_ds = driver.CreateDataSource(r"C:\Temp\3Di Global\test_shapefile_dnipro_transformed.gpkg")

    transformed_layer = transform_layer(
        layer=layer,
        dest_datasource=transformed_ds,
        dest_layer_name="test_shapefile_dnipro_transformed",
        source_epsg=source_epsg,
        dest_epsg=dest_epsg
    )


# test_transform_layer()
create_threedimodel(
    threedi_api_key="7AVjXEza.d82pBLvjcuUaLVly9q3X02bMu6wNe1lG",
    lizard_api_key="HUA82re5.UD47nZQYGyGJtoZpkVIKjCgM0OZYScxY",
    organisation_uuid=ORGANISATION_UUID,
    local_dir=r"C:\Temp\3Di Global",
    schematisation_name="Dnipro",
    extent_filename=r"C:\Temp\3Di Global\test_shapefile_dnipro.shp",
    pixel_size=10,
    nr_cells=50000,
    dem_raster_uuid="eae92c48-cd68-4820-9d82-f86f763b4186",
)
