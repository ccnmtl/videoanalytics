# flake8: noqa
from settings_shared import *

try:
    from videoanalytics.local_settings import *
except ImportError:
    pass
