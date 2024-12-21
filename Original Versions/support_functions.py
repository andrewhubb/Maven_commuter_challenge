import pandas as pd
import numpy as np
import matplotlib as plt  # For testing forecasting - to be removed
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import socket  # For finding next free port
from config import (
    services,
    dark_blue,
    dark_orange
)
from typing import Tuple


def calculate_baseline_ridership(mta_data: pd.DataFrame, ridership_cols: list, baseline_period: pd.Series) -> float:
    """
    Calculate the baseline ridership based on actual ridership columns.

    Args:
        mta_data (pd.DataFrame)    : DataFrame containing ridership data.
        baseline_period (pd.Series): Series of dates

    Returns:
        float: The total baseline ridership.
    """
    # Convert Date to datetime if not already
    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Calculate total baseline ridership
    baseline_ridership = mta_data.loc[baseline_period,
                                      ridership_cols].sum().sum()

    return baseline_ridership


def calculate_current_ridership(mta_data: pd.DataFrame, ridership_cols: list, current_period: pd.Series) -> float:
    """
    Calculate the current ridership for the same period (e.g., March 2023).

    Args:
        mta_data (pd.DataFrame): DataFrame containing ridership data.

    Returns:
        float: The total current ridership.
    """

    # Calculate total current ridership for March 2024
    current_ridership = mta_data.loc[current_period,
                                     ridership_cols].sum().sum()

    return current_ridership


def calculate_total_recovery(mta_data: pd.DataFrame, ridership_cols) -> float:
    """
    Calculate total ridership recovery as a percentage of pre-pandemic levels (comparing March 2023 with March 2020).

    Args:
        mta_data (pd.DataFrame): The DataFrame containing ridership data.

    Returns:
        float: The total recovery percentage.
    """
    # Define baseline period: dates < 11/03/2020
    baseline_period = (mta_data['Date'] < '2020-03-11')
    
    current_period = (mta_data['Date'].dt.year == 2024) & (
        mta_data['Date'].dt.month == 10) & (mta_data['Date'].dt.day < 11)
        
    baseline_ridership = calculate_baseline_ridership(
        mta_data, ridership_cols, baseline_period)
    current_ridership = calculate_current_ridership(
        mta_data, ridership_cols, current_period)

    # Calculate total recovery percentage
    total_recovery = (current_ridership / baseline_ridership) * \
        100 if baseline_ridership > 0 else 0

    return total_recovery


def calculate_top_service_recovery(mta_data: pd.DataFrame, baseline_period: pd.Series, current_period: pd.Series) -> Tuple[str, float]:
    """
    Calculate the top-performing service based on recovery percentage.

    Args:
        mta_data (pd.DataFrame)    : DataFrame containing ridership data with service columns.
        baseline_period (pd.Series): baseline period        
        current_period (pd.Series) : current_perid        

    Returns:
        Tuple[str, float]  The top-performing service based on recovery percentage and the top-performing service recovery percentage
    """
    # Convert 'Date' to datetime format
    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Select relevant columns: ridership data and pre-pandemic percentage columns
    services = [col.split(':')[0]
                for col in mta_data.columns if ': % of Pre-Pandemic' in col]

    # Calculate recovery for each service
    recovery_percentages = {}

    for service in services:
        # Get ridership for the current period and baseline period
        baseline_ridership = mta_data.loc[baseline_period, service].sum()
        current_ridership = mta_data.loc[current_period, service].sum()

        # Calculate recovery percentage for the service
        if baseline_ridership > 0:
            recovery_percentage = (current_ridership /
                                   baseline_ridership) * 100
        else:
            recovery_percentage = 0

        recovery_percentages[service] = recovery_percentage

    # Identify the top-performing service based on the highest recovery percentage
    top_service = max(recovery_percentages, key=recovery_percentages.get)

    return top_service, recovery_percentages[top_service]


def create_thousand_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Divides the ridership value by 1,000 to make the numbers easier to read

    Args:
    df: The dataframe to process

    Returns:
    pd.DataFrame: The dataframe with the adjusted figures
    """

    df_thousands = df.copy()
    columns_to_divide = [
        'Subways',
        'Buses',
        'LIRR',
        'Metro-North',
        'Access-A-Ride',
        'Bridges and Tunnels',
        'Staten Island Railway'
    ]
    # Perform the division and update only those columns
    df_thousands[columns_to_divide] = round(
        df[columns_to_divide] / 1_000, 0)  # Removed dividing by 1_000
    return df_thousands


def resample_data(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    """
    Resample the dataframe to the selected granularity.

    Args:
        df         : The dataframe to resample (must have a DatetimeIndex)
        granularity: The level of detail to use

    Returns:
        pd.DataFrame: The dataframe resampled to the specified granularity
    """
    # Check if the DataFrame index is a DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError('The DataFrame must have a DatetimeIndex to resample.')

    granularity_freq_mapping = {
        'Day': None,
        'Week': 'W',
        'Month': 'ME',
        'Quarter': 'QE',
        'Year': 'YE'
    }
    granularity_freq = granularity_freq_mapping.get(granularity, 'ME')
    # Convert DataFrame to string and write it to the file
    # Resample the data based on the granularity frequency
    # Resample and aggregate data using mean
    resampled_df = df.resample(granularity_freq).mean()
    # Round the resampled data before converting to integer
    resampled_df = resampled_df.round().astype(int)
    resampled_df.reset_index(inplace=True)

    if granularity == 'Year':
        resampled_df['Year'] = resampled_df['Date'].dt.year

    return resampled_df


def find_free_port(start_port=8700, max_port=8800) -> int:
    """   
    Finds the next available port starting from `start_port` up to `max_port`.    

    Args:
    start_port: the start of the port range. Default: 8700
    end_port  : the end of the port range. Default: 8800

    Returns:
    int: The next available port in the range

    Raises:
    RuntimeError: If no free ports are available in the specified range.
    """
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))  # Try binding to the port
                return port
            except OSError:
                continue  # Port is in use, try the next one
    raise RuntimeError('No free ports available in the specified range.')


def create_metrics(granular_data: pd.DataFrame, selected_services: list) -> dict:
    """
    Resample the dataframe to the selected granularity.

    Args:
        granular_data    : The selected granularity dataframe
        selected_services: The level of detail to use

    Returns:
        dict: The dictionary containing the metrics to store
    """
    # Metrics Calculation
    metrics = {}
    for service in selected_services:
        # Extract last and second-last periods for the service
        last_period_value = granular_data[service].iloc[-1]
        previous_period_value = granular_data[service].iloc[-2]
        if last_period_value > 1_000:
            ridership_last_period = '{:0.1f}M'.format(
                round(last_period_value/1_000, 1))
        else:
            ridership_last_period = '{:,}K'.format(int(last_period_value))
        percent_change = round(
            ((last_period_value - previous_period_value) / previous_period_value) * 100, 2)

        # Store metrics in the dictionary
        metrics[service] = {
            'ridership_last_period': ridership_last_period,
            'percent_change': percent_change
        }
    return metrics


def find_highest_ridership_day(df: pd.DataFrame) -> Tuple[str, str]:
    """
    Calculates the day with the highest ridership and the number of riders

    Args:
        df         : The dataframe to use for calculating 
        granularity: The level of detail to use

    Returns:
        Tuple [str, str]: the highest ridership day, and the total ridership
    """
# Define the post-pandemic start date
    post_pandemic_start = pd.Timestamp('2020-03-01')

    # Filter data to only include post-pandemic dates
    post_pandemic_data = df[df['Date'] >= post_pandemic_start]

    # Calculate total ridership across all services
    post_pandemic_data['Total_Ridership'] = post_pandemic_data[services].sum(
        axis=1)

    # Find the row with the highest total ridership
    highest_ridership = post_pandemic_data.loc[post_pandemic_data['Total_Ridership'].idxmax(
    )]
    highest_ridership_day = highest_ridership['Date'].strftime('%d %b %Y')
    total_ridership = f'{
        highest_ridership['Total_Ridership'] // 1_000_000:.1f}M'

    return highest_ridership_day, total_ridership


def calculate_yoy_growth(mta_data: pd.DataFrame, baseline_period: pd.Series, current_period: pd.Series, ridership_cols: list) -> float:
    """
    Calculate Year-on-Year growth for the latest period.

    Args:
        mta_data (pd.DataFrame)    : DataFrame containing ridership data.
        baseline_period (pd.Series): Boolean mask for the baseline period (e.g., October 2023).
        current_period (pd.Series) : Boolean mask for the current period (e.g., October 2024).
        ridership_cols (list)      : List of columns containing ridership values

    Returns:
        float: The YoY growth rate as a percentage.
    """

    # Calculate total ridership for the baseline period
    baseline_ridership = calculate_baseline_ridership(
        mta_data, ridership_cols, baseline_period)

    # Calculate total ridership for the current period
    current_ridership = calculate_current_ridership(
        mta_data, ridership_cols, current_period)

    # Calculate YoY growth percentage
    if baseline_ridership > 0:
        yoy_growth = ((current_ridership - baseline_ridership) /
                      baseline_ridership) * 100
    else:
        yoy_growth = 0  # Handle cases with no baseline ridership

    return yoy_growth


def prepare_comparison_table(mta_data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a comparison table for ridership metrics.

    Args:
        mta_data: DataFrame with ridership values by service and time.

    Returns:
        comparison_table: DataFrame with comparison metrics.
    """
    # Convert Date to datetime
    mta_data['Date'] = pd.to_datetime(mta_data['Date'])

    # Define time ranges
    pre_pandemic_range = mta_data[mta_data['Date'] < '2020-03-11']    
    first_post_pandemic_range = mta_data[(mta_data['Date'].dt.year == 2021) & (
        mta_data['Date'].dt.month == 10) & (mta_data['Date'].dt.day < 11)]
    current_year_range = mta_data[(mta_data['Date'].dt.year == 2024) & (
        mta_data['Date'].dt.month == 10) & (mta_data['Date'].dt.day < 11)]
    
    # Identify ridership columns
    ridership_cols = [
        col for col in mta_data.columns if ': % of Pre-Pandemic' not in col and col != 'Date']

    # Summarise data for ridership metrics
    pre_pandemic_totals = pre_pandemic_range[ridership_cols].sum()
    first_post_pandemic_totals = first_post_pandemic_range[ridership_cols].sum(
    )
    current_year_totals = current_year_range[ridership_cols].sum()

    # Calculate % of Pre-Pandemic as averages
    pre_pandemic_averages = pre_pandemic_range[ridership_cols].mean()
    post_pandemic_averages = first_post_pandemic_range[ridership_cols].mean()
    current_year_averages = current_year_range[ridership_cols].mean()

    post_pandemic_percentage = (
        post_pandemic_averages / pre_pandemic_averages) * 100
    current_year_percentage = (
        current_year_averages / pre_pandemic_averages) * 100

    # Create a comparison table
    comparison_table = pd.DataFrame({
        'Service': ridership_cols,
        'Pre-Pandemic': pre_pandemic_totals.values,
        'First Post-Pandemic Year': first_post_pandemic_totals.values,
        'Current Year': current_year_totals.values,
        '% of Pre-Pandemic (Post)': post_pandemic_percentage.values,
        '% of Pre-Pandemic (Current)': current_year_percentage.values,
    })

    expected_columns = ['Pre-Pandemic', 'First Post-Pandemic Year', 'Current Year',
                        '% of Pre-Pandemic (Post)', '% of Pre-Pandemic (Current)']
    missing_columns = [
        col for col in expected_columns if col not in comparison_table.columns]

    if missing_columns:
        raise ValueError(f"The following expected columns are missing: {
                         missing_columns}")

    # Format the table
    # Format numeric columns with commas and round percentages
    comparison_table['Pre-Pandemic'] = comparison_table['Pre-Pandemic'].map(
        '{:,.0f}'.format)
    comparison_table['First Post-Pandemic Year'] = comparison_table['First Post-Pandemic Year'].map(
        '{:,.0f}'.format)
    comparison_table['Current Year'] = comparison_table['Current Year'].map(
        '{:,.0f}'.format)

    # Format percentage columns with 1 decimal place
    comparison_table['% of Pre-Pandemic (Post)'] = comparison_table['% of Pre-Pandemic (Post)'].map(
        '{:.1f}%'.format)
    comparison_table['% of Pre-Pandemic (Current)'] = comparison_table['% of Pre-Pandemic (Current)'].map(
        '{:.1f}%'.format)

    return comparison_table


def create_average_rideships(mta_data: pd.DataFrame) -> Tuple[str, str]:
    """
    Calculates the average rideships for lockdown and post lockdown periods

    Args:
        mta_data: DataFrame with ridership values by service and time.

    Returns:
        Tuple[str, str]: the formatted ridership values
    """
    lockdown_start = '2020-03-11'
    lockdown_end = '2020-06-08'  # Last day of lockdown
    post_lockdown_start = '2020-06-09'  # First day of post-lockdown
    ridership_cols = [
        col for col in mta_data.columns if ': % of Pre-Pandemic' not in col and col != 'Date']

    # Convert 'Date' column to datetime if not already
    mta_data['Date'] = pd.to_datetime(mta_data['Date'])

    # Filter the data
    lockdown_data = mta_data[(mta_data['Date'] >= lockdown_start) & (
        mta_data['Date'] <= lockdown_end)]
    post_lockdown_data = mta_data[mta_data['Date'] >= post_lockdown_start]

    # Identify ridership columns
    ridership_cols = [
        col for col in mta_data.columns if ': % of Pre-Pandemic' not in col and col != 'Date']

    # Calculate averages
    average_ridership_lockdown = f'{
        lockdown_data[ridership_cols].sum(axis=1).mean():,.0f}'
    average_ridership_post_lockdown = f'{
        post_lockdown_data[ridership_cols].sum(axis=1).mean():,.0f}'

    return average_ridership_lockdown, average_ridership_post_lockdown


def create_kpis(mta_data: pd.DataFrame) -> dict:
    """
    Creates the dictionary of KPIs for storing for later use.

    Args: 
        mta_data: The complete MTA DataFrame with recovery percentage columns and a time column.

    Returns: 
        Figure: Plotly Figure object with the dual axis chart.
    """
    ridership_cols = [
        col for col in mta_data.columns if ': % of Pre-Pandemic' not in col and col != 'Date']

    # Metrics Calculations
    highest_ridership_day, total_ridership = find_highest_ridership_day(
        mta_data)
    total_recovery = f'{calculate_total_recovery(
        mta_data, ridership_cols):.1f}%'

    baseline_period = (mta_data['Date'] < '2020-03-11')    
    current_period = (mta_data['Date'].dt.year == 2024) & (
        mta_data['Date'].dt.month == 10) & (mta_data['Date'].dt.day < 11)    
    top_service, recovery_percentage = calculate_top_service_recovery(
        mta_data, baseline_period, current_period)

    baseline_period = (mta_data['Date'].dt.year == 2023) & (
        mta_data['Date'].dt.month == 10)
    current_period = (mta_data['Date'].dt.year == 2024) & (
        mta_data['Date'].dt.month == 10)

    yoy_growth = calculate_yoy_growth(
        mta_data, baseline_period, current_period, ridership_cols)

    average_ridership_lockdown, average_ridership_post_lockdown = create_average_rideships(
        mta_data)
    kpis = {
        'total_ridership': total_ridership,
        'highest_ridership_day': highest_ridership_day,
        'total_recovery': total_recovery,
        'top_service': top_service,
        'recovery_percentage': recovery_percentage,
        'yoy_growth': yoy_growth,
        'avg_lockdown_ridership': average_ridership_lockdown,
        'avg_post_lockdown_ridership': average_ridership_post_lockdown
    }
    return kpis
