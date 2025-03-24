import sys
import os
import pytest

# Add the project root directory to the Python path before any tests are imported.
# This ensures that imports like 'from src.backend...' work correctly.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# You can also define shared fixtures here later if needed.
# For example, the db_fixture could potentially be moved here
# if multiple test files need the same database setup.