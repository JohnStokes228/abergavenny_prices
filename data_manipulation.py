"""
just to clean up engineer_data file which currently has a lot of code which probably doesnt belong there. Prehaps we
should think again about building that generic John functions package just for ease of import for some things...?

"""
import pandas as pd
import numpy as np
import re
import hashlib
from typing import Tuple, Dict, Any


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


def convert_column_to_boolean(
    column: pd.Series,
    true_value: Any,
) -> pd.Series:
    """Convert some input column into bool dtype.

    Parameters
    ----------
    column : Column to become bool.
    true_value : which value will map to True, all else maps to False.

    Returns
    -------
    pd.Series
        Series of dtype bool.
    """
    return np.where(column == true_value, True, False)
