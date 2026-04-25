import sys
import os

# Define the paths
current_dir = os.path.dirname(os.path.abspath(__file__))
flask_app_dir = os.path.join(current_dir, 'sales-forecast', 'sales_forecasting', 'flask_app')

# Add the directory to sys.path
sys.path.append(flask_app_dir)

# Import the actual app from the subfolder
# Because the file is named main.py, 'import app' will correctly look for app.py in sys.path
import app as flask_module

# Expose the application instance
app = flask_module.app
