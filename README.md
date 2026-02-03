# BIThub - Datapad

A PyQt5-based desktop application for managing, visualizing, and analyzing test run data from CXL DNA BIT devices.

## Features

- **Database Management**: Connect to SQLite databases containing test runs, readings, and assay definitions
- **Remote Device Access**: SSH/SFTP connectivity to retrieve database files from embedded devices
- **Data Visualization**: Plot test signals with matplotlib (5-channel PD readings)
- **Google Sheets Integration** (optional): Log test results directly to Google Sheets for team collaboration
- **Export Capabilities**: Export test runs to CSV files with detailed readings and plots
- **Filtering & Search**: Filter runs by result (POS/NEG/INVALID), assay name, or date

## Project Structure

```
BIThub/
├── Datapad/
│   ├── datapad_main.py          # Main application entry point
│   ├── helpers/
│   │   ├── detectMethods.py     # BIT signal detection algorithms
│   │   ├── gcpApi.py            # Google Cloud Platform API utilities
│   │   ├── gsOps.py             # Google Sheets operations
│   │   ├── mongoOps.py          # MongoDB operations
│   │   └── sqlOps.py            # SQLite operations & data models
│   └── views/
│       ├── widgetsCtrl.py       # Widget controllers
│       ├── runsPlotWidget.py    # Signal plotting widget
│       └── resources/           # Qt UI files and compiled Python UI
bin/Build/
├── datapad_env.yml              # Conda environment specification
└── datapadBuild.py              # PyInstaller build script
```

## Requirements

- Python 3.9+
- PyQt5
- pandas
- matplotlib (3.6+)
- SQLAlchemy
- paramiko (for SSH/SFTP)
- gspread (optional, for Google Sheets)
- numpy

## Installation

1. Create a conda environment:

```bash
conda env create -f bin/Build/datapad_env.yml
conda activate datapadBuild
```

2. Or install dependencies via pip:

```bash
pip install pyqt5 pandas matplotlib sqlalchemy paramiko gspread numpy
```

## Usage

Run the main application:

```bash
cd BIThub/Datapad
python datapad_main.py
```

### Main Workflow

1. **Load Database**: Click "Load DB" to load test runs from a local SQLite database
2. **Browse Runs**: View test runs in the list, filter by result type or assay
3. **Visualize**: Double-click a run to view the 5-channel signal plot
4. **Export**: Select runs and export to CSV/PNG
5. **Log to Sheets**: Log selected runs to the configured Google Sheet (requires valid Google credentials)

## Database Schema

The application works with SQLite databases containing these tables:

| Table | Description |
|-------|-------------|
| `Runs` | Test run metadata (ID, sample ID, barcode, result) |
| `TargetResults` | Per-channel target results and voltage differences |
| `Readings` | Time-series PD readings (5 channels) |
| `LysisReadings` | Lysis phase temperature and timing data |
| `AssayDefinitions` | Assay protocol definitions |

## Notes

- Google Sheets integration is optional and will gracefully degrade if credentials are missing or expired
- The application uses matplotlib's `seaborn-v0_8-bright` style for plots (requires matplotlib 3.6+)

## License

Proprietary - Internal use only
