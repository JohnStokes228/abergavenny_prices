"""
Utilise long / lat info to construct polygonal view of the region.

TODO - figure out what to do about the rim of the region
     - figure out what to do about the bounding polygons - do they actually matter tbf? <- yes, especially for less
     gritty bits and bobs
"""
import pandas as pd
from scipy.spatial import Voronoi
from shapely import geometry, ops
import geopandas as gpd


df = pd.read_csv('data/monmouthshire_properties.csv')
df = df[['longitude', 'latitude', 'property_id',
         'postcode_sector_longitude', 'postcode_sector_latitude', 'postcode_sector',
         'postcode_district_longitude', 'postcode_district_latitude', 'postcode_district']].drop_duplicates()
df.dropna(axis=0, inplace=True)


def create_voronoi_tessellation(
    point_set: pd.DataFrame,
    file_name: str,
) -> None:
    """Create a shapefile for the resultant polygons when calculating a voronoi tessellation out of an input point set.

    Notes
    -----
    Currently the output here has 0 method to identify which point generated which polygon, which makes it effectively
    useless :( Luckily I have a plan to aggressively browse stack overflow until I can mysteriously come up with a
    solution to this issue all by myself with 0 aid.

    Parameters
    ----------
    point_set : DataFrame of long / lat values for a set of unique points, whose index is point IDs.
    file_name : Name to save the shapefile under.
    """
    tessellation = Voronoi(point_set)
    edges = [geometry.LineString(tessellation.vertices[line])
             for line in tessellation.ridge_vertices
             if -1 not in line]  # taken from a helpful stack overflow comment

    polygons = [gpd.GeoSeries(poly) for poly in ops.polygonize(edges)]
    polygons = gpd.GeoSeries(pd.concat(polygons))

    polygons.to_file(f'data/polygons/{file_name}.shp',
                     driver='ESRI Shapefile',
                     index=False)


### shit code just for testing ###
"""
Looking for a way to carry ID across from the input data to the resultant geopandas frame.
"""
point_set = df[['postcode_sector_longitude', 'postcode_sector_latitude', 'postcode_sector']].drop_duplicates()
point_set.set_index('postcode_sector', inplace=True)
tessellation = Voronoi(point_set)
edges = [geometry.LineString(tessellation.vertices[line])
         for line in tessellation.ridge_vertices
         if -1 not in line]

polygons = [gpd.GeoSeries(poly) for poly in ops.polygonize(edges)]
polygons = gpd.GeoDataFrame(pd.concat(polygons))
polygons.columns = ['geometry']

point_set["geometry"] = point_set.apply(lambda row: geometry.Point(row["postcode_sector_longitude"], row["postcode_sector_latitude"]), axis=1)
del(point_set['postcode_sector_longitude'], point_set['postcode_sector_latitude'])
point_set = gpd.GeoDataFrame(point_set, geometry='geometry')
test = gpd.tools.sjoin(polygons, point_set, how='left')
test.set_index('index_right', inplace=True)
# I *love* sjoin thats so cool ohmygod
# it just knows if the points are contained within each other and joins based on overlap
# only carries the left geometry over though incase that becomes relevant later
