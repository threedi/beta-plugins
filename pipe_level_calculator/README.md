# Pipe Level Calculator

A QGIS plugin intended to calculate pipe levels based on a design with pipe diameters and a DEM.

## Functionality

### Constraints
- Design input should be a shapefile 
- Design should consist of single line features
- Design shapefile should contain a column named 'id' and 'diameter' 
- Diameter values should be in mm
- DEM input should be a .tif file

###  Parameters
- *Mininum cover:* minimum distance from pipe top to surface level
- *Maximum drop height:* maximum difference between bottom levels for pipes connected to the same manhole
- *Smooth gradient straight pipes/ minimum angle for smoothing*: pipes that lie at an angle larger than the mininum angle will always have a connecting start and end level.
- *Gradient table:* for each pipe the distance to a source is calculated (furthest upstream point). This distance is used to assign a gradient. Distances can be specified like this:


| From (m) | To (m) | Gradient (m/m) |
|:--------:|:------:|:--------------:|
|     0    |   300  |      0.003     |
| 300      | 10000  |      0.002     |