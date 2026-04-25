import sys
import os
import importlib.util

# 1. Define the exact path to your real Flask app file
inner_app_path = os.path.join(os.path.dirname(__file__), 'sales-forecast', 'sales_forecasting', 'flask_app', 'app.py')

# 2. Add the subfolder to path so it can find 'models' and other imports
sys.path.append(os.path.dirname(inner_app_path))

# 3. Load the inner module manually to avoid the circular import name conflict
spec = importlib.util.spec_from_file_location("real_app", inner_app_path)
real_app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(real_app)

# 4. Expose the Flask instance as 'app' for Gunicorn
app = real_app.app
