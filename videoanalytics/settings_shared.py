# flake8: noqa
# Django settings for videoanalytics project.
import os.path
from ccnmtlsettings.shared import common

project = 'videoanalytics'
base = os.path.dirname(__file__)
locals().update(common(project=project, base=base))

PROJECT_APPS = [
    'videoanalytics.main',
]

USE_TZ = True
USE_I18N = True

TEMPLATES[0]['OPTIONS']['context_processors'].append(  # noqa
    'videoanalytics.main.views.context_processor'
)

MIDDLEWARE += [  # noqa
    'django.middleware.csrf.CsrfViewMiddleware'
]

INSTALLED_APPS += [  # noqa
    'bootstrap3',
    'typogrify',
    'bootstrapform',
    'django_extensions',
    'pagetree',
    'pageblocks',
    'quizblock',
    'videoanalytics.main'
]

PAGEBLOCKS = [
    'pageblocks.TextBlock',
    'pageblocks.HTMLBlock',
    'quizblock.Quiz',
    'main.QuizSummaryBlock',
    'main.YouTubeBlock']

MEDIA_ROOT = 'uploads'
