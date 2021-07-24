"""
Visualisation dashboard, to play with the data. Will gradually update this as new possibilities are possible, but prior.
for obvious reasons...

TODO:
    - add some basic data exploration graphs i.e. null values, etc...
    - add a year slider to properties map
    - consider further analysis that might be chill
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
                          labelStyle={'display': 'block'},
                          ),

            dcc.Graph(id='properties_scatter',
                      figure={},
                      style={'display': 'inline-block', 'width': '85%'})
        ], style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'}),

    dcc.Markdown("""It looks like the town label is a bit sus here, especially for Crickhowell which seems to have most
    of its properties marked as belonging to Abergavenny. It looks like Caldicot may only be half covered by the
    Monmouthshire data we have too. Finally, we appear to be missing towns like Rhaglan (sick castle btw) entirely.
    """)
    ])
])


@app.callback(
    Output(component_id='properties_scatter', component_property='figure'),
    [Input(component_id='properties_to_plot', component_property='value')]
)
def update_scatter_plot(properties_to_plot: List[int]) -> px.scatter:
    """Choose which data to plot on the scatter axis.

    Parameters
    ----------
    properties_to_plot : List of desired values from the 'town' column of the property dataset.

    Returns
    -------
    px.scatter
        Plotly graph containing the desired points in space
    """
    df_to_plot = df[df['town'].isin(properties_to_plot)]

    fig = px.scatter(
        data_frame=df_to_plot,
        x='longitude',
        y='latitude',
        color='town',
        title='Location of properties with price data available in Monmouthshire'
    )

    return fig


if __name__ == '__main__':
    app.run_server()
