mesh_layer = QgsProject.instance().mapLayersByName('mesh2d')[0]
transform = QgsCoordinateTransform()
mesh_layer.startFrameEditing(transform)
editor = mesh_layer.meshEditor()
error = editor.addFace([51, 52, 25])
error.errorType
# <MeshEditingErrorType.UniqueSharedVertex: 4>
error.elementIndex
# 51