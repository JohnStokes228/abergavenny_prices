"""
Visualisation dashboard, to play with the data. Will gradually update this as new possibilities are possible, but prior.
for obvious reasons...

TODO:
    - add some basic data exploration graphs i.e.:
        - column ranges as violin plots?
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

DF = pd.read_csv('data/monmouthshire_properties.csv')
VARIABLES = pd.read_csv('data/metadata/variable_info.csv')
SHAPE = pd.read_csv('data/metadata/property_data_shape.csv')


app = dash.Dash(__name__)
app.layout = html.Div([
    html.H1("Monmouthshire Properties Analysis", style={'text-align': 'center'}),

    html.H1("0 - Validation", style={'text-align': 'center'}),

    html.Div([
        html.H2("Select File to Validate: ", style={'display': 'inline-block'}),


        html.Div([
            dcc.Dropdown(id='choose_file',
                         options=[{'label': 'monmouthshire_postcodes', 'value': 'monmouthshire_postcodes'},
                                  {'label': 'monmouthshire_prices', 'value': 'monmouthshire_prices'},
                                  {'label': 'geolytix_supermarkets_locations', 'value': 'geolytix_supermarkets_locations'},
                                  {'label': 'constructed by Johnno', 'value': 'constructed by Johnno'},
                                  {'label': 'Complete', 'value': 'Complete'}],
                         value='Complete',
                         multi=False)
        ], style={'width': '20%', 'display': 'inline-block', 'justifyContent': 'center', 'align-items': 'center'}),
    ], style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'}),

    html.Div([
        html.H2('0.1 File Shape Info'),

        html.Div([
            dash_table.DataTable(id='file_shape',
                                 fixed_rows={'headers': True},
                                 style_table={'height': '300px', 'overflowY': 'auto'},
                                 style_cell={'minWidth': 100, 'maxWidth': 1000},
                                 fill_width=False
                                 )
        ], style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'}),
    ]),

    html.Div([
        html.H3('0.2 Column info for Selected File'),

        html.Div([
                dcc.Dropdown(id='sort_by',
                             options=[{'label': 'Variable Name', 'value': 'Variable Name'},
                                      {'label': 'Data Type', 'value': 'Data Type'},
                                      {'label': 'Uniques', 'value': 'Uniques'},
                                      {'label': 'NULLs', 'value': 'NULLs'},
                                      {'label': 'Source File', 'value': 'Source File'}],
                             value=['Variable Name'],
                             multi=True),
            ], style={'width': '50%', 'justifyContent': 'center', 'align-items': 'center'}),

        html.Div([
            dash_table.DataTable(id='variable_info',
                                 fixed_rows={'headers': True},
                                 style_table={'height': '300px', 'overflowY': 'auto'},
                                 style_cell={'minWidth': 100},
                                 )
        ], style={'display': 'flex', 'justifyContent': 'center', 'align-items': 'center'})
    ]),

    html.Div([
        html.H2('0.3 NULL Value Visualisations'),

        dcc.Graph(id='null_bars',
                  figure={},
                  style={'display': 'inline-block',
                         'width': '50%',
                         'height': '200%'}),

        dcc.Graph(id='null_heatmap',
                  figure={},
                  style={'display': 'inline-block',
                         'width': '40%',
                         'height': '200%'})
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
    shape_data = SHAPE[SHAPE['File Name'] == chosen_file]
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
    """Reduce the contents of the Dash data table displaying the shape info on the dataset.

    Parameters
    ----------
    sort_by : Column name to sort the data on.
    chosen_file : Chosen File to display data for.

    Returns
    -------
    Tuple[Dict[str, str], List[Dict[str, str]]]
        Required outputs to fill the column headers and data content for the Dash table
    """
    if chosen_file != 'Complete':
        results = VARIABLES[VARIABLES['Source File'] == chosen_file].copy()  # reduce the visible variables
    else:
        results = VARIABLES

    results.sort_values(by=sort_by, inplace=True)

    return results.to_dict(orient='records'), [{'id': col, 'name': col} for col in results.columns]


@app.callback(
    Output(component_id='null_bars', component_property='figure'),
    Input(component_id='choose_file', component_property='value')
)
def update_null_bar_chart(chosen_file: str) -> px.bar:
    """Display NULL values counts across selected columns as a bar chart.

    Notes
    -----
    Usually you'd use like a heatmap or something for this purpose but I think 120k rows is just too many for that to
    really be legible unfortunately. In lieu of there being an obvious way for the user to filter that down I'm instead
    for now opting for the prehaps rather odd bar chart you see below.

    Parameters
    ----------
    chosen_file : The file name to display info for, or the value 'Complete' if the whole dataset is desired.

    Returns
    -------
    px.bar
        Bar chart displaying number of rows with each number of NULLs in.
    """
    if chosen_file != 'Complete':
        variables = VARIABLES[VARIABLES['Source File'] == chosen_file]['Variable Name'].tolist()
    else:
        variables = VARIABLES['Variable Name'].tolist()

    df_to_plot = pd.DataFrame(
        DF[variables]
        .isnull()
        .sum(axis=1)
        .round(2)
        .value_counts()
    ).reset_index().sort_values(by='index')  # get number of NULL columns per row
    df_to_plot.columns = ['Number of NULL Cells', 'Row Count']

    fig = px.bar(df_to_plot,
                 x='Number of NULL Cells',
                 y='Row Count',
                 title='0.3.1 Number of NULLs Per Row for Selected File Bar Chart')

    return fig


@app.callback(
    Output(component_id='null_heatmap', component_property='figure'),
    Input(component_id='choose_file', component_property='value')
)
def update_null_heatmap(chosen_file: str) -> px.imshow:
    """Update NULL value heatmap to display only the columns from the chosen file.

    Parameters
    ----------
    chosen_file : Name of file to display info for.

    Returns
    -------
    px.density_heatmap
        Heatmap of NULL locations in given file.
    """
    if chosen_file != 'Complete':
        variables = VARIABLES[VARIABLES['Source File'] == chosen_file]['Variable Name'].tolist()
    else:
        variables = VARIABLES['Variable Name'].tolist()

    df_to_plot = DF[variables].isnull()
    df_to_plot = df_to_plot.loc[(df_to_plot != 0).any(1), (df_to_plot != 0).any(0)]

    fig = px.imshow(df_to_plot,
                    labels=dict(x="Column Names", y="Row IDs"),
                    title='0.3.2 Column NULL Map')

    return fig


if __name__ == '__main__':
    app.run_server(debug=False)
