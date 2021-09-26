"""
Analysis dashboard, as youd expect from a file with the name of 'analysis_dashboard'. Will contain all raw
analysis plots etc... but no weirdo models just yet.

TODO: - add something amazing
      - bask in awe at the output from the prior step
      - legit though maybe a choropleth based on our constructed polygons or something? could be norty just sayin'
"""
import pandas as pd
from typing import List
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input
import plotly.express as px
DF = pd.read_csv('data/monmouthshire_properties.csv')


app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div([
        html.H2('1.1 Locations of Sold Properties', style={'display': 'flex',
                                                           'justifyContent': 'center',
                                                           'align-items': 'center'}),

        html.Div([
            dcc.Checklist(id='properties_to_plot',
                          options=[{'label': 'Coleford', 'value': 'COLEFORD'},
                                   {'label': 'Newport', 'value': 'NEWPORT'},
                                   {'label': 'Usk', 'value': 'USK'},
                                   {'label': 'Chepstow', 'value': 'CHEPSTOW'},
                                   {'label': 'Monmouth', 'value': 'MONMOUTH'},
                                   {'label': 'Caldicot', 'value': 'CALDICOT'},
                                   {'label': 'Abergavenny', 'value': 'ABERGAVENNY'},
                                   {'label': 'Crickhowell', 'value': 'CRICKHOWELL'}],
                          value=['ABERGAVENNY'],
                          style={'display': 'inline-block'},
                          labelStyle={'display': 'block'}),

            dcc.Graph(id='properties_scatter',
                      figure={},
                      style={'display': 'inline-block', 'width': '85%'})

        ], style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'}),

        dcc.RangeSlider(id='date_range_for_price_data',
                        min=1995,
                        max=2021,
                        step=1,
                        value=[2010, 2020],
                        marks={1995: {'label': '1995'},
                               2000: {'label': '2000'},
                               2005: {'label': '2005'},
                               2010: {'label': '2010'},
                               2015: {'label': '2015'},
                               2020: {'label': '2020'}}),

    ]),

    html.Div([
        html.H2('1.2 Price vs Numeric Variables', style={'display': 'flex',
                                                         'justifyContent': 'center',
                                                         'align-items': 'center'}),

        html.Div([
            dcc.Dropdown(id='variables_dropdown',
                         options=[{'label': 'new_build', 'value': 'new_build'},
                                  {'label': 'altitude', 'value': 'altitude'},
                                  {'label': 'supermarkets_in_area', 'value': 'supermarkets_in_area'},
                                  {'label': 'supermarkets_in_sector', 'value': 'supermarkets_in_sector'},
                                  {'label': 'supermarkets_in_district', 'value': 'supermarkets_in_district'},
                                  {'label': 'distance_to_closest_supermarket', 'value': 'distance_to_closest_supermarket'},
                                  {'label': 'number_stores_in_radius', 'value': 'number_stores_in_radius'}],
                         value='altitude',
                         multi=False)
            ], style={'width': '20%', 'display': 'inline-block', 'justifyContent': 'center', 'align-items': 'center'}),

        html.Div([
            dcc.Graph(id='cost_scatter',
                      figure={})
        ])
    ]),

    html.Div([
        html.H2('1.3 Price vs Categorical Variables', style={'display': 'flex',
                                                             'justifyContent': 'center',
                                                             'align-items': 'center'}),

        dcc.Dropdown(id='variables_dropdown_2',
                     options=[{'label': 'property_type', 'value': 'property_type'},
                              {'label': 'estate_type', 'value': 'estate_type'},
                              {'label': 'building_type', 'value': 'building_type'},
                              {'label': 'town', 'value': 'town'},
                              {'label': 'district', 'value': 'district'},
                              {'label': 'transaction_category', 'value': 'transaction_category'},
                              {'label': 'parish', 'value': 'parish'},
                              {'label': 'postcode_area', 'value': 'postcode_area'},
                              {'label': 'postcode_district', 'value': 'postcode_district'},
                              {'label': 'postcode_sector', 'value': 'postcode_sector'},
                              {'label': 'closest_store', 'value': 'closest_store'},
                              {'label': 'ward', 'value': 'ward'}],
                     value='building_type',
                     multi=False),

        html.Div([
            dcc.Graph(id='cost_violins',
                      figure={})
        ])
    ]),
])


def get_requested_df(
    properties_to_plot: List[str],
    date_range: List[int],
) -> pd.DataFrame:
    """Get the requested data from the various pushy buttons bits.

    Parameters
    ----------
    properties_to_plot : List of desired values from the 'town' column of the property dataset.
    date_range : List of start and end date of desired date range.

    Returns
    -------
    pd.DataFrame
        Requested data pls.
    """
    requested_df = DF[DF['town'].isin(properties_to_plot)]
    requested_df = requested_df[(requested_df['year'] >= date_range[0]) & (requested_df['year'] <= date_range[1])]

    return requested_df


@app.callback(
    Output(component_id='properties_scatter', component_property='figure'),
    [Input(component_id='properties_to_plot', component_property='value'),
     Input(component_id='date_range_for_price_data', component_property='value')]
)
def update_scatter_plot(
    properties_to_plot: List[str],
    date_range: List[int],
) -> px.scatter:
    """Choose which data to plot on the scatter axis.

    Parameters
    ----------
    properties_to_plot : List of desired values from the 'town' column of the property dataset.
    date_range : List of start and end date of desired date range.

    Returns
    -------
    px.scatter
        Plotly graph containing the desired points in space
    """
    df_to_plot = get_requested_df(properties_to_plot, date_range)
    df_to_plot = df_to_plot[df_to_plot['true_price'] == 1]

    fig = px.scatter(
        data_frame=df_to_plot,
        x='longitude',
        y='latitude',
        color='town',
    )

    return fig


@app.callback(
    Output(component_id='cost_scatter', component_property='figure'),
    [Input(component_id='date_range_for_price_data', component_property='value'),
     Input(component_id='properties_to_plot', component_property='value'),
     Input(component_id='variables_dropdown', component_property='value')]
)
def update_cost_scatter(
    date_range: List[int],
    properties_to_plot: List[str],
    variable_to_plot: str,
) -> px.scatter:
    """Update contents of scatter plot which plots some scattered points for cost of property over time vs some other
    variable chosen by a dropdown menu.

    Notes
    -----
    Currently this includes interpolated prices, might be worth ditching these or making it possible to turn them on
    or off prehaps?

    Parameters
    ----------
    date_range : List of start and end date of desired date range.
    properties_to_plot : List of towns to include in the graph.
    variable_to_plot : Variable that will become the x axis for the resultant scatter plot.

    Returns
    -------
    px.scatter
        Plotly express scatter plot object displaying the analysis for the chosen period / variables
    """
    df_to_plot = get_requested_df(properties_to_plot, date_range)

    fig = px.scatter(data_frame=df_to_plot,
                     x=variable_to_plot,
                     y='interpolated_price',
                     trendline='lowess')

    return fig


@app.callback(
    Output(component_id='cost_violins', component_property='figure'),
    [Input(component_id='date_range_for_price_data', component_property='value'),
     Input(component_id='properties_to_plot', component_property='value'),
     Input(component_id='variables_dropdown_2', component_property='value')]
)
def update_violin_plots(
    date_range: List[int],
    properties_to_plot: List[str],
    variable_to_plot: str,
) -> px.violin:
    """Update contents of violin plots for categorical data

    Notes
    -----
    Currently this includes interpolated prices, might be worth ditching these or making it possible to turn them on
    or off prehaps?

    Parameters
    ----------
    date_range : List of start and end date of desired date range.
    properties_to_plot : List of towns to include in the graph.
    variable_to_plot : Variable that will become the x axis for the resultant violin plot.

    Returns
    -------
    px.violin
        Plotly express violin plot object displaying the analysis for the chosen period / variables
    """
    df_to_plot = get_requested_df(properties_to_plot, date_range)

    fig = px.violin(data_frame=df_to_plot,
                    x=variable_to_plot,
                    y='interpolated_price')

    return fig


if __name__ == '__main__':
    app.run_server()
