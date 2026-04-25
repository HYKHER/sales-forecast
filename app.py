import sys
import os

# Add the subdirectory to the Python path so it can find models and other files
path = os.path.join(os.path.dirname(__file__), 'sales-forecast', 'sales_forecasting', 'flask_app')
sys.path.append(path)

# Import the actual app from the subfolder
from app import app as application

# This is what Gunicorn will look for
app = application
