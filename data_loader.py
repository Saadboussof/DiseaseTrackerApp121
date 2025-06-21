# data_loader.py
"""Functions for loading disease data from various sources."""

import math
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import config  # Import configuration
import traceback # Import traceback

# --- Specific Loaders ---

def load_covid_raw_data( file_path=config.COVID_LOCAL_DATA_FILE ):
    """Loads the raw COVID data CSV file."""
    full_path = os.path.abspath(file_path)
    print(f"[COVID Loader] Attempting to load data from: {full_path}")
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                print("[COVID Loader] UTF-8 failed, trying latin1 encoding...")
                df = pd.read_csv(file_path, encoding='latin1')
            except UnicodeDecodeError:
                print("[COVID Loader] latin1 failed, trying cp1252 encoding...")
                df = pd.read_csv(file_path, encoding='cp1252')

        if df.empty:
            raise ValueError(f"The file '{file_path}' is empty.")
        print(f"[COVID Loader] Data loaded successfully. Shape: {df.shape}")

        if 'country' not in df.columns:
            print("[COVID Loader] WARNING: 'country' column not found!")
        elif 'date' not in df.columns:
             # This check is less critical now as date is converted later
            print("[COVID Loader] WARNING: A column named 'date' not found initially!")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Error: COVID file '{file_path}' not found at {full_path}."
        )
    except pd.errors.EmptyDataError:
        raise ValueError(f"Error: COVID file '{file_path}' is empty/invalid.")
    except Exception as e:
        raise Exception(f"Error reading COVID data file '{file_path}': {e}")


def load_real_influenza_data(file_path=config.GRIPPE_DATA_SOURCE):
    """
    Loads the raw influenza data file.
    Checks for essential columns (Country, Date, Cases specified in config).
    Returns the *entire* raw DataFrame for later filtering.
    """
    full_path = os.path.abspath(file_path)
    print(f"[Influenza Loader] Attempting to load ALL Influenza data from: {full_path}")
    try:
        # Handle potential mixed types warning if needed
        df = pd.read_csv(file_path, low_memory=False)

        if df.empty:
            raise ValueError(f"The file '{file_path}' is empty.")
        print(f"[Influenza Loader] Raw data loaded successfully. Shape: {df.shape}")

        # Check required raw columns exist GLOBALLY in the file
        # Note: GRIPPE_DEATHS_COL is None, so only cases are checked here
        required_raw_cols = [config.GRIPPE_RAW_COUNTRY_COL, config.GRIPPE_DATE_COL, config.GRIPPE_CASES_COL]
        missing_raw = [col for col in required_raw_cols if col not in df.columns]
        if missing_raw:
            raise ValueError(f"Missing required columns in the raw influenza file: {missing_raw}. Found: {list(df.columns)}")
        print(f"[Influenza Loader] Essential raw columns ({required_raw_cols}) found.")

        # ** NO COUNTRY FILTERING HERE **
        # ** NO COLUMN RENAMING HERE ** (Done during preprocessing for the selected country)
        # ** NO TYPE CONVERSION HERE ** (Done during preprocessing)

        print(f"[Influenza Loader] Raw Influenza data load complete. Returning full DataFrame.")
        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"Error: Influenza file '{file_path}' not found at {full_path}.")
    except Exception as e:
        print(f"[Influenza Loader] Error reading Influenza file '{file_path}': {e}")
        traceback.print_exc()
        raise # Re-raise the exception


def load_zika_data(file_path=config.ZIKA_DATA_FILE):
    """
    Loads the enhanced Zika virus data file.
    Checks for essential columns and additional COVID-like columns if available.
    Returns the entire raw DataFrame for later filtering.
    """
    full_path = os.path.abspath(file_path)
    print(f"[Zika Loader] Attempting to load ALL Zika data from: {full_path}")
    try:
        df = pd.read_csv(file_path)

        if df.empty:
            raise ValueError(f"The file '{file_path}' is empty.")
        print(f"[Zika Loader] Raw data loaded successfully. Shape: {df.shape}")

        # Check required columns exist in the file
        required_raw_cols = [config.ZIKA_COUNTRY_COL, config.ZIKA_DATE_COL, 
                            config.ZIKA_CASES_COL, config.ZIKA_DEATHS_COL]
        missing_raw = [col for col in required_raw_cols if col not in df.columns]
        if missing_raw:
            raise ValueError(f"Missing required columns in the Zika file: {missing_raw}. Found: {list(df.columns)}")
        print(f"[Zika Loader] Essential raw columns ({required_raw_cols}) found.")
        
        # Check for enhanced columns (not required, but useful to report)
        if hasattr(config, 'ZIKA_RELEVANT_COLUMNS'):
            available_enhanced = [col for col in config.ZIKA_RELEVANT_COLUMNS if col in df.columns]
            if len(available_enhanced) > len(required_raw_cols):
                print(f"[Zika Loader] Enhanced dataset detected with {len(available_enhanced)} additional columns")
            else:
                print("[Zika Loader] Basic dataset detected with minimal columns")

        # Return the full DataFrame - preprocessing happens later for selected country
        print(f"[Zika Loader] Raw Zika data load complete. Returning full DataFrame.")
        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"Error: Zika file '{file_path}' not found at {full_path}.")
    except Exception as e:
        print(f"[Zika Loader] Error reading Zika file '{file_path}': {e}")
        traceback.print_exc()
        raise # Re-raise the exception


def simulate_disease_data(disease_name):
    """Generates simulated data for demonstration (always represents 'cases')."""
    print(f"[SIM Loader] Simulating data for: {disease_name}")
    today = datetime.now()
    # Generate more data points for better simulation display
    num_days_sim = 730 # Simulate 2 years
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d')
             for i in range(num_days_sim, 0, -1)]
    cases = []
    np.random.seed(42) # Keep consistent simulation

    # Use generic pattern for all simulations now, Grippe uses real data
    print(f"[SIM Loader] Using generic simulation pattern for {disease_name}.")
    for i in range(num_days_sim):
         date = datetime.strptime(dates[i], '%Y-%m-%d'); m = date.month
         # Basic seasonality centered around mid-year (adjust as needed)
         seasonal_factor = 1.0 + 0.8 * math.exp(-min((m - 7.5) % 12, (19.5 - m) % 12)**2 / 6)
         base = np.random.uniform(50, 150) # Random base level
         cyclic = 100 * seasonal_factor * np.sin(i / 90 + np.random.uniform(0, 6)) # Random phase/amplitude
         noise = np.random.normal(0, 30 * seasonal_factor)
         cases.append(int(base + cyclic + noise))

    simulated_df = pd.DataFrame({
        'date': dates,
        config.PREDICTION_CASES_TARGET_COL: [max(0, c) for c in cases] # Ensure non-negative cases, use standard name
    })
    # Ensure 'date' column is datetime type
    try:
        simulated_df['date'] = pd.to_datetime(simulated_df['date'])
    except Exception as e:
        print(f"[SIM Loader] Error converting simulated date column: {e}")
        return pd.DataFrame()

    # Return only essential columns ('date' and 'cases')
    return simulated_df[['date', config.PREDICTION_CASES_TARGET_COL]].copy()

# --- Dispatcher (MODIFIED for Grippe) ---
def get_data_source(disease_name):
    """
    Selects the appropriate data loading function based on disease name.
    Returns the raw DataFrame (or None if loading fails).
    For COVID & Grippe, returns the full raw DataFrame.
    For others, returns a DataFrame with 'date' and 'cases' (simulated).
    """
    print(f"[Data Dispatcher] Getting source for: {disease_name}")
    if disease_name == "COVID-19":
        try:
            # Returns the full raw COVID DataFrame
            return load_covid_raw_data()
        except Exception as e:
            print(f"[Data Dispatcher] Error loading COVID data: {e}")
            raise

    elif disease_name == "Grippe":
        try:
            # Returns the full raw Influenza DataFrame
            return load_real_influenza_data()
        except Exception as e:
            print(f"[Data Dispatcher] Error loading REAL Grippe data: {e}. Falling back to SIMULATION.")
            # Fallback returns DataFrame with 'date', 'cases'
            return simulate_disease_data(disease_name)
            
    elif disease_name == "Zika":
        try:
            # Returns the full raw Zika DataFrame
            return load_zika_data()
        except Exception as e:
            print(f"[Data Dispatcher] Error loading REAL Zika data: {e}. Falling back to SIMULATION.")
            # Fallback returns DataFrame with 'date', 'cases'
            return simulate_disease_data(disease_name)

    # --- FUTURE: Add calls to real data loaders here ---
    elif disease_name == "Dengue":
        # return load_real_dengue_data(...)
        print(f"[Data Dispatcher] Using SIMULATED data for {disease_name}")
        return simulate_disease_data(disease_name) # Returns 'date', 'cases'
    elif disease_name == "Paludisme":
        # return load_real_malaria_data(...)
        print(f"[Data Dispatcher] Using SIMULATED data for {disease_name}")
        return simulate_disease_data(disease_name) # Returns 'date', 'cases'

    # Fallback for placeholders if any defined in config
    elif disease_name in config.AVAILABLE_DISEASES: # Check against config list
        print(f"[Data Dispatcher] No specific loader for {disease_name}. Using SIMULATED data.")
        return simulate_disease_data(disease_name) # Returns 'date', 'cases'
    else:
        print(f"[Data Dispatcher] No data source defined for: {disease_name}")
        return None # Return None for unknown/unlisted diseases