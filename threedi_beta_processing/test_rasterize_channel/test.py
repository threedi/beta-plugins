from rasterize_channel import *

sqlite = 'empty.sqlite'
output_raster = 'test.tif'

import shapely
from shapely.geometry import MultiPoint, Polygon, LineString
from shapely.wkb import loads
# vragen aan Ivar
# is het ook geschikt voor andere projecties dan 28992?
# gelijk aan het begin checken of alle inputs en output(locatie)s valide zijn
# duurt lang, analyseren waar dat door komt: rasterizeren of opzoekfuncties (joins). je doet wel iets met spatial index
# maar ik vraag me af of die ook gebruikt wordt
# zou fijn zijn als je in de attribute table van v2_channel kan selecteren welke je wilt rasterizeren
# optie om gelijk te burnen in de dem
# optie om bij het burnen in de dem 'alleen verlagen' aan te kunnen vinken
# de interpolatie gaat nog niet helemaal lekker (zie plaatje), misschien gaat het beter met arjan z'n fill algoritme?
# TODO: use sqlalchemy and standardised 3Di object-relations mappings


rasterize_channels('hillegersberg-schiebroek.sqlite', 'hilligersberg-schiebroek7.tif',[10093])