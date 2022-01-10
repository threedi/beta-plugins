import sys; import os
sys.path.append('C:/Users/stijn.overmeen/Documents/GitHub/beta-plugins/threedi_beta_processing')
from rasterize_channel import *

from pathlib import Path
folder=Path(r"C:/Users/stijn.overmeen/Documents/Projecten_lokaal/Intern/Rasterize channel")
sqlite=os.path.join(folder,'hillegersberg-schiebroek.sqlite')
dem=os.path.join(folder,'dem.tif')
output_raster=os.path.join(folder,'test_one_script_profile.tif')

#10065 skipped (wrong geometry)
list_of_channels=[40032,11029,11007,10903,10902,10901,10894,10893,10892,10891,10890,10885,10884,10883,10882,10881,10880,10878,10877,
                  10876,10873,10867,10866,10855,10854,10848,10844,10843,10842,10839,10838,10837,10836,10835,10834,10833,10832,10831,
                  10830,10829,10828,10824,10823,10822,10821,10820,10818,10796,10795,10794,10793,10787,10776,10775,10768,10767,10765,
                  10720,10719,10543,10517,10259,10258,10257,10256,10231,10230,10229,10228,10227,10226,10225,10224,10223,10222,10216,
                  10210,10209,10208,10207,10191,10186,10182,10181,10178,10177,10176,10175,10174,10171,10170,10169,10168,10167,10166,
                  10165,10163,10161,10160,10159,10158,10157,10156,10152,10151,10150,10149,10148,10147,10146,10145,10144,10142,10141,
                  10140,10139,10138,10137,10131,10130,10129,10128,10127,10126,10125,10124,10123,10122,10121,10119,10115,10114,10113,
                  10112,10111,10110,10109,10102,10101,10094,10093,10091,10090,10089,10088,10087,10086,10085,10082,10081,10080,10079,
                  10078,10077,10076,10075,10074,10073,10072,10071,10070,10068,10064,10063,10062,10061,10060,10059,10058,10057,10056,
                  10054,10053,10052,10051,10050,10049,10048,10047,10046,10045,10044,10043,10042,10041,10040,10039,10038,10037,10036,
                  10025,10022,10021,10020,10009,10008,10007]

rasterize_channels(sqlite,dem,output_raster,'profile',True,0,28992,list_of_channels)
    #sqlite / dem / output raster / rasterize profile or bank level? / lower (profile) or higher (bank_level) only /
    #add constant value / projection EPSG / list of channel id's

'''    
Vragen aan Ivar
      is het ook geschikt voor andere projecties dan 28992?
      gelijk aan het begin checken of alle inputs en output(locatie)s valide zijn
      duurt lang, analyseren waar dat door komt: rasterizeren of opzoekfuncties (joins). je doet wel iets met spatial index
      maar ik vraag me af of die ook gebruikt wordt
      zou fijn zijn als je in de attribute table van v2_channel kan selecteren welke je wilt rasterizeren
      optie om gelijk te burnen in de dem
      optie om bij het burnen in de dem 'alleen verlagen' aan te kunnen vinken
      de interpolatie gaat nog niet helemaal lekker (zie plaatje), misschien gaat het beter met arjan z'n fill algoritme?
      use sqlalchemy and standardised 3Di object-relations mappings

Comments Stijn:
    Logging toegevoegd
        -> Hieruit blijkt dat het interpoleren 3 min van de 5 min opneemt (test voor maar 1 channel!)
    Target projectie variabel gemaakt
    Interpoleren sneller gemaakt met gdal.rasterize en gdal.fillnodata, van 3 min naar 3 sec!
    Interpolatie nu ook beter bij randen kanaal
    Profile tool omgezet naar bank level tool (quick and dirty)
    Optie waarde bovenop bank level toegevoegd (verzoek Ivar)
    Check meerdere channels, twee gaat goed
    Problemen bij alle channels tegelijk: een invalid polygon -> 10065, weglaten
    Script runt 5 minuten voor alle 200 channels 
    Er gaat nog veel fout
    Polygonen moet punten volgen (polygonen worden niet juist gecreeerd): channel outline is herzien
        door buitenste punten te verzamelen. Meest tijdrovend geweest om juiste module te vinden
    Polygonen sloten nog niet precies aan op nodes, bij elke begin en eind vertice dus nog twee punten
        verzameld uit line.coords en toegevoegd aan boundary points
    Samensmeltingen van channels, hoe hier mee om te gaan?
        Net niet samenkomende polygonen? Deze moeten eigenlijk aangesloten worden, zie plaatje
            fix door dissolve, buffer 1m, buffer -1m
        Bij overlappende polygonen moeten de punten van maar 1 channel gebruikt worden voor de interpolatie.
            Nu is het een zooitje met punten die door elkaar lopen met verschillende hoogtes van verschillende profielen.
            When adding the points, check if points are already within existing polygon, 
            if so, don't add them
                Zou betekenen dat de channel met het laagste id-nummer leidend is
                TODO: nadenken of dit handiger kan
                    Aan de andere kant ook ingewikkeld om dit door de gebruiker te laten bepalen
            Deze zoektocht of elk punt binnen een van de polygonen valt vertraagd het proces enorm
            En is toenemend trager naarmate er mee polygonen bijkomen
                Sommige channels bevatten heel erg veel punten, niet alle punten hoeven gecheckt te worden
                Alleen bij uiteindes channel
                    Rule nu: bij eerste 10 of laatste 10 langspunten
    Script runt nu 7 minuten voor alle channels
        Bank level tool kan nog wat sneller worden als minder hoogtepunten worden meegenomen
    Het ziet er nog niet overal optimaal uit bij samenvoegingen, maar gebruiker kan zelf ook kritisch kijken
    naar schematisatie/ rasters
    Burnen in op te geven DEM toegevoegd, bank level leidend over dem
    Profile tool ook even ingekopt (kleine wijziging ten opzichte van huidige bank level tool)
    Optie toegevoegd: alleen verlagen (lijkt me alleen interessant voor profile tool)
    Optie toegevoegd: alleen verhogen (lijkt me alleen interessant voor bank level tool)
    Scripts samengevoegd en opgeschoond tot 1 rasterize_channel met keuze voor rasterizeren bank level of profiel
        Alleen boundary points verzamelen voor bank level tool scheelt 2 minuten (resultaten identiek)
    Uiteindelijk duurt het script 5 minuten als bank level tool en 7 minuten als profile tool voor 200 channels
    TODO: Check bij Leendert en hulp van Leendert bij
        omschrijven tot class met functions
        plug-in maken
    
'''