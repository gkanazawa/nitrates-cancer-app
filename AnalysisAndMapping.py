''' This file contains functions which will access the required geoprocessing
tools. The steps are:
 - Prepare folder for first run if needed
 - Interpolate nitrate levels from sample wells via IDW
 - Summarize results of IDW interpolation at tract level
 - Update nitrates field in tracts shapefile
 - Run OLS linear regression
 - Run Moran's I spatial autocorrelation on OLS results
 '''

import arcpy
from arcpy import env
import os

wells = "data/well_nitrate.shp"
tracts = "data/cancer_tracts.shp"
counties = "data/cancer_county.shp"

dir = 'C:\\Geog777\\Project1\\'
# env.workspace = dir + "workspace"
arcpy.env.overwriteOutput = True


def initialize():

    for path in [
            'data/rasters',
            'data/ols_layers',
            'ols_reports'
        ]:
        os.makedirs(path, exist_ok=True)


def run_idw(wells, counties, k):

    in_point_features = wells
    z_field = 'nitr_ran'
    power = k

    idwPath = f'data/rasters/{str(k).replace(".", "_")}.tif'

    arcpy.env.mask = counties

    outIDW = arcpy.sa.Idw(in_point_features, z_field, power=power, cell_size=0.003)
    outIDW.save(idwPath)

    return idwPath


def get_avg_nitrate(tracts, zoneField, idw, k):

    outTable = r"memory\zonalStats"

    arcpy.sa.ZonalStatisticsAsTable(tracts, zoneField, idw, outTable)

    nitrateDict = {}
    cursor = arcpy.da.SearchCursor(r"memory\zonalStats", [zoneField, "MEAN"])
    for tract, mean in cursor:
        nitrateDict[tract] = mean

    outPath = r'C:\Geog777\Project1\CancerNitrates.gdb'
    
    arcpy.TableToTable_conversion(r"memory\zonalStats", outPath, "zonalConvTable")
    
    return nitrateDict


def update_nitrates_field(nitrateVals, tracts):

    # check if tracts has mean_nitrate field; if not, create it
    fields = [field.name for field in arcpy.ListFields(tracts)]

    if "MEAN" not in fields:
        print("Creating nitrate mean field")
        arcpy.AddField_management(tracts, "MEAN", "DOUBLE")

    cursor = arcpy.da.UpdateCursor(tracts, ["GEOID10", "MEAN"])
    for row in cursor:
        try:
            id = row[0]
            val = nitrateVals[id]

            row[1] = val
            cursor.updateRow(row)

        except Exception as e:
            print(f'Error updating id {id}')


 # Runs OLS linear regression; saves report file in output folder.
def run_ols(tracts, k):

    #Add Unique ID field to cancer tracts layer
    fields = [field.name for field in arcpy.ListFields(tracts)]
    if "UID" not in fields:
        arcpy.AddField_management(tracts, "UID", "LONG")
        with arcpy.da.UpdateCursor(tracts, ["FID", "UID"]) as cur:
            for row in cur:
                row[1] = row[0]
                cur.updateRow(row)

    arcpy.OrdinaryLeastSquares_stats(tracts, "UID", f'data/ols_layers/OLS_{str(k).replace(".", "_")}.shp', 'canrate', 'MEAN', Output_Report_File=f"ols_reports/{k}_ols.pdf")

# run spatial autocorrelation and return path to report
def run_moransI(k):

    olsFile = f'data/ols_layers/OLS_{str(k).replace(".", "_")}.shp'
    mI = arcpy.SpatialAutocorrelation_stats(olsFile, 'StdResid', 'GENERATE_REPORT', 'INVERSE_DISTANCE', 'EUCLIDEAN_DISTANCE', 'ROW')
    report = mI.getOutput(3)
    return report


def update_data_source(layer, k):
    newCP = layer.connectionProperties
    newSource = f'{str(k).replace(".","_")}.tif'
    newCP['dataset'] = newSource
    layer.updateConnectionProperties(layer.connectionProperties, newCP)

def generate_maps(k):

    aprx = arcpy.mp.ArcGISProject(r'C:\Geog777\Project1\CancerNitrates.aprx')

    # update IDW raster in map
    IDWMap = aprx.listMaps('Map')[0]
    IDWLayer = IDWMap.listLayers('Idw*')[0]
    update_data_source(IDWLayer, k)

    #update K label in layout
    IDWLayout = aprx.listLayouts('IDW*')[0]
    lblK = IDWLayout.listElements('TEXT_ELEMENT', '*')[1]
    lblK.text = f'K = {k}'

    #export IDW map
    IDWLayout.exportToPNG(r'reports/IDW_{}.png'.format(str(k).replace(".","_")), 200)

    #update OLS in map
    OLSMap = aprx.listMaps('OLS_Map')[0]
    OLSLayer = OLSMap.listLayers('OLS*')[0]
    update_data_source(OLSLayer, k)

    #export OLS map
    OLSLayout = aprx.listLayouts('OLS_Layout')[0]
    OLSK = OLSLayout.listElements('TEXT_ELEMENT', '*')[1]
    OLSK.text = f'K = {k}'
    OLSLayout.exportToPNG(r'reports/OLS_{}.png'.format(str(k).replace(".","_")), 200)

    aprx.save()


# def generate_maps(k):
#     #projectPath = r'CancerNitrates.aprx'

#     aprx = arcpy.mp.ArcGISProject(r'C:\Geog777\Project1\CancerNitrates.aprx')

#     # update IDW raster in map
#     IDWMap = aprx.listMaps('Map')[0]
#     IDWLayer = IDWMap.listLayers('Idw*')[0]
#     update_data_source(IDWLayer, k)

#     #update K label in layout
#     IDWLayout = aprx.listLayouts('IDW*')[0]
#     lblK = IDWLayout.listElements('TEXT_ELEMENT', '*')[1]
#     lblK.text = f'K = {k}'

#     #export IDW map
#     IDWLayout.exportToPNG(r'reports/IDW_{}.png'.format(str(k).replace(".","_")), 150)

#     #update OLS in map
#     OLSMap = aprx.listMaps('OLS_Map')[0]
#     OLSLayer = OLSMap.listLayers('OLS*')[0]
#     # OLSLayer = OLSMap.listLayers('*')[0]
#     update_data_source(OLSLayer, k)

#     #export OLS map
#     olsLayout = aprx.listLayouts('OLS_Layout')[0]
#     olsK = olsLayout.listElements('TEXT_ELEMENT', '*')[1]
#     olsK.text = f'K = {k}'
#     olsLayout.exportToPNG(r'reports/OLS_{}.png'.format(str(k).replace(".","_")), 150)

#     aprx.save()
