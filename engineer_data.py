"""
Joining datasets together to form a single csv. Doing additional feature engineering where necessary to prep for the
analysis.
"""
import re
import pandas as pd
from typing import Dict


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

    full_df = prices.merge(postcodes, on='postcode', how='outer')
    full_df.to_csv('data/monmouthshire_properties.csv', index=False)  # the third 'p'


if __name__ == '__main__':
    engineering_main()
