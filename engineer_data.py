"""
Joining datasets together to form a single csv. Doing additional feature engineering where necessary to prep for the
analysis.
these include:
    - joining price and location data to form a single dataset.
    - creating a unique property ID based on postcode, house number and road name.
    - interpolating the probable value of the property in years between sales.
    - *extracting a bunch of extra info from some columns*

*text* = not yet but will do soon lol.

TODO: - fix the interpolation join so it still gets all the extra info
      - add extra data such as distance to nearest services / from centroids / etc...
"""
import re
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Tuple


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


def create_col_hash(
    df: pd.DataFrame,
    cols_to_hash: Tuple[pd.Series, ...],
) -> pd.DataFrame:
    """Create 16 character alphanumeric hash function using specified columns.

    Parameters
    ----------
    df : Input dataframe.
    cols_to_hash : Tuple of the columns you wish to hash, which are supplied as a sum of pandas series for some reason.

    Returns
    -------
    pd.DataFrame
        Dataframe with extra 'bout_id' column.
    """
    df['property_id'] = (
        cols_to_hash
        .apply(lambda x: hashlib.md5(x.encode('utf-8')).hexdigest())
    )

    return df


def replace_multiple(
    text: str,
    replacements: Dict[str, str],
    simultaneous: bool = True,
) -> str:
    """Replaces multiple norty characters in a singe string.

    Notes
    -----
    As dictionaries have no order in python, the user must choose whether to simultaneously replace in a single pass,
    using regex, or run chained replacements, which could potentially affect the output. I doubt I'll use this feature
    but it was cool to add in.

    Parameters
    ----------
    text : Input text to be replaced upon.
    replacements : dictionary of each current - replacement pair.
    simultaneous : set True to replace everything in a single pass, or False to chain replacements in random order.

    Returns
    -------
    str
        Text but with the requested replacements made.
    """
    if simultaneous:
        replacements = dict((re.escape(k), v) for k, v in replacements.items())
        pattern = re.compile("|".join(replacements.keys()))
        text = pattern.sub(lambda m: replacements[re.escape(m.group(0))], text)

    else:
        for i, j in replacements.items():
            text = text.replace(i, j)

    return text


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column headers of capitals, punctuation, etc...

    Parameters
    ----------
    df : Input dataframe hoping to have its column headers cleaned.

    Returns
    -------
    pd.DataFrame
        Input dataframe but with column headers cleaned and subsequently, a satisfied smile.
    """
    replacements = {
        ' ': '_',
        '?': '',
    }
    df.columns = [replace_multiple(text=col.lower(),
                                   replacements=replacements,
                                   simultaneous=True)
                  for col in df.columns]

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
    df['postcode_area_latitude'] = df.groupby('postcode_area')['latitude'].transform('sum')
    df['postcode_area_longitude'] = df.groupby('postcode_area')['longitude'].transform('sum')

    df['postcode_district'] = df[postcode_col].str.split().str[0]  # i.e. 'CF14'
    df['postcode_district_latitude'] = df.groupby('postcode_district')['latitude'].transform('sum')
    df['postcode_district_longitude'] = df.groupby('postcode_district')['longitude'].transform('sum')

    df['postcode_sector'] = df[postcode_col].str[:-2]  # i.e. 'CF14 9'
    df['postcode_sector_latitude'] = df.groupby('postcode_sector')['latitude'].transform('sum')
    df['postcode_sector_longitude'] = df.groupby('postcode_sector')['longitude'].transform('sum')

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
    true_years['true_price'] = 1
    full_df.drop(['price_paid', 'year', 'unique_id', 'deed_date'], inplace=True, axis=1)
    full_df = full_df.drop_duplicates(subset='property_id', keep='last')

    full_df = full_df.merge(interpolated_yearly_value, on=['property_id'], how='outer')
    full_df = full_df.merge(true_years, on=['year', 'property_id'], how='left')
    full_df['true_price'] = full_df['true_price'].fillna(0)

    full_df.to_csv('data/monmouthshire_properties.csv', index=False)  # the third 'p'


if __name__ == '__main__':
    engineering_main()
