# flake8: noqa
from videoanalytics.settings_shared import *
from ccnmtlsettings.production import common

locals().update(
    common(
        project=project,
        base=base,
        INSTALLED_APPS=INSTALLED_APPS,
        STATIC_ROOT=STATIC_ROOT,
    ))

LOCALE_PATHS = ('/var/www/videoanalytics/videoanalytics/locale',)

try:
    from videoanalytics.local_settings import *
except ImportError:
    pass
