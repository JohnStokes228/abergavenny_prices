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


def get_tesselation_ids(
        longitude: str,
        latitude: str,
        point_set: pd.DataFrame,
        polygons: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Attach meaningful IDs to a series of polygons, based on the row index of points in a dataframe which fall
    within the polygons.

    Notes
    -----
    I *love* sjoin thats so cool ohmygod it just knows if the points are contained within each other and joins based
    on overlap only carries the left geometry over though incase that becomes relevant later. according to google the
    column by name 'geometry' is the 'active geometry' of the dataframe, so if we wish to retain both geometries we
    need only add a column equal to geometry for right df but with a different name. i.e.
    right_df['geomtery_store'] = right_df['geometry']
    total = gpd.tools.sjoin(left_df, right_df, how='left')
    looks like you can use alternate rules for joins using the 'op' variable too, which defaults to = 'intersects',
    hence the behaviour observed in this function.

    Parameters
    ----------
    longitude : Variable name of longitude variable in point_set.
    latitude : Variable name of latitude variable in point_set.
    point_set : Input dataframe whose index is the desired ID variable for the polygons.
    polygons : GeoPandas DataFrame of voronoi polygons.

    Returns
    -------
    gpd.GeoDataFrame
        As 'polygons' input, but with the extra column 'right_index', which will contain the desired IDs.
    """
    point_set["geometry"] = (
        point_set
        .apply(lambda row: geometry.Point(row[longitude], row[latitude]), axis=1)
    )
    del (point_set[longitude], point_set[latitude])

    point_set = gpd.GeoDataFrame(point_set, geometry='geometry')

    polygons = gpd.tools.sjoin(polygons, point_set, how='left')
    polygons.set_index('index_right', inplace=True)

    return polygons


def create_voronoi_tessellation(
    point_set: pd.DataFrame,
    file_name: str,
    longitude: str,
    latitude: str,
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
    longitude : Column name of longitude variable in point_set df.
    latitude : Column name of latitude variable in point_set df.
    """
    tessellation = Voronoi(point_set)
    edges = [geometry.LineString(tessellation.vertices[line])
             for line in tessellation.ridge_vertices
             if -1 not in line]  # taken from a helpful stack overflow comment

    polygons = [gpd.GeoSeries(poly) for poly in ops.polygonize(edges)]
    polygons = gpd.GeoDataFrame(pd.concat(polygons))
    polygons.columns = ['geometry']

    polygons = get_tesselation_ids(longitude=longitude,
                                   latitude=latitude,
                                   point_set=point_set,
                                   polygons=polygons)
    polygons.to_file(f'data/polygons/{file_name}.shp',
                     driver='ESRI Shapefile',
                     index=False)


df = pd.read_csv('data/monmouthshire_properties.csv')
df = df[['longitude', 'latitude', 'property_id',
         'postcode_sector_longitude', 'postcode_sector_latitude', 'postcode_sector',
         'postcode_district_longitude', 'postcode_district_latitude', 'postcode_district']].drop_duplicates()
df.dropna(axis=0, inplace=True)
test = df[['longitude', 'latitude', 'property_id']].drop_duplicates()
test.set_index('property_id', inplace=True)
create_voronoi_tessellation(test, 'postcode_polygons', 'longitude', 'latitude')

test = df[['postcode_sector_longitude', 'postcode_sector_latitude', 'postcode_sector']].drop_duplicates()
test.set_index('postcode_sector', inplace=True)
create_voronoi_tessellation(test, 'postcode_sector_polygons', 'postcode_sector_longitude', 'postcode_sector_latitude')

test = df[['postcode_district_longitude', 'postcode_district_latitude', 'postcode_district']].drop_duplicates()
test.set_index('postcode_district', inplace=True)
create_voronoi_tessellation(test, 'postcode_district_polygons', 'postcode_district_longitude', 'postcode_district_latitude')
