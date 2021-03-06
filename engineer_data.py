"""
Joining datasets together to form a single csv. Doing additional feature engineering where necessary to prep for the
analysis.
these include:
    - joining price and location data to form a single dataset.
    - creating a unique property ID based on postcode, house number and road name.
    - interpolating the probable value of the property in years between sales.
    - adding info on distance to and brand of closest supermarket.
    - *extracting a bunch of extra info from some columns*

*text* = not yet but will do soon lol.

TODO: - add extra data such as distance from centroids / etc...
"""
import pandas as pd
import numpy as np
from functools import reduce
from scipy.spatial.distance import cdist
from data_manipulation import (
    create_col_hash,
    clean_column_names,
    convert_column_to_boolean,
)


def interpolate_price_paid(df: pd.DataFrame) -> pd.DataFrame:
    """Interpolate the value of the property for years where it has none, rename columns ready for the join.

    Notes
    -----
    So far as I can tell pandas' "interpolate" functionality will only be used to fill nans that fall between non-nan
    elements. As such its important we dont create fake rows prior to this step. that said, if the point of
    interpolating is to get a consistent time series then we'll need to forecast / backcast the prices for properties
    who were first sold after 1995, or last sold prior to 2021.

    Parameters
    ----------
    df : Data, including unique property_id and deed_date as datetime type.

    Returns
    -------
    pd.DataFrame
        Resampled data with a row per property per year and interpolated price values.
    """
    df = df[['property_id', 'deed_date', 'price_paid']]
    df.set_index('deed_date', inplace=True)

    df = df.groupby('property_id').resample('Y').mean()  # row per id per year between earliest and latest year for id
    df['price_paid'] = df['price_paid'].interpolate()  # linear - is this the best spline to fit?

    df.reset_index(inplace=True)
    df['year'] = df['deed_date'].dt.to_period('Y')
    df.drop('deed_date', inplace=True, axis=1)
    df.rename(columns={'price_paid': 'interpolated_price'}, inplace=True)

    return df


def get_postcode_columns(
    df: pd.DataFrame,
    postcode_col: str = 'postcode',
) -> pd.DataFrame:
    """Transform an input postcode column into each level of grit in the postcode. Also adds postcode level long / lat.

    Parameters
    ----------
    df : Input dataframe containing a postcode column.
    postcode_col : Name of the column containing postcode info.

    Returns
    -------
    pd.DataFrame
        Input dataframe with postcode columns added.
    """
    df['postcode_area'] = df[postcode_col].str.extract(r'([a-zA-Z ]*)\d*.*')  # i.e. 'CF'
    df['postcode_area_latitude'] = df.groupby('postcode_area')['latitude'].transform('mean')
    df['postcode_area_longitude'] = df.groupby('postcode_area')['longitude'].transform('mean')

    df['postcode_district'] = df[postcode_col].str.split().str[0]  # i.e. 'CF14'
    df['postcode_district_latitude'] = df.groupby('postcode_district')['latitude'].transform('mean')
    df['postcode_district_longitude'] = df.groupby('postcode_district')['longitude'].transform('mean')

    df['postcode_sector'] = df[postcode_col].str[:-2]  # i.e. 'CF14 9'
    df['postcode_sector_latitude'] = df.groupby('postcode_sector')['latitude'].transform('mean')
    df['postcode_sector_longitude'] = df.groupby('postcode_sector')['longitude'].transform('mean')

    return df


def get_property_type(df: pd.DataFrame) -> pd.DataFrame:
    """Extract property type from the 'paon' and 'saon' columns. wonder what 'paon' and 'saon' even mean...

    Parameters
    ----------
    df : Input dataframe with a 'paon' and a 'saon' column to extract from.

    Returns
    -------
    pd.DataFrame
        Input dataframe with a new 'building_type' column.
    """
    rules = [df['paon'].str.contains('BARN', na=False),
             df['paon'].str.contains('FARM', na=False),
             df['paon'].str.contains('LAND AT', na=False),
             df['paon'].str.contains('BUNGALOW', na=False),
             df['paon'].str.contains('HOTEL', na=False),
             df['paon'].str.contains(' ARMS', na=False),
             df['saon'].str.contains('FLAT', na=False)]
    values = ['Farm', 'Farm', 'Land only', 'Bungalow', 'Hotel', 'Pub', 'Flat']

    df['building_type'] = np.select(rules, values, default='House')  # assume all else is residences

    return df


def get_supermarket_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Read in and utilise the supermarket data from geolityx in some kind of nonspecific but deffo impressive way
    (trust me yeah). Quite possibly the ugliest function I've written in a while but ack well it does its thing I
    guess...

    Parameters
    ----------
    df : Property data to be joined.

    Returns
    -------
    pd.DataFrame
        Input data but with supermarket info added on in a few ways. Don't ask what ways though. Can you tell I wrote
        the docstring before the function. Because I didn't. just lazy.
    """
    supermarket_df = pd.read_csv('data/geolityx_supermarkets_locations.csv')
    supermarket_df = supermarket_df[supermarket_df['county'].isin(['Gwent', 'Powys'])]

    supermarket_df['postcode_area'] = supermarket_df['postcode'].str.extract(r'([a-zA-Z ]*)\d*.*')  # i.e. 'CF'
    supermarket_df['postcode_district'] = supermarket_df['postcode'].str.split().str[0]  # i.e. 'CF14'
    supermarket_df['postcode_sector'] = supermarket_df['postcode'].str[:-2]  # i.e. 'CF14 9'

    supermarket_df['supermarkets_in_area'] = (supermarket_df
                                              .groupby('postcode_area')['id']
                                              .transform('count')
                                              .fillna(0)
                                              .astype(int))
    supermarket_df['supermarkets_in_district'] = (supermarket_df
                                                  .groupby('postcode_district')['id']
                                                  .transform('count')
                                                  .fillna(0)
                                                  .astype(int))
    supermarket_df['supermarkets_in_sector'] = (supermarket_df
                                                .groupby('postcode_sector')['id']
                                                .transform('count')
                                                .fillna(0)
                                                .astype(int))

    dist_df = cdist(df[['latitude', 'longitude']], supermarket_df[['lat_wgs', 'long_wgs']], metric='euclidean')
    dist_df = pd.DataFrame(dist_df, index=df['property_id'], columns=supermarket_df['fascia'])
    closest_dist = pd.DataFrame(dist_df.min(axis=1)).reset_index().drop_duplicates()  # distance to closest
    closest_dist.columns = ['property_id', 'distance_to_closest_supermarket']
    closest_store = pd.DataFrame(dist_df.idxmin(axis=1)).reset_index().drop_duplicates()  # name of closest
    closest_store.columns = ['property_id', 'closest_store']
    stores_in_radius = dist_df < 0.1  # defines a radius to check for stores in - no idea how big in km terms
    stores_in_radius = pd.DataFrame(stores_in_radius.sum(axis=1)).reset_index().drop_duplicates()
    stores_in_radius.columns = ['property_id', 'number_stores_in_radius']

    counts_list = [df,
                   supermarket_df[['postcode_area', 'supermarkets_in_area']].drop_duplicates(),
                   supermarket_df[['postcode_district', 'supermarkets_in_district']].drop_duplicates(),
                   supermarket_df[['postcode_sector', 'supermarkets_in_sector']].drop_duplicates(),
                   closest_dist,
                   closest_store,
                   stores_in_radius]

    df = reduce(lambda left, right: pd.merge(left, right, how='left'), counts_list)

    return df


def add_basic_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the raw columns needed to the data, set dtype where needed.

    Parameters
    ----------
    df : Input property data, received after merge.

    Returns
    -------
    pd.DataFrame
        Data but with the basic columns added on. Can you tell I didn't know what the basic columns would be yet when I
        wrote this?
    """
    df[['postcode', 'paon', 'street']] = df[['postcode', 'paon', 'street']].fillna('')  # we hash these so need no null
    df = create_col_hash(df=df, cols_to_hash=(df.postcode + df.paon + df.street))

    df['deed_date'] = pd.to_datetime(df['deed_date'], format='%Y-%m-%d')
    df['year'] = df['deed_date'].dt.to_period('Y')  # to join interpolated data on later

    df = get_postcode_columns(df)
    df = get_property_type(df)

    return df


def generate_shape_info(df: pd.DataFrame) -> None:
    """Generate the shape info dataframe to be displayed in the dashboard

    Parameters
    ----------
    df : Complete engineered dataframe.
    """
    results = pd.DataFrame(df.dtypes).reset_index()
    origins = pd.read_csv('data/metadata/file_of_origin.csv')

    results['Uniques'] = [len(df[col].unique()) for col in df.columns]
    results['NULLs'] = [df[col].isnull().sum(axis=0) for col in df.columns]
    results['prop NULLS'] = [round(df[col].isnull().mean(axis=0), 2) for col in df.columns]
    results['Sample Values'] = [', '.join(df[df[col].notnull()][col].unique()[:2].astype(str)) for col in df.columns]

    results.columns = ['Variable Name', 'Data Type', 'Uniques', 'NULLs', 'proportion NULL', 'Sample Values']
    results['Data Type'] = results['Data Type'].astype(str)
    results['Sample Values'] = results['Sample Values'].str[:70]
    results = results.merge(origins)

    results.to_csv('data/metadata/variable_info.csv', index=False)


def engineering_main() -> None:
    """Run the engineering pipeline end to end, saving output to csv (how do I typehint a csv output?).

    Notes
    -----
    We clearly don't get price data for anywhere near the amount of properties we have postcodes for. It remains to be
    seen what impact this might have on the analysis.
    P.S. I've no idea what the comments about the three p's are, chalk them up to heat stroke I guess it hit 30 degrees
    today.
    """
    postcodes = pd.read_csv('data/monmouthshire_postcodes.csv')  # the first 'p'
    postcodes = clean_column_names(df=postcodes)

    prices = pd.read_csv('data/monmouthshire_prices.csv')  # the second 'p'

    full_df = prices.merge(postcodes, on='postcode', how='left')
    full_df = add_basic_columns(full_df)

    interpolated_yearly_value = interpolate_price_paid(full_df)

    true_years = full_df[['year', 'property_id']]
    true_years['true_price'] = True
    full_df.drop(['price_paid', 'year', 'unique_id', 'deed_date'], inplace=True, axis=1)
    full_df = full_df.drop_duplicates(subset='property_id', keep='last')

    full_df = full_df.merge(interpolated_yearly_value, on=['property_id'], how='outer')
    full_df = full_df.merge(true_years, on=['year', 'property_id'], how='left')
    full_df['true_price'] = full_df['true_price'].fillna(False)

    full_df['in_use'] = convert_column_to_boolean(full_df['in_use'], 'Yes')
    full_df['new_build'] = convert_column_to_boolean(full_df['new_build'], 'Y')
    full_df['introduced'] = pd.to_datetime(full_df['introduced'], format='%Y-%m-%d')
    full_df['last_updated'] = pd.to_datetime(full_df['last_updated'], format='%Y-%m-%d')
    full_df['terminated'] = pd.to_datetime(full_df['terminated'], format='%Y-%m-%d')

    full_df = get_supermarket_stats(full_df)

    full_df.to_csv('data/monmouthshire_properties.csv', index=False)  # the third 'p'
    generate_shape_info(full_df)


if __name__ == '__main__':
    engineering_main()
