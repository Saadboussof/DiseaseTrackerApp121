# EpiForecast - Disease Tracking and Prediction Application

A comprehensive disease surveillance and forecasting application built with Python and Tkinter, designed to analyze and predict disease trends for multiple epidemiological datasets.

## Features

### 🦠 Multi-Disease Support
- **COVID-19**: Cases and deaths analysis with country-specific data
- **Influenza (Grippe)**: Weekly surveillance data processing
- **Zika Virus**: Cases and deaths tracking
- **Simulated Diseases**: Built-in simulation capabilities for testing

### 📊 Advanced Analytics
- **Trend Analysis**: Historical data visualization with growth rate calculations
- **Statistical Dashboard**: Real-time statistics with animated cards
- **Risk Assessment**: Automated risk level classification
- **Monthly Aggregation**: Seasonal pattern analysis

### 🔮 Predictive Modeling
- **Machine Learning**: LSTM-based forecasting models
- **Customizable Forecasts**: 30-730 day prediction ranges
- **Visual Predictions**: Interactive charts with confidence intervals
- **Performance Metrics**: Peak detection and trend statistics

### 🎨 Modern UI
- **Dark Theme**: Professional dark-themed interface
- **Animated Components**: Particle background effects and loading indicators
- **Responsive Design**: Adaptive layout with gradient frames
- **Interactive Charts**: Matplotlib integration with navigation tools

## Installation

### Prerequisites
```bash
pip install pandas numpy matplotlib scikit-learn tensorflow tkinter pillow
```

### Required Dependencies
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Data visualization
- **scikit-learn**: Machine learning utilities
- **tensorflow**: Neural network models
- **tkinter**: GUI framework (usually included with Python)
- **pillow**: Image processing for UI components

### Project Structure
```
DiseaseTrackerApp/
├── main_app.py              # Main application controller
├── config.py                # Configuration settings
├── data_loader.py           # Data loading utilities
├── processing.py            # Data preprocessing pipeline
├── analysis.py              # Statistical analysis functions
├── prediction.py            # Machine learning models
├── ui_components.py         # Custom UI widgets
├── views/
│   ├── __init__.py
│   ├── dashboard_view.py    # Overview dashboard
│   ├── analysis_view.py     # Trend analysis view
│   └── prediction_view.py   # Forecasting interface
└── disease/                 # Data directory (optional)
```

## Usage

### Starting the Application
```bash
python main_app.py
```

### Basic Workflow
1. **Select Disease**: Choose from COVID-19, Grippe, Zika, or simulated datasets
2. **Auto-Loading**: Data loads automatically upon disease selection
3. **Choose Parameters**: Select country and target (Cases/Deaths)
4. **Analyze**: Generate statistical analysis and visualizations
5. **Predict**: Create forecasts using machine learning models
6. **Export**: Save cleaned data for all countries

### Navigation
- **🏠 Dashboard**: Overview statistics and current status
- **📊 Analysis**: Detailed trend analysis and historical charts
- **🔮 Prediction**: Machine learning forecasts and projections

## Data Sources

### COVID-19
- Format: CSV with country, date, cases, deaths columns
- Processing: Country-specific filtering and cleaning
- Targets: Cases and Deaths analysis

### Influenza (Grippe)
- Format: Weekly surveillance data
- Processing: Resampling to daily frequency
- Target: Cases only (deaths not available)

### Zika Virus
- Format: Similar to COVID-19 structure
- Processing: Country and target-specific filtering
- Targets: Cases and Deaths analysis

## Configuration

Key settings in `config.py`:
```python
# Application Settings
APP_TITLE = "EpiForecast Dark v1.18"
WINDOW_GEOMETRY = "1450x900"

# Prediction Parameters
PREDICTION_MIN_DAYS = 30
PREDICTION_MAX_DAYS = 730
PREDICTION_DEFAULT_DAYS = 360

# Data Files
COVID_LOCAL_DATA_FILE = "path/to/covid_data.csv"
GRIPPE_DATA_SOURCE = "path/to/grippe_data.csv"
ZIKA_DATA_SOURCE = "path/to/zika_data.csv"
```

## Features in Detail

### Statistical Analysis
- **Growth Rate Calculation**: Daily percentage changes
- **Moving Averages**: 7-day smoothed trends
- **Monthly Aggregation**: Seasonal pattern detection
- **Risk Classification**: Automatic low/medium/high assessment

### Machine Learning Models
- **LSTM Networks**: Long Short-Term Memory for time series
- **Feature Engineering**: Date-based and lag features
- **Data Scaling**: MinMax normalization for neural networks
- **Validation**: Train/test split with performance metrics

### Export Functionality
- **Bulk Processing**: All countries processed simultaneously
- **Clean Data Export**: Preprocessed datasets ready for analysis
- **Multiple Formats**: CSV export with encoding support
- **Error Handling**: Robust processing with detailed logging

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all dependencies are installed
2. **Data File Missing**: Check file paths in `config.py`
3. **Memory Issues**: Large datasets may require system optimization
4. **Display Problems**: Update graphics drivers for smooth animations

### Performance Tips
- Close unused applications when processing large datasets
- Use SSD storage for faster data loading
- Ensure adequate RAM (8GB+ recommended)
- Update Python to latest stable version

## Development

### Architecture
- **MVC Pattern**: Separation of model, view, and controller logic
- **Threading**: Background processing for data loading and analysis
- **Event-Driven**: Responsive UI with callback-based interactions
- **Modular Design**: Separate modules for different functionalities

### Extending the Application
- Add new diseases by implementing data loaders
- Create custom analysis functions in `analysis.py`
- Develop new prediction models in `prediction.py`
- Design additional UI views in the views/ directory

## License

This project is developed for epidemiological research and education purposes. Please ensure compliance with data usage policies when working with real disease surveillance data.

## Support

For technical issues or questions:
- Check console output for detailed error messages
- Verify data file formats match expected structure
- Ensure all dependencies are correctly installed
- Review configuration settings for accuracy

---

**EpiForecast** - Advanced Disease Surveillance and Prediction Platform
