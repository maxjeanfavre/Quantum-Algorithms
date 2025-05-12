# config.py

import sys
import os

# Get the current file's directory and move up to the project root
root_path = os.path.dirname(os.path.abspath(__file__))

# Add the root path to the system path for importing
if root_path not in sys.path:
    sys.path.append(root_path)

# Also handle running from subdirectories
parent_path = os.path.abspath(os.path.join(root_path, ".."))
if parent_path not in sys.path:
    sys.path.append(parent_path)

