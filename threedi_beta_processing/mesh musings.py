project=QgsProject.instance()
mesh_layer=project.mapLayersByName('mesh')[0]
transform=QgsCoordinateTransform()
transform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:28992"),
                                   QgsCoordinateReferenceSystem("EPSG:28992"), QgsProject.instance())
mesh_layer.startFrameEditing(transform)
editor = mesh_layer.meshEditor()
editor.addPointsAsVertices([QgsPoint(93100, 44111, 3)], 10)
