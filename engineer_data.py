"""
Joining datasets together to form a single csv. Doing additional feature engineering where necessary to prep for the
analysis.
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

    df = df.groupby('property_id').resample('Y').mean()
    df['price_paid'] = df['price_paid'].interpolate()

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
    df : Input dataframe to have its column headers cleaned.

    Returns
    -------
    pd.DataFrame
        Input dataframe but with column headers cleaned.
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
    df['has_price_data'] = np.where(df['price_paid'].notnull(), 1, 0)

    df[['postcode', 'paon', 'street']] = df[['postcode', 'paon', 'street']].fillna('')  # we hash these so need no null
    df = create_col_hash(df=df, cols_to_hash=(df.postcode + df.paon + df.street))

    df['deed_date'] = pd.to_datetime(df['deed_date'], format='%Y-%m-%d')
    df['year'] = df['deed_date'].dt.to_period('Y')  # to join on later

    return df


def engineering_main() -> None:
    """Run the engineering pipeline end to end, saving output to csv (how do I typehint a csv output?).

    Notes
    -----
    We clearly don't get price data for anywhere near the amount of properties we have postcodes for. It remains to be
    seen what impact this might have on the analysis.
    P.S. I've no idea what the comments about the three p's are, chalk them up to heat stroke I guess.
    """
    postcodes = pd.read_csv('data/monmouthshire_postcodes.csv')  # the first 'p'
    postcodes = clean_column_names(df=postcodes)

    prices = pd.read_csv('data/monmouthshire_prices.csv')  # the second 'p'

    full_df = prices.merge(postcodes, on='postcode', how='left')
    full_df = add_basic_columns(full_df)

    interpolated_yearly_value = interpolate_price_paid(full_df)
    # forecast data forwards and backwards such that interpolated_yearly_value runs from 1995 - 2021 for all properties
    full_df = full_df.merge(interpolated_yearly_value, on=['year', 'property_id'], how='outer')

    full_df.to_csv('data/monmouthshire_properties.csv', index=False)  # the third 'p'


if __name__ == '__main__':
    engineering_main()
