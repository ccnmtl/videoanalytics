import django.contrib.auth.views
import djangowind.views
import debug_toolbar
from django.conf import settings
from django.conf.urls import include, url
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

auth_urls = url(r'^accounts/', include('django.contrib.auth.urls'))

logout_page = url(r'^accounts/logout/$',
                  django.contrib.auth.views.logout,
                  {'next_page': redirect_after_logout})
admin_logout_page = url(r'^accounts/logout/$',
                        django.contrib.auth.views.logout,
                        {'next_page': '/admin/'})

if hasattr(settings, 'CAS_BASE'):
    auth_urls = url(r'^accounts/', include('djangowind.urls'))
    logout_page = url(r'^accounts/logout/$',
                      djangowind.views.logout,
                      {'next_page': redirect_after_logout})
    admin_logout_page = url(r'^admin/logout/$',
                            djangowind.views.logout,
                            {'next_page': redirect_after_logout})


urlpatterns = [
    url(r'^$', ensure_csrf_cookie(IndexView.as_view())),
    url(r'^admin/', include(admin.site.urls)),

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
    url(r'^stats/$', TemplateView.as_view(template_name="stats.html")),
    url(r'smoketest/', include('smoketest.urls')),
    url(r'^pagetree/', include('pagetree.urls')),
    url(r'^quizblock/', include('quizblock.urls')),

    url(r'^report/$', ReportView.as_view(), {}, 'report-view'),
    url(r'^track/$', TrackVideoView.as_view()),

    # Group One
    url(r'^pages/a/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="a", hierarchy_base="/pages/a/")),
    url(r'^pages/a/(?P<path>.*)$', login_required(RestrictedPageView.as_view(
        hierarchy_name="a", hierarchy_base="/pages/a/", gated=True)),
        {}, 'view-alpha-page'),

    # Group Two
    url(r'^pages/b/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="b", hierarchy_base="/pages/b/")),
    url(r'^pages/b/(?P<path>.*)$', login_required(RestrictedPageView.as_view(
        hierarchy_name="b", hierarchy_base="/pages/b/", gated=True)),
        {}, 'view-beta-page'),

    # Videos
    url(r'^pages/videos/edit/(?P<path>.*)$', RestrictedEditView.as_view(
        hierarchy_name="videos", hierarchy_base="/pages/videos/")),
    url(r'^pages/videos/(?P<path>.*)$', login_required(VideoPageView.as_view(
        hierarchy_name="videos", hierarchy_base="/pages/videos/", gated=True)),
        {}, 'view-beta-page'),
]


if settings.DEBUG:
    urlpatterns += [url(r'^__debug__/', include(debug_toolbar.urls))]
