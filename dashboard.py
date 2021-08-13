"""
Visualisation dashboard, to play with the data. Will gradually update this as new possibilities are possible, but prior.
for obvious reasons...

TODO:
    - add some basic data exploration graphs i.e.:
        - shape data needs updating
        - column data needs updating - percent nulls and metadata columns
        - Null count bar charts?
        - group ranges as violin plots?
        - value counts as divided bars for certain columns?
    - consider further analysis that might be chill
    - build as a multi page app with different themes and shit <- this is the big next step I think
"""
import pandas as pd
from typing import List, Tuple, Dict
import dash
import dash_table
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Output, Input
import plotly.express as px

df = pd.read_csv('data/monmouthshire_properties.csv')


app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Monmouthshire Properties Analysis", style={'text-align': 'center'}),

    html.Div([
        html.H2('0. File Shape Data and Variable Information', style={'display': 'flex',
                                                                      'justifyContent': 'center',
                                                                      'align-items': 'center'}),

        html.Div([
            dcc.Dropdown(id='choose_file',
                         options=[{'label': 'monmouthshire_postcodes', 'value': 'monmouthshire_postcodes'},
                                  {'label': 'monmouthshire_prices', 'value': 'monmouthshire_prices'},
                                  {'label': 'geolytix_supermarkets_locations', 'value': 'geolytix_supermarkets_locations'},
                                  {'label': 'constructed by Johnno', 'value': 'constructed by Johnno'},
                                  {'label': 'Complete', 'value': 'Complete'}],
                         value='Complete',
                         multi=False)
        ], style={'width': '20%', 'justifyContent': 'center', 'align-items': 'center'}),

        html.Div([
            dash_table.DataTable(id='file_shape',
                                 fixed_rows={'headers': True},
                                 style_table={'height': '300px', 'overflowY': 'auto'},
                                 style_cell={'minWidth': 100, 'maxWidth': 1000},
                                 fill_width=False
                                 )
        ], style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'})
    ]),

    html.Div([
        html.H3('0.1 Complete Dataset Used Column Info For Selected Source File'),

        html.Div([
                dcc.Dropdown(id='sort_by',
                             options=[{'label': 'Variable Name', 'value': 'Variable Name'},
                                      {'label': 'Data Type', 'value': 'Data Type'},
                                      {'label': 'Unique Values', 'value': 'Unique Values'},
                                      {'label': 'NULL Values', 'value': 'NULL Values'},
                                      {'label': 'Source File', 'value': 'Source File'}],
                             value=['Variable Name'],
                             multi=True)
            ], style={'width': '50%', 'justifyContent': 'center', 'align-items': 'center'}),

        html.Div([
            dash_table.DataTable(id='variable_info',
                                 fixed_rows={'headers': True},
                                 style_table={'height': '300px', 'overflowY': 'auto'},
                                 style_cell={'minWidth': 100}
                                 )
        ])
    ]),

    html.Div([
        html.H2('2. Locations of Sold Properties', style={'display': 'flex',
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
])


@app.callback(
    [Output(component_id='file_shape', component_property='data'),
     Output(component_id='file_shape', component_property='columns')],
    Input(component_id='choose_file', component_property='value')
)
def get_file_shape_table(chosen_file: str) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Choose which file to display the contents of in the shape table.

    Parameters
    ----------
    chosen_file : Name of file to display shape data for

    Returns
    -------
    Tuple[Dict[str, str], List[Dict[str, str]]]
        Required outputs to fill the column headers and data content for the Dash table
    """
    shape_data = pd.read_csv('data/metadata/property_data_shape.csv')
    shape_data = shape_data[shape_data['File Name'] == chosen_file]
    shape_data.drop('File Name', inplace=True, axis=1)

    return shape_data.to_dict(orient='records'), [{'id': col, 'name': col} for col in shape_data.columns]


@app.callback(
    [Output(component_id='variable_info', component_property='data'),
     Output(component_id='variable_info', component_property='columns')],
    [Input(component_id='sort_by', component_property='value'),
     Input(component_id='choose_file', component_property='value')]
)
def get_variable_info_table(
    sort_by: str,
    chosen_file: str,
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Generate the contents of the Dash data table displaying the shape info on the dataset.

    Parameters
    ----------
    sort_by : Column name to sort the data on.
    chosen_file : Chosen File to display data for.

    Returns
    -------
    Tuple[Dict[str, str], List[Dict[str, str]]]
        Required outputs to fill the column headers and data content for the Dash table
    """
    results = pd.DataFrame(df.dtypes).reset_index()
    origins = pd.read_csv('data/metadata/file_of_origin.csv')

    results['Unique Values'] = [len(df[col].unique()) for col in df.columns]
    results['NULL Values'] = [df[col].isnull().sum() for col in df.columns]
    results['Sample Values'] = [', '.join(df[df[col].notnull()][col].unique()[:2].astype(str)) for col in df.columns]

    results.columns = ['Variable Name', 'Data Type', 'Unique Values', 'NULL Values', 'Sample Values']
    results['Data Type'] = results['Data Type'].astype(str)
    results['Sample Values'] = results['Sample Values'].str[:70]
    results = results.merge(origins)

    if chosen_file != 'Complete':
        results = results[results['Source File'] == chosen_file]  # reduce the visible variables

    results.sort_values(by=sort_by, inplace=True)

    return results.to_dict(orient='records'), [{'id': col, 'name': col} for col in results.columns]


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
    )

    return fig


if __name__ == '__main__':
    app.run_server()
