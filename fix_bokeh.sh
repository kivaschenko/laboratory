#!/bin/bash

# Fix Bokeh plotting issues by installing compatible versions

echo "Fixing Bokeh compatibility issues..."

# Install compatible versions
pip install "bokeh>=3.0,<3.5" "pandas>=2.0,<2.2" "numpy>=1.24,<1.26"

echo "Testing Bokeh import..."
python3 -c "
import bokeh
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.embed import components
print(f'Bokeh version: {bokeh.__version__}')
print(f'Pandas version: {pd.__version__}')
print(f'NumPy version: {np.__version__}')
print('All imports successful!')
"

echo "Bokeh fix completed!"