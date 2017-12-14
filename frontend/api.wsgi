mport os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from api import app as application
