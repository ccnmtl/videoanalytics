# flake8: noqa
from videoanalytics.settings_shared import *

try:
    from videoanalytics.local_settings import *
except ImportError:
    pass
