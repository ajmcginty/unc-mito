# UNC Mitochondria Viewer

A web application for viewing and analyzing mitochondria from the H01 dataset. This tool provides an interactive interface to visualize mitochondria in 3D from multiple angles.

## Overview

This application allows users to:
- View mitochondria from the H01 dataset in a grid layout
- See each mitochondrion from 360 degrees with 8 different angles
- Navigate through large sets of mitochondria with pagination
- Generate and manage 3D visualizations with enhanced depth perception

## Data Sources

The application uses the following data sources:
- Mitochondria meshes: `precomputed://https://rhoana.rc.fas.harvard.edu/ng/h01_mito/36750893213`
- Full neuron data: `precomputed://gs://h01-release/data/20210601/c3`
- Materialization file: CSV containing mitochondria metadata (positions, IDs)

## Requirements

- Python 3.8+
- Flask
- NumPy
- Pandas
- CloudVolume
- PyVista
- Pillow

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd unc-mito
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Place your materialization CSV file in an accessible location
2. Update the CSV path in `unc_mito/routes.py`
3. Run the application:
```bash
flask run
```
4. Open a web browser and navigate to `http://localhost:5000`

## Project Structure

- `unc_mito/`: Main application package
  - `backend/`: Backend processing modules
    - `materialization.py`: Handles mitochondria data loading and processing
    - `screenshot_generator_360.py`: Generates 360-degree mitochondria views using CloudVolume and PyVista
  - `static/`: Static files (CSS, JavaScript, screenshots)
  - `templates/`: HTML templates
  - `routes.py`: Flask routes and API endpoints

## Technical Details

- Uses CloudVolume to fetch 3D mesh data from the H01 dataset
- Renders mitochondria using PyVista with enhanced 3D visualization features:
  - 360-degree views with 8 different angles
  - Eye-dome lighting for better depth perception
  - Edge enhancement and smooth shading
- Implements server-side screenshot generation for better performance
- Provides a responsive grid layout with client-side pagination and view controls

## Credits

Developed for the UNC Neuroscience Center to facilitate mitochondria analysis in the H01 dataset.

## License

[Add your license information here]
