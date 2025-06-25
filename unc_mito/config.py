"""Configuration settings for the UNC mitochondria viewer."""

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'unc_mito', 'static')

# Data paths
MATERIALIZATION_CSV = os.environ.get(
    'MITO_CSV_PATH',
    os.path.join(BASE_DIR, 'data', '36750893213_mito_materialization.csv')
)

# URLs
MITO_URL = "precomputed://https://rhoana.rc.fas.harvard.edu/ng/h01_mito/36750893213"
NEURON_URL = "precomputed://gs://h01-release/data/20210601/c3"

# Screenshot settings
SCREENSHOTS_DIR = os.path.join(STATIC_DIR, 'screenshots')
DEFAULT_SCREENSHOT = os.path.join(STATIC_DIR, 'img', 'default_mito.png') 