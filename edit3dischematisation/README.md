# Plugin to quickly alter 1D schematisations.

When toggled the views are altered to make them editable. While views are normally not editable they can now be used to update and/or insert new features into the source tables. On top of that the edit forms are filled with default values and numbers are changed into text to make it more intuitive. 

The views can be used to fill the fields of the source tables. The connection nodes can no longer be specified, these are instead filled through snapping the start and endpoint of the line features to (existing) connection nodes. Weirs, culverts, pumpstations and orifices will automatically create connection nodes when inserted or updated if they are not present yet. Pipes, on the other hand, have to be drawn from manhole to manhole, as this is a requirement in 3Di as well. If pipe invert levels are left empty the bottom of the adjoining manhole is taken.
