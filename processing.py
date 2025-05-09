# processing.py
"""Functions for data processing, cleaning, and feature engineering."""

import pandas as pd
import numpy as np
from datetime import timedelta
import config # Import configuration
import traceback # Import traceback


def preprocess_covid_data(
    df, country_to_process, target_type="Cases", # Added target_type parameter
    relevant_cols=config.COVID_RELEVANT_COLUMNS,
    threshold=config.COVID_MISSING_VALUE_THRESHOLD,
    zero_fill_cols=config.COVID_COLS_TO_FILL_ZERO,
    drop_cols=config.COVID_COLS_TO_DROP_EXPLICITLY
):
    """
    Filters, cleans, and prepares COVID data for a specific country and target type (Cases or Deaths).
    Renames the selected target column to a standard internal name ('cases' or 'deaths').
    """
    print(f"\n[COVID Preprocessing] Starting for country: '{country_to_process}', Target: '{target_type}'")
    if df is None or df.empty: raise ValueError("Input DataFrame is None/empty.")
    if 'country' not in df.columns: raise ValueError("'country' column missing in COVID data.")

    # Determine target column names based on target_type
    if target_type == "Cases":
        source_target_col = config.COVID_CASES_INPUT_COL
        final_target_col_name = config.PREDICTION_CASES_TARGET_COL # 'cases'
    elif target_type == "Deaths":
        source_target_col = config.COVID_DEATHS_INPUT_COL
        final_target_col_name = config.PREDICTION_DEATHS_TARGET_COL # 'deaths'
    else:
        raise ValueError(f"Invalid target_type specified: '{target_type}'. Must be 'Cases' or 'Deaths'.")

    print(f"[COVID Proc] Source target column: '{source_target_col}', Final internal name: '{final_target_col_name}'")

    # Filter for the country first
    country_df = df[df['country'].eq(country_to_process)].copy()
    if country_df.empty:
        available_countries = df['country'].unique()
        print(f"Available COVID countries (sample): {list(available_countries[:min(len(available_countries), 10)])}")
        raise ValueError(f"No COVID data rows found for the selected country: '{country_to_process}'.")
    print(f"[COVID Proc] Filtered for '{country_to_process}'. Initial shape: {country_df.shape}")

    # Check if the required source target column exists *before* selecting relevant cols
    if source_target_col not in country_df.columns:
         raise ValueError(f"Required source target column '{source_target_col}' for target type '{target_type}' "
                          f"not found in data for '{country_to_process}'. Available columns: {list(country_df.columns)}")

    # Select only relevant columns that actually exist in the filtered data
    available_relevant_cols = [col for col in relevant_cols if col in country_df.columns]
    # Ensure the selected source target column is included if not already in relevant_cols
    if source_target_col not in available_relevant_cols:
        available_relevant_cols.append(source_target_col)
    print(f"[COVID Proc] Relevant columns available for '{country_to_process}': {available_relevant_cols}")
    country_df = country_df[available_relevant_cols].copy()
    print(f"[COVID Proc] Selected relevant columns. Shape: {country_df.shape}.")

    if country_df.empty:
        print("[COVID Proc] DataFrame became empty after selecting relevant columns.")
        return country_df # Return empty df

    # Convert date early
    if 'date' in country_df.columns:
        try:
            country_df['date'] = pd.to_datetime(country_df['date'])
            print("[COVID Proc] Converted 'date' to datetime.")
            country_df = country_df.sort_values('date').reset_index(drop=True)
            print("[COVID Proc] Sorted by date.")
        except Exception as e:
            print(f"[COVID Proc] WARNING: Date conversion failed: {e}. Proceeding without conversion.")
            # Attempt to sort anyway if possible, might raise error later
            try: country_df = country_df.sort_values('date').reset_index(drop=True)
            except: pass
    else:
         print("[COVID Proc] WARNING: 'date' column not found for conversion/sorting.")

    # Drop columns based on missing value threshold *within the country's data*
    missing_percentage = (country_df.isnull().sum() / len(country_df)) * 100
    cols_to_drop_thresh = missing_percentage[missing_percentage > (threshold * 100)].index.tolist()
    if cols_to_drop_thresh:
        essential = ['date', source_target_col] # Check against source target before rename
        cols_to_drop_thresh = [col for col in cols_to_drop_thresh if col not in essential]
        if cols_to_drop_thresh:
            # Use try-except in case a column was already dropped
            try:
                country_df = country_df.drop(columns=cols_to_drop_thresh)
                print(f"[COVID Proc] Dropped sparse columns (>{threshold*100}% missing): {cols_to_drop_thresh}")
                print(f"[COVID Proc] Shape after dropping sparse: {country_df.shape}.")
            except KeyError as ke:
                print(f"[COVID Proc] Warning: Tried to drop already missing column {ke}")


    # Fill specific columns with 0
    existing_zero_fill_cols = [col for col in zero_fill_cols if col in country_df.columns]
    if existing_zero_fill_cols:
        # Use .loc to avoid SettingWithCopyWarning
        country_df.loc[:, existing_zero_fill_cols] = country_df[existing_zero_fill_cols].fillna(0)
        print(f"[COVID Proc] Filled NaNs with 0 for: {existing_zero_fill_cols}")

    # Drop explicitly specified columns if they exist
    existing_cols_to_drop = [col for col in drop_cols if col in country_df.columns]
    if existing_cols_to_drop:
        try:
            country_df = country_df.drop(columns=existing_cols_to_drop)
            print(f"[COVID Proc] Dropped explicitly specified columns: {existing_cols_to_drop}")
            print(f"[COVID Proc] Shape after dropping explicit: {country_df.shape}.")
        except KeyError as ke:
            print(f"[COVID Proc] Warning: Tried to drop explicitly missing column {ke}")

    # Process the target column
    if source_target_col not in country_df.columns:
        raise ValueError(f"[COVID Proc] Source target column '{source_target_col}' is missing right before final processing step. "
                         f"Available columns: {list(country_df.columns)}")

    # Convert source target to numeric, fill NaNs with 0
    country_df.loc[:, source_target_col] = pd.to_numeric(country_df[source_target_col], errors='coerce').fillna(0)
    print(f"[COVID Proc] Converted source '{source_target_col}' to numeric, filled NaNs with 0.")

    # Rename the source target column to the final internal name ('cases' or 'deaths')
    if source_target_col != final_target_col_name:
        if final_target_col_name in country_df.columns:
            # If the final name already exists (e.g., 'cases' was in relevant_cols and target='Cases')
            # we need to handle this. Overwriting is usually fine if it's the same intended column.
            # If target='Deaths' and 'deaths' exists but wasn't the source_target_col, it's ambiguous.
            # For simplicity here, we assume overwriting is okay if names collide after processing source.
            print(f"[COVID Proc] Warning: Final target name '{final_target_col_name}' already exists. Overwriting with processed '{source_target_col}'.")
        country_df = country_df.rename(columns={source_target_col: final_target_col_name})
        print(f"[COVID Proc] Renamed '{source_target_col}' to '{final_target_col_name}'.")
    else:
        # If source and final names are the same (e.g., target='Cases', source='cases', final='cases')
        print(f"[COVID Proc] Target column already named '{final_target_col_name}'.")

    # Final Check for essential columns 'date' and the *final* target name
    essential_cols = ['date', final_target_col_name]
    missing_essential = [col for col in essential_cols if col not in country_df.columns]
    if missing_essential:
        raise ValueError(f"[COVID Proc] Essential columns missing after processing: {missing_essential}. Final columns: {list(country_df.columns)}")

    # Select only essential columns + any other remaining relevant ones (optional, keeps df cleaner)
    final_columns = essential_cols + [col for col in country_df.columns if col not in essential_cols]
    country_df = country_df[final_columns]


    if country_df.empty:
         print(f"[COVID Proc] Warning: DataFrame is empty after processing for '{country_to_process}'.")
    else:
        print(f"[COVID Proc] Preprocessing complete for '{country_to_process}' ({target_type}). Final shape: {country_df.shape}. Final columns: {list(country_df.columns)}")

    return country_df # Returns df with 'date' and either 'cases' or 'deaths' as the target


def preprocess_influenza_data(df_raw, country_to_process):
    """
    Filters raw influenza data for a specific country, selects, renames,
    and cleans the date and cases columns. NOTE: Currently only handles CASES ('ALL_INF').
    Outputs a DataFrame with 'date' and 'cases' columns.
    """
    print(f"\n[Influenza Preprocessing] Starting for country: '{country_to_process}' (Target: Cases Only)")
    if df_raw is None or df_raw.empty:
        raise ValueError("Input Raw Influenza DataFrame is None/empty.")

    raw_country_col = config.GRIPPE_RAW_COUNTRY_COL
    raw_date_col = config.GRIPPE_DATE_COL
    raw_cases_col = config.GRIPPE_CASES_COL
    final_target_col_name = config.PREDICTION_CASES_TARGET_COL # Always 'cases' for Influenza currently

    # Check required raw columns exist for cases
    required_raw_cols = [raw_country_col, raw_date_col, raw_cases_col]
    missing_raw = [col for col in required_raw_cols if col not in df_raw.columns]
    if missing_raw:
         raise ValueError(f"Missing required raw columns for Influenza processing: {missing_raw}")

    # Filter for the country (case-insensitive matching recommended)
    try:
        # Ensure the country column is string type before applying string methods
        df_raw[raw_country_col] = df_raw[raw_country_col].astype(str)
        country_df = df_raw[df_raw[raw_country_col].str.strip().str.lower() == country_to_process.strip().lower()].copy()
    except Exception as filter_err:
         print(f"[Influenza Proc] Error filtering country '{country_to_process}': {filter_err}")
         raise ValueError(f"Could not filter Influenza data for country '{country_to_process}'.")


    if country_df.empty:
        available_countries = df_raw[raw_country_col].unique()
        print(f"Available Influenza countries (sample): {list(available_countries[:min(len(available_countries), 10)])}")
        raise ValueError(f"No Influenza data rows found for the selected country: '{country_to_process}'.")
    print(f"[Influenza Proc] Filtered for '{country_to_process}'. Initial shape: {country_df.shape}")

    # Select only the date and cases columns
    df_std = country_df[[raw_date_col, raw_cases_col]].copy()

    # Rename to standard names 'date' and 'cases'
    df_std = df_std.rename(columns={
        raw_date_col: 'date',
        raw_cases_col: final_target_col_name # 'cases'
    })
    print(f"[Influenza Proc] Selected and renamed columns ('date', '{final_target_col_name}'). Shape: {df_std.shape}")

    # Convert 'date' to datetime, handle errors
    try:
        df_std['date'] = pd.to_datetime(df_std['date'], errors='coerce')
        initial_rows = len(df_std)
        df_std.dropna(subset=['date'], inplace=True)
        if len(df_std) < initial_rows:
             print(f"[Influenza Proc] Warning: Dropped {initial_rows - len(df_std)} rows due to invalid dates.")
        if df_std.empty:
             raise ValueError("DataFrame empty after handling date conversions.")
        print("[Influenza Proc] Converted 'date' column to datetime.")
    except Exception as e:
        print(f"[Influenza Proc] Error converting date column: {e}")
        traceback.print_exc()
        raise ValueError("Date conversion failed.") from e

    # Convert 'cases' to numeric, fill NaNs with 0, ensure integer
    try:
        df_std[final_target_col_name] = pd.to_numeric(df_std[final_target_col_name], errors='coerce').fillna(0).astype(int)
        print(f"[Influenza Proc] Converted '{final_target_col_name}' to numeric (int), filled NaNs with 0.")
    except Exception as e:
        print(f"[Influenza Proc] Error converting cases column: {e}")
        traceback.print_exc()
        raise ValueError("Cases conversion failed.") from e

    # Sort by date and remove duplicates (keeping the last entry for a given date)
    df_std = df_std.sort_values('date').drop_duplicates(subset=['date'], keep='last')
    df_std = df_std.reset_index(drop=True)
    print("[Influenza Proc] Sorted by date and removed potential duplicates.")

    if df_std.empty:
         print(f"[Influenza Proc] Warning: DataFrame is empty after processing for '{country_to_process}'.")
    else:
         print(f"[Influenza Proc] Preprocessing complete for '{country_to_process}'. Shape: {df_std.shape}")

    # Returns DataFrame with columns 'date' and 'cases'
    return df_std


def common_post_processing(df_preprocessed, target_col_name):
    """
    Applies common feature engineering steps needed for analysis and prediction.
    Expects a DataFrame with 'date' and the specified target column ('cases' or 'deaths').
    Detects weekly data and resamples to daily using forward fill.
    Calculates features based on the provided target_col_name.
    Returns DataFrame with added features ('day_of_year', 'month', 'day',
    'day_of_week', '{target_col_name}_7d_avg', 'growth_rate').
    """
    if df_preprocessed is None or df_preprocessed.empty:
        print("[Common PostProc] Input DataFrame is empty or None.")
        return pd.DataFrame() # Return empty DataFrame

    required = ['date', target_col_name]
    if not all(col in df_preprocessed.columns for col in required):
         print(f"[Common PostProc] Error: Missing required columns: {required}. Found: {list(df_preprocessed.columns)}")
         return pd.DataFrame() # Return empty

    print(f"[Common PostProc] Applying steps for target '{target_col_name}' to DataFrame with shape {df_preprocessed.shape}...")
    df_processed = df_preprocessed.copy() # Ensure copy

    # Ensure Data Types
    try:
        if not pd.api.types.is_datetime64_any_dtype(df_processed['date']):
             df_processed['date'] = pd.to_datetime(df_processed['date'])
             print("[Common PostProc] Converted 'date' to datetime.")

        # Target column type handled in preprocess step, but double-check
        if target_col_name in df_processed.columns:
             df_processed[target_col_name] = pd.to_numeric(
                 df_processed[target_col_name], errors='coerce'
             ).fillna(0)
             print(f"[Common PostProc] Ensured '{target_col_name}' is numeric and NaNs filled with 0.")
        else:
             # This shouldn't happen if preprocess worked, but check anyway
             print(f"[Common PostProc] CRITICAL Error: Target column '{target_col_name}' not found during type check.")
             return pd.DataFrame()

    except Exception as e:
        print(f"[Common PostProc] Error during data type conversion: {e}")
        traceback.print_exc()
        return pd.DataFrame() # Fail early

    # Sort by Date (Crucial before resampling and rolling calculations)
    if 'date' in df_processed.columns:
        df_processed = df_processed.sort_values('date').reset_index(drop=True)
        print("[Common PostProc] Sorted by date.")
    else:
        print("[Common PostProc] Error: 'date' column not found for sorting.")
        return pd.DataFrame()

    # Resample Weekly Data to Daily (if necessary)
    if len(df_processed) > 1:
        # Calculate median difference only on valid date entries
        date_diffs = df_processed['date'].dropna().diff().median()
        if pd.notna(date_diffs) and pd.Timedelta('6 days') <= date_diffs <= pd.Timedelta('8 days'):
            print(f"[Common PostProc] Detected weekly data (median diff: {date_diffs}). Resampling to daily using forward fill...")
            try:
                df_processed = df_processed.set_index('date')
                # Ensure all columns needed are preserved during resampling
                # Usually ffill() works well for numeric data like cases/deaths
                df_resampled = df_processed.resample('D').ffill()
                # Reset index to get 'date' back as a column
                df_processed = df_resampled.reset_index()
                print(f"[Common PostProc] Resampling complete. Shape after resampling: {df_processed.shape}")
            except Exception as resample_err:
                print(f"[Common PostProc] Error during resampling: {resample_err}")
                # Attempt to continue without resampling if it fails critically
                df_processed = df_preprocessed.sort_values('date').reset_index(drop=True) # Start from sorted preprocessed
        elif pd.notna(date_diffs):
            print(f"[Common PostProc] Data does not appear to be weekly (median diff: {date_diffs}). Skipping resampling.")
        else:
            print("[Common PostProc] Could not determine data frequency (median diff is NaN). Skipping resampling.")

    else:
         print("[Common PostProc] Not enough data points to determine frequency for resampling.")

    # Ensure target column is integer after resampling/processing
    if target_col_name in df_processed.columns:
         try:
             df_processed[target_col_name] = df_processed[target_col_name].astype(int)
             print(f"[Common PostProc] Ensured '{target_col_name}' is integer type.")
         except Exception as int_err:
              print(f"[Common PostProc] Warning: Could not convert '{target_col_name}' to int after processing: {int_err}. Keeping as float.")

    # Add Date Features (for modeling)
    try:
        df_processed['day_of_year'] = df_processed['date'].dt.dayofyear
        df_processed['month'] = df_processed['date'].dt.month
        df_processed['day'] = df_processed['date'].dt.day
        df_processed['day_of_week'] = df_processed['date'].dt.dayofweek
        print("[Common PostProc] Added date features (day_of_year, month, day, day_of_week).")
    except AttributeError as e:
         print(f"[Common PostProc] Error adding date features ('date' might not be datetime): {e}")
         for col in ['day_of_year', 'month', 'day', 'day_of_week']:
             if col not in df_processed.columns: df_processed[col] = 0 # Add as 0 if missing

    # Add Analysis Features (rolling avg, growth rate based on target_col_name)
    if target_col_name in df_processed.columns:
        avg_col_name = f"{target_col_name}_7d_avg" # e.g., 'cases_7d_avg' or 'deaths_7d_avg'
        df_processed[avg_col_name] = df_processed[target_col_name].rolling(
            window=7, min_periods=1 # Use min_periods=1 to get avg even at start
        ).mean()
        print(f"[Common PostProc] Added '{avg_col_name}'.")

        # Calculate growth rate based on the target column
        # Handle division by zero or NaN resulting from pct_change on zeros
        pct_change = df_processed[target_col_name].pct_change(fill_method=None) # Don't fill NaNs here yet
        # Replace inf/-inf with NaN, then multiply by 100, then fill remaining NaNs (from pct_change or inf) with 0
        df_processed['growth_rate'] = (pct_change.replace([np.inf, -np.inf], np.nan) * 100).fillna(0)
        print("[Common PostProc] Added 'growth_rate' (based on target column).")
    else:
        # This case should already be caught earlier, but for safety:
        print(f"[Common PostProc] CRITICAL Error: Target column '{target_col_name}' not found for analysis feature calculation.")
        # Add empty columns to prevent downstream errors, although data is likely unusable
        avg_col_name = f"{target_col_name}_7d_avg"
        if avg_col_name not in df_processed.columns: df_processed[avg_col_name] = np.nan
        if 'growth_rate' not in df_processed.columns: df_processed['growth_rate'] = np.nan


    # Ensure 'month' column exists for monthly analysis plot (add as int if missing)
    if 'month' not in df_processed.columns:
        try:
            df_processed['month'] = df_processed['date'].dt.month
        except:
            df_processed['month'] = 0 # Fallback
    # Ensure month is integer type for grouping in analysis plot
    df_processed['month'] = df_processed['month'].fillna(0).astype(int)


    print(f"[Common PostProc] Common post-processing completed for target '{target_col_name}'. Final shape: {df_processed.shape}. "
          f"Columns: {list(df_processed.columns)}")
    return df_processed
