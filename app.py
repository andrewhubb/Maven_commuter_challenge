#!/usr/bin/env python
# coding: utf-8

# In[2]:


import pandas as pd
import numpy as np
from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template
import dash_dangerously_set_inner_html
import plotly.express as px
import plotly.graph_objects as go
from dash_extensions.enrich import Trigger

from config import (
    services,
    service_colours,    
    dark_blue,
    dark_orange
)

from visual_functions import (
    create_title, 
    create_key_insights,
    create_kpi_cards,
    create_ridership_cards,
    create_granularity_dropdown, 
    create_services_dropdown,    
    create_service_line_chart,
    create_correlation_matrix,
    create_dual_axis_chart,
    create_recovery_bar_chart,
    create_recovery_heatmap,
    create_ridership_pie_chart,
    create_ridership_scatterplot,
    create_before_after_chart,
    create_daily_variability_boxplot,
    create_comparison_table,
    create_whats_next
)

from support_functions import (
    calculate_total_recovery, 
    create_thousand_dataframe,     
    resample_data, 
    find_free_port,
    create_metrics,
    prepare_comparison_table,
    create_kpis,    
)
import json
from io import StringIO # This is to solve the problem of future pandas versions removing the ability to directly pass a JSON string to read_json


# In[3]:


mta_data = pd.read_csv('./data/MTA_Daily_Ridership.csv',parse_dates=['Date'])


# In[4]:


mta_data = mta_data.rename(columns={
            'Subways: Total Estimated Ridership' : 'Subways',
            'Subways: % of Comparable Pre-Pandemic Day' : 'Subways: % of Pre-Pandemic',
            'Buses: Total Estimated Ridership' : 'Buses',
            'Buses: % of Comparable Pre-Pandemic Day' : 'Buses: % of Pre-Pandemic',
            'LIRR: Total Estimated Ridership' : 'LIRR',
            'LIRR: % of Comparable Pre-Pandemic Day' : 'LIRR: % of Pre-Pandemic',
            'Metro-North: Total Estimated Ridership' : 'Metro-North',
            'Metro-North: % of Comparable Pre-Pandemic Day' : 'Metro-North: % of Pre-Pandemic',
            'Access-A-Ride: Total Scheduled Trips' : 'Access-A-Ride',
            'Access-A-Ride: % of Comparable Pre-Pandemic Day' : 'Access-A-Ride: % of Pre-Pandemic',
            'Bridges and Tunnels: Total Traffic' : 'Bridges and Tunnels',
            'Bridges and Tunnels: % of Comparable Pre-Pandemic Day' : 'Bridges and Tunnels: % of Pre-Pandemic',
            'Staten Island Railway: Total Estimated Ridership' : 'Staten Island Railway',
            'Staten Island Railway: % of Comparable Pre-Pandemic Day' : 'Staten Island Railway: % of Pre-Pandemic'
            },
            )


# The following is The code for the Dash app I will keep it in one cell

# In[6]:


dbc_css = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css'

app = Dash(
    __name__, external_stylesheets=[dbc.themes.COSMO, dbc_css],  # Was PULSE
    suppress_callback_exceptions=True
)
server = app.server
# comparison_table = create_comparison_table(mta_data)
kpis = create_kpis(mta_data)

app.layout = dbc.Container(
    [
        html.Link(
            rel='stylesheet',
            # Assuming your CSS file is named 'style.css' and is placed in the 'assets' folder
            href='/assets/style.css'
        ),
        # Store data for later use
        dcc.Store(id='selected_services_store'),
        dcc.Store(id='granular_data_json_store'),
        dcc.Store(id='mta_data_json_store'),
        dcc.Store(id='granularity_store'),
        dcc.Store(id='metrics_store'),
        dcc.Store(id='kpi_store'),

        # Title row
        dbc.Row(create_title()),

        # Dropdowns row
        dbc.Row([
            dbc.Col(create_granularity_dropdown()),
            dbc.Col(create_services_dropdown()),
        ]),
        dbc.Row([
            dbc.Col(create_key_insights()),
        ]),
        # Tabs
        dcc.Tabs(
            className='dbc',
            id='tabs',
            children=[
                # Overview & Key Metrics Tab
                dcc.Tab(
                    id='Overview_and_key_metrics',
                    label='Overview & Key Metrics',
                    className='dbc',
                    children=[
                        # dbc.Row(),
                        dbc.Row(
                            id='kpi_card_row',
                            children=create_kpi_cards(kpis),
                            style={
                                'display': 'flex',
                                'justify-content': 'flex-start',
                                'gap': '2px',  # Space between cards
                                'flex-wrap': 'wrap',
                                'margin-bottom': '0.8em',
                                'width': '98%'
                            },
                        ),
                        dbc.Row(id='ridership_card_row',
                                style={
                                    'display': 'flex',
                                    'justify-content': 'flex-start',
                                    'align-items': 'flex-start',
                                    'gap': '2px',  # Space between cards
                                    'flex-wrap': 'wrap',
                                    'margin-bottom': '0.8em',
                                    'width': '100%'
                                },
                                ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Loading(
                                        id='loading',
                                        children=[
                                            dcc.Graph(
                                                id='service_line_chart',
                                                config={
                                                    'displayModeBar': False  # Turn off the toolbar
                                                },                                                                               
                                            ),
                                        ],
                                        type='circle',  # Loading spinner type
                                    ),                                    
                                    style={'backgroundColor': 'transparent'},
                                ),
                            ],
                            style={'backgroundColor': 'transparent'},
                        ),
                    ],
                ),

                # Service Recovery Analysis Tab
                dcc.Tab(
                    id='service_recovery_analysis',
                    label='Service Recovery Analysis',
                    className='dbc',
                    children=[
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                         html.Div(
                                        [
                                            html.Button(
                                                'i', id='info-button6', className='info-button'
                                            ),
                                            dbc.Tooltip(
                                                html.Span([
                                                    'Comparison Dates:',
                                                    html.Br(),
                                                    'Pre-Pandemic (Mar 1-10, 2020),',
                                                    html.Br(),
                                                    'Post-Pandemic (Oct 1-10, 2024)'
                                                ]),
                                                target='info-button6',
                                                placement='top',
                                            )
                                        ],
                                        style={
                                            'position': 'absolute',  # Absolute positioning
                                            'top': '30px',           # Position from top
                                            'right': '15px',         # Position from right
                                            'z-index': '10'          # Ensure it appears above other elements
                                        }
                                    ),
                                        dcc.Graph(
                                            id='recovery_bar_chart',
                                            style={
                                                'backgroundColor': 'transparent'},
                                            config={
                                                'displayModeBar': False  # Turn off the toolbar
                                            }
                                        ),
                                    ],
                                    style={
                                        'width': '50%',
                                        # 'height': '70vh',  # Adjust the height to make it more visible
                                        'position': 'relative',  # Parent div needs to be relative
                                        'backgroundColor': 'transparent'},
                                ),
                                dbc.Col(
                                    [
                                        dcc.Graph(
                                            id='correlation_heatmap',
                                            config={
                                                'displayModeBar': False  # Turn off the toolbar
                                            }
                                        ),
                                        html.P(
                                        'Note: Strong a correlation value of 0.97 between Metro-North and LIRR suggest a similar recovery pattern, '
                                        'reflecting the interdependence of these suburban transit lines post-pandemic.',
                                        style={
                                            'text-align': 'left',  # Center the annotation below the matrix
                                            'margin-top': '1em',      # Add some spacing from the matrix
                                            'font-size': '14px',      # Adjust the font size for better readability
                                            'color': 'grey'           # Set the color to grey to distinguish it from the main text
                                        }
                                        ),
                                        html.P(
                                        'There is strong correlation value of 0.89 between Access-A-Ride and LIRR which suggests that Access-A-Ride'
                                        ' may be used to deliver passengers to LIRR stations instead of passengers using the bus.',
                                        style={
                                            'text-align': 'left',  # Center the annotation below the matrix
                                            'margin-top': '0.5em',      # Add some spacing from the matrix
                                            'font-size': '14px',      # Adjust the font size for better readability
                                            'color': 'grey'           # Set the color to grey to distinguish it from the main text
                                            }
                                        )
                                    ],
                                    style={'width': '50%',
                                           'position': 'relative',  # Parent div needs to be relative
                                           'backgroundColor': 'transparent'},
                                ),
                            ],
                            style={
                                'width': '100%',
                                'backgroundColor': 'transparent'}
                        ),

                        dbc.Row([
                            dbc.Col(
                                dcc.Graph(
                                    id='recovery_heatmap',
                                    config={
                                        'displayModeBar': False  # Turn off the toolbar
                                    }
                                ),
                                style={'width': '100%',
                                       'backgroundColor': 'transparent'},
                            ),
                        ],
                            style={'backgroundColor': 'transparent'}
                        ),


                    ]
                ),
                # Ridership Comparisons Tab
                dcc.Tab(
                    id='ridership_comparisons',
                    label='Ridership Comparisons',
                    className='dbc',
                    children=[
                    # First row: Pie chart with info button
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Button(
                                                'i', id='info-button1', className='info-button'
                                            ),
                                            dbc.Tooltip(
                                                html.Span([
                                                    'Comparison Dates:',
                                                    html.Br(),
                                                    'Pre-Pandemic (Mar 1-10, 2020),',
                                                    html.Br(),
                                                    'Post-Pandemic (Oct 1-10, 2024)'
                                                ]),
                                                target='info-button1',
                                                placement='top',
                                            )
                                        ],
                                        style={
                                            'position': 'absolute',  # Absolute positioning
                                            'top': '5px',           # Position from top
                                            'right': '15px',         # Position from right
                                            'z-index': '10'          # Ensure it appears above other elements
                                        }
                                    ),
                                    dcc.Graph(
                                        id='ridership_pie_chart',
                                        config={
                                            'displayModeBar': False  # Turn off the toolbar
                                        }
                                    ),
                                ],
                                style={
                                    'width': '40%',
                                    'position': 'relative',
                                    'backgroundColor': 'transparent'
                                }
                            ),
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.Button(
                                                'i', id='info-button2', className='info-button'
                                            ),
                                            dbc.Tooltip(
                                                html.Span([
                                                    'Comparison Dates:',
                                                    html.Br(),
                                                    'Pre-Pandemic (Mar 1-10, 2020),',
                                                    html.Br(),
                                                    'Post-Pandemic (Oct 1-10, 2024)'
                                                ]),
                                                target='info-button2',
                                                placement='top',
                                            )
                                        ],
                                        style={
                                            'position': 'absolute',  # Absolute positioning
                                            'top': '5px',           # Position from top
                                            'right': '15px',         # Position from right
                                            'z-index': '10'          # Ensure it appears above other elements
                                        }
                                    ),
                                    dcc.Graph(
                                        id='before_after_chart',
                                        config={
                                            'displayModeBar': False  # Turn off the toolbar
                                        },
                                        style={
                                            'padding': '0',          # Remove any internal padding
                                            'margin-bottom': '0px',  # Remove space below the chart
                                        }
                                    ),
                                    html.P(
                                        'Buses have shown slower recovery compared to other modes, likely due to reduced demand'
                                        ' for shared transportation post-pandemic'
                                        ,
                                        style={
                                            'text-align': 'left',  # Center the annotation below the matrix
                                            'margin-top': '-3em',      # Add some spacing from the matrix
                                            'font-size': '14px',      # Adjust the font size for better readability
                                            'color': 'grey'           # Set the color to grey to distinguish it from the main text
                                            }
                                        )
                                ],
                                style={
                                    'width': '60%',
                                    'position': 'relative',
                                    'backgroundColor': 'transparent'
                                }
                            ),
                        ],
                        style={'backgroundColor': 'transparent'}
                        ),
                    # Second row: Comparison table
                        dbc.Row(
                        [
                            dbc.Col(                            
                                [
                                    html.Div(
                                        [
                                            html.Button(
                                                'i', id='info-button7', className='info-button'
                                            ),
                                            dbc.Tooltip(
                                                html.Span([
                                                    'Comparison Dates:',
                                                    html.Br(),
                                                    'Pre-Pandemic (Mar 1-10, 2020),',
                                                    html.Br(),
                                                    'First Post-Pandemic (Oct 1-10, 2021),',
                                                    html.Br(),
                                                    'Post-Pandemic (Oct 1-10, 2024)'
                                                ]),
                                                target='info-button7',
                                                placement='top',
                                            )
                                        ],
                                        style={
                                            'position': 'absolute',  # Absolute positioning
                                            'top': '25px',           # Position from top
                                            'right': '15px',         # Position from right
                                            'z-index': '10'          # Ensure it appears above other elements
                                        }
                                    ),
                                    # Add a title above the table
                                    html.H5(
                                        'Service Ridership Comparison Table',
                                        style={
                                            'text-align': 'center',  # Center-align the title
                                            'margin-bottom': '1em',  # Space below the title
                                            'margin-top': '1em',  # Optional space above the title
                                            'font-weight': 'bold'  # Make the title bold
                                        }
                                    ),
                                    html.Div(
                                        dbc.Table(id='comparison_table'),
                                        style={
                                            'width': '100%',
                                            'backgroundColor': 'transparent'
                                        },
                                    ),
                                ],
                                style={
                                'position': 'relative',
                                'backgroundColor': 'transparent'
                                }
                            ),
                        ],
                        style={'backgroundColor': 'transparent'}
                        ),
                    ],
                ),
                # Detailed Service Trends Tab
                dcc.Tab(
                    id='detailed_service_trends',
                    label='Detailed Service Trends',
                    className='dbc',
                    children=[                        
                        dbc.Row([
                            dbc.Col(
                                dcc.Graph(
                                    id='dual_axis_chart',
                                    config={
                                        'displayModeBar': False  # Turn off the toolbar
                                    }
                                ),
                                style={'backgroundColor': 'transparent'},
                            ),
                        ],
                            style={'backgroundColor': 'transparent'}
                        ),
                        dbc.Row([
                            dbc.Col(
                                dcc.Graph(
                                    id='ridership_scatterplot',
                                    config={
                                        'displayModeBar': False  # Turn off the toolbar
                                    }
                                ),
                                style={'width': '100%',
                                       'backgroundColor': 'transparent'},
                            ),
                        ],
                            style={'backgroundColor': 'transparent'}
                        ),
                        dbc.Row([
                            dbc.Col(
                                dcc.Graph(
                                    id='daily_variability_boxplot',
                                    config={
                                        'displayModeBar': False  # Turn off the toolbar
                                    }
                                ),
                                style={'width': '100%',
                                       'backgroundColor': 'transparent'},
                            ),
                        ],
                            style={'backgroundColor': 'transparent'}
                        ),
                    ],
                ),
                dcc.Tab(                    
                    id='whats-next',
                    label='What\'s Next?',                    
                    className='dbc',
                    children=[
                        dbc.Row([
                            dbc.Col([
                                create_whats_next() # Use the function call directly to provide the content
                            ],
                            )
                        ]
                        )
                    ]
                )    	                       
            ],
            style={'margin-bottom': '0.8em'},
        ),
    ],
)


@app.callback(
    Output('ridership_card_row', 'children'),
    [
        Input('selected_services_store', 'data'),
        Input('granular_data_json_store', 'data'),
        Input('granularity_store', 'data'),
        Input('metrics_store', 'data'),
        Input('tabs', 'value')
    ],
    prevent_initial_call='initial_duplicate',
)
def update_ridership_cards(selected_services, granular_data_json, granularity, metrics_json, tab):
    if tab == 'Overview_and_key_metrics':
        if granular_data_json is None:
            return []
        granular_data = pd.read_json(granular_data_json, orient='split')
        if not selected_services:
            selected_services = services
        return create_ridership_cards(granular_data, selected_services, granularity, metrics)
    else:
        # Return the current state of the ridership cards
        raise PreventUpdate


@app.callback(
    Output('kpi_card_row', 'children'),  # Update the row with new cards
    Input('kpi_store', 'data'),
)
def update_kpi_cards(kpis_json):
    kpis = json.loads(kpis_json)
    return create_kpi_cards(kpis)


@app.callback(
    Output('ridership_card_row', 'children', allow_duplicate=True),
    [
        Input('selected_services_store', 'data'),
        Input('granular_data_json_store', 'data'),
        Input('granularity_store', 'data'),
        Input('metrics_store', 'data'),
    ],
    prevent_initial_call='initial_duplicate',
)
def update_ridership_cards(selected_services, granular_data_json, granularity, metrics_json):
    metrics = json.loads(metrics_json)
    if granular_data_json is None:
        return []
    granular_data = pd.read_json(StringIO(granular_data_json), orient='split')
    if not selected_services:
        selected_services = services
    return create_ridership_cards(granular_data, selected_services, granularity, metrics)


@app.callback(
    [
        Output('report_title', 'children'),
        Output('service_line_chart', 'figure'),
        Output('selected_services_store', 'data'),
        Output('granular_data_json_store', 'data'),
        Output('granularity_store', 'data'),
        Output('mta_data_json_store', 'data'),
        Output('metrics_store', 'data'),
        Output('kpi_store', 'data'),
        Output('correlation_heatmap', 'figure'),
        Output('dual_axis_chart', 'figure'),
        Output('recovery_bar_chart', 'figure'),
        Output('recovery_heatmap', 'figure'),
        Output('ridership_pie_chart', 'figure'),
        Output('ridership_scatterplot', 'figure'),
        Output('before_after_chart', 'figure'),
        Output('daily_variability_boxplot', 'figure'),
        Output('comparison_table', 'children'),
    ],
    [
        Input('granularity_dropdown', 'value'),
        Input('services_dropdown', 'value'),
        Input('selected_services_store', 'data'),
    ],
    prevent_initial_call='initial_duplicate',
)
def display_information(granularity_dropdown_value, service_dropdown_value, selected_services):
    title = 'MTA Ridership Dashboard'
    selected_services = (
        services
        if service_dropdown_value == 'all_services' or not service_dropdown_value
        else service_dropdown_value
    )
    mta_thousands = create_thousand_dataframe(mta_data)
    mta_thousands.set_index('Date', inplace=True)
    granular_data = resample_data(mta_thousands, granularity_dropdown_value)
    granular_data_json = granular_data.to_json(orient='split')
    mta_data_json = mta_data.to_json(orient='split')
    service_line_chart = create_service_line_chart(
        granular_data, granularity_dropdown_value, selected_services
    )
    kpis = create_kpis(mta_data)
    kpis_json = json.dumps(kpis)
    metrics = create_metrics(granular_data, selected_services)
    metrics_json = json.dumps(metrics)
    correlation_matrix = create_correlation_matrix(
        granular_data, granularity_dropdown_value)
    dual_axis_chart = create_dual_axis_chart(
        granular_data, granularity_dropdown_value, selected_services)
    start_date = mta_data['Date'].min()
    end_date = mta_data['Date'].max()
    recovery_bar_chart = create_recovery_bar_chart(mta_data)
    recovery_heatmap = create_recovery_heatmap(
        granular_data, granularity_dropdown_value)
    ridership_pie_chart = create_ridership_pie_chart(mta_data)
    ridership_scatterplot = create_ridership_scatterplot(
        mta_data, selected_services)
    before_after_chart = create_before_after_chart(mta_data, services)
    daily_variability_boxplot = create_daily_variability_boxplot(
        mta_data, services, start_date, end_date)
    comparison_table = create_comparison_table(mta_data)
    return (
        title,
        service_line_chart,
        selected_services,
        granular_data_json,
        granularity_dropdown_value,
        mta_data_json,
        metrics_json,
        kpis_json,
        correlation_matrix,
        dual_axis_chart,
        recovery_bar_chart,
        recovery_heatmap,
        ridership_pie_chart,
        ridership_scatterplot,
        before_after_chart,
        daily_variability_boxplot,
        comparison_table,
    )


if __name__ == '__main__':
    free_port = find_free_port()
    print(f'Port used = {free_port}')
    app.run_server(debug=True, mode='inline', port=free_port)


# In[ ]:





# In[ ]:





# In[ ]:




