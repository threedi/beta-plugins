uri = "1.0, 2.0 \n" \
      "2.0, 2.0 \n" \
      "3.0, 2.0 \n" \
      "2.0, 3.0 \n" \
      "1.0, 3.0 \n" \
      "---" \
      "0, 1, 3, 4 \n" \
      "1, 2, 3 \n"

mesh_layer = QgsMeshLayer(uri, "Memory Mesh", "mesh_memory")
QgsProject.instance().addMapLayer(mesh_layer)
transform = QgsCoordinateTransform()
# transform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:28992"),
#                                   QgsCoordinateReferenceSystem("EPSG:28992"), QgsProject.instance())
mesh_layer.startFrameEditing(transform)
editor = mesh_layer.meshEditor()
editor.addPointsAsVertices([QgsPoint(0, 0, 0), QgsPoint(50, 100, 10), QgsPoint(100, 0, 20)], 10)
mesh_layer.stopFrameEditing(transform)

# -------
from uuid import uuid4

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsMesh,
    QgsMeshLayer,
    QgsPoint,
    QgsProcessingUtils,
    QgsProviderRegistry
)

provider_meta = QgsProviderRegistry.instance().providerMetadata('mdal')

# create a mesh on disk
mesh = QgsMesh()
temp_mesh_filename = f"{uuid4()}.nc"
temp_mesh_fullpath = QgsProcessingUtils.generateTempFilename(temp_mesh_filename)
mesh_format = 'Ugrid'
crs = QgsCoordinateReferenceSystem()
provider_meta.createMeshData(mesh, temp_mesh_fullpath, mesh_format, crs)

# open the mesh
mesh_layer = QgsMeshLayer(temp_mesh_fullpath, 'editable mesh', 'mdal')
QgsProject.instance().addMapLayer(mesh_layer)
print(mesh_layer.isValid())
print(mesh_layer.supportsEditing())
transform = QgsCoordinateTransform()
mesh_layer.startFrameEditing(transform)
print(mesh_layer.meshVertexCount())  # -> 0
print(mesh_layer.meshFaceCount())  # -> 0
vertices = [QgsPoint(0, 0, 0), QgsPoint(50, 100, 10), QgsPoint(100, 0, 20)]
mesh_layer.meshEditor().addPointsAsVertices(vertices, 1)
print(mesh_layer.meshVertexCount())  # ->3
mesh_layer.meshEditor().addFace([0, 1, 2])
print(mesh_layer.meshFaceCount())  # ->1
vertices = [QgsPoint(0, 0, 0), QgsPoint(50, -100, 10), QgsPoint(100, 0, 20)]
mesh_layer.meshEditor().addPointsAsVertices(vertices, 1)
mesh_layer.commitFrameEditing(transform, continueEditing=False)
