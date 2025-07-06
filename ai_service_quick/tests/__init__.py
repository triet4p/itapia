import sys
import os
init_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print(init_dir)
sys.path.append(init_dir)