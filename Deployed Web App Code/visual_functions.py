import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from scipy.stats import linregress

from config import (
    services,
    service_colours,
    dark_blue,
    dark_orange
)

from support_functions import (
    prepare_comparison_table,
)

import textwrap

import logging

logging.basicConfig(filename='debug.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def wrap_comment(comment, width=50):
    '''Wrap the comment text to a specified width.'''
    return '<br>'.join(textwrap.wrap(comment, width=width))


def create_title():
    '''
    Creates the report title

    Returns:
        the dbc.Col array with children that holds the html code for the title
    '''
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

def create_key_insights():
    '''
    Creates the report key insights

    Returns:
        the dbc.Col array with children that holds the html code for the insights
    '''
    return [
        dbc.Col(
            [
                html.P([
                    html.B('Key Insights:'),
                    ' Metro-North and Access-A-Ride have shown the strongest recovery, exceeding pre-pandemic ridership levels, with Metro-North now at 135.5% and Access-A-Ride at 124.6% of their pre-pandemic values. Bridges & Tunnels have also surpassed pre-pandemic levels at 109.2%. In contrast, Subways and Buses are recovering more slowly, with current ridership at 84.0% and 72.8% of pre-pandemic levels, respectively.',
                ],
                id='key_insights',
                className='card-text',
                style={'font-size': '0.8em', 'margin-bottom': '0.8em'}
                ),
            ]
        )
    ]

def create_whats_next() -> list:
    '''
    Creates the What is next Tab content

    Returns:
        the html.Div block array
    '''
    whats_next_content = html.Div([
    html.H4('What\'s Next?', style={'margin-bottom': '1em'}),  # Title for the tab
    html.Ul([  # Unordered list for bullet points
        html.Li([html.B('Metro-North'),' and ', html.B('Access-A-Ride'), ' have shown significant recovery, exceeding pre-pandemic ridership levels. This suggests a stable and growing need for suburban and accessible transport options.']),
        html.Li([html.B('Congestion Charge Impact:'),' Starting in January 2025, New York City will implement the first congestion charge in North America, aimed at reducing traffic in highly congested areas of the city. This charge will impact drivers entering certain zones during peak hours, making it more expensive to drive into the city. This new policy is expected to:']),
        html.Ul([
            html.Li(['Reduce the volume of private cars on the road, potentially lowering the demand for ',html.B('Bridges and Tunnels.')]),
            html.Li(['Increase ridership on public transportation services like ',html.B('Subways'),', ',html.B('Buses'),', ',html.B('Metro-North'),', and',html.B('LIRR'),' as commuters seek more affordable alternatives to driving.']),
            html.Li([html.B('Impact recovery trends:'),' Services that have not yet returned to pre-pandemic levels, such as ', html.B('Buses'),' and ',html.B('Staten Island Railway'),' might see significant growth post-2025 as driving becomes less attractive.']),
            html.Li([html.B('Projections:'),' If a significant percentage of current car users switch to public transportation, the ',html.B('MTA'),' could see recovery levels for services like ', html.B('Subways'),' and ',html.B('Buses'),' exceed 100% of pre-pandemic ridership, driving continued growth and reducing congestion on city streets.']),
            html.Li([html.B('Monitor Effects of Congestion Pricing:'),' After the implementation of congestion charges, it will be essential to monitor its effect on public transit usage and adjust service offerings accordingly.']),
        ]),
        html.Li([html.B('Return to Office Trends:'),' As more companies adopt hybrid work policies or return to office schedules, services like ',html.B('Metro-North'),' and ', html.B('LIRR'),' are likely to see further increases in ridership.']),
        html.Li([html.B('Infrastructure Investment:'),' The ',html.B('MTA'),' should prioritize investments in improving train, track, and signal reliability. Service reliability will be crucial to gain the trust of commuters and keep them using public transit.']),
        html.Li([html.B('Accessibility Improvements:'),' The ',html.B('MTA'),'> should resume and complete the ',html.B('23 subway station elevator projects'),' that were put on hold. Improving accessibility will directly impact ridership, especially for those relying on Access-A-Ride and those with mobility challenges.']),
        html.Li([html.B('Cost Control and Fare Evasion Measures:'),' Keeping fare prices affordable while controlling ',html.B('fare evasion'),' is essential to maintain financial sustainability. Reducing ',html.B('fare evasion'),' would increase funds available to invest in service reliability.']),
    ],
            style={
                'margin-top': '1em',
                'font-size': '14px'
            }
           )  # Styling for bullet points
], style={'padding': '2em'})  # Additional padding for overall block styling

    return whats_next_content
def create_granularity_dropdown() -> list:
    '''
    Creates the granulatity dropdown

    Returns:
        the dbc.Card array with children that holds the dropdown
    '''
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
                    className='custom-dropdown',
                    clearable=False
                ),
            ],
            style={'border': 'none', 'margin-bottom': '0.8em'},
        )
    ]


def create_services_dropdown() -> list:
    '''
    Creates the services dropdown

    Returns:
        the dbc.Card array with children that holds the dropdown
    '''
    return [
        dbc.Card(
            [
                dcc.Markdown('&nbsp;'),
                dcc.Dropdown(
                    options=[
                        {
                            'label': service,
                            'value': service
                        }
                        for service in services
                    ],
                    value='all_services',
                    id='services_dropdown',
                    placeholder='Select a Service...',
                    multi=True,
                    className='custom-dropdown'      # Apply custom class
                ),
            ],
            style={'border': 'none', 'margin-bottom': '0.8em'}
        )
    ]


def create_sparkline(granular_data: pd.DataFrame, service: list, granularity: str, metrics: dict) -> go.Figure:
    '''
    Creates a sparkline visual for display in ridership cards

    Args:
        granular_data: The resampled dataframe.
        service      : The current service for the card
        granularity  : The selected granularity level
        metrics      : The metrics to be used from the metrics_store

    Returns:
        sparkline_figure: A Plotly Go Objects line chart
    '''
    if granularity == 'Year':
        max_date = granular_data['Year'].max()
        last_year_data = granular_data[granular_data['Year'] >= max_date - 1]
    else:
        max_date = granular_data['Date'].max()
        last_year_data = granular_data[granular_data['Date']
                                       > max_date - pd.DateOffset(years=1)]

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
            # Format text to display ridership values
            text=last_year_data[service].apply(lambda x: f'{x:,.0f}'),
            # Display the ridership value on hover
            hovertemplate='%{text}<extra></extra>',
        )
    )
    sparkline_figure.update_layout(
        height=60,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            )
        ),
    )

    return sparkline_figure


def create_kpi_cards(kpis):
    '''
    Create a Row of cards to show KPI values.

    Args:
        kpis: The KPI values from the kpi_store

    Returns:
        cards: A list containing the cards to display on the row
    '''
    logging.debug(f"Started create_kpi_cards with: {kpis}")
    if not isinstance(kpis, dict):
        logging.error(f"kpis is not a dictionary. Received: {kpis}")
        raise TypeError("kpis must be a dictionary.")

    if 'total_ridership' not in kpis:
        logging.error(f"Key 'total_ridership' is missing in kpis. Available keys: {kpis.keys()}")
        raise KeyError("Missing key 'total_ridership' in kpis.")

    # Proceed with creating cards
    total_ridership = kpis["total_ridership"]
    highest_ridership_day = kpis["highest_ridership_day"]
    total_recovery = kpis["total_recovery"]
    top_service = kpis["top_service"]
    recovery_percentage = kpis["recovery_percentage"]

    # Continue with the card creation logic
    # Set the height of the cards for all the cards on this row
    card_height = '100px'
    detail_font_weight = '600'

    total_ridership = kpis["total_ridership"]
    highest_ridership_day = kpis["highest_ridership_day"]
    total_recovery = kpis["total_recovery"]
    top_service = kpis["top_service"]
    recovery_percentage = kpis["recovery_percentage"]
    yoy_growth = kpis["yoy_growth"]
    avg_lockdown_ridership = kpis["avg_lockdown_ridership"]
    avg_post_lockdown_ridership = kpis["avg_post_lockdown_ridership"]

    value_text_style = {'font-size': '1.25em',
                        'font-weight': 'bold',
                        'text-align': 'center',
                        'margin-top': '0em',
                        'margin-bottom': '0em'}
    detail_text_style = {'font-size': '1em',
                         'font-weight': detail_font_weight,
                         'text-align': 'center',
                         'margin-top': '0em',
                         'margin-bottom': '0em'}
    other_text_style = {'font-size': '0.9em',
                        'font-weight': '400',
                        'text-align': 'center',
                        'margin-top': '0em',
                        'margin-bottom': '0em'}

    cards = [
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Highest Ridership',
                           className='card-title',
                           style={'font-size': '12px', 'margin-bottom': '0em'}
                           ),  # Reduced margin for title
                    html.P(f'{total_ridership}',
                           className='card-text',
                           style=value_text_style
                           ),
                    html.P(highest_ridership_day,
                           className='card-text',
                           style=other_text_style
                           )
                ]),
                style={
                    'height': card_height,
                    'border-radius': '15px',  # Rounded corners
                    'padding': '0.1em',
                    'margin-bottom': '0.8em',
                    'max-width': '150px'
                },
            ),
            style={'margin-bottom': '0.8em'},
            width='auto'
        ),
        dbc.Col(
            [
                html.Div(
                    [
                        # Button and tooltip
                        html.Button('i', id='info-button5', className='info-button'),
                        dbc.Tooltip(
                            html.Span([
                                'This card represents the percentage recovery in ridership compared to pre-pandemic levels.',
                                html.Br(),
                                html.Br(),
                                'Comparison Dates:',
                                html.Br(),
                                'Lockdown Period',
                                html.Br(),
                                '(Mar 1-10, 2020),',
                                html.Br(),
                                'Post Lockdown Period:',
                                html.Br(),
                                '(Oct 1-10, 2024)'
                            ]),
                            target='info-button5',
                            placement='top',
                        )
                    ],
                    style={
                        'position': 'absolute',  # Button is positioned absolutely within this relative container
                        'top': '2px',
                        'right': '15px',
                        'z-index': '10'  # Ensure it appears above other elements
                    }
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.P('Overall Ridership Recovery',
                               className='card-title',
                               style={'margin-bottom': '0em',
                                      'text-align': 'center',
                                      'font-size': '12px'
                                      }
                               ),
                        html.P(f'{total_recovery}',
                               className='card-text',
                               style=value_text_style
                               ),
                    ]),
                    style={
                        'height': card_height,
                        'border-radius': '15px',  # Rounded corners
                        'padding': '0.1em',
                        'max-width': '150px',
                        'position': 'relative',  # Relative position for the button to align properly
                        'display': 'flex',
                        'align-items': 'center'
                    },

                ),

            ],
            style={
                    'margin-bottom': '0.8em',
                    'position': 'relative'  # Relative position for the column
            },
            width='auto'
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Top Recovered Service',
                           className='card-title',
                           style={'font-size': '12px', 'margin-bottom': '0em'}
                           ),
                    html.P(f'{top_service}',
                           className='card-text',
                           style=detail_text_style
                           ),
                    html.P(f'{recovery_percentage:.1f}%',
                           className='card-text',
                           style=value_text_style,
                           )
                ]),
                style={
                    'height': card_height,
                    'border-radius': '15px',  # Rounded corners
                    'padding': '0.1em',
                    'max-width': '220px'
                }
            ),
            style={'margin-bottom': '0.8em'},
            width='auto'
        ),
        dbc.Col(
        [
        # Parent container with position: relative for proper absolute positioning of the button
        html.Div(
            [
                # Button and tooltip
                html.Button('i', id='info-button3', className='info-button'),
                dbc.Tooltip(
                    html.Span([
                        'Comparison Dates:',
                        html.Br(),
                        'Lockdown Period (Mar 1-10, 2020),',
                        html.Br(),
                        'Post Lockdown Period (Oct 1-10, 2024)'
                    ]),
                    target='info-button3',
                    placement='top',
                )
            ],
            style={
                'position': 'absolute',  # Button is positioned absolutely within this relative container
                'top': '2px',
                'right': '15px',
                'z-index': '10'  # Ensure it appears above other elements
            }
        ),
        # Card container
        dbc.Card(
            dbc.CardBody([
                    html.P(
                        'Lockdown Period Avg. Ridership',
                        className='card-title',
                        style={
                            'margin-bottom': '0em',
                            'text-align': 'center',
                            'font-size': '12px'
                        }
                    ),
                    html.P(
                        f'{avg_lockdown_ridership}',
                        className='card-text',
                        style=value_text_style
                    ),
                ]
            ),
            style={
                'width': '180px',
                'height': card_height,
                'border-radius': '15px',  # Rounded corners
                'padding': '0.1em',
                'margin-bottom': '2em',
                'max-width': '150px',
                'position': 'relative'  # Relative position for the button to align properly
            },
        ),
        ],
        style={
        'margin-bottom': '0.8em',
        'position': 'relative'  # Relative position for the column
        },
        width='auto'
        ),
        dbc.Col(
        [
        # Parent container with position: relative for proper absolute positioning of the button
            html.Div(
                [
                    # Button and tooltip
                    html.Button('i', id='info-button4', className='info-button'),
                    dbc.Tooltip(
                        html.Span([
                            'Comparison Dates:',
                            html.Br(),
                            'Lockdown Period (Mar 1-10, 2020),',
                            html.Br(),
                            'Post Lockdown Period (Oct 1-10, 2024)'
                        ]),
                        target='info-button4',
                        placement='top',
                    )
                ],
                style={
                    'position': 'absolute',  # Button is positioned absolutely within this relative container
                    'top': '2px',
                    'right': '15px',
                    'z-index': '10'  # Ensure it appears above other elements
                }
            ),
            # Card container
            dbc.Card(
                dbc.CardBody([
                    html.P(
                        'Post Lockdown Avg. Ridership',
                        className='card-title',
                        style={
                            'margin-bottom': '0em',
                            'text-align': 'center',
                            'font-size': '12px'
                        }
                    ),
                    html.P(  # Correctly place this html.P
                        f'{avg_post_lockdown_ridership}',
                        className='card-text',
                        style=value_text_style
                    ),
                ]),
                style={
                    'width': '180px',
                    'height': card_height,
                    'border-radius': '15px',  # Rounded corners
                    'padding': '0.1em',
                    'margin-bottom': '2em',
                    'max-width': '150px',
                    'position': 'relative'  # Relative position for the button to align properly
                },
            ),
        ],
        style={
        'margin-bottom': '0.8em',
        'position': 'relative'  # Relative position for the column
        },
        width='auto'
        ),

        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.P('Year on Year Growth',
                           className='card-title',
                           style={'font-size': '12px', 'margin-bottom': '0em'}
                           ),
                    html.P(f'{yoy_growth:.1f}%',
                           className='card-text',
                           style=value_text_style
                           ),
                    html.P(html.Br(),
                           className='card-text',
                           style=detail_text_style,
                           )
                ]),
                style={
                    'height': card_height,
                    'border-radius': '15px',  # Rounded corners
                    'padding': '0.1em',
                    'max-width': '150px'
                }
            ),
            style={'margin-bottom': '0.8em'},
            width='auto'
        )
    ]

    return cards


def create_ridership_cards(granular_data: pd.DataFrame, selected_services: list, granularity: str, metrics: dict) -> go.Figure:

    logging.debug(f'Granular Data: {granular_data.head()}')
    logging.debug(f'Selected Services: {selected_services}')
    logging.debug(f'Metrics: {metrics}')

    card_height = '210px'
    up_arrow = chr(8593)  # Upward arrow (↑)
    down_arrow = chr(8595)  # Downward arrow (↓)
    cards = []

    # Trim services if needed
    trimmed_services = selected_services[:4] + [selected_services[5]] if len(
        selected_services) > 5 else selected_services

    for service in trimmed_services:
        ridership_last_period = metrics[service]['ridership_last_period']
        percent_change = metrics[service]['percent_change']

        # Set style based on change
        if percent_change > 0:
            card_text_style = {
                'font-size': '2em', 'font-weight': 'bold',
                'text-align': 'center', 'color': dark_blue
            }
            percent_change_style = {
                'margin-bottom': '0.2em', 'color': dark_blue}
            percent_change_text = f'% Change: {percent_change:.1f}% {up_arrow}'
        elif percent_change < 0:
            card_text_style = {
                'font-size': '2em', 'font-weight': 'bold',
                'text-align': 'center', 'color': dark_orange
            }
            percent_change_style = {
                'margin-bottom': '0.2em', 'color': dark_orange}
            percent_change_text = f'% Change: {percent_change:.1f}% {down_arrow}'
        else:
            card_text_style = {'font-size': '2em',
                               'font-weight': 'bold', 'text-align': 'center'}
            percent_change_style = {'margin-bottom': '0.2em'}
            percent_change_text = f'% Change: {percent_change:.1f}%'

        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.P(service, style={
                               'font-size': '17px', 'font-weight': '600', 'margin-bottom': '0em'}),
                        html.P(f'Avg {granularity}ly Ridership',
                               style={'margin-bottom': '0.2em'}),
                        html.P(ridership_last_period, style=card_text_style),
                        html.P(percent_change_text,
                               style=percent_change_style),
                        dcc.Graph(
                            id=f'{service.lower().replace(" ", "_").replace("-", "_")}_sparkline',
                            figure=create_sparkline(
                                granular_data, service, granularity, metrics),
                            config={'displayModeBar': False,
                                    'responsive': True},
                            style={
                                'height': '50px', 'width': '80%',
                                'margin': '0 auto'
                            }
                        ),
                    ]),
                    style={
                        'border-radius': '15px',
                        'flex-basis': '18%',  # Controls how the cards distribute
                        'height': card_height,
                        'padding': '0.1em',
                        'max-width': '200px',  # Explicit width
                        'width': 'auto'
                    }
                ),
                style={'margin-bottom': '0.2em'},
                width='auto'
            )
        )
    return cards


def create_service_line_chart(granular_data: pd.DataFrame, granularity: str, selected_services: list) -> go.Figure:
    '''
    Create a Plotly line chart for service data based on selected granularity.

    Args:
        granular_data: The resampled dataframe.
        granularity  : The selected granularity level.

    Returns:
        fig: A Plotly Graph Objects figure.
    '''
    if granularity == 'Year':
        granular_data['Year'] = granular_data['Year'].astype(str)
        x_axis_values = granular_data['Year']  # Use the 'Year' column directly
    else:
        x_axis_values = granular_data['Date']  # Use the 'Date' column directly

    if granularity == 'Year':
        formatted_labels = granular_data['Year']
    elif granularity == 'Quarter':
        formatted_labels = [
            f'{date.year}-Q{((date.month - 1) // 3) + 1}' for date in granular_data['Date']
        ]
    else:  # Month
        formatted_labels = [date.strftime('%Y-%b') for date in granular_data['Date']]

    max_labels = 12 if granularity == 'Month' else 8
    label_step = max(1, len(granular_data) // max_labels)

    if granularity == 'Year':
        x_axis_tickvals = granular_data['Year'][::label_step]
    else:
        x_axis_tickvals = granular_data['Date'][::label_step]

    x_axis_ticktext = [formatted_labels[i] for i in range(0, len(formatted_labels), label_step)]

    fig = go.Figure()
    # Create the chart for each service
    for service in selected_services:
        if service in granular_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=x_axis_values,
                    y=granular_data[service],
                    mode='lines',
                    name=service,
                    line=dict(color=service_colours[service]['colour']),
                    # Add full service name for tooltip
                    customdata=[service] * len(granular_data),
                    hovertemplate=(
                        # Show full service name
                        '<b>Service:</b> %{customdata}<br>'
                        '<b>Date:</b> %{x|%d %B %Y}<br>'  # Format date nicely
                        # Format ridership with commas
                        '<b>Ridership:</b> %{y:,.0f} (000\'s) <extra></extra>'
                    )
                )
            )

    # Set chart title and axis labels
    fig.update_layout(
        title=f'{granularity} Recovery Trends in Ridership by Time Period',
        xaxis_title=None,
        yaxis_title='Average Ridership (Thousands)',
        template='plotly_white',
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            )
        )
    )

    # Set the x-axis range manually to avoid squeezing the chart
    fig.update_xaxes(
        # Ensures the x-axis starts from the first date
        range=[granular_data['Date'].min(), granular_data['Date'].max()],
        showgrid=False, gridcolor='#F2F2F2',
        tickvals=x_axis_tickvals,
        ticktext=x_axis_ticktext
    )
    fig.update_yaxes(
        showgrid=False,
        gridcolor='#F2F2F2',
        tickformat=',0f',
    )

    if granularity == 'Month':
        # Add an annotation with indented text and no padding
        annotation_x1 = granular_data['Date'].iloc[0]
        # First service's initial value
        annotation_y1 = granular_data[selected_services[0]].iloc[0]
        # Corresponding y-value
        annotation_x2 = granular_data['Date'].iloc[2]  # Choose a later date
        # Use the last service's value
        annotation_y2 = granular_data[selected_services[-1]].iloc[2]

        fig.add_annotation(
            x=annotation_x1,  # x-coordinate from data (use actual value)
            y=annotation_y1,  # y-coordinate from data (use actual value)
            # Text to be displayed
            text='March 11, 2020<br>WHO Declared<br>Global Covid<br>Pandemic.',
            showarrow=True,  # Show an arrow from the annotation to the point
            arrowhead=7,  # Arrowhead size
            ax=40,  # x-coordinate of the arrow tail (relative to annotation)
            ay=-20,  # y-coordinate of the arrow tail (relative to annotation)
            font=dict(
                family='Arial',  # Font family
                size=12,  # Font size
                color='black'  # Font color
            ),
            align='left',  # Align the text to the left of the annotation point
            xanchor='left',  # Anchor the text to the left of the x-coordinate
            yanchor='bottom',  # Anchor the text in the middle of the y-coordinate
            bgcolor='white',  # Background color for text
            opacity=0.8,  # Opacity of the annotation text
        )

        fig.add_annotation(
            x=annotation_x2,  # x-coordinate from data (use actual value)
            y=annotation_y2,  # y-coordinate from data (use actual value)
            # Text to be displayed
            text='Monday, June 8, 2020<br>NYC Starts Phase 1<br>of Reopening Plan.',
            showarrow=True,  # Show an arrow from the annotation to the point
            arrowhead=7,  # Arrowhead size
            ax=130,  # x-coordinate of the arrow tail (relative to annotation)
            ay=-190,  # y-coordinate of the arrow tail (relative to annotation)
            font=dict(
                family='Arial',  # Font family
                size=12,  # Font size
                color='black'  # Font color
            ),
            align='left',  # Align the text to the right of the annotation point
            xanchor='left',  # Anchor the text to the right of the x-coordinate
            yanchor='bottom',  # Anchor the text in the top of the y-coordinate
            bgcolor='white',  # Background color for text
            opacity=0.8,  # Opacity of the annotation text
        )

    return fig


import plotly.graph_objects as go
import pandas as pd

def create_correlation_matrix(granular_data: pd.DataFrame, granularity) -> go.Figure:
    '''
    Creates a correlation matrix with a heatmap colouring.

    Args:
        granular_data: Aggregated DataFrame with recovery percentage columns and a time column.
        granularity  : The granularity level ('Month', 'Quarter', 'Year').

    Returns:
        fig:  Plotly Figure object with the heatmap.
    '''
    # Filter and process data based on granularity
    filtered_cols = [col for col in granular_data.columns if not any(
        p in col.lower() for p in ['% of pre-pandemic', '% pre-pandemic'])]
    df_filtered = granular_data[filtered_cols]

    # Calculate correlation
    if granularity == 'Year':
        df_filtered = df_filtered.iloc[:, 1:-1]
    else:
        df_filtered = df_filtered.iloc[:, 1:].corr().round(2)

    correlation_matrix = df_filtered.corr().round(2)
    min_value = correlation_matrix.min().min()

    # Create heatmap with Plotly (flip the z values to match the reversed y-axis)
    fig = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.values[::-1, :],  # Reverse the z values to align with the y-axis flip
            x=correlation_matrix.columns,
            y=correlation_matrix.index[::-1],  # Flip y-axis to get diagonal top-left to bottom-right
            colorscale='RdBu_r',  # Negative values are blue, positive values are red
            zmin=min_value,
            zmax=1,
            hoverinfo='text',
            showscale=False  # This turns off the color scale bar (legend)
        )
    )

    # Add annotations for each cell to dynamically set text color
    annotations = []
    for i, row in enumerate(correlation_matrix.index[::-1]):  # Reverse index to match heatmap
        for j, col in enumerate(correlation_matrix.columns):
            value = correlation_matrix.values[::-1, :][i][j]  # Reverse values accordingly

            # Set dynamic color based on value (blue cells need white text)
            text_color = 'white' if value < -0.5 or value > 0.7 else '#404040'
            display_value = f'{int(value)}' if value == 1 else f'{value:.2f}' # Format 1.00 as 1 like in other correlation matrices.
            annotations.append(
                dict(
                    x=col,
                    y=row,
                    text=f'{display_value}',
                    font=dict(
                        size=12,
                        color=text_color
                    ),
                    showarrow=False,
                    xref='x',
                    yref='y'
                )
            )

    # Update layout for the figure
    fig.update_layout(
        annotations=annotations,
        title=dict(
            text=f'Service Recovery Correlation ({granularity})',
            y=0.9255,  # Adjust this value to move the title
            x=0.5,
            xanchor='center',
            yanchor='top'
        ),
        height=500,
        margin=dict(t=100, l=10, r=10, b=10),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hoverlabel=dict(
            bgcolor='#0A1128',
            font=dict(
                color='#FFFFFF',
                size=14
            ),
        )
    )

    return fig


def create_dual_axis_chart(granular_data: pd.DataFrame, granularity: str, selected_services: list) -> go.Figure:
    '''
    Creates a dual axis chart showing the average recovery percentage by service accross all time periods.

    Args:
        granular_data    : Aggregated DataFrame with recovery percentage columns and a time column.
        granularity      : The granularity level ('Month', 'Quarter', 'Year').
        selected_services: The list of services selected from the services dropdown.

    Returns:
        fig: Plotly Figure object with the dual axis chart.
    '''

    if granularity == 'Year':
        granular_data['Year'] = granular_data['Year'].astype(str)
        x_axis_values = granular_data['Year']  # Use the 'Year' column directly
    else:
        x_axis_values = granular_data['Date']  # Use the 'Date' column directly


    if granularity == 'Year':
        granular_data['Year'] = granular_data['Year'].astype(str)
        x_axis_values = granular_data['Year']  # Use the 'Year' column directly
    else:
        x_axis_values = granular_data['Date']  # Use the 'Date' column directly

    if granularity == 'Year':
        formatted_labels = granular_data['Year']
    elif granularity == 'Quarter':
        formatted_labels = [
            f'{date.year}-Q{((date.month - 1) // 3) + 1}' for date in granular_data['Date']
        ]
    else:  # Month
        formatted_labels = [date.strftime('%Y-%b') for date in granular_data['Date']]

    max_labels = 12 if granularity == 'Month' else 8
    label_step = max(1, len(granular_data) // max_labels)

    if granularity == 'Year':
        x_axis_tickvals = granular_data['Year'][::label_step]
    else:
        x_axis_tickvals = granular_data['Date'][::label_step]

    x_axis_ticktext = [formatted_labels[i] for i in range(0, len(formatted_labels), label_step)]



    # Create the dual-axis chart
    fig = make_subplots(specs=[[{'secondary_y': True}]])

    for service in selected_services:
        fig.add_trace(
            go.Scatter(
                x=x_axis_values,
                y=granular_data[service],
                mode='lines',
                name=f'{service} Ridership',
                line=dict(color=service_colours[service]['colour']),
                # Add full service name for tooltip
                customdata=[service] * len(granular_data),
                hovertemplate=(
                    # Show full service name
                    '<b>Service:</b> %{customdata}<br>'
                    '<b>Date:</b> %{x|%d %B %Y}<br>'  # Format date nicely
                    # Format ridership with commas
                    '<b>Ridership:</b> %{y:,.0f} (000\'s)<extra></extra>'
                )
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
                line=dict(
                    color=service_colours[service]['tinted_colour'], dash='dot'),
                # Add full service name for tooltip
                customdata=[service] * len(granular_data),
                hovertemplate=(
                    # Show full service name
                    '<b>Service:</b> %{customdata}<br>'
                    '<b>Date:</b> %{x|%d %B %Y}<br>'  # Format date nicely
                    # Format ridership with commas
                    '<b>Recovery:</b> %{y:.0f}%<extra></extra>'
                )
            ),
            secondary_y=True
        )

    # Update axes titles
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        title='Ridership and Recovery Percentage by Service',
        xaxis_title=None,
        yaxis_title=None,
        xaxis=dict(automargin=True,
                   showgrid=False  # Hide gridlines for x-axis
                   ),
        yaxis2_title='% of Pre-Pandemic',
        margin=dict(l=50, r=50, b=50, t=50),
        template='plotly_white',
        legend=dict(
            orientation='v',  # Vertical orientation
            xanchor='right',  # Align right
            yanchor='top',   # Align top
            x=1.3,          # Adjust x-position to place it outside the chart
            y=1,           # Adjust y-position to align with the top of the chart
        ),
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            )
        ),
        yaxis2=dict(
            showgrid=False  # Hide gridlines for y-axis
        )
    )

    # Update axis ranges and layout
    fig.update_yaxes(title_text=None,
                     tickformat=',0f', secondary_y=False)
    fig.update_yaxes(title_text='Recovery Percentage (%)',
                     tickformat='.0f', secondary_y=True)

    fig.update_xaxes(
        tickvals=x_axis_tickvals,
        ticktext=x_axis_ticktext,
        #tickangle=45  # Optional: Angle for better readability
    )
    return fig


def create_recovery_bar_chart(mta_data: pd.DataFrame) -> go.Figure:
    '''
    Create a bar chart showing the average recovery percentage by service accross all time periods.

    Args:
        granular_data: Aggregated DataFrame with recovery percentage columns and a time column.

    Returns:
        fig: Plotly Figure object with the bar chart.
    '''

    baseline_period = (mta_data['Date'] < '2020-03-11')

    current_period = (mta_data['Date'].dt.year == 2024) & (
        mta_data['Date'].dt.month == 10) & (mta_data['Date'].dt.day < 11)

    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Select relevant columns: ridership data and pre-pandemic percentage columns
    services = [col.split(':')[0]
                for col in mta_data.columns if ': % of Pre-Pandemic' in col]

    # Calculate recovery for each service
    recovery_percentages = {}

    comments_dict = {
    service: (
        wrap_comment(
            'Access-A-Ride, providing transportation for people with disabilities, exceeded pre-pandemic levels at 124.6%, reflecting consistent need for accessible transportation.'
        ) if service == 'Access-A-Ride' else
        wrap_comment(
            'Bridges and Tunnels, Note: The upcoming congestion charge in January 2025 may lead to reduced usage of Bridges and Tunnels, as drivers may opt for public transportation.'
        ) if service == 'Bridges and Tunnels' else
        ''
    )
    for service in services
}

    for service in services:
        baseline_ridership = mta_data.loc[baseline_period, service].sum()
        current_ridership = mta_data.loc[current_period, service].sum()
        # Calculate recovery percentage for the service
        if baseline_ridership > 0:
            recovery_percentage = round(
                (current_ridership / baseline_ridership) * 100, 1)
        else:
            recovery_percentage = 0

        recovery_percentages[service] = recovery_percentage

   # Set the bar colours from the service_colours dictionary
    bar_colours = [service_colours[service]['colour'] for service in services]

    # Calculate the average recovery
    average_recovery = pd.Series(recovery_percentages).sort_values(ascending=True)
    aligned_services = average_recovery.index.tolist()
    #formatted_recovery = [f'{value:.1f}%' for value in average_recovery]
    # Assign Values to Customdata from dictionary
    comments = [comments_dict[service] for service in aligned_services]
    tooltip_customdata = [[service, comment] for service, comment in zip(aligned_services, comments)]

    # Create the horizontal bar chart
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=average_recovery,  # Recovery percentages on the x-axis
            y=aligned_services,  # Services on the y-axis
            # Add text labels for percentages with one decimal place
            text=average_recovery.round(1).astype(str) + '%',
            textposition='auto',
            marker=dict(color=bar_colours),  # Set bar color
            orientation='h',  # Horizontal orientation
            customdata=tooltip_customdata,  # Pass the 2D array with service names and comments
            hovertemplate=(
                '<b>Service:</b> %{customdata[0]}<br>'  # Show full service name
                '<b>Recovery:</b> %{x:.1f}%<br>'        # Format recovery percentage
                '%{customdata[1]}<extra></extra>'       # Comment (if exists)
            ),
        )
    )

    # Customize layout
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        title='MTA Service Recovery Since 2020',
        xaxis_title=None,  # 'Recovery Percentage (% of Pre-Pandemic)',
        yaxis_title=None,
        xaxis_tickformat='.0f',  # Ensure whole number format
        yaxis=dict(
            automargin=True,  # Adjusts margin to avoid overlap
            ticklabelposition='outside'  # Move labels outside for spacing
        ),
        xaxis=dict(
            showticklabels=False,  # Hides the y-axis tick labels
            showgrid=False         # Optionally hides the grid lines for the y-axis
        ),
        template='plotly_white',
        margin=dict(l=150),  # Increase left margin for better spacing
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14,           # Font size (optional)
            ),
            align='left',  # Align text to the left for readability
            namelength=-1  # Prevent truncating long labels
        ),
        annotations=[
            {
                'text': '<b>Metro-North</b> has shown the most complete recovery.',
                'x': 0.5,  # Center it horizontally with the title
                'y': 1.08,  # Position it above the chart
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {
                    'size': 12,
                    'color': 'grey'
                }
            }
        ]
    )
    return fig  # Return the chart figure


def create_recovery_heatmap(granular_data: pd.DataFrame, granularity: str) -> go.Figure:
    '''
    Create a heatmap of recovery ridership by service and time period.

    Args:
        granular_data: Aggregated DataFrame with ridership columns and a time column.
        granularity  : The granularity level ('Month', 'Quarter', 'Year').
    Returns:
        fig: Plotly Figure object with the heatmap.
    '''
    # Determine the time column based on granularity
    time_column = 'Year' if granularity == 'Year' else 'Date'

    # Pivot the data: Time in columns, services in rows
    heatmap_data = granular_data.melt(
        id_vars=[time_column],
        value_vars=services,
        var_name='Service',
        value_name='Recovery Ridership'
    )
    heatmap_pivot = heatmap_data.pivot(
        index='Service', columns=time_column, values='Recovery Ridership'
    )

    # Normalize each service's ridership to its own maximum
    normalized_heatmap_pivot = heatmap_pivot.apply(lambda x: (x / x.max()) * 100, axis=1).fillna(0)

    # Format x-axis labels based on granularity
    if granularity == 'Year':
        formatted_labels = [str(int(year)) for year in normalized_heatmap_pivot.columns]
    elif granularity == 'Quarter':
        formatted_labels = [
            f'{col.year}-Q{((col.month - 1) // 3) + 1}' for col in normalized_heatmap_pivot.columns
        ]
    else:  # Month
        formatted_labels = [col.strftime('%Y-%b') for col in normalized_heatmap_pivot.columns]

    # Handle axis label optimization for Month or Quarter
    max_labels = 12 if granularity == 'Month' else 8
    label_step = max(1, len(normalized_heatmap_pivot.columns) // max_labels)
    x_axis_tickvals = normalized_heatmap_pivot.columns[::label_step]
    x_axis_ticktext = [formatted_labels[i] for i in range(0, len(formatted_labels), label_step)]

    # Create the heatmap with normalized values
    fig = go.Figure(
        data=go.Heatmap(
            z=normalized_heatmap_pivot.values,
            x=normalized_heatmap_pivot.columns,
            y=normalized_heatmap_pivot.index,
            colorscale='RdBu',
            colorbar=dict(title='Recovery Percentage', len=0.5),
            zmin=0,  # Minimum percentage is 0%
            zmax=100 # Maximum percentage is 100%
        )
    )

    # Update layout for readability
    fig.update_layout(
        title=f'Ridership Recovery by Service and Time ({granularity})',
        xaxis=dict(
            title=None,
            tickmode='array',
            tickvals=x_axis_tickvals,
            ticktext=x_axis_ticktext,
            tickangle=45 if granularity in ['Month', 'Quarter'] else 0,  # Rotate for readability
            tickfont=dict(size=10 if granularity == 'Month' else 12)  # Adjust font size
        ),
        yaxis=dict(
            title=None,
        ),
        template='plotly_white',
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            )
        ),
        annotations=[
            {
                'text': 'Metro-North and LIRR took until October 2021 to recover more than 50% of Pre-Pandemic Levels',
                'x': 0.5,  # Center it horizontally with the title
                'y': 1.08,  # Position it above the chart
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {
                    'size': 12,
                    'color': 'grey'
                }
            }
        ]
    )

    return fig


def create_ridership_pie_chart(mta_data: pd.DataFrame) -> go.Figure:
    '''
    Create a ridership composition pie chart comparing pre- and post-pandemic periods.

    Args:
        mta_data: DataFrame with ridership values by service and time.

    Returns:
        fig: Plotly Figure object with the pie charts.
    '''

    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Identify ridership columns
    ridership_cols = [
        col for col in mta_data.columns if ': % of Pre-Pandemic' not in col and col != 'Date']

    # Filter the dataset to the pre- and post-pandemic date ranges
    pre_pandemic_data = mta_data[mta_data['Date'] < '2020-03-11']
    post_pandemic_data = mta_data[
        (mta_data['Date'].dt.year == 2024) &
        (mta_data['Date'].dt.month == 10) &
        (mta_data['Date'].dt.day < 11)
    ]

    # Sum ridership values for pre- and post-pandemic periods
    pre_pandemic_totals = pre_pandemic_data[ridership_cols].sum()
    post_pandemic_totals = post_pandemic_data[ridership_cols].sum()

    # Compute the total ridership for both periods
    total_pre_pandemic = pre_pandemic_totals.sum()
    total_post_pandemic = post_pandemic_totals.sum()

    # Set the bar colours from the service_colours dictionary
    slice_colours = [service_colours[service]['colour']
                     for service in services]
    # Create a figure
    fig = go.Figure()
    chart_type = 'Pre-Pandemic'
    # Add pre-pandemic pie chart
    fig.add_trace(
        go.Pie(
            labels=pre_pandemic_totals.index,
            values=pre_pandemic_totals.values,
            name=chart_type,
            hole=0.60,
            sort=True,
            direction='clockwise',
            marker=dict(colors=slice_colours),
            hoverinfo='skip',  # Skip default hover info to use hovertemplate
            hovertemplate=(
                f'<b>Chart Type:</b> {chart_type}<br>'  # Add chart type to tooltip
                '<b>Service:</b> %{label}<br>'         # Service name
                '<b>Ridership:</b> %{value:,}<br>'     # Ridership value with commas
                '<b>Percentage:</b> %{percent:.1%}<extra></extra>'  # Percentage
            )
        )
    )

    # Add post-pandemic pie chart

    chart_type = 'Post-Pandemic'
    fig.add_trace(
        go.Pie(
            labels=post_pandemic_totals.index,
            values=post_pandemic_totals.values,
            name=chart_type,
            hole=0.60,
            sort=True,
            direction='clockwise',
            marker=dict(colors=slice_colours),
            hoverinfo='skip',  # Skip default hover info to use hovertemplate
            hovertemplate=(
                f'<b>Chart Type:</b> {chart_type}<br>'  # Add chart type to tooltip
                '<b>Service:</b> %{label}<br>'         # Service name
                '<b>Ridership:</b> %{value:,}<br>'     # Ridership value with commas
                '<b>Percentage:</b> %{percent:.1%}<extra></extra>'  # Percentage
            )
        )
    )
    # Initially show only pre-pandemic chart
    fig.data[1].visible = False

    # Define annotations for the total ridership values
    pre_pandemic_annotation = dict(
        text=f'<b>{total_pre_pandemic:,.0f}</b>',
        x=0.5,
        y=0.5,
        font=dict(size=24, color='black'),
        showarrow=False
    )
    post_pandemic_annotation = dict(
        text=f'<b>{total_post_pandemic:,.0f}</b>',
        x=0.5,
        y=0.5,
        font=dict(size=24, color='black'),
        showarrow=False
    )

    # Add toggle buttons for annotations and pie chart visibility
    fig.update_layout(
        title=dict(
            text='Ridership Composition', # Chart title text
            x=0,                     # Align to the left
            xanchor='left',          # Anchor the title to the left
            font=dict(size=16)       # Optional: Adjust font size or style
        ),
        width=600,
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=75, b=0, l=0, r=0),
        legend=dict(
            orientation='h',      # Horizontal legend
            traceorder='normal',
            yanchor='top',        # Align the top of the legend box
            # Position the legend below the chart (-0.1 moves it slightly below)
            y=-0.1,
            xanchor='center',     # Align the center of the legend box
            x=0.5,                # Position the legend at the center of the chart horizontally
            font=dict(size=10),
        ),
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            ),
        ),
        updatemenus=[
            dict(
                type='buttons',
                direction='down',
                buttons=[
                    dict(
                        label='Pre-Pandemic',
                        method='update',
                        args=[
                            {'visible': [True, False]},  # Pie visibility
                            # Annotation for pre-pandemic
                            {'annotations': [pre_pandemic_annotation,
                                             {
                                                 # Additional note below the chart
                                                 'text': 'The shift in ridership share highlights evolving commuting patterns post-pandemic.',
                                                 'x': 0.5,  # Center it below the chart
                                                 'y': -0.1,  # Position it below the pie chart
                                                 'xref': 'paper',
                                                 'yref': 'paper',
                                                 'showarrow': False,
                                                 'font': {
                                                     'size': 12,
                                                     'color': 'grey'
                                                 },
                                                 'align': 'center'
                                             }
                                             ]
                             }
                        ]
                    ),
                    dict(
                        label='Post-Pandemic',
                        method='update',
                        args=[
                            {'visible': [False, True]},  # Pie visibility
                            # Annotation for post-pandemic
                            {'annotations': [post_pandemic_annotation,
                                             {
                                                 # Additional note below the chart
                                                 'text': 'The shift in ridership share highlights evolving commuting patterns post-pandemic.',
                                                 'x': 0.5,  # Center it below the chart
                                                 'y': -0.1,  # Position it below the pie chart
                                                 'xref': 'paper',
                                                 'yref': 'paper',
                                                 'showarrow': False,
                                                 'font': {
                                                     'size': 12,
                                                     'color': 'grey'
                                                 },
                                                 'align': 'center'
                                             }
                                             ]
                             }
                        ]
                    )
                ],
                showactive=True,
                x=0.1,
                y=1.1,
            )
        ],
        # Start with pre-pandemic annotation
        annotations=[
            pre_pandemic_annotation,
            {
                # Additional note below the chart
                'text': 'The shift in ridership share highlights evolving commuting patterns post-pandemic.',
                'x': 0.5,  # Center it below the chart
                'y': -0.1,  # Position it below the pie chart
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {
                    'size': 12,
                    'color': 'grey'
                },
                'align': 'center'
            }
        ],
        template='plotly_white',
    )

    return fig


def create_ridership_scatterplot(mta_data: pd.DataFrame, selected_services: list) -> go.Figure:
    '''
    Create a scatter plot with trendlines for selected services to visualise their recovery trajectories.

    Args:
        mta_data: DataFrame with ridership values by service and time.
        selected_services: List of service names to plot (e.g., ['Subways', 'Buses', 'LIRR']).

    Returns:
        fig: Plotly Figure object with scatter plots and trendlines for the selected services.
    '''
    # Create a figure
    fig = go.Figure()

    # Loop through the selected services
    for service in selected_services:
        # Filter the data for the selected service
        service_data = mta_data[['Date', service]].dropna()

        # Perform linear regression for the trendline
        # Convert dates to ordinal numbers for regression
        x = service_data['Date'].map(pd.Timestamp.toordinal)
        y = service_data[service]
        slope, intercept, r_value, p_value, std_err = linregress(x, y)

        # Calculate the trendline
        trendline_y = slope * x + intercept

        # Scatter plot for the selected service's ridership
        fig.add_trace(
            go.Scatter(
                x=service_data['Date'],
                y=service_data[service],
                mode='markers',
                name=f'{service} Ridership',
                marker=dict(
                    size=6,
                    color=service_colours[service]['colour'],
                ),
                showlegend=True,

                # Add full service name for tooltip
                customdata=[service] * len(mta_data),
                hovertemplate=(
                    # Show full service name
                    '<b>Service:</b> %{customdata}<br>'
                    # Format date nicely
                    '<b>Date:</b> %{x|%d %B %Y}<br>'
                    # Format ridership with commas
                    '<b>Ridership:</b> %{y:,.0f}<extra></extra>'
                )
            )
        )

        # Add the trendline for the selected service
        fig.add_trace(
            go.Scatter(
                x=service_data['Date'],
                y=trendline_y,
                mode='lines',
                name=f'{service} Trendline',
                line=dict(
                    dash='dash',
                    color=service_colours[service]['tinted_colour']),
                showlegend=True
            )
        )

    # Customize the layout
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        title='Ridership Recovery Trajectories for Selected Services',
        xaxis_title=None,
        yaxis_title=None,
        template='plotly_white',
        margin=dict(
            r=150,  # Increase the right margin to accommodate the legend
            l=50,   # Left margin (if necessary)
            t=50,   # Top margin (if necessary)
            b=50    # Bottom margin (if necessary)
        ),
        legend=dict(
            orientation='v',   # Vertical legend to save space
            yanchor='top',     # Position legend at the top of the plot
            # Place the legend slightly outside the plot (adjustable)
            y=0.9,
            xanchor='right',   # Align legend to the right of the plot
            x=1.25,
        ),
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            ),
        ),
        xaxis=dict(
            showgrid=False  # Hide gridlines for x-axis
        ),
    )

    return fig


def create_before_after_chart(mta_data: pd.DataFrame, services: list) -> go.Figure:
    '''
    Create a side-by-side bar chart comparing ridership pre-pandemic vs. post-pandemic,
    sorted by descending pre-pandemic ridership.

    Args:
        mta_data: DataFrame containing ridership data.
        services: List of selected services to include in the comparison.

    Returns:
        fig: Plotly Figure object.
    '''
    # Convert dates to datetime for filtering
    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Filter for pre-pandemic and post-pandemic date ranges
    pre_pandemic_data = mta_data[mta_data['Date'] < '2020-03-11']
    post_pandemic_data = mta_data[
        (mta_data['Date'].dt.year == 2024) &
        (mta_data['Date'].dt.month == 10) &
        (mta_data['Date'].dt.day < 11)
    ]
    # Aggregate data by service
    pre_pandemic_totals = pre_pandemic_data[services].sum()
    post_pandemic_totals = post_pandemic_data[services].sum()

    # Combine totals into a DataFrame
    totals_df = pd.DataFrame({
        'Service': services,
        'Post-Pandemic': post_pandemic_totals,
        'Pre-Pandemic': pre_pandemic_totals
    })

    # Store the first service before sorting for the legend (always Subways)
    first_service = totals_df.sort_values(by='Pre-Pandemic', ascending=False).iloc[0]['Service']

    # Sort totals_df in ascending order for proper bar chart display
    totals_df = totals_df.sort_values(by='Pre-Pandemic', ascending=True)

    # Extract sorted services and values
    sorted_services = totals_df['Service']
    sorted_pre_pandemic = totals_df['Pre-Pandemic']
    sorted_post_pandemic = totals_df['Post-Pandemic']

    # Use colours for the legend based on the first service (Subways)
    pre_legend_color = service_colours[first_service]['tinted_colour']
    post_legend_color = service_colours[first_service]['colour']

    # Colours for the bars
    before_bar_colours = [service_colours[service]['tinted_colour'] for service in sorted_services]
    after_bar_colours = [service_colours[service]['colour'] for service in sorted_services]

    # Create the figure
    fig = go.Figure()

    # Add post-pandemic bars
    fig.add_trace(
        go.Bar(
            y=sorted_services,
            x=[value / 1_000_000 for value in sorted_post_pandemic],
            orientation='h',
            name='Post-Pandemic',
            marker=dict(color=after_bar_colours),
            customdata=sorted_services,
            text=[f'{value / 1_000_000:.1f}M' for value in sorted_post_pandemic],
            textposition='outside',
            hovertemplate=(
                'Post-Pandemic<br>'
                '<b>Service:</b> %{customdata}<br>'
                '<b>Ridership:</b> %{x:.1f}M<extra></extra>'
            ),
            showlegend=False  # Hide legend for actual data trace
        )
    )

    # Add pre-pandemic bars
    fig.add_trace(
        go.Bar(
            y=sorted_services,
            x=[value / 1_000_000 for value in sorted_pre_pandemic],
            orientation='h',
            name='Pre-Pandemic',
            marker=dict(color=before_bar_colours),
            customdata=sorted_services,
            text=[f'{value / 1_000_000:.1f}M' for value in sorted_pre_pandemic],
            textposition='outside',
            hovertemplate=(
                'Pre-Pandemic<br>'
                '<b>Service:</b> %{customdata}<br>'
                '<b>Ridership:</b> %{x:.1f}M<extra></extra>'
            ),
            showlegend=False  # Hide legend for actual data trace
        )
    )

    # Add dummy traces for legend
    fig.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            name='Pre-Pandemic',
            marker=dict(color=pre_legend_color),
            showlegend=True
        )
    )

    fig.add_trace(
        go.Bar(
            x=[None],
            y=[None],
            name='Post-Pandemic',
            marker=dict(color=post_legend_color),
            showlegend=True
        )
    )

    # Update layout
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        title=dict(
            text='Service Ridership Comparison: Pre-Pandemic vs. Post-Pandemic',
            x=0,
            xanchor='left',
            font=dict(size=16)
        ),
        barmode='group',
        template='plotly_white',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='center',
            x=0.5
        ),
        hoverlabel=dict(
            bgcolor='#0A1128',
            font=dict(color='#FFFFFF', size=14)
        ),
        margin=dict(l=0, r=20, t=80, b=50),
        xaxis=dict(
            showticklabels=False,  # Hide tick labels
            showgrid=False,        # Hide grid lines
            title=None             # Remove the axis title
        ),
    )

    return fig


def create_daily_variability_boxplot(mta_data: pd.DataFrame, services: list, start_date: str, end_date: str) -> go.Figure:
    '''
    Create a box plot to visualise daily ridership variability for selected services
    over a specified time range.

    Args:
        mta_data: DataFrame containing ridership data.
        services: List of selected services to include in the box plot.
        start_date: Start of the user-selected time range (inclusive).
        end_date: End of the user-selected time range (inclusive).

    Returns:
        fig: Plotly Figure object with the box plot.
    '''
    # Convert dates to datetime for filtering
    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Filter the data for the user-selected time range
    filtered_data = mta_data[
        (mta_data['Date'] >= pd.to_datetime(start_date)) &
        (mta_data['Date'] <= pd.to_datetime(end_date))
    ]

    # Create a figure
    fig = go.Figure()

    # Add a box plot for each selected service
    for service in services:
        fig.add_trace(
            go.Box(
                y=filtered_data[service],
                name=service,
                boxmean='sd',  # Show mean and standard deviation
                marker_color=service_colours[service]['colour'],
                line=dict(width=1),
            )
        )

    # Update layout
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for plot area
        # Transparent background for whole figure
        paper_bgcolor='rgba(0,0,0,0)',
        title=f'Daily Ridership Variability by Service ({start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")})',
        yaxis_title='Ridership',
        xaxis_title=None,
        template='plotly_white',
        showlegend=False,
        height=600,
        hoverlabel=dict(
            bgcolor='#0A1128',  # Background colour
            font=dict(
                color='#FFFFFF',  # Text colour
                size=14           # Font size (optional)
            )
        ),  # Adjust height to avoid scrollbars
    )

    return fig


def create_comparison_table(mta_data: pd.DataFrame) -> dbc.Table:
    '''
    Create a dbc.Table visual for ridership comparison metrics.

    Args:
        mta_data: DataFrame with ridership values by service and time.

    Returns:
        display_table: dbc.Table object for display.
    '''
    # Prepare the comparison table data
    comparison_table = prepare_comparison_table(mta_data)

    # Generate table header
    header = [html.Th(col) for col in comparison_table.columns]

    # Generate table rows
    rows = [
        html.Tr([html.Td(value) for value in row])
        for row in comparison_table.itertuples(index=False, name=None)
    ]

    # Create the dbc.Table
    display_table = dbc.Table(
        # Table content
        children=[
            html.Thead(html.Tr(header)),
            html.Tbody(rows)
        ],
        bordered=True,
        striped=False,
        hover=True,
        responsive=True,
        className='table-sm',  # Smaller font and padding for compact display
    )

    return display_table
