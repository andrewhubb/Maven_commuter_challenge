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
from config import (
    services,
    full_colours,
    colours,
    colours_pct,
    dark_blue,
    dark_orange
)


def create_title():
    """ 
    Creates the report title
    
    Returns: 
        the dbc.Col array with children that holds the html code for the title
    """
    return [
                dbc.Col(
                    [
                        html.H2(
                            id='report_title',
                            className='bg-primary text-white p-2 mb-2 text-center',
                        )
                    ]
                )
            ]
    
def create_granularity_dropdown():
    """
    Creates the granulatity dropdown

    Returns: 
        the dbc.Card array with children that holds the dropdown
    """
    return [
        dbc.Card(
            [ 
                dcc.Markdown('Select a Report Granularity:'),
                dcc.Dropdown(
                    ['Month',
                     'Quarter',
                     'Year'                     
                    ],
                    'Month',
                    id='granularity_dropdown',                                                                        
                    multi=False,
                    className='dbc',
                    clearable=False
                ),
             ],
              style={'border': 'none','margin-bottom': '0.8em'},
         )       
    ]     

def create_services_dropdown():
    """
    Creates the services dropdown

    Returns: 
        the dbc.Card array with children that holds the dropdown
    """    
    return [
        dbc.Card(
            [ 
                dcc.Markdown('Select a Transportation Type:'),
                dcc.Dropdown(
                    options=[
                        {'label': service, 'value': service}
                        for service in services
                    ],
                    value='all_services',
                    id='services_dropdown',                                                                        
                    multi=True,
                    className='dbc',
                ),
             ],
             style={'border': 'none','margin-bottom': '0.8em'}            
         )       
    ]


def create_sparkline(granular_data: pd.DataFrame, service: list, granularity: str, metrics: dict) -> go.Figure:
    """
    Creates a sparkline visual for display in ridership cards

    Args:
        granular_data : The resampled dataframe.
        service       : The current service for the card
        granularity   : The selected granularity level
        metrics       : The metrics to be used from the metrics_store

    Returns:
        sparkline_figure : A Plotly Go Objects line chart
    """
    if granularity == 'Year':
        max_date = granular_data['Year'].max()
        last_year_data = granular_data[granular_data['Year'] >= max_date - 1]
    else:
        max_date = granular_data['Date'].max()
        last_year_data = granular_data[granular_data['Date'] > max_date - pd.DateOffset(years=1)]            
        
    percent_change = metrics[service]['percent_change']
    if percent_change >= 0:
        line_colour = dark_blue
    else:
        line_colour = dark_orange
        
    sparkline_figure = go.Figure()
    sparkline_figure.add_trace(
        go.Scatter(
            x=last_year_data['Date'],  # x-axis is the Date
            y=last_year_data[service],  # y-axis is the ridership value
            mode='lines',
            line=dict(width=2, color=line_colour),
            showlegend=False,
            text=last_year_data[service].apply(lambda x: f'{x:,.0f}'),  # Format text to display ridership values
            hovertemplate='%{text}<extra></extra>',  # Display the ridership value on hover
        )    
    )
    sparkline_figure.update_layout(
        height=80,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)', # Transparent background for plot area
        paper_bgcolor='rgba(0,0,0,0)' # Transparent background for whole figure
    )
    return sparkline_figure

   
def create_kpi_cards(kpis):    
    """
    Create a Row of cards to show KPI values.

    Args:        
        kpis : The KPI values from the kpi_store

    Returns:
        cards: A list containing the cards to display on the row
    """
    total_ridership = kpis['total_ridership']
    highest_ridership_day = kpis['highest_ridership_day']
    total_recovery = kpis['total_recovery']
    
    
    value_text_style = {'font-size': '2.5em',
                       'font-weight': 'bold',
                       'text-align': 'center',
                       'margin-top': '0em', 
                       'margin-bottom': '0em'}
    detail_text_style = {'font-size': '1.5em',
                       'font-weight': 'bold',
                       'text-align' : 'center',
                       'margin-top': '0em', 
                       'margin-bottom': '0em'}

    cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Highest Ridership', 
                           className='card-title', 
                           style={'margin-bottom': '0em', 'font-weight': 600}
                          ),  # Reduced margin for title
                    html.P(f'{total_ridership}', 
                           className='card-text',
                           style=value_text_style
                          ),
                    html.P(highest_ridership_day, 
                           className='card-text',
                           style=detail_text_style
                          )
               ]),
                style={
                    'border-radius': '15px',  # Rounded corners
                    'box-shadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Optional shadow for better visuals
                    'padding': '0.1em'
                    }
            ),                                             
            width=4,
            style={'margin-bottom': '0.8em'}
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Total Recovery', 
                           className='card-title', 
                           style={'margin-bottom': '0em', 'font-weight': 600}
                          ),
                    html.P(f'{total_recovery}', 
                           className='card-text',
                           style=value_text_style
                          ),
                    html.P(html.Br(),  
                       className='card-text',
                       style=detail_text_style,                       
                    )  
                ]),
                style={
                    'border-radius': '15px',  # Rounded corners
                    'box-shadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Optional shadow for better visuals
                    'padding': '0.1em'
                    }
            ),                                             
            width=4,
            style={'margin-bottom': '0.8em'}
        )                
    ]
        
    return cards


                             
def create_ridership_cards(granular_data, selected_services, granularity, metrics) -> list:
    """
    Create a Row of cards to show ridership values and sparkline visuals.

    Args:
        granular_data    : The resampled dataframe.
        selected_services: The services selected from the service dropdown 
        granularity      : The selected granularity level.

    Returns:
        cards: A list containing the cards to display on the row
    """
    up_arrow = chr(8593)  # Upward arrow (↑)
    down_arrow = chr(8595)  # Downward arrow (↓)
    cards = []
        
    for service in selected_services[:3]:        
        ridership_last_period = metrics[service]['ridership_last_period']
        percent_change = metrics[service]['percent_change']

        if percent_change > 0:
            percent_change_style = {'margin-top': '0', 'margin-bottom': '0.2em', 'color': dark_blue}
            percent_change_text = f'% Change: {percent_change:.1f}% {up_arrow}'
            card_text_style = {'font-size': '4em',
                               'font-weight': 'bold',
                               'text-align': 'center',
                               'margin-top': '0', 
                               'margin-bottom': '0em', 
                               'color': dark_blue}
        elif percent_change < 0:
            percent_change_style = {'margin-top': '0', 'margin-bottom': '0.2em', 'color': dark_orange}
            percent_change_text = f'% Change: {percent_change:.1f}% {down_arrow}'
            card_text_style = {'font-size': '4em',
                               'font-weight': 'bold',
                               'text-align': 'center',
                               'margin-top': '0', 
                               'margin-bottom': '0em', 
                               'color': dark_orange}
        else:
            percent_change_style = {'margin-top': '0', 'margin-bottom': '0.2em'}
            percent_change_text = f'% Change: {percent_change:.1f}%'
            card_text_style = {'font-size': '4em',
                               'font-weight': 'bold',
                               'text-align': 'center',
                               'margin-top': '0', 
                               'margin-bottom': '0em'}       
        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.H5(service, 
                                className='card-title',
                                style={'margin-bottom': '0em' }
                               ),
                        html.P(f'Avg {granularity}ly Ridership', style={'margin-bottom': '0.0em'}),
                        html.P(ridership_last_period, 
                               className='card-text',
                               style=card_text_style),                        
                            html.P(percent_change_text, 
                                   className='card-text',
                                   style=percent_change_style),                       
                                 
                        dcc.Graph(
                            figure=create_sparkline(granular_data, service, granularity,metrics),  # Your sparkline function
                            config={'displayModeBar': False}                        
                        ),
                    ]),  
                    style={
                    'border-radius': '15px', # Rounded corners
                    'padding': '0.1em'
                    }
                ),
                width=4,
                style={'margin-bottom': '0.2em'}
            ),           
        )
    return cards 

                               
def create_service_line_chart(granular_data: pd.DataFrame, granularity: str, selected_services: list) -> go.Figure:
    """
    Create a Plotly line chart for service data based on selected granularity.

    Args:
        granular_data: The resampled dataframe.
        granularity: The selected granularity level.

    Returns:
        fig: A Plotly Graph Objects figure.
    """
    fig = go.Figure()    
    # Create the chart for each service
    for service in selected_services:
        if service in granular_data.columns:
            if granularity == 'Year':
                fig.add_trace(
                    go.Scatter(                    
                        x=granular_data['Year'],
                        y=granular_data[service],
                        mode='lines',
                        name=service,
                        line=dict(color=full_colours[services.index(service)]),
                    )
                )    
            else:
                fig.add_trace(
                    go.Scatter(                    
                        x=granular_data['Date'],
                        y=granular_data[service],
                        mode='lines',
                        name=service,
                        line=dict(color=full_colours[services.index(service)]),
                    )
                )

    # Set chart title and axis labels
    fig.update_layout(
        title=f'{granularity} Ridership by Transportation Type',
        xaxis_title=None,
        yaxis_title='Average Ridership (Thousands)',
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)', # Transparent background for plot area
        paper_bgcolor='rgba(0,0,0,0)' # Transparent background for whole figure
    )
    
    # Format the X and Y axes
    fig.update_xaxes(showgrid=True, gridcolor='lightgrey')
    fig.update_yaxes(showgrid=True, gridcolor='lightgrey')

    return fig