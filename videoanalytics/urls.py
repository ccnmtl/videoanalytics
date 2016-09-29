import debug_toolbar
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_change, password_change_done, \
    password_reset_done, password_reset_confirm, password_reset_complete
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from videoanalytics.main.views import IndexView, ReportView, \
    RestrictedEditView, RestrictedPageView, TrackVideoView, VideoPageView


admin.autodiscover()

redirect_after_logout = getattr(settings, 'LOGOUT_REDIRECT_URL', None)

auth_urls = (r'^accounts/', include('django.contrib.auth.urls'))

logout_page = (r'^accounts/logout/$',
               'django.contrib.auth.views.logout',
               {'next_page': redirect_after_logout})
admin_logout_page = (r'^accounts/logout/$',
                     'django.contrib.auth.views.logout',
                     {'next_page': '/admin/'})

if hasattr(settings, 'CAS_BASE'):
    auth_urls = (r'^accounts/', include('djangowind.urls'))
    logout_page = (r'^accounts/logout/$',
                   'djangowind.views.logout',
                   {'next_page': redirect_after_logout})
    admin_logout_page = (r'^admin/logout/$',
                         'djangowind.views.logout',
                         {'next_page': redirect_after_logout})


urlpatterns = patterns(
    '',
    (r'^$', ensure_csrf_cookie(IndexView.as_view())),
    (r'^admin/', include(admin.site.urls)),

    # password change & reset. overriding to gate them.
    url(r'^accounts/password_change/$',
        password_change,
        name='password_change'),
    url(r'^accounts/password_change/done/$',
        password_change_done,
        name='password_change_done'),
    url(r'^password/reset/done/$', password_reset_done,
        name='password_reset_done'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        password_reset_confirm,
        name='password_reset_confirm'),
    url(r'^password/reset/complete/$',
        password_reset_complete, name='password_reset_complete'),

    auth_urls,

    url(r'^_impersonate/', include('impersonate.urls')),
    (r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    (r'smoketest/', include('smoketest.urls')),
    (r'^pagetree/', include('pagetree.urls')),
    (r'^quizblock/', include('quizblock.urls')),

    (r'^report/$', ReportView.as_view(), {}, 'report-view'),
    (r'^track/$', TrackVideoView.as_view()),

    # Group One
    (r'^pages/a/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="a", hierarchy_base="/pages/a/")),
    (r'^pages/a/(?P<path>.*)$', login_required(RestrictedPageView.as_view(
        hierarchy_name="a", hierarchy_base="/pages/a/", gated=True)),
        {}, 'view-alpha-page'),

    # Group Two
    (r'^pages/b/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="b", hierarchy_base="/pages/b/")),
    (r'^pages/b/(?P<path>.*)$', login_required(RestrictedPageView.as_view(
        hierarchy_name="b", hierarchy_base="/pages/b/", gated=True)),
     {}, 'view-beta-page'),

    # Videos
    (r'^pages/videos/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="videos", hierarchy_base="/pages/videos/")),
    (r'^pages/videos/(?P<path>.*)$', login_required(VideoPageView.as_view(
        hierarchy_name="videos", hierarchy_base="/pages/videos/", gated=True)),
     {}, 'view-beta-page')
)


if settings.DEBUG:
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)))
