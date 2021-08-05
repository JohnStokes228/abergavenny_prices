"""
Visualisation dashboard, to play with the data. Will gradually update this as new possibilities are possible, but prior.
for obvious reasons...

TODO:
    - add some basic data exploration graphs i.e.:
        - Null count heatmap? <- filter by region prehaps to keep it legible?
        - group ranges as violin plots?
        - number of unique values in some columns?
        - value counts as divided bars for certain columns?
    - consider further analysis that might be chill
    - build as a multi page app with different themes and shit <- this is the big next step I think
"""
import pandas as pd
from typing import List
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input
import plotly.express as px


df = pd.read_csv('data/monmouthshire_properties.csv')

app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Monmouthshire Properties Analysis", style={'text-align': 'center'}),

    html.Div([
        html.H2('1. Maps of Raw Data', style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'}),

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

        dcc.Markdown("""It looks like the town label is a bit sus here, especially for Crickhowell which seems to have 
        most of its properties marked as belonging to Abergavenny. It looks like Caldicot may only be half covered by 
        the Monmouthshire data we have too. Finally, we appear to be missing towns like Rhaglan (sick castle btw) 
        entirely.
        """)
    ])
])


@app.callback(
    Output(component_id='properties_scatter', component_property='figure'),
    [Input(component_id='properties_to_plot', component_property='value'),
     Input(component_id='date_range_for_price_data', component_property='value')]
)
def update_scatter_plot(
    properties_to_plot: List[int],
    date_range: List[int],
) -> px.scatter:
    """Choose which data to plot on the scatter axis.

    Parameters
    ----------
    properties_to_plot : List of desired values from the 'town' column of the property dataset.
    date_range : List of start and end date of desired date range

    Returns
    -------
    px.scatter
        Plotly graph containing the desired points in space
    """
    df_to_plot = df[df['town'].isin(properties_to_plot)]
    df_to_plot = df_to_plot[(df_to_plot['year'] >= date_range[0]) & (df_to_plot['year'] <= date_range[1])]
    df_to_plot = df_to_plot[df_to_plot['true_price'] == 1]

    fig = px.scatter(
        data_frame=df_to_plot,
        x='longitude',
        y='latitude',
        color='town',
        title='Location of properties with price data available in Monmouthshire for a given time period.'
    )

    return fig


if __name__ == '__main__':
    app.run_server()
