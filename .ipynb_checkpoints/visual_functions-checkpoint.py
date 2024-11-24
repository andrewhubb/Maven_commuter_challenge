import pandas as pd
import numpy as np
from dash import Dash, dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
from dash_bootstrap_templates import load_figure_template
import dash_dangerously_set_inner_html
import plotly.express as px
from plotly.subplots import make_subplots  # Add this line
import plotly.graph_objects as go

from config import (
    services,
    full_colours,
    colours,
    colours_pct,
    dark_blue,
    dark_orange
)
from typing import Tuple

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
    top_service = kpis['top_service']
    recovery_percentage = kpis['recovery_percentage']
    yoy_growth = kpis['yoy_growth']         
        
    value_text_style = {'font-size': '1.25em',
                       'font-weight': 'bold',
                       'text-align': 'center',
                       'margin-top': '0em', 
                       'margin-bottom': '0em'}
    detail_text_style = {'font-size': '1.25em',
                       'font-weight': 600,
                       'text-align' : 'center',
                       'margin-top': '0em', 
                       'margin-bottom': '0em'}
    card_120px_style = {'width': '120px'}

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
                           #style=value_text_style
                           style=detail_text_style
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
            #width=3,
            style={'margin-bottom': '0.8em'},            
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Total Recovery', 
                           className='card-title', 
                           style={'margin-bottom': '0em', 
                                  'text-align': 'center',
                                  'font-weight': 600}
                          ),
                    html.P(f'{total_recovery}', 
                           className='card-text',
                           #style=value_text_style
                           style=detail_text_style
                          ),
                    html.P(html.Br(),  
                       className='card-text',
                       style=detail_text_style,                       
                    )  
                ]),
                style={
                    'width': '150px',
                    'border-radius': '15px',  # Rounded corners
                    'box-shadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Optional shadow for better visuals
                    'padding': '0.1em'
                    },
                
            ),                                             
            #width=3,
            style={'margin-bottom': '0.8em'}
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Highest Recovery Transport Type', 
                           className='card-title', 
                           style={'margin-bottom': '0em', 'font-weight': 600}
                          ),
                    html.P(f'{top_service}', 
                           className='card-text',
                           style=detail_text_style
                          ),                    
                    html.P(f'{recovery_percentage:.1f}%',  
                       className='card-text',
                       style=detail_text_style,                       
                    )  
                ]),
                style={
                    'width': '280px',
                    'border-radius': '15px',  # Rounded corners
                    'box-shadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Optional shadow for better visuals
                    'padding': '0.1em'
                    }
            ),                                             
            #width=3,
            style={'margin-bottom': '0.8em'},            
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Year on Year Growth', 
                           className='card-title', 
                           style={'margin-bottom': '0em', 'font-weight': 600}
                          ),
                    html.P(f'{yoy_growth:.1f}%', 
                           className='card-text',
                           style=detail_text_style
                          ),
                    html.P(html.Br(),  
                       className='card-text',
                       style=detail_text_style,                       
                    )  
                ]),
                style={
                    'width': '180px',
                    'border-radius': '15px',  # Rounded corners
                    'box-shadow': '0px 4px 6px rgba(0, 0, 0, 0.1)',  # Optional shadow for better visuals
                    'padding': '0.1em'
                    }
            ),                                             
            #width=3,
            style={'margin-bottom': '0.8em'},            
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
    fig.update_yaxes(showgrid=True, gridcolor='lightgrey',tickformat=',0f')        
    
    return fig


def create_correlation_matrix(granular_data: pd.DataFrame, granularity) -> go.Figure:
    # Resample data based on granularity    
    filtered_cols = [col for col in granular_data.columns if not any(p in col.lower() for p in ["% of pre-pandemic", "% pre-pandemic"])]
    #filtered_cols = [col for col in granular_data.columns if not any(p in col.lower() for p in ["% of Pre-Pandemic", "% Pre-Pandemic"])]
    df_filtered = granular_data[filtered_cols]
    
    # Calculate correlation
    if granularity == 'Year':
        df_filtered = df_filtered.iloc[:, 1:-1]
    else:
        df_filtered = df_filtered.iloc[:,1:].corr().round(3)
        
    correlation_matrix = df_filtered.corr().round(3)
    min_value = correlation_matrix.min().min()
    
    # Create heatmap
    fig = px.imshow(
        correlation_matrix,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        zmin = min_value,
        zmax = 1,
        title=f"Service Recovery Correlation ({granularity})",
        labels={'color': 'Correlation Coefficient'}        
    )
    fig.update_layout(
        height=600,
        #width=,        
    )
    fig.update_traces(
        dict(showscale=False, 
             coloraxis=None, 
             colorscale='RdBu_r'), 
            selector={'type':'heatmap'}
    )
    return fig


def create_dual_axis_chart(granular_data: pd.DataFrame,granularity: str, service: str) -> go.Figure:    

    if granularity == 'Year':
        granular_data['Year'] = granular_data['Year'].astype(str)
        x_axis_values = granular_data['Year']  # Use the 'Year' column directly
    else:
        x_axis_values = granular_data['Date']  # Use the 'Date' column directly
    # Create the dual-axis chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    
    # Add ridership data to the primary y-axis
    fig.add_trace(
        go.Scatter(
            x=x_axis_values,
            y=granular_data[service],
            mode='lines',
            name=f'{service} Ridership',
            line=dict(color='blue')
        ),
        secondary_y=False
    )
    
    # Add recovery percentage data to the secondary y-axis
    fig.add_trace(
        go.Scatter(
            x=x_axis_values,
            y=granular_data[f'{service}: % of Pre-Pandemic'],
            mode='lines',
            name=f'{service} Recovery %',
            line=dict(color='green', dash='dot')
        ),
        secondary_y=True
    )
    
    # Update axes titles
    fig.update_layout(
        title=f'{service} Ridership and Recovery Percentage',
        xaxis_title=None,
        yaxis_title='Ridership',
        yaxis2_title='% of Pre-Pandemic',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    # Update axis ranges and layout
    fig.update_yaxes(title_text='Ridership', tickformat=',0f', secondary_y=False)
    fig.update_yaxes(title_text='Recovery Percentage (%)', tickformat='.0f', secondary_y=True)
    
    return fig


def create_recovery_bar_chart(granular_data: pd.DataFrame) -> go.Figure:
    # Extract recovery columns
    recovery_cols = [col for col in granular_data.columns if ': % of Pre-Pandemic' in col]
    
    # Validate and align services with recovery columns
    extracted_services = [col.split(':')[0] for col in recovery_cols]  # Remove ": % of Pre-Pandemic" suffix
    aligned_services = [service for service in services if service in extracted_services]
    
    # Ensure alignment between services and recovery columns
    recovery_cols = [f"{service}: % of Pre-Pandemic" for service in aligned_services]

   
        
    # Calculate the average recovery
    average_recovery = granular_data[recovery_cols].mean()        
    average_recovery = average_recovery.sort_values(ascending=True)
    aligned_services = average_recovery.index.str.replace(": % of Pre-Pandemic", "").tolist()   
    
    # Create the horizontal bar chart
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=average_recovery,  # Recovery percentages on the x-axis
            y=aligned_services,  # Services on the y-axis
            text=average_recovery.round(1),  # Add text labels for percentages
            textposition='auto',
            marker_color='teal',  # Optional: Set bar color
            orientation='h'  # Horizontal orientation
        )
    )    
    
    # Customize layout
    fig.update_layout(
        
        title='MTA Service Recovery Since 2020',
        xaxis_title="Recovery Percentage (% of Pre-Pandemic)",
        yaxis_title=None,
        xaxis_tickformat=".0f",  # Ensure whole number format
        yaxis=dict(
            automargin=True,  # Adjusts margin to avoid overlap
            ticklabelposition="outside"  # Move labels outside for spacing
        ),
        template="plotly_white",
        margin=dict(l=150)  # Increase left margin for better spacing
    )
    
    #fig.update_xaxes(range=[-20, None])
    return fig  # Return the chart figure


def create_recovery_heatmap(granular_data: pd.DataFrame, granularity: str) -> go.Figure:
    """
    Create a heatmap of recovery percentages by service and time period.
    
    :param granular_data: Aggregated DataFrame with recovery percentage columns and a time column.
    :param granularity: The granularity level ('Month', 'Quarter', 'Year').
    :return: Plotly Figure object with the heatmap.
    """
    # Determine the time column based on granularity
    time_column = 'Year' if granularity == 'Year' else 'Date'

    # Extract recovery percentage columns
    recovery_cols = [col for col in granular_data.columns if ': % of Pre-Pandemic' in col]

    # Pivot the data: Services in rows, time periods in columns
    heatmap_data = granular_data.melt(
        id_vars=[time_column],
        value_vars=recovery_cols,
        var_name="Service",
        value_name="Recovery Percentage"
    )
    heatmap_pivot = heatmap_data.pivot(index="Service", columns=time_column, values="Recovery Percentage")

    # Format x-axis labels based on granularity
    if granularity == 'Year':
        formatted_labels = [str(int(year)) for year in heatmap_pivot.columns]
    elif granularity == 'Quarter':
        formatted_labels = [
            f"{col.year}-Q{((col.month - 1) // 3) + 1}" for col in heatmap_pivot.columns
        ]
    else:  # Month
        formatted_labels = [col.strftime('%Y-%b') for col in heatmap_pivot.columns]

    # Handle axis label optimisation for Month or Quarter
    max_labels = 12 if granularity == 'Month' else 8  # Adjust based on expected number of labels
    label_step = max(1, len(heatmap_pivot.columns) // max_labels)
    x_axis_tickvals = heatmap_pivot.columns[::label_step]
    x_axis_ticktext = [formatted_labels[i] for i in range(0, len(formatted_labels), label_step)]

    # Create the heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='RdBu',
            colorbar=dict(title="Recovery %"),
            zmin=0,  # Adjust these based on your dataset
            zmax=100
        )
    )

    # Update layout for readability
    fig.update_layout(
        title=f"Recovery by Service and Time ({granularity})",
        xaxis=dict(
            title=None,
            tickmode='array',
            tickvals=x_axis_tickvals,
            ticktext=x_axis_ticktext,
            tickangle=-45 if granularity in ['Month', 'Quarter'] else 0,  # Rotate for readability
            tickfont=dict(size=10 if granularity == 'Month' else 12)  # Adjust font size
        ),
        yaxis=dict(
            title=None,
        ),
        template="plotly_white"
    )

    return fig
