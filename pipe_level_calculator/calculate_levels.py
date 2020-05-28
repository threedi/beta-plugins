# -*- coding: utf-8 -*-
"""
Created on Thu May 14 21:28:45 2020

@author: Emile.deBadts
"""

import pandas
import networkx
import gdal,ogr
import json
import numpy as np

MEM_DRIVER = ogr.GetDriverByName('MEMORY') 
MAX_ITERATIONS = 100

def get_angle(p0, p1=np.array([0,0]), p2=None):

    if p2 is None:
        p2 = p1 + np.array([1, 0])
    v0 = np.array(p0) - np.array(p1)
    v1 = np.array(p2) - np.array(p1)

    angle = np.math.atan2(np.linalg.det([v0,v1]),np.dot(v0,v1))
    return np.degrees(angle)

def bereken_bobs(task, trace_fn, dem_fn, minimale_dekking, maximale_valhoogte, egalisatie, verhang_tabel, egalisatiehoek):

    # DEM met gdal
    dem_ds = gdal.Open(dem_fn)
    dem_rb = dem_ds.GetRasterBand(1)
    demNoData =  dem_rb.GetNoDataValue()
    gt = dem_ds.GetGeoTransform()
    
    # lees trace vanaf shape
    network = networkx.read_shp(path = trace_fn, geom_attrs = True)

    # leest trace met ogr
    trace_ds = ogr.Open(trace_fn)
    trace_layer = trace_ds.GetLayer(0)
    
    # lees trace met pandas
    trace_df = pandas.DataFrame(columns=['id', 'diameter','source_coordinate', 'target_coordinate','source','target','length', 'source_elevation','target_elevation','startpoint_distance', 'gradient'])
    
    # Voeg id toe aan iedere node
    for i, node in enumerate(network.nodes):
        network.nodes[node]['id'] = i
    
    # Voeg id's toe aan de edges van het netwerk
    trace_layer.ResetReading()
    for feature in trace_layer:
        
        if feature.diameter is None:
            raise Exception('Pipe with id {leiding_id} doesnt have a diameter'.format(leiding_id = feature.id))
        if feature.id is None:
            raise Exception('Not all pipes have an ID')
                
        feature_id = feature.id
        feature_geometry = feature.GetGeometryRef()
        geometry_json = feature_geometry.ExportToJson()
        geometry_coordinates = json.loads(geometry_json)['coordinates']
        geometry_length = feature_geometry.Length()
        
        edge_source_coordinates = tuple(geometry_coordinates[0])
        edge_target_coordinates = tuple(geometry_coordinates[1]) 
        edge_key = (edge_source_coordinates, edge_target_coordinates)
        network.edges[edge_key]['id'] = feature_id
        network.edges[edge_key]['length'] = geometry_length
        
        # Source node en target node van de huigdige edge 
        source_id = network.nodes[edge_source_coordinates]['id']
        target_id = network.nodes[edge_target_coordinates]['id']

        # sample dem voor begin en eindpunt van de leiding
        p_source_x = int((edge_source_coordinates[0] - gt[0]) / gt[1]) #x pixel
        p_source_y = int((edge_source_coordinates[1] - gt[3]) / gt[5]) #y pixel

        p_target_x = int((edge_target_coordinates[0] - gt[0]) / gt[1]) #x pixel
        p_target_y = int((edge_target_coordinates[1] - gt[3]) / gt[5]) #y pixel
                
        p_source_dem = dem_rb.ReadAsArray(p_source_x,p_source_y,1,1)
        p_target_dem = dem_rb.ReadAsArray(p_target_x,p_target_y,1,1)
        
        if p_source_dem is None:
            raise Exception('Startpoint of pipe {leiding_id} is outside DEM extent'.format(leiding_id = feature_id))
        if p_target_dem is None:
            raise Exception('Endpoint of pipe {leiding_id} is outside DEM extent'.format(leiding_id = feature_id))
        
        p_source_dem = p_source_dem[0]
        p_target_dem = p_target_dem[0]
                        
        if p_source_dem == demNoData:
            raise Exception('No Data value in DEM for startpoint of pipe {leiding_id}'.format(leiding_id = feature_id))
        if p_target_dem == demNoData:
            raise Exception('No Data value in DEM for endpoint of pipe {leiding_id}'.format(leiding_id = feature_id))       
            

        append_dict = {'id': feature_id, 
                       'diameter':feature.diameter,
                       'source_coordinate':[edge_source_coordinates],
                       'target_coordinate':[edge_target_coordinates],
                       'source': source_id,
                       'target': target_id,
                       'length': geometry_length, 
                       'source_elevation': p_source_dem,
                       'target_elevation': p_target_dem,
                       'startpoint_distance': 0}
        
        trace_df = trace_df.append(pandas.DataFrame(append_dict, index=[feature_id]), sort = False)
    
    # calculate distance matrix 
    reverse_network = network.reverse()  # reverses het netwerk, we willen de afstand naar het begin
    distance_matrix = dict(networkx.all_pairs_dijkstra(reverse_network, weight='length'))
    
    for node in network.nodes:
        node_id = network.nodes[node]['id']
        distance_dictionary = distance_matrix[node][0]
        max_distance = list(distance_dictionary.items())[-1][1]   
        trace_df.loc[trace_df.source==node_id, 'startpoint_distance'] = max_distance + trace_df.length
        
    # Sample de dem voor het begin en eindpunt van de leidingen
    # Bepaal voor elke buis wat het verhang moet zijn op basis van de afstand tot het beginpunt
    for index, p in trace_df.iterrows():
        p_id = p.id
        p_startpoint_distance = p.startpoint_distance                     
        for category in verhang_tabel:
            if p_startpoint_distance >= category[0] and p_startpoint_distance < category[1]:
                trace_df.loc[trace_df.id == p_id, 'gradient'] = category[2]
                break
                 
    
    # Bereken de bob's op basis van de dem en de minimale dekking     
    trace_df['invert_level_start_point'] = trace_df['source_elevation'] - minimale_dekking - (trace_df['diameter'] / 1000)
    trace_df['invert_level_end_point'] = trace_df['source_elevation'] - minimale_dekking - (trace_df['gradient'] * trace_df.length) - (trace_df['diameter'] / 1000)
    
    # doordat verhang van het maaiveld groter is dan het verhang van de buis kan de bob_eind niet genoeg dekking krijgen
    trace_df.loc[(trace_df.invert_level_end_point + trace_df.diameter/1000) > (trace_df.target_elevation - minimale_dekking), 'invert_level_start_point'] = trace_df['invert_level_start_point'] - ((trace_df['invert_level_end_point'] + trace_df.diameter/1000) - (trace_df.target_elevation - minimale_dekking))
    trace_df.loc[(trace_df.invert_level_end_point + trace_df.diameter/1000) > (trace_df.target_elevation - minimale_dekking), 'invert_level_end_point'] = trace_df['invert_level_end_point'] - ((trace_df['invert_level_end_point'] + trace_df.diameter/1000) - (trace_df.target_elevation - minimale_dekking))
    
    wrong_pipes = True
    iterations = 0
    
    while wrong_pipes and iterations < MAX_ITERATIONS:
                
        wrong_pipes = False
        
        for p_index, p_row in trace_df.iterrows():
                        
            p_id = p_row.id
                
            p_source_id = p_row.source
            p_target_id = p_row.target
            
            # Find connected pipes to current pipe
            connected_pipes = trace_df.loc[((trace_df.source == p_target_id) |   
                                                (trace_df.target == p_source_id)) &
                                                (trace_df.id != p_id)]
            
            if len(connected_pipes) > 0:
                
                for pc_index, pc_row in connected_pipes.iterrows():
                                        
                    if pc_row.source == p_target_id:
                        
                        # Calculate angle between pipe and connected pipe
                        angle = get_angle(p_row.source_coordinate, p_row.target_coordinate, pc_row.target_coordinate)

                    
                        if pc_row.invert_level_start_point > p_row.invert_level_end_point:
                            
                            wrong_pipes = True
                            
                            # connected pipe bob start becomes p_invert_level_end_point
                            pipe_drop =  pc_row.invert_level_start_point - p_row.invert_level_end_point
                            trace_df.loc[trace_df.id == pc_row.id, 'invert_level_start_point'] = pc_row.invert_level_start_point - pipe_drop
                            trace_df.loc[trace_df.id == pc_row.id, 'invert_level_end_point'] = pc_row.invert_level_end_point - pipe_drop
                        
                        if ((p_row.invert_level_end_point - pc_row.invert_level_start_point) - maximale_valhoogte) > 0.001:        
                        
                            wrong_pipes = True
                            
                            # connected pipe bob end becomes p_invert_level_start_point    
                            pipe_drop =  (p_row.invert_level_end_point - pc_row.invert_level_start_point) - maximale_valhoogte
                            trace_df.loc[trace_df.id == p_row.id, 'invert_level_start_point'] = p_row.invert_level_start_point - pipe_drop
                            trace_df.loc[trace_df.id == p_row.id, 'invert_level_end_point'] = p_row.invert_level_end_point - pipe_drop
                        
                        if egalisatie and (p_row.invert_level_end_point - pc_row.invert_level_start_point) > 0.0001 and abs(angle) > egalisatiehoek:

                            wrong_pipes = True
                            
                            # connected pipe bob end becomes p_invert_level_start_point    
                            pipe_drop =  (p_row.invert_level_end_point - pc_row.invert_level_start_point)
                            trace_df.loc[trace_df.id == p_row.id, 'invert_level_start_point'] = p_row.invert_level_start_point - pipe_drop
                            trace_df.loc[trace_df.id == p_row.id, 'invert_level_end_point'] = p_row.invert_level_end_point - pipe_drop                        

                    elif pc_row.target == p_source_id:

                        # Calculate angle between pipe and connected pipe
                        angle = get_angle(p_row.target_coordinate, p_row.source_coordinate, pc_row.source_coordinate)
                        
                        if pc_row.invert_level_end_point < p_row.invert_level_start_point:        
                        
                            wrong_pipes = True
                            
                            # connected pipe bob end becomes p_invert_level_start_point    
                            pipe_drop =  p_row.invert_level_start_point - pc_row.invert_level_end_point
                            trace_df.loc[trace_df.id == p_id, 'invert_level_start_point'] = p_row.invert_level_start_point - pipe_drop
                            trace_df.loc[trace_df.id == p_id, 'invert_level_end_point'] = p_row.invert_level_end_point - pipe_drop
                            
                        if ((pc_row.invert_level_end_point - p_row.invert_level_start_point) - maximale_valhoogte) > 0.001:        
                            
                            wrong_pipes = True
                            
                            # connected pipe bob end becomes p_invert_level_start_point    
                            pipe_drop =  (pc_row.invert_level_end_point - p_row.invert_level_start_point) - maximale_valhoogte
                            trace_df.loc[trace_df.id == pc_row.id, 'invert_level_start_point'] = pc_row.invert_level_start_point - pipe_drop
                            trace_df.loc[trace_df.id == pc_row.id, 'invert_level_end_point'] = pc_row.invert_level_end_point - pipe_drop
                        
                        if egalisatie and (pc_row.invert_level_end_point - p_row.invert_level_start_point) > 0.0001 and abs(angle) > egalisatiehoek:
                            
                            wrong_pipes = True
                            
                            pipe_drop =  pc_row.invert_level_end_point - p_row.invert_level_start_point 
                            trace_df.loc[trace_df.id == pc_row.id, 'invert_level_start_point'] = pc_row.invert_level_start_point - pipe_drop
                            trace_df.loc[trace_df.id == pc_row.id, 'invert_level_end_point'] = pc_row.invert_level_end_point - pipe_drop
                        
                        
        iterations+=1
    
    
    out_ds = MEM_DRIVER.CreateDataSource('mem_source')
    out_layer = out_ds.CopyLayer(trace_ds.GetLayer(0), 'trace_df_bobs')
 
    source_field = ogr.FieldDefn('source', ogr.OFTInteger)
    out_layer.CreateField(source_field)
    
    target_field = ogr.FieldDefn('target', ogr.OFTInteger)
    out_layer.CreateField(target_field)
    
    for field in trace_df.columns[6:]:
        field_name = ogr.FieldDefn(field, ogr.OFTReal)
        out_layer.CreateField(field_name)
    
    for feature in out_layer:
        feature_id = feature.id
        for field_name in trace_df.columns[4:]:
            feature.SetField(field_name, float(trace_df.loc[trace_df.id==feature_id, field_name].values[0]))
        out_layer.SetFeature(feature)    
        feature = None  

    trace_ds = None        
    trace_layer = None
    out_layer = None 
    
    return({'network_ds':out_ds,'iteraties':iterations})

