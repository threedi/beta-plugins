from qgis.core import QgsProject
from qgis.core import QgsSnappingConfig
from qgis.core import QgsTolerance
from qgis.core import QgsRelation
from qgis.core import QgsEditorWidgetSetup
from qgis.utils import iface
import os


def reactivate_snapping():
    connodes_point_locator = iface.mapCanvas().snappingUtils().clearAllLocators()

def manhole_xsec_commit():
    v2_manhole_view = QgsProject.instance().mapLayersByName("v2_manhole_view")[0]
    if v2_manhole_view.isEditable() and v2_manhole_view.isModified():
        v2_manhole_view.commitChanges()
        v2_manhole_view.startEditing()

    v2_cross_section_definition = QgsProject.instance().mapLayersByName(
        "v2_cross_section_definition"
    )[0]
    if (
        v2_cross_section_definition.isEditable()
        and v2_cross_section_definition.isModified()
    ):
        v2_cross_section_definition.commitChanges()
        v2_cross_section_definition.startEditing()

def qgs_signals(tables):
    for table in tables:
        qgs_table = QgsProject.instance().mapLayersByName(table)[0]
        qgs_table.featureAdded.connect(reactivate_snapping)
        if not table in ['v2_manhole_view']:
            qgs_table.beforeCommitChanges.connect(manhole_xsec_commit)

def configure_snapping_settings():
    my_snap_config = QgsSnappingConfig()
    my_snap_config.setEnabled(True)
    my_snap_config.setMode(QgsSnappingConfig.AllLayers)
    my_snap_config.setType(QgsSnappingConfig.Vertex)
    my_snap_config.setUnits(QgsTolerance.Pixels)
    my_snap_config.setTolerance(10)
    my_snap_config.setIntersectionSnapping(True)

    QgsProject.instance().setSnappingConfig(my_snap_config)

def set_relations():
    v2_pipe_view = QgsProject.instance().mapLayersByName("v2_pipe_view")[0]
    v2_pipe_id = v2_pipe_view.id()
    pipe_idx = v2_pipe_view.fields().indexFromName("pipe_cross_section_definition_id")

    v2_orifice_view = QgsProject.instance().mapLayersByName("v2_orifice_view")[0]
    v2_orifice_id = v2_orifice_view.id()
    orf_idx = v2_orifice_view.fields().indexFromName("orf_cross_section_definition_id")
        
    v2_weir_view = QgsProject.instance().mapLayersByName("v2_weir_view")[0]
    v2_weir_id = v2_weir_view.id()
    weir_idx = v2_weir_view.fields().indexFromName("weir_cross_section_definition_id")
        
    v2_culvert_view = QgsProject.instance().mapLayersByName("v2_culvert_view")[0]
    v2_culvert_id = v2_culvert_view.id()
    cul_idx = v2_culvert_view.fields().indexFromName("cul_cross_section_definition_id")

    v2_cross_section_location_view = QgsProject.instance().mapLayersByName("v2_cross_section_location_view")[0]
    v2_cross_section_location_id = v2_cross_section_location_view.id()
    xsec_loc_idx = v2_cross_section_location_view.fields().indexFromName("loc_definition_id")
    
    v2_global_settings = QgsProject.instance().mapLayersByName("v2_global_settings")[0]
    v2_global_settings_id = v2_global_settings.id()
    glob_num_idx = v2_global_settings.fields().indexFromName("numerical_settings_id")
    glob_inf_idx = v2_global_settings.fields().indexFromName("simple_infiltration_settings_id")
    glob_ground_idx = v2_global_settings.fields().indexFromName("groundwater_settings_id")
    glob_int_idx = v2_global_settings.fields().indexFromName("interflow_settings_id")
    
    v2_numerical_settings = QgsProject.instance().mapLayersByName("v2_numerical_settings")[0]
    v2_numerical_settings_id = v2_numerical_settings.id()
    
    v2_simple_infiltration = QgsProject.instance().mapLayersByName("v2_simple_infiltration")[0]
    v2_simple_infiltration_id = v2_simple_infiltration.id()

    v2_groundwater = QgsProject.instance().mapLayersByName("v2_groundwater")[0]
    v2_groundwater_id = v2_groundwater.id()

    v2_interflow = QgsProject.instance().mapLayersByName("v2_interflow")[0]
    v2_interflow_id = v2_interflow.id()

    v2_cross_section_definition = QgsProject.instance().mapLayersByName(
        "v2_cross_section_definition"
    )[0]
    v2_cross_section_definition_id = v2_cross_section_definition.id()

    global_setting_relations = [["6","glob_num",0,v2_global_settings_id,v2_numerical_settings_id,"numerical_settings_id"],
    ["7","glob_inf",0,v2_global_settings_id,v2_simple_infiltration_id,"simple_infiltration_settings_id"],
    ["8","glob_ground",0,v2_global_settings_id,v2_groundwater_id,"groundwater_settings_id"],
    ["9","glob_int",0,v2_global_settings_id,v2_interflow_id,"interflow_settings_id"]]
    
    for id, name, strength, referencing_layer,referenced_layer,referencing_field in global_setting_relations:
        rel = QgsRelation()
        rel.setReferencingLayer(referencing_layer)
        rel.setReferencedLayer(referenced_layer)
        rel.addFieldPair(referencing_field, "id")
        rel.setId(id)
        rel.setName(name)
        rel.setStrength(strength)
        QgsProject.instance().relationManager().addRelation(rel)
    
    cross_section_relations = [["1","pipe_xsec",0,v2_pipe_id,v2_cross_section_definition_id,"pipe_cross_section_definition_id"],
    ["2","weir_xsec",0,v2_weir_id,v2_cross_section_definition_id,"weir_cross_section_definition_id"],
    ["3","orf_xsec",0,v2_orifice_id,v2_cross_section_definition_id,"orf_cross_section_definition_id"],
    ["4","cul_xsec",0,v2_culvert_id,v2_cross_section_definition_id,"cul_cross_section_definition_id"],
    ["5","loc_view_xsec",0,v2_cross_section_location_id,v2_cross_section_definition_id,"loc_definition_id"]]
        
    for id, name, strength, referencing_layer,referenced_layer,referencing_field in cross_section_relations:
        rel = QgsRelation()
        rel.setReferencingLayer(referencing_layer)
        rel.setReferencedLayer(referenced_layer)
        rel.addFieldPair(referencing_field, "id")
        rel.setId(id)
        rel.setName(name)
        rel.setStrength(strength)
        QgsProject.instance().relationManager().addRelation(rel)

    cfg = dict()
    cfg["OrderByValue"] = True
    cfg["AllowNULL"] = False
    cfg["ShowOpenFormButton"] = True
    cfg["AllowAddFeatures"] = True
    cfg["ShowForm"] = False
    cfg["FilterFields"] = []
    cfg["ChainFilters"] = False
    settingssetup = QgsEditorWidgetSetup("RelationReference", cfg)
    
    cfg = dict()
    cfg["OrderByValue"] = True
    cfg["AllowNULL"] = False
    cfg["ShowOpenFormButton"] = False
    cfg["AllowAddFeatures"] = True
    cfg["ShowForm"] = False
    cfg["FilterFields"] = ["shape", "width", "height"]
    cfg["ChainFilters"] = False
    xsecsetup = QgsEditorWidgetSetup("RelationReference", cfg)
    
    settings_list = [[v2_global_settings,glob_num_idx],
                      [v2_global_settings,glob_inf_idx],
                      [v2_global_settings,glob_ground_idx],
                      [v2_global_settings,glob_int_idx]]

    xsec_list = [[v2_weir_view, weir_idx],
                   [v2_pipe_view, pipe_idx],
                   [v2_culvert_view, cul_idx],
                   [v2_orifice_view, orf_idx],
                   [v2_cross_section_location_view,xsec_loc_idx]]

    for view, idx in xsec_list:
        view.setEditorWidgetSetup(idx, xsecsetup)
        
    for view, idx in settings_list:
        view.setEditorWidgetSetup(idx, settingssetup)
        
    expression = " id || ' code: ' || code "
    v2_cross_section_definition.setDisplayExpression(expression)

def configure_open_file_button():
    v2_global_settings = QgsProject.instance().mapLayersByName("v2_global_settings")[0]
    v2_simple_infiltration = QgsProject.instance().mapLayersByName("v2_simple_infiltration")[0]

    sqlite_file = (
            v2_global_settings.dataProvider()
            .dataSourceUri()
            .split(" table")[0]
            .replace("dbname=", "")
            .replace("'", "")
            )
    sqlite_dir = os.path.dirname(sqlite_file)
    setup = QgsEditorWidgetSetup("ExternalResource",{"DefaultRoot": sqlite_dir,
                                                 "RelativeStorage": 2,
                                                 "StorageMode": "GetFile"})
    idx = v2_global_settings.fields().indexFromName("frict_coef_file")
    v2_global_settings.setEditorWidgetSetup(idx,setup) 
    idx = v2_global_settings.fields().indexFromName("initial_groundwater_level_file")
    v2_global_settings.setEditorWidgetSetup(idx,setup) 
    idx = v2_global_settings.fields().indexFromName("initial_waterlevel_file")
    v2_global_settings.setEditorWidgetSetup(idx,setup) 
    idx = v2_global_settings.fields().indexFromName("dem_file")
    v2_global_settings.setEditorWidgetSetup(idx,setup)
    
    idx = v2_simple_infiltration.fields().indexFromName("infiltration_rate_file")
    v2_simple_infiltration.setEditorWidgetSetup(idx,setup)
    idx = v2_simple_infiltration.fields().indexFromName("max_infiltration_capacity_file")
    v2_simple_infiltration.setEditorWidgetSetup(idx,setup)