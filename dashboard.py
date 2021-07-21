"""
Visualisation dashboard, to play with the data. Will gradually update this as new possibilities are possible, but prior.
for obvious reasons...

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

    dcc.Checklist(id='properties_to_plot',
                  options=[{'label': 'has price data available', 'value': 1},
                           {'label': 'no price data available', 'value': 0}],
                  value=[1],
                  labelStyle={'display': 'block'}),

    html.H2('property locations across Monmouthshire'),
    dcc.Graph(id='properties_scatter', figure={}),
    html.Br(),
])


@app.callback(
    Output(component_id='properties_scatter', component_property='figure'),
    [Input(component_id='properties_to_plot', component_property='value')]
)
def update_scatter_plot(properties_to_plot: List[int]) -> px.scatter:
    """Choose which data to plot on the scatter axis.

    Parameters
    ----------
    properties_to_plot : List of desired values from the 'has_price_data' column of the property dataset.

    Returns
    -------
    px.scatter
        Plotly graph containing the desired points in space
    """
    df_to_plot = df[df['has_price_data'].isin(properties_to_plot)]

    fig = px.scatter(
        data_frame=df_to_plot,
        x='longitude',
        y='latitude',
        color='has_price_data',
        title='location of properties with available data in monmouthshire'
    )

    return fig


if __name__ == '__main__':
    app.run_server()
