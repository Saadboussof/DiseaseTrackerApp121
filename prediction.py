# prediction.py
"""Functions for model training, prediction generation, and plotting."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # Import mdates for better date formatting
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta
import traceback
import calendar
import config # Import configuration for colors and settings


def train_prediction_model(df, target_col_name):
    """
    Trains a RandomForestRegressor model on historical data for the specified target column.
    """
    target_type_label = target_col_name.capitalize()
    print(f"[Predict Train] Training model for {target_type_label}...")

    # Features are always the same date-based columns
    feature_cols = config.PREDICTION_FEATURE_COLS
    required_cols = feature_cols + [target_col_name] # Add the specific target column

    if df is None or df.empty:
        raise ValueError("Input DataFrame for training is empty.")

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for modeling {target_type_label}: {missing}. Available: {list(df.columns)}")

    # Drop rows with NaN in *any* required column BEFORE splitting
    model_data = df[required_cols].dropna()
    if model_data.empty:
        raise ValueError(f"No valid historical data for {target_type_label} modeling after dropping NaNs from required columns.")

    # Add check for sufficient data after dropna
    min_training_rows = 10 # Example threshold, adjust if needed
    if len(model_data) < min_training_rows:
         raise ValueError(f"Insufficient data ({len(model_data)} rows) for {target_type_label} remaining after cleaning for model training. Need at least {min_training_rows}.")

    X_hist = model_data[feature_cols].values
    y_hist = model_data[target_col_name].values # Use the specified target column

    # Scale features (X)
    scaler_X = StandardScaler()
    X_hist_scaled = scaler_X.fit_transform(X_hist)

    # Initialize and train the model
    model = RandomForestRegressor(
        n_estimators=config.RF_N_ESTIMATORS,
        random_state=config.RF_RANDOM_STATE,
        n_jobs=-1 # Use all available cores
    )
    model.fit(X_hist_scaled, y_hist)
    print(f"[Predict Train] Model training complete for {target_type_label}.")
    return model, scaler_X


def generate_predictions(model, scaler, num_days, last_hist_date, target_col_name):
    """
    Generates future dates and predicts target values (cases or deaths).
    Uses last_hist_date to start predictions immediately after historical data ends.
    """
    target_type_label = target_col_name.capitalize()
    if model is None or scaler is None:
        raise ValueError(f"Model or Scaler not provided for {target_type_label} prediction.")
    if not isinstance(num_days, int) or num_days <= 0:
        raise ValueError(f"Invalid number of days to predict: {num_days}. Must be a positive integer.")
    if not isinstance(last_hist_date, pd.Timestamp):
         # Try converting if it's a datetime object or similar
         try: last_hist_date = pd.to_datetime(last_hist_date)
         except: raise ValueError("last_hist_date must be a pandas Timestamp or convertible.")

    print(f"[Predict Generate] Generating future dates for {num_days} days for {target_type_label}...")

    # Start predictions the day after the last historical date
    prediction_start_date = last_hist_date.date() + timedelta(days=1)
    print(f"[Predict Generate] Using start date: {prediction_start_date}")

    future_dates = [prediction_start_date + timedelta(days=i) for i in range(num_days)]
    print(f"[Predict Generate] Predicting {target_type_label} for {num_days} days: "
          f"{future_dates[0]} to {future_dates[-1]}")

    # Create future features based on dates
    future_features = []
    for date in future_dates:
        future_features.append(
            [date.timetuple().tm_yday, date.month, date.day, date.weekday()]
        )

    try:
        future_features_scaled = scaler.transform(future_features)
        predictions_raw = model.predict(future_features_scaled)
        # Ensure predictions are non-negative integers
        predictions = np.maximum(0, np.round(predictions_raw)).astype(int)
    except Exception as e:
        print(f"[Predict Generate] Error during scaling or prediction for {target_type_label}: {e}")
        traceback.print_exc()
        raise ValueError(f"Failed to generate {target_type_label} predictions.") from e

    # Create prediction DataFrame with a dynamic column name
    pred_col_name = f"predicted_{target_col_name}" # e.g., predicted_cases or predicted_deaths
    prediction_df = pd.DataFrame({
        'date': future_dates,
        pred_col_name: predictions
    })
    prediction_df['date'] = pd.to_datetime(prediction_df['date']) # Ensure datetime type
    print(f"[Predict Generate] {target_type_label} predictions generated.")
    return prediction_df


def plot_prediction_chart(hist_df, pred_df, disease_name, target_col_name, source_info="", forecast_days=None):
    """
    Generates the prediction plot (History + Forecast) for the specified target - Dark Theme.
    Adds a note for long forecasts and uses better date formatting.

    Args:
        hist_df (pd.DataFrame): Historical data with 'date' and target_col_name.
        pred_df (pd.DataFrame): Prediction data with 'date' and f'predicted_{target_col_name}'.
        disease_name (str): Name of the disease.
        target_col_name (str): 'cases' or 'deaths'.
        source_info (str): Additional info like country.
        forecast_days (int, optional): Number of forecast days for labeling/warnings.

    Returns:
        matplotlib.figure.Figure: The generated figure object, or an error figure.
    """
    target_type_label = target_col_name.capitalize()
    pred_col_name = f"predicted_{target_col_name}" # predicted_cases or predicted_deaths

    print(f"[Predict Plot] Generating prediction chart for {target_type_label} (Dark Theme)...")

    # Basic checks for data existence
    if hist_df is None or hist_df.empty:
        print("[Predict Plot] Warning: Historical data is missing or empty. Plotting forecast only.")
        # Allow plotting only forecast if history is missing
    if pred_df is None or pred_df.empty:
        print(f"[Predict Plot] Error: Prediction data ('{pred_col_name}') is missing or empty.")
        return None # Cannot plot without predictions

    # Check required columns
    hist_cols_ok = True
    if hist_df is not None and not hist_df.empty:
        required_hist_cols = ['date', target_col_name]
        if not all(col in hist_df.columns for col in required_hist_cols):
            print(f"[Predict Plot] Error: Historical data missing required columns: {required_hist_cols}. Found: {list(hist_df.columns)}")
            hist_cols_ok = False # Mark as problematic but might still plot forecast

    required_pred_cols = ['date', pred_col_name]
    if not all(col in pred_df.columns for col in required_pred_cols):
         print(f"[Predict Plot] Error: Prediction data missing required columns: {required_pred_cols}. Found: {list(pred_df.columns)}")
         return None # Cannot proceed without prediction columns

    fig = None # Initialize
    try:
        fig = plt.figure(figsize=(10, 6), dpi=100) # Use rcParams facecolor
        ax = fig.add_subplot(111)

        # Select colors based on target
        colors = config.PLOT_COLORS_DARK
        if target_col_name == 'cases':
            hist_color = colors["history_cases"]
            pred_color = colors["prediction_cases"]
        elif target_col_name == 'deaths':
            hist_color = colors["history_deaths"]
            pred_color = colors["prediction_deaths"]
        else: # Fallback
            hist_color = "#CCCCCC"
            pred_color = "#999999"

        line_color = colors["separator_lines"]
        text_color = plt.rcParams['text.color']

        # Add note to title for long forecasts
        title = f'{disease_name} - {target_type_label} History & Forecast{source_info}'
        warning_note = ""
        long_forecast_threshold = 180 # Example threshold
        if forecast_days and forecast_days > long_forecast_threshold:
             warning_note = f"\n(Note: {forecast_days}-day forecast based on simple seasonal model - interpret with caution)"
        full_title = title + warning_note

        # Ensure Dates are Datetime Type (Handle potential errors)
        try:
            if hist_df is not None and not hist_df.empty and hist_cols_ok and not pd.api.types.is_datetime64_any_dtype(hist_df['date']):
                 hist_df['date'] = pd.to_datetime(hist_df['date'])
            if not pd.api.types.is_datetime64_any_dtype(pred_df['date']):
                 pred_df['date'] = pd.to_datetime(pred_df['date'])
        except Exception as e:
             print(f"[Predict Plot] Warning: Error converting date columns: {e}. Plotting may fail.")
             pass # Try plotting anyway

        # Plot Historical Data (if available and columns are ok)
        last_hist_date = None
        if hist_df is not None and not hist_df.empty and hist_cols_ok:
            # Ensure target column is numeric before plotting
            hist_df[target_col_name] = pd.to_numeric(hist_df[target_col_name], errors='coerce')
            ax.plot(hist_df['date'], hist_df[target_col_name], color=hist_color, label=f'Historical Daily {target_type_label}', linewidth=1.5, alpha=0.8)
            if not hist_df['date'].empty:
                 last_hist_date = hist_df['date'].iloc[-1]

        # Plot Prediction Data
        pred_label = f'Predicted {target_type_label}'
        if forecast_days: pred_label += f' ({forecast_days} days)'
        # Ensure prediction column is numeric
        pred_df[pred_col_name] = pd.to_numeric(pred_df[pred_col_name], errors='coerce')
        ax.plot(pred_df['date'], pred_df[pred_col_name], color=pred_color, linestyle='--', label=pred_label, linewidth=2)

        # Vertical Lines (Ensure dates are valid before accessing)
        first_pred_date = None
        if not pred_df.empty and 'date' in pred_df.columns:
             first_pred_date = pred_df['date'].iloc[0]

        if last_hist_date and isinstance(last_hist_date, pd.Timestamp):
            ax.axvline(x=last_hist_date, color=line_color, linestyle=':', alpha=0.8, label=f'History End ({last_hist_date.date()})')

        if first_pred_date and isinstance(first_pred_date, pd.Timestamp):
            # Only draw forecast start line if it's distinct from history end or if no history exists
            draw_pred_start_line = not last_hist_date or (isinstance(last_hist_date, pd.Timestamp) and (first_pred_date - last_hist_date).days > 0)
            if draw_pred_start_line:
                 ax.axvline(x=first_pred_date, color=colors.get('negative_growth', '#B12025'), linestyle=':', alpha=0.8, label=f'Forecast Start ({first_pred_date.date()})')

        # Labels and Title (use modified title)
        ax.set_title(full_title, fontsize=11, weight='bold') # Reduced size slightly for note
        ax.set_xlabel('Date', fontsize=9)
        ax.set_ylabel(f'Number of {target_type_label}', fontsize=9) # Dynamic Y label
        ax.legend(fontsize=8)
        ax.tick_params(axis='x', labelsize=8, rotation=15)
        ax.tick_params(axis='y', labelsize=8)
        ax.grid(True, linestyle='--', alpha=0.4) # Grid color from rcParams

        # Adjust X-axis formatter/locator
        try:
            locator = mdates.AutoDateLocator(minticks=5, maxticks=12)
            formatter = mdates.ConciseDateFormatter(locator)
            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
        except Exception as e_fmt:
            print(f"[Predict Plot] Warning: Failed to apply auto date ticks: {e_fmt}")
            plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

        # Set X Limits (Full Range - Robust handling)
        first_date_hist = None
        if hist_df is not None and not hist_df.empty and hist_cols_ok and not hist_df['date'].empty:
             first_date_hist = hist_df['date'].iloc[0]
        last_date_pred = None
        if not pred_df.empty and not pred_df['date'].empty:
             last_date_pred = pred_df['date'].iloc[-1]

        # Determine overall start and end dates for limits
        all_dates = []
        if isinstance(first_date_hist, pd.Timestamp): all_dates.append(first_date_hist)
        if isinstance(last_hist_date, pd.Timestamp): all_dates.append(last_hist_date)
        if isinstance(first_pred_date, pd.Timestamp): all_dates.append(first_pred_date)
        if isinstance(last_date_pred, pd.Timestamp): all_dates.append(last_date_pred)

        if all_dates:
            min_plot_date = min(all_dates)
            max_plot_date = max(all_dates)
            try:
                time_delta = (max_plot_date - min_plot_date)
                if isinstance(time_delta, pd.Timedelta) and time_delta.days >= 0:
                    x_padding = timedelta(days=max(2, time_delta.days * 0.02)) # Ensure min padding
                    ax.set_xlim(left=min_plot_date - x_padding, right=max_plot_date + x_padding)
                else:
                    ax.set_xlim(left=min_plot_date - timedelta(days=5), right=max_plot_date + timedelta(days=5))
            except Exception as xlim_err:
                print(f"[Predict Plot] Warning: Error setting X limits: {xlim_err}")
                # Fallback limits
                if min_plot_date: ax.set_xlim(left=min_plot_date - timedelta(days=5))
                if max_plot_date: ax.set_xlim(right=max_plot_date + timedelta(days=5))
        else:
            print("[Predict Plot] Warning: Could not determine date range for X limits.")


        # Set Y Limits (Full Range - Robust calculation including both hist and pred)
        all_values = []
        if hist_df is not None and not hist_df.empty and hist_cols_ok:
             numeric_hist = pd.to_numeric(hist_df[target_col_name], errors='coerce').dropna()
             if not numeric_hist.empty: all_values.extend(numeric_hist.tolist())
        if not pred_df.empty:
             numeric_pred = pd.to_numeric(pred_df[pred_col_name], errors='coerce').dropna()
             if not numeric_pred.empty: all_values.extend(numeric_pred.tolist())

        if all_values:
            min_y = min(all_values)
            max_y = max(all_values)
            y_range = max_y - min_y
            y_padding = y_range * 0.05 if y_range > 0 else 5 # Add padding, ensure min padding if range is 0
            ax.set_ylim(bottom=max(0, min_y - y_padding), top=max_y + y_padding)
        else:
             ax.set_ylim(bottom=0, top=10) # Default if no valid numeric data

        fig.autofmt_xdate() # Auto-format date labels if needed
        fig.tight_layout() # Adjust layout

        return fig

    except Exception as e:
        print(f"[Predict Plot] Error during plotting for {target_type_label}: {e}")
        traceback.print_exc()
        if fig: plt.close(fig) # Close figure if created before error
        # Return error figure (dark theme)
        fig_err, ax_err = plt.subplots(figsize=(10, 6))
        error_color = config.PLOT_COLORS_DARK.get('negative_growth', '#FF0000') # Use config color or default red
        fig_err.patch.set_facecolor(config.DARK_PLOT_STYLE.get("figure.facecolor", "#000000")) # Set fig background
        ax_err.set_facecolor(config.DARK_PLOT_STYLE.get("axes.facecolor", "#000000")) # Set axes background
        ax_err.text(0.5, 0.5, f"Error generating prediction plot for {target_type_label}:\n{e}",
                    ha='center', va='center', color=error_color, wrap=True, fontsize=12)
        # Hide axes details for error plot
        ax_err.set_xticks([]); ax_err.set_yticks([])
        ax_err.spines['top'].set_visible(False); ax_err.spines['right'].set_visible(False)
        ax_err.spines['bottom'].set_visible(False); ax_err.spines['left'].set_visible(False)
        return fig_err


def calculate_prediction_stats(pred_df, target_col_name):
    """Calculates summary statistics for the prediction period for the specified target."""
    target_type_label = target_col_name.capitalize()
    pred_col_name = f"predicted_{target_col_name}" # predicted_cases or predicted_deaths
    print(f"[Predict Stats] Calculating stats for {target_type_label} predictions...")

    stats_values = {} # Return dict
    if pred_df is None or pred_df.empty:
        stats_values["info"] = f"No {target_type_label} prediction data available"
        return stats_values
    if pred_col_name not in pred_df.columns:
        stats_values["error"] = f"Predicted {target_type_label} column ('{pred_col_name}') not found."
        return stats_values

    try:
        # Ensure predicted column is numeric, drop NaNs for calculations
        numeric_pred = pd.to_numeric(pred_df[pred_col_name], errors='coerce').dropna()
        if numeric_pred.empty:
             stats_values["info"] = f"No valid numeric predicted {target_type_label} data."
             return stats_values

        peak_pred = int(numeric_pred.max())
        peak_idx = numeric_pred.idxmax() # Use index from the numeric series
        # Find corresponding date in original df using the valid index
        peak_date = pred_df.loc[peak_idx, 'date'] if pd.notna(peak_idx) and peak_idx in pred_df.index else None

        avg_pred = numeric_pred.mean()
        total_pred = int(numeric_pred.sum())
        period_days = len(pred_df) # Use original length before dropping NaNs for period

        # Formatted values (generic names, context from UI)
        stats_values["peak_pred_fmt"] = f"{peak_pred:,}" if not pd.isna(peak_pred) else "N/A"
        stats_values["peak_date_fmt"] = peak_date.strftime('%b %d, %Y') if peak_date else "N/A"
        stats_values["avg_pred_fmt"] = f"{avg_pred:.1f}" if not pd.isna(avg_pred) else "N/A"
        stats_values["total_pred_fmt"] = f"{total_pred:,}" if not pd.isna(total_pred) else "N/A"
        stats_values["period_days_fmt"] = f"{period_days} days"

        # Add target type for context
        stats_values["target_type"] = target_type_label

        print(f"[Predict Stats] Calculated for {target_type_label}: {stats_values}")
        return stats_values

    except Exception as e:
        print(f"Error calculating prediction statistics for {target_type_label}: {e}")
        traceback.print_exc()
        return {"error": f"Could not calculate {target_type_label} prediction stats"}
