import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import socket #For finding next free port
from config import (
    services,
    full_colours,
    colours,
    colours_pct,
    dark_blue,
    dark_orange
)



def calculate_baseline_ridership(mta_data: pd.DataFrame, ridership_cols: list) -> float:
    """
    Calculate the baseline ridership based on actual ridership columns.

    Args:
        mta_data (pd.DataFrame): DataFrame containing ridership data.

    Returns:
        float: The total baseline ridership.
    """
    # Convert Date to datetime if not already
    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')
    
    
    # Define baseline period: dates < 11/03/2020
    baseline_period = (mta_data['Date'] < '2020-03-11')
    print(f"Baseline Period True Count: {baseline_period.sum()}")  # Debugging step
    
    # Calculate total baseline ridership
    baseline_ridership = mta_data.loc[baseline_period, ridership_cols].sum().sum()
    
    return baseline_ridership

  
def calculate_current_ridership(mta_data: pd.DataFrame, ridership_cols: list) -> float:
    """
    Calculate the current ridership for the same period (e.g., March 2023).
    
    Args:
        mta_data (pd.DataFrame): DataFrame containing ridership data.
    
    Returns:
        float: The total current ridership.
    """
    # Define current period: 1 March 2024 to 10 March 2024
    current_period = (mta_data['Date'].dt.year == 2024) & (mta_data['Date'].dt.month == 3) & (mta_data['Date'].dt.day < 11)
    # Calculate total current ridership for March 2024
    current_ridership = mta_data.loc[current_period, ridership_cols].sum().sum()
    
    return current_ridership

def calculate_total_recovery(mta_data: pd.DataFrame) -> float:
    """
    Calculate total ridership recovery as a percentage of pre-pandemic levels (comparing March 2023 with March 2020).
    
    Args:
        mta_data (pd.DataFrame): The DataFrame containing ridership data.
    
    Returns:
        float: The total recovery percentage.
    """
    ridership_cols = [col for col in mta_data.columns if ": % of Pre-Pandemic" not in col and col != 'Date']
    
    baseline_ridership = calculate_baseline_ridership(mta_data, ridership_cols)
    current_ridership = calculate_current_ridership(mta_data, ridership_cols)
    
    # Calculate total recovery percentage
    total_recovery = (current_ridership / baseline_ridership) * 100 if baseline_ridership > 0 else 0
    
    return total_recovery


def calculate_top_service_recovery(mta_data: pd.DataFrame, baseline_period: pd.Series, current_period: pd.Series):
    """
    Calculate the top-performing service based on recovery percentage.

    Args:
        mta_data (pd.DataFrame): DataFrame containing ridership data with service columns.
        baseline_period (pd.Series): baseline period        
        current_period (pd.Series): current_perid        

    Returns:
        top_service (str): The top-performing service based on recovery percentage.
        recovery_percentages[top_service] (float): The top-performing service recovery percentage
    """
    # Convert 'Date' to datetime format
    mta_data['Date'] = pd.to_datetime(mta_data['Date'], format='%m/%d/%Y')

    # Select relevant columns: ridership data and pre-pandemic percentage columns
    services = [col.split(":")[0] for col in mta_data.columns if ": % of Pre-Pandemic" in col]

    # Calculate recovery for each service
    recovery_percentages = {}

    for service in services:
        # Get ridership for the current period and baseline period        
        baseline_ridership = mta_data.loc[baseline_period, service].sum()
        current_ridership = mta_data.loc[current_period, service].sum()
        
        # Calculate recovery percentage for the service
        if baseline_ridership > 0:
            recovery_percentage = (current_ridership / baseline_ridership) * 100
        else:
            recovery_percentage = 0

        recovery_percentages[service] = recovery_percentage
        print(f'service : {service} - baseline ridership : {baseline_ridership}, current_ridership : {current_ridership}, recovery_percentage : {recovery_percentages[service]}')
    
    # Identify the top-performing service based on the highest recovery percentage
    top_service = max(recovery_percentages, key=recovery_percentages.get)
    # For Debugging 
    print(f'Top-performing service: {top_service} with a recovery percentage of {recovery_percentage}%')
    return top_service, recovery_percentages[top_service]


def create_thousand_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Divides the ridership value by 1,000 to make the numbers easier to read

    Args:
    df: The dataframe to process

    Returns:
    df_thousands: The dataframe with the adjusted figures
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
    df_thousands[columns_to_divide] = round(df[columns_to_divide] / 1000,0)
    return df_thousands


def get_resample_value(granularity: str) -> str:   
    """
    Returns the resample value based on the selected granularity.    

    Args: 
        granularity: the string returned from the granularity dropdown

    Returns:
        selected granularity code to pass to resample. 
    """
    
    match granularity:
        case 'Year':
            return 'YE'
        case 'Month':
            return 'ME'
        case 'Quarter':
            return 'QE'
        case 'Week':
            return 'W'
        case _:
            return 'ME'  # Default case for anything not matched


def resample_data(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    """
    Resample the dataframe to the selected granularity.
    
    Args:
        df: The dataframe to resample
        granularity: The level of detail to use
    
    Returns:
        resampled_df: The dataframe resampled to the specified granularity
    """
    resample_value = get_resample_value(granularity)
    
    
    resampled_df = df.resample(resample_value, on='Date').mean() # Resampling and aggregating data using mean        
    resampled_df = resampled_df.round().astype(int) # Round the resampled data before converting to integer    
    resampled_df.reset_index(inplace=True) # Reset index to make 'Date' a column again  
    # If the granularity is Year, add the 'Year' column
    if granularity == 'Year':
        resampled_df['Year'] = resampled_df['Date'].dt.year.astype(str)  # Use str for better axis label formatting
    
    return resampled_df


def find_free_port(start_port=8700, max_port=8800):
    """   
    Finds the next available port starting from `start_port` up to `max_port`.    

    Args:
    start_port: the start of the port range. Default: 8700
    end_port: the end of the port range. Default: 8800

    Returns:
    port: The next available port in the range

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
    # Metrics Calculation
    metrics = {}    
    for service in selected_services:
        # Extract last and second-last periods for the service
        last_period_value = granular_data[service].iloc[-1]
        
        previous_period_value = granular_data[service].iloc[-2]        
        # Calculate metrics
        ridership_last_period = '{:,}K'.format(int(last_period_value))        
        percent_change = round(((last_period_value - previous_period_value) / previous_period_value) * 100,2)
    
        # Store metrics in the dictionary
        metrics[service] = {
            'ridership_last_period': ridership_last_period,
            'percent_change': percent_change
        }
    return metrics


def find_highest_ridership_day(df: pd.DataFrame):
# Define the post-pandemic start date
    post_pandemic_start = pd.Timestamp('2020-03-01')
    
    # Filter data to only include post-pandemic dates
    post_pandemic_data = df[df['Date'] >= post_pandemic_start]
    
    # Calculate total ridership across all services
    post_pandemic_data['Total_Ridership'] = post_pandemic_data[services].sum(axis=1)
    
    # Find the row with the highest total ridership
    highest_ridership = post_pandemic_data.loc[post_pandemic_data['Total_Ridership'].idxmax()]
    highest_ridership_day = highest_ridership['Date'].strftime('%d %b %Y')
    total_ridership = f'{highest_ridership['Total_Ridership'] // 1_000_000:.1f}M'
    
    return highest_ridership_day, total_ridership
    

def create_kpis(mta_data: pd.DataFrame) -> dict:
    # Metrics Calculation
    highest_ridership_day, total_ridership = find_highest_ridership_day(mta_data)
    total_recovery = f'{calculate_total_recovery(mta_data):.1f}%'    

    baseline_period = (mta_data['Date'] < '2020-03-11')
    current_period = (mta_data['Date'].dt.year == 2024) & (mta_data['Date'].dt.month == 3) & (mta_data['Date'].dt.day < 11)

    # Example usage
    top_service, recovery_percentage = calculate_top_service_recovery(mta_data, baseline_period, current_period)    

    print('create kpis')
    print(f'top service: {top_service}')
    print(f'recovery percentage: {recovery_percentage}')
    print('_'*80)
    kpis = {}    
    kpis = {
        'total_ridership': total_ridership,
        'highest_ridership_day': highest_ridership_day,
        'total_recovery': total_recovery
    }
    return kpis