setlocal EnableDelayedExpansion

for /l %%x in (12, 1, 12) do (
   set "rank=000000%%x"
   echo !rank:~-2!
   echo ogr2ogr -f "PostgreSQL" PG:"host=utr-gis-db-01 user=postgis password=postgis dbname=w0176_3di_goes_global" -lco schema=hydrobasins -nln "level_!rank:~-2!" -nlt PROMOTE_TO_MULTI "HydroBASINS Europe v1c\hybas_eu_lev!rank:~-2!_v1c.shp"
   ogr2ogr -f "PostgreSQL" PG:"host=utr-gis-db-01 user=postgis password=postgis dbname=w0176_3di_goes_global" -lco schema=hydrobasins -nln "level_!rank:~-2!" -nlt PROMOTE_TO_MULTI "HydroBASINS Europe v1c\hybas_eu_lev!rank:~-2!_v1c.shp"
)
echo done!
pause
