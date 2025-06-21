# config.py
"""Configuration constants for the Disease Tracker application."""

import os
import matplotlib.pyplot as plt # Needed for defining style

# ... (other UI config) ...
PLACEHOLDER_COLOR = "#6A5C94"

# --- File Paths ---
COVID_LOCAL_DATA_FILE = "disease\\compact_covid_data.csv"
GRIPPE_DATA_SOURCE = "disease\\influenza_weekly.csv" # Keep path
# DENGUE_DATA_SOURCE = "https://api.example.com/dengue"
# PALUDISME_DATA_SOURCE = "path/to/malaria_db_conn_string"

# --- COVID-19 Specific ---

ALLOWED_COVID_COUNTRIES = [ # Keep this list for COVID
    'United States', 'France', 'Algeria', 'Germany', 'Italy', 'Spain',
    'United Kingdom', 'China', 'Russia', 'India', 'Brazil', 'Canada',
    'Australia', 'Japan', 'South Korea', 'South Africa', 'Mexico',
    'Saudi Arabia', 'Turkey', 'Morocco']
COVID_RELEVANT_COLUMNS = [ # Keep relevant columns needed for BOTH cases and deaths
    'date', 'country', 'total_cases', 'new_cases', 'new_cases_smoothed',
    'total_deaths', 'new_deaths', 'new_deaths_smoothed', # Ensure death columns are here
    'hosp_patients',
    'weekly_hosp_admissions', 'icu_patients', 'stringency_index',
    'reproduction_rate', 'total_tests', 'new_tests', 'positive_rate',
    'tests_per_case', 'total_vaccinations', 'people_vaccinated',
    'people_fully_vaccinated', 'population', 'population_density', 'median_age'
]
COVID_MISSING_VALUE_THRESHOLD = 0.4
COVID_COLS_TO_FILL_ZERO = ['new_cases', 'new_deaths', 'total_cases', 'total_deaths'] # Added death cols
COVID_COLS_TO_DROP_EXPLICITLY = ['new_deaths_smoothed', 'new_cases_smoothed'] # Drop smoothed if using raw new_*

# --- Target Column Definitions ---
COVID_CASES_INPUT_COL = 'new_cases'      # Raw column name for cases in COVID file
COVID_DEATHS_INPUT_COL = 'new_deaths'    # Raw column name for deaths in COVID file
PREDICTION_CASES_TARGET_COL = 'cases'    # Standard internal name for cases
PREDICTION_DEATHS_TARGET_COL = 'deaths'  # Standard internal name for deaths


# --- Grippe Specific ---

GRIPPE_RAW_COUNTRY_COL = 'Country' # Raw column name for country in influenza file
GRIPPE_DATE_COL = 'EDATE'      # Raw column name for date in influenza file
GRIPPE_CASES_COL = 'ALL_INF'   # Raw column name for cases in influenza file
GRIPPE_DEATHS_COL = None # No specific death column identified in the provided list

# --- Zika Specific ---
ZIKA_DATA_FILE = "disease\\enhanced_zika_data_large.csv"
ZIKA_COUNTRY_COL = 'country'   # Raw column name for country in Zika file
ZIKA_DATE_COL = 'date'         # Raw column name for date in Zika file
ZIKA_CASES_COL = 'cases'       # Raw column name for cases in Zika file
ZIKA_DEATHS_COL = 'deaths'     # Raw column name for deaths in Zika file
ZIKA_RELEVANT_COLUMNS = [ # Similar to COVID_RELEVANT_COLUMNS
    'date', 'country', 'cases', 'deaths', 'population_density',
    'total_cases', 'new_cases_smoothed', 'total_deaths', 'new_deaths_smoothed',
    'hosp_patients', 'weekly_hosp_admissions', 'icu_patients', 'stringency_index',
    'reproduction_rate', 'total_tests', 'new_tests', 'positive_rate',
    'tests_per_case', 'total_vaccinations', 'people_vaccinated',
    'people_fully_vaccinated', 'population', 'median_age', 'gdp_per_capita',
    'continent', 'life_expectancy'
]
ALLOWED_ZIKA_COUNTRIES = [
    'United States', 'Brazil', 'France', 'Germany', 'Italy', 'Spain',
    'United Kingdom', 'China', 'Russia', 'India', 'Japan', 'South Korea', 
    'South Africa', 'Mexico', 'Canada', 'Australia', 'Turkey',
    'Saudi Arabia', 'Algeria', 'Morocco'
]

# --- Plotting ---
HISTORICAL_CONTEXT_DAYS = 120
DARK_PLOT_STYLE = {
    "figure.facecolor": "#261758", "axes.facecolor": "#261758",
    "axes.edgecolor": "#8A7CB4", "axes.labelcolor": "#8A7CB4",
    "axes.titlecolor": "#FFFFFF", "xtick.color": "#8A7CB4",
    "ytick.color": "#8A7CB4", "grid.color": "#3A2E70",
    "text.color": "#FFFFFF", "legend.facecolor": "#261758",
    "legend.edgecolor": "#8A7CB4", "legend.labelcolor": "#FFFFFF"
}
plt.style.use('dark_background')
plt.rcParams.update(DARK_PLOT_STYLE)

PLOT_COLORS_DARK = {
    # Cases Colors
    "daily_cases": "#FF3366",        # Pinkish-Red for daily cases
    "avg_line_cases": "#00CCB8",     # Teal for case average line
    "history_cases": "#00CCB8",      # Teal for case history line in prediction
    "prediction_cases": "#FC6657",   # Orange for case prediction line
    # Deaths Colors
    "daily_deaths": "#C70039",       # Darker Red/Crimson for daily deaths
    "avg_line_deaths": "#FFA500",    # Orange for death average line
    "history_deaths": "#FFA500",     # Orange for death history line in prediction
    "prediction_deaths": "#FF6347",  # Tomato/Coral for death prediction line
    # Common Colors
    "positive_growth": "#28A745",    # Green
    "negative_growth": "#B12025",    # Dark Red
    "monthly_avg": "#8A7CB4",        # Purple/Lavender
    "separator_lines": "#8A7CB4",    # Purple/Lavender for vlines
}


# --- Modeling ---
PREDICTION_MIN_DAYS = 30
PREDICTION_MAX_DAYS = 730
PREDICTION_DEFAULT_DAYS = 360

# --- UI ---
APP_TITLE = "EpiForecast v1.19" # version
WINDOW_GEOMETRY = "1450x900"
AVAILABLE_DISEASES = [
    "COVID-19", "Grippe", "Zika", # Added Zika disease
]
# Options for the target selector Combobox
ANALYSIS_TARGETS = ["Cases", "Deaths"]
DEFAULT_ANALYSIS_TARGET = "Cases"

# --- Modeling ---
PREDICTION_FEATURE_COLS = ['day_of_year', 'month', 'day', 'day_of_week']
# Target cols are defined above (PREDICTION_CASES_TARGET_COL, PREDICTION_DEATHS_TARGET_COL)
RF_N_ESTIMATORS = 100
RF_RANDOM_STATE = 42
