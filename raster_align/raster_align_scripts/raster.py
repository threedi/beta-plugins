# -*- coding: utf-8 -*-
"""
Created on Wed Jan 29 18:20:00 2020

@author: chris.kerklaan


"""
import os
import numpy as np
from osgeo import osr, ogr, gdal, gdal_array

# globals
DRIVER_GDAL_GTIFF = gdal.GetDriverByName('GTiff')
DRIVER_GDAL_MEM = gdal.GetDriverByName('MEM')
WRITE_OPTIONS = ["COMPRESS=DEFLATE",
                 "NUM_THREADS=4"
                 "ZLEVEL=9"]

type_mapping = {gdal.GDT_Byte: ogr.OFTInteger,
                    gdal.GDT_UInt16: ogr.OFTInteger,
                    gdal.GDT_Int16: ogr.OFTInteger,
                    gdal.GDT_UInt32: ogr.OFTInteger,
                    gdal.GDT_Int32: ogr.OFTInteger,
                    gdal.GDT_Float32: ogr.OFTReal,
                    gdal.GDT_Float64: ogr.OFTReal,
                    gdal.GDT_CInt16: ogr.OFTInteger,
                    gdal.GDT_CInt32: ogr.OFTInteger,
                    gdal.GDT_CFloat32: ogr.OFTReal,
                    gdal.GDT_CFloat64: ogr.OFTReal}
_loc_ras = 0

class Raster(object):
    def __init__(self, path, band_num=1, edit=False, name=None):
        """  Input can either be a path or a numpy array
             Edit mode loads the raster into memory
        """
        
        if name:
            self.name = name
  
        if type(path) is str:
            self.info(path, band_num, edit)
            self.type='str'
        else:
            self.type='ds'
            self.info(path, band_num, edit)
            
            
    def info(self, path, band_num=1, edit=1):
        """ input can be ds or str"""
        if type(path) is str:
             self.ds = gdal.Open(path, edit)
        else:
            self.ds = path
            
        self.data_type = self.band.DataType
        self.np_dt = gdal_array.GDALTypeCodeToNumericTypeCode(self.data_type)
        self.nodata_value = self.band.GetNoDataValue()
        self.pixel_width  = self.geotransform[1]
        self.pixel_height = -self.geotransform[5]
        self.rows = self.band.YSize
        self.columns = self.band.XSize
        self.shape = (self.rows, self.columns)
        
        self.minx, self.maxx, self.miny, self.maxy = self.get_extent()
        self.width = self.maxx - self.minx
        self.height = self.maxy - self.miny

        self.projection = self.ds.GetProjection()
        self.sr = osr.SpatialReference()
        self.sr.ImportFromWkt(self.projection)
        
        self.size = self.rows * self.columns
        self.chunks = 100
        
        for key, value in self.ds.GetMetadata().items():
            if key == 'name' and not hasattr(self, 'name'):
                setattr(self, key, value)
            
    
    def __setitem__(self, key, value):
        if key == 'chunks':
            self.chunks = value    
        elif key == "geotransform":
            self.ds.SetGeoTransform(value)
        else:
            x, y = key
            return self.band.WriteArray(value, x, y)
        
    def __getitem__(self, key):
        x, y = key
        return self.band.ReadAsArray(x, y, self.w, self.h)
        
    @property
    def array(self):
        return self.set_nan(self.band.ReadAsArray())
    
    @property
    def band(self):
        return self.ds.GetRasterBand(1)
    
    @property
    def geotransform(self):
        return self.ds.GetGeoTransform()
    
        
    def get_extent(self):
        return get_extent(self.geotransform, self.columns, self.rows)
 
    def set_projection(self, epsg=None, wkt=None):
        if epsg:
            srs = osr.SpatialReference()  
            srs.ImportFromEPSG(epsg)
            wkt = srs.ExportToWkt()
        
        self.ds.SetProjection(wkt)
        
    def set_geotransform(self, gt):
        self.ds.SetGeoTransform(gt)
        
    def copy(self, ds, overwrite=False):
        self.dir = loc_dir(mem=True, add=False)
        ds = DRIVER_GDAL_GTIFF.CreateCopy(self.dir, ds, 
                                          options=WRITE_OPTIONS)
        return self.change_source(ds)
        
    def close(self):
        self.ds = None
        self.array = None
        
    def change_source(self, in_ds):
        """closes old source and gets info of new souce"""        
        self.ds = None         
        self.info(in_ds, edit=1)
        
    def empty_copy(self, rows=None, columns=None, data_type=None, epsg=28992):
        if not rows:
            rows = self.rows
        if not columns:
            columns = self.columns
        if not data_type:
            data_type = self.data_type

        out = create_source(columns, rows, data_type)
        out.SetGeoTransform(self.geotransform)
        srs = osr.SpatialReference()  
        srs.ImportFromEPSG(epsg)
        out.SetProjection(srs.ExportToWkt())  # export coords to file
        out.GetRasterBand(1).SetNoDataValue(self.nodata_value)

        return Raster(out)
        
    def replace_nodata(self, value=-9999, tiled=False):
        array = self.array
        array[array == self.nodata_value] = value
        self.update_band(array)

        self.band.SetNoDataValue(value)
        self.nodata_value = value
        
    def set_nan(self, array):
        return set_nan(array, self.nodata_value)
    
    def update_band(self, array, x=0, y=0):            
        self.band.WriteArray(array, x, y)
        self.band.FlushCache()       
        array = None


    def align(self, template=None, fill_value=None, nodata_align=True, quiet=True):
        return align(self, template, fill_value, nodata_align, quiet)
               
              
    def write(self, filename, array=None, geotransform=None, epsg=28992, nodata=-9999, 
              copy=False, metadata=None, overwrite=True):
        if self.type == 'array':
            if not geotransform and not hasattr(self, 'geotransform'):
                print('geotransform is None, whilst type is array')
        
        if array is not None:
            copy = False
        
        if overwrite:
            if os.path.exists(filename):
                DRIVER_GDAL_GTIFF.Delete(filename)
        
        # Copy is stabdard false --> we want a standardized output even though copy is faster
        if copy:
            
            ds = DRIVER_GDAL_GTIFF.CreateCopy(filename, 
                                              self.ds,
                                              options=WRITE_OPTIONS
                                              )
            
            if nodata is not None:
                ds.GetRasterBand(1).SetNoDataValue(nodata)
            else:
                ds.GetRasterBand(1).SetNoDataValue(self.nodata_value)
                
            srs = osr.SpatialReference()  
            srs.ImportFromEPSG(epsg)
            ds.SetProjection(srs.ExportToWkt()) 

            if not geotransform:
                geotransform = self.geotransform
                
            ds.SetGeoTransform(geotransform)
            
            if hasattr(self, 'name'):
                mdata = {'name': self.name}
                
            if metadata and hasattr(self, 'name'):
                mdata.update(metadata)
            
            if metadata or hasattr(self, 'name'):                
                ds.SetMetadata(mdata)
            
            ds = None
            return
        
        if array is None and hasattr(self, 'array'):
            array = self.array
            
        if not geotransform:
            geotransform = self.geotransform
            
        out = DRIVER_GDAL_GTIFF.Create(
            filename,
            self.columns,
            self.rows,
            1, # band
            self.data_type,
            options=WRITE_OPTIONS,
        )
        
        
        out.SetGeoTransform(geotransform)
        srs = osr.SpatialReference()  
        srs.ImportFromEPSG(epsg)
        out.SetProjection(srs.ExportToWkt())
        
        if array is None:            
            array = self.array
            
        array[np.isnan(array)] = self.nodata_value
        out.GetRasterBand(1).WriteArray(array)

        if nodata is not None:
            out.GetRasterBand(1).SetNoDataValue(nodata)
        else:
            out.GetRasterBand(1).SetNoDataValue(self.nodata_value)

        if hasattr(self, 'name'):
            mdata = {'name': self.name}
            
        if metadata and hasattr(self, 'name'):
            mdata.update(metadata)
        
        if metadata or hasattr(self, 'name'):                
            out.SetMetadata(mdata)
            
        out.FlushCache()  # write to disk
        out = None
   

def loc_dir(_dir=None, _type='ras', ext='tif', mem=False, add=True):
    global _loc_ras 
    if add:
        _loc_ras = _loc_ras + 1
    
    if mem:
        _dir = '/vsimem'
    return _dir + f'/{_type}_{_loc_ras}.{ext}'

def create_source(columns, rows, data_type):
        
    out = DRIVER_GDAL_MEM.Create(
        loc_dir(mem=True, add=True),
        columns,
        rows,
        1,
        data_type,
        options=WRITE_OPTIONS,
    )
    return out

def set_nan(array: np.array, nan_value=-9999):
    if np.dtype(array.dtype).char in np.typecodes['AllInteger']:
        array = array.astype(float)
    array[array==nan_value] = np.nan
    return array

def get_extent(transform, cols, rows):
    minx = transform[0]
    maxx = transform[0] + cols * transform[1] + rows * transform[2]

    miny = transform[3] + cols * transform[4] + rows * transform[5]
    maxy = transform[3]
    return minx, maxx, miny, maxy

    
def align(raster, template=None, fill_value=None, nodata_align=True,
          quiet=True):
    """ 
        Assumes the current location of the rasters is correct 
        and a similar pixel size

    """
    
    # template info
    gtt = template.geotransform
    columns = template.columns
    rows = template.rows

    # coordinate difference
    gti = raster.geotransform
    gtt_x, gtt_y = (gtt[0], gtt[3]) 
    gti_x, gti_y = (gti[0], gti[3])
    x_dif = (gtt_x - gti_x) / gtt[1]
    y_dif = (gtt_y - gti_y) / abs(gtt[5])
    
    
    if not quiet:
        print("Padding and deleting raster pixels where needed")
    
    raster_array = raster.array
    raster_sum = np.nansum(np.round(raster_array,2))
    
    raster_array[np.isnan(raster_array)] = raster.nodata_value
    
    if x_dif > 0:
        raster_array = raster_array[:, abs(int(x_dif)) :]
        # raster is to much to the left, delete values to the left
    elif x_dif < 0:
        # raster is too much to the right, add values on the left side
        raster_array = np.pad(
            raster_array,
            (
                (0, 0),  # pad upside  # pad downside
                (abs(int(x_dif)), 0),  # pad left side  # pad on the right side
            ),
            constant_values=raster.nodata_value,
        )

    col_dif = columns - raster_array.shape[1]
    if col_dif > 0:
        # add columns, width is too small
        raster_array = np.pad(
            raster_array,
            [
                (0, 0),  # pad upside  # pad downside
                (0, abs(int(col_dif))),  # pad left side  # pad on the right side
            ],
            constant_values=raster.nodata_value,
        )

    elif col_dif < 0:
        # delete columns 
        raster_array = raster_array[:, 0 : raster_array.shape[1] - abs(int(col_dif))]
        

    # works
    if y_dif > 0:
        # raster is to low
        # add rows on the upside if raster is to low
        raster_array = np.pad(
            raster_array,
            [
                (abs(int(y_dif)), 0),  # pad upside  # pad downside
                (0, 0),  # pad left side  # pad on the right side
            ],
            constant_values=raster.nodata_value,
        )
    elif y_dif < 0:
        # raster is too high
        # delete rows from upside if raster is too hgh
        raster_array = raster_array[abs(int(y_dif)) :, :]

    row_dif = rows - raster_array.shape[0]
    if row_dif > 0:
        raster_array = np.pad(
            raster_array,
            [
                (0, abs(int(row_dif))),  # pad upside  # pad downside
                (0, 0),  # pad left side  # pad on the right side
            ],
            constant_values=raster.nodata_value,
        )

    elif row_dif < 0:
        # raster is too large in height
        raster_array = raster_array[0 : raster_array.shape[0] - abs(int(row_dif)) :, :]

    
    if nodata_align:
        if not quiet:
            print("Padding nodata values onto the to be aligned array")
        
        nodata_index = np.isnan(template.array)
        raster_array[nodata_index] = raster.nodata_value

        if np.sum(raster_array == raster.nodata_value) != np.sum(nodata_index):    
            if fill_value == None:
                
                (values,counts) = np.unique(raster_array, return_counts=True)
                fill_value= values[np.argmax(counts)]
                if fill_value == raster.nodata_value:
                    fill_value = values[np.argmax(counts)-1]
                
            if not quiet:
                print(f"Padding fill value {fill_value} onto the to be aligned array")
            raster_array[~nodata_index & (raster_array == raster.nodata_value)] = fill_value

    raster_array[raster_array == raster.nodata_value] = np.nan
    if raster_sum != np.nansum(raster_array):
        #print('Raster sum input and output not the same, difference is', raster_sum - np.nansum(np.round(raster_array,2)))
        print('Note sum maybe different in numpy, please check qgis raster statistics')
    
    
    output = template.empty_copy()    
    output.update_band(raster_array)   
    return output



if __name__ == '__main__':
    pass

