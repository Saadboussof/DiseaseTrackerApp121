# analysis.py
"""Functions for creating analysis plots and calculating statistics."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates # Import for date formatting/locating
from datetime import timedelta, datetime # Import datetime explicitly
import traceback
import config # Import configuration for colors

def plot_analysis_charts(df, disease_name, target_col_name, source_info=""):
    """
    Generates the 3-panel analysis plot (dark theme) for the specified target column.
    1. Daily Target Value (Bar) + 7-Day Avg (Line)
    2. Daily Growth Rate (Color-coded Bars)
    3. Monthly Average Target Value (Bar)

    Args:
        df (pd.DataFrame): Processed DataFrame with required columns
                           ('date', target_col_name, f'{target_col_name}_7d_avg', 'growth_rate', 'month').
        disease_name (str): Name of the disease.
        target_col_name (str): The name of the target column ('cases' or 'deaths').
        source_info (str): Additional info like country or "(Simulated)".

    Returns:
        matplotlib.figure.Figure: The generated figure object, or None if error.
    """
    target_type_label = target_col_name.capitalize() # "Cases" or "Deaths"
    print(f"[Analysis Plot] Generating 3-panel analysis charts for {target_type_label} (Dark Theme)...")

    # Determine required columns based on target
    avg_col_name = f"{target_col_name}_7d_avg"
    required_cols = ['date', target_col_name, avg_col_name, 'growth_rate', 'month']

    if df is None or df.empty:
        print("[Analysis Plot] Error: Input DataFrame is empty.")
        return None

    # Convert date early and handle potential errors
    try:
        if 'date' not in df.columns:
             raise ValueError("Missing required column: 'date'")
        # Ensure 'date' column is suitable for conversion before attempting
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            # Check if it looks like a date string before conversion
            if pd.api.types.is_string_dtype(df['date']) or pd.api.types.is_object_dtype(df['date']):
                 df['date'] = pd.to_datetime(df['date'], errors='coerce')
                 if df['date'].isnull().any():
                      print("[Analysis Plot] Warning: Some dates failed to convert. Check date format.")
                      # Optionally drop rows with NaT dates if necessary: df.dropna(subset=['date'], inplace=True)
                 print("[Analysis Plot] Converted 'date' column to datetime early.")
            else:
                 # If it's numeric or other non-string/object type, conversion is unlikely to work
                 raise TypeError("Date column has an unexpected non-datetime, non-string type.")
        # Drop rows with NaT dates if conversion failed for some
        df.dropna(subset=['date'], inplace=True)
        if df.empty:
             print("[Analysis Plot] Error: DataFrame empty after handling date conversion/dropping NaTs.")
             return None

    except Exception as e:
        print(f"[Analysis Plot] Error preparing date column: {e}")
        traceback.print_exc()
        return None # Cannot proceed without valid dates

    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"[Analysis Plot] Error: Missing required columns for target '{target_col_name}' after date handling: {missing}")
        print(f"[Analysis Plot] Available columns: {list(df.columns)}")
        # Provide more specific feedback
        if target_col_name not in df.columns:
            print(f"--> Specific target column '{target_col_name}' is missing.")
        if avg_col_name not in df.columns:
             print(f"--> Specific average column '{avg_col_name}' is missing.")
        return None

    fig = None # Initialize fig
    try:
        # Style is set globally in config.py now
        fig, axes = plt.subplots(
            3, 1, figsize=(10, 9), dpi=100,
            sharex=False,
            gridspec_kw={'height_ratios': [2.2, 1, 1.1]}
        )
        fig.subplots_adjust(hspace=0.65, bottom=0.12, top=0.92)

        ax1, ax2, ax3 = axes # Unpack axes

        # Colors from config and title setup based on target
        colors = config.PLOT_COLORS_DARK
        if target_col_name == 'cases':
            bar_color = colors["daily_cases"]
            avg_color = colors["avg_line_cases"]
        elif target_col_name == 'deaths':
            bar_color = colors["daily_deaths"]
            avg_color = colors["avg_line_deaths"]
        else: # Fallback
            bar_color = "#CCCCCC"
            avg_color = "#999999"

        positive_growth_color = colors["positive_growth"]
        negative_growth_color = colors["negative_growth"]
        monthly_color = colors["monthly_avg"]
        text_color = plt.rcParams['text.color']

        # Dynamic Title based on Target
        title = f'{disease_name} - {target_type_label} Analysis{source_info}'
        fig.suptitle(title, fontsize=14, weight='bold', color=text_color)

        # --- Define Robust X-axis Limits ---
        if df['date'].empty:
            xmin_limit_date = pd.to_datetime(datetime.now().date() - timedelta(days=365))
            xmax_limit_date = pd.to_datetime(datetime.now().date() + timedelta(days=30))
        else:
            first_hist_date = df['date'].min()
            last_hist_date = df['date'].max()
            cutoff_date = pd.to_datetime('2025-01-15') # Desired cutoff (Example, adjust if needed)

            if last_hist_date > cutoff_date + timedelta(days=60):
                xmax_limit_date = cutoff_date
            else:
                xmax_limit_date = last_hist_date + timedelta(days=15) # Show full range + buffer

            xmin_limit_date = first_hist_date - timedelta(days=15)

            if xmin_limit_date >= xmax_limit_date:
                xmin_limit_date = xmax_limit_date - timedelta(days=30) # Force at least 30 day window

        print(f"[Analysis Plot] X-axis limits set: {xmin_limit_date.date()} to {xmax_limit_date.date()}")

        # --- Plot 1: Daily Target Value (Bar) & 7-Day Avg (Line) ---
        if target_col_name in df.columns and not df[target_col_name].isnull().all():
            # Calculate dynamic bar width based on date frequency
            date_diffs = df['date'].diff().dt.days.fillna(1).median() # Use median day difference
            bar_width = max(0.5, min(1.0, date_diffs * 0.7)) # Adjust multiplier as needed

            ax1.bar(df['date'], df[target_col_name], color=bar_color, width=bar_width, alpha=0.7, label=f'Daily {target_type_label}')
            if avg_col_name in df.columns:
                ax1.plot(df['date'], df[avg_col_name], color=avg_color, linewidth=2.5, label='7-Day Avg')
            else:
                 print(f"[Analysis Plot] Warning: Average column '{avg_col_name}' not found for plot 1.")

            ax1.set_title(f'Daily {target_type_label} and 7-Day Average', fontsize=11, weight='semibold')
            ax1.set_ylabel(f'Number of {target_type_label}', fontsize=9)
            ax1.legend(fontsize=8)
            ax1.tick_params(axis='x', labelsize=8, rotation=15)
            ax1.tick_params(axis='y', labelsize=8)
            ax1.grid(True, linestyle='--', alpha=0.4)

            # Robust calculation of Y limits for the target column
            numeric_target = pd.to_numeric(df[target_col_name], errors='coerce').dropna()
            if not numeric_target.empty:
                min_y1 = numeric_target.min()
                max_y1 = numeric_target.max()
                # Ensure non-negative lower limit, add padding, handle zero max
                ax1.set_ylim(bottom=max(0, min_y1 * 0.95 if min_y1 > 0 else 0),
                             top=max(max_y1 * 1.05 if max_y1 > 0 else 10, 10)) # Min top limit of 10
            else:
                 ax1.set_ylim(bottom=0, top=10) # Fallback

            ax1.set_xlim(left=xmin_limit_date, right=xmax_limit_date) # Apply X limit
        else:
             ax1.text(0.5, 0.5, f"{target_type_label}/Date data unavailable", ha='center', va='center', transform=ax1.transAxes, color=text_color)
             ax1.set_ylim(0, 10); ax1.set_xlim(left=xmin_limit_date, right=xmax_limit_date)

        # --- Plot 2: Daily Growth Rate (Color-coded Bars) ---
        # Growth rate calculation should be based on the primary target (handled in common_post_processing)
        if 'growth_rate' in df.columns:
            # Ensure growth_rate is numeric, handle potential inf/-inf/NaN
            growth_data = pd.to_numeric(df['growth_rate'], errors='coerce').replace([np.inf, -np.inf], 0).fillna(0)

            if not growth_data.empty and not growth_data.isnull().all():
                positive_mask = growth_data > 0
                # Use valid indices from the mask for date slicing
                valid_pos_dates = df.loc[positive_mask[positive_mask].index, 'date']
                valid_neg_dates = df.loc[positive_mask[~positive_mask].index, 'date']

                ax2.bar(valid_pos_dates, growth_data[positive_mask],
                        color=positive_growth_color, width=bar_width, alpha=0.8, label='Positive Growth')
                ax2.bar(valid_neg_dates, growth_data[~positive_mask],
                        color=negative_growth_color, width=bar_width, alpha=0.8, label='Negative/Zero Growth')

                ax2.axhline(y=0, color=plt.rcParams['axes.edgecolor'], linestyle='-', linewidth=0.5)
                ax2.set_title(f'Daily {target_type_label} Growth Rate (%)', fontsize=11, weight='semibold') # Dynamic title
                ax2.set_ylabel('Growth (%)', fontsize=9)
                ax2.tick_params(axis='x', labelsize=8, rotation=15)
                ax2.tick_params(axis='y', labelsize=8)
                ax2.grid(True, linestyle='--', alpha=0.4)

                # Calculate robust Y limits using quantiles on valid numeric growth data
                numeric_growth = growth_data.dropna() # Already handled inf/nan above
                if not numeric_growth.empty:
                    q05 = numeric_growth.quantile(0.05); q95 = numeric_growth.quantile(0.95)
                    # Avoid issues if all values are the same
                    if q05 == q95:
                        lim_bottom = q05 - 5
                        lim_top = q95 + 5
                    else:
                        y_range = q95 - q05
                        y_padding = max(5, y_range * 0.1) # Ensure minimum padding
                        lim_bottom = q05 - y_padding
                        lim_top = q95 + y_padding

                    # Ensure limits are not equal after padding
                    if lim_bottom >= lim_top: lim_bottom -= 1; lim_top += 1

                    ax2.set_ylim(bottom=lim_bottom, top=lim_top)
                else:
                     ax2.set_ylim(-10, 10) # Default if no valid growth data

                ax2.set_xlim(left=xmin_limit_date, right=xmax_limit_date) # Apply X limit
            else:
                 ax2.text(0.5, 0.5, "Growth rate data unavailable/invalid", ha='center', va='center', transform=ax2.transAxes, color=text_color)
                 ax2.set_ylim(-10, 10); ax2.set_xlim(left=xmin_limit_date, right=xmax_limit_date)
        else:
             ax2.text(0.5, 0.5, "Growth rate column missing", ha='center', va='center', transform=ax2.transAxes, color=text_color)
             ax2.set_ylim(-10, 10); ax2.set_xlim(left=xmin_limit_date, right=xmax_limit_date)

        # --- Plot 3: Monthly Average Target Value (Bar) ---
        if 'month' in df.columns and target_col_name in df.columns:
             # Create a copy to avoid modifying the original df slice
             monthly_data = df[['month', target_col_name]].copy()
             # Ensure month is numeric (should be int after processing, but check)
             monthly_data['month'] = pd.to_numeric(monthly_data['month'], errors='coerce')
             monthly_data.dropna(subset=['month'], inplace=True)

             if not monthly_data.empty:
                monthly_data['month'] = monthly_data['month'].astype(int)
                # Ensure target column is numeric for aggregation
                numeric_monthly_target = pd.to_numeric(monthly_data[target_col_name], errors='coerce')
                monthly_data[target_col_name] = numeric_monthly_target # Assign back potentially coerced data
                monthly_data.dropna(subset=[target_col_name], inplace=True) # Drop rows where target became NaN

                if not monthly_data.empty:
                    # Group by month and calculate the mean of the target column
                    monthly_avg = monthly_data.groupby('month')[target_col_name].mean()
                    # Reindex to ensure all 12 months are present, fill missing with 0
                    monthly_avg = monthly_avg[monthly_avg.index.isin(range(1,13))].reindex(range(1, 13), fill_value=0)

                    if not monthly_avg.empty:
                        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        ax3.bar(monthly_avg.index, monthly_avg.values, color=monthly_color, alpha=0.8)
                        ax3.set_title(f'Average Daily {target_type_label} per Month', fontsize=11, weight='semibold') # Dynamic title
                        ax3.set_ylabel(f'Avg {target_type_label}', fontsize=9) # Dynamic label
                        ax3.set_xticks(range(1, 13)); ax3.set_xticklabels(months, rotation=45, ha="right")
                        ax3.tick_params(axis='x', labelsize=8)
                        ax3.tick_params(axis='y', labelsize=8)
                        ax3.grid(True, axis='y', linestyle='--', alpha=0.4)
                        # Calculate Y limits based on monthly averages
                        max_y3 = monthly_avg.max()
                        ax3.set_ylim(bottom=0, top=max(max_y3 * 1.05 if max_y3 > 0 else 10, 10)) # Min top limit of 10
                    else:
                        ax3.text(0.5, 0.5, "Monthly data aggregation failed (no data after cleaning)", ha='center', va='center', transform=ax3.transAxes, color=text_color)
                        ax3.set_ylim(0, 10)
                else:
                     ax3.text(0.5, 0.5, "No valid numeric target data for monthly average", ha='center', va='center', transform=ax3.transAxes, color=text_color)
                     ax3.set_ylim(0, 10)
             else:
                 ax3.text(0.5, 0.5, "Month data invalid or empty", ha='center', va='center', transform=ax3.transAxes, color=text_color)
                 ax3.set_ylim(0, 10)
        else:
             ax3.text(0.5, 0.5, f"Month or {target_type_label} data unavailable", ha='center', va='center', transform=ax3.transAxes, color=text_color)
             ax3.set_ylim(0, 10)

        # --- Auto-format Date Ticks for limited range ---
        for ax in [ax1, ax2]:
             try: # Add try-except around locator/formatter in case limits cause issues
                 locator = mdates.AutoDateLocator(minticks=4, maxticks=10) # Allow slightly more ticks
                 formatter = mdates.ConciseDateFormatter(locator)
                 ax.xaxis.set_major_locator(locator)
                 ax.xaxis.set_major_formatter(formatter)
             except Exception as e:
                  print(f"[Analysis Plot] Warning: Failed to apply auto date ticks: {e}")
                  # Fallback: Just rotate existing labels if formatter fails
                  plt.setp(ax.get_xticklabels(), rotation=30, ha='right')

        return fig

    except Exception as e:
        print(f"[Analysis Plot] Error during plotting for {target_type_label}: {e}")
        traceback.print_exc()
        if fig: plt.close(fig)
        # Return error figure (using config colors)
        fig_err, ax_err = plt.subplots(figsize=(10, 7))
        error_color = config.PLOT_COLORS_DARK.get('negative_growth', '#FF0000') # Use config color or default red
        fig_err.patch.set_facecolor(config.DARK_PLOT_STYLE.get("figure.facecolor", "#000000")) # Set fig background
        ax_err.set_facecolor(config.DARK_PLOT_STYLE.get("axes.facecolor", "#000000")) # Set axes background
        ax_err.text(0.5, 0.5, f"Error generating analysis plot for {target_type_label}:\n{e}",
                    ha='center', va='center', color=error_color, wrap=True, fontsize=12)
        # Hide axes details for error plot
        ax_err.set_xticks([]); ax_err.set_yticks([])
        ax_err.spines['top'].set_visible(False); ax_err.spines['right'].set_visible(False)
        ax_err.spines['bottom'].set_visible(False); ax_err.spines['left'].set_visible(False)
        return fig_err


def calculate_analysis_stats(df, target_col_name):
    """Calculates key statistics from the processed DataFrame for the specified target."""
    target_type_label = target_col_name.capitalize()
    print(f"[Analysis Stats] Calculating stats for {target_type_label}...")
    if df is None or df.empty:
        print("[Analysis Stats] Input data is empty.")
        return {"error": "Input data is empty"}

    stats_values = {}
    try:
        if target_col_name not in df.columns or df[target_col_name].isnull().all():
            print(f"[Analysis Stats] Target column '{target_col_name}' missing or all NaN.")
            return {"error": f"{target_type_label} data missing"}

        # Convert target column to numeric robustly for calculations
        numeric_target = pd.to_numeric(df[target_col_name], errors='coerce').dropna()
        if numeric_target.empty:
             print(f"[Analysis Stats] No valid numeric '{target_col_name}' data found.")
             return {"error": f"No valid {target_type_label} data"}

        # Raw calculations based on the target column
        raw_total = numeric_target.sum()
        raw_avg = numeric_target.mean()
        raw_max = numeric_target.max()
        raw_peak_date = None
        # Find peak date using the original index on the numeric target data
        if 'date' in df and not numeric_target.empty:
            try:
                max_numeric_idx = numeric_target.idxmax() # Get index from the filtered numeric series
                if pd.notna(max_numeric_idx) and max_numeric_idx in df.index: # Check if index exists in original df
                    raw_peak_date = df.loc[max_numeric_idx, 'date']
            except ValueError: pass # idxmax raises ValueError if data is all NaN (already handled)
            except KeyError: pass # Handle if index somehow doesn't align

        stats_values["raw_total"] = raw_total
        stats_values["raw_avg"] = raw_avg
        stats_values["raw_max"] = raw_max
        stats_values["raw_peak_date"] = raw_peak_date

        # Risk level and trend based on 'growth_rate' (which itself is based on the target)
        stats_values["risk_level"] = "Medium"; stats_values["trend_desc"] = "Stable"
        if 'growth_rate' in df and not df['growth_rate'].isnull().all() and len(df) >= 7:
            # Calculate mean growth over the last 7 days robustly
            recent_growth_numeric = pd.to_numeric(df['growth_rate'].iloc[-7:], errors='coerce').dropna()
            if not recent_growth_numeric.empty:
                recent_growth = recent_growth_numeric.mean()
                if pd.notna(recent_growth):
                    # Define thresholds for risk/trend (can be adjusted)
                    if recent_growth > 5: stats_values["risk_level"] = "High"; stats_values["trend_desc"] = "↗️ Increasing"
                    elif recent_growth < -5: stats_values["risk_level"] = "Low"; stats_values["trend_desc"] = "↘️ Decreasing"
                    elif recent_growth > 1: stats_values["risk_level"] = "Medium"; stats_values["trend_desc"] = "↗️ Slightly Inc" # Finer grain trend
                    elif recent_growth < -1: stats_values["risk_level"] = "Low"; stats_values["trend_desc"] = "↘️ Slightly Dec" # Finer grain trend
                    # else: remains Medium / Stable
                else:
                    stats_values["trend_desc"] = "Growth unclear (NaN)" # Mean was NaN
            else:
                stats_values["trend_desc"] = "Growth unclear (No recent data)" # No numeric data in last 7 days
        elif 'growth_rate' in df and not df.empty:
            stats_values["trend_desc"] = "Insufficient history"
        else:
            stats_values["trend_desc"] = "Growth N/A"

        # --- Formatted Stats (generic names, context comes from UI) ---
        stats_values["total_fmt"] = f"{int(stats_values['raw_total']):,}" if pd.notna(stats_values['raw_total']) else "N/A"
        stats_values["avg_daily_fmt"] = f"{stats_values['raw_avg']:.1f}" if pd.notna(stats_values['raw_avg']) else "N/A"
        peak_date_str = stats_values["raw_peak_date"].strftime('%b %d, %Y') if pd.notna(stats_values["raw_peak_date"]) else "N/A"
        stats_values["peak_daily_fmt"] = f"{int(stats_values['raw_max']):,}" if pd.notna(stats_values['raw_max']) else "N/A"
        stats_values["peak_date_fmt"] = peak_date_str

        # Add the target type to the dictionary for context if needed elsewhere
        stats_values["target_type"] = target_type_label

        print(f"[Analysis Stats] Calculated for {target_type_label}: {stats_values}")
        return stats_values
    except Exception as e:
        print(f"Error calculating analysis statistics for {target_type_label}: {e}")
        traceback.print_exc()
        return {"error": f"Could not calculate {target_type_label} stats"}
