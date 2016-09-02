from json import loads
import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.test import TestCase
from django.test.client import Client, RequestFactory
from pagetree.helpers import get_hierarchy
from pagetree.models import UserPageVisit

from videoanalytics.main.models import UserVideoView


class BasicTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_root(self):
        response = self.client.get("/")
        self.assertEquals(response.status_code, 200)

    def test_smoketest(self):
        response = self.client.get("/smoketest/")
        self.assertEquals(response.status_code, 200)
        assert "PASS" in response.content


class PagetreeViewTestsLoggedOut(TestCase):
    def setUp(self):
        self.client = Client()
        self.hierarchy = get_hierarchy("en", "/pages/en/")
        self.root = self.hierarchy.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

    def test_page(self):
        r = self.client.get("/pages/en/section-1/")
        self.assertEqual(r.status_code, 302)

    def test_edit_page(self):
        r = self.client.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 302)


class PagetreeViewTestsLoggedIn(TestCase):
    def setUp(self):
        self.client = Client()

        self.hierarchy = get_hierarchy("en", "/pages/en/")
        self.root = self.hierarchy.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })
        self.user = User.objects.create(username="testuser")
        self.user.set_password("test")
        self.user.save()

        self.client.login(username="testuser", password="test")
        self.superuser = User.objects.create(
            username="superuser", is_superuser=True)
        self.superuser.set_password("test")
        self.superuser.save()

    def test_page(self):
        r = self.client.get("/pages/en/section-1/")
        self.assertEqual(r.status_code, 200)

    def test_edit_page(self):
        self.assertTrue(self.user.is_authenticated())

        # you must be a superuser to edit pages
        r = self.client.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 302)

        self.client.login(username="superuser", password="test")
        r = self.client.get("/pages/en/edit/section-1/")
        self.assertEqual(r.status_code, 200)


class ChangePasswordTest(TestCase):

    def test_logged_out(self):
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 405)

    def test_user(self):
        self.assertTrue(self.client.login(
            username=self.user.username, password="test"))
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 200)


class IndexViewTest(TestCase):

    def test_anonymous_user(self):
        response = self.client.get('/')
        self.assertTrue('Log In' in response.content)
        self.assertFalse('Log Out' in response.content)
        self.assertEquals(response.template_name[0], "main/splash.html")
        self.assertEquals(response.status_code, 200)

    def test_user(self):
        self.assertTrue(self.client.login(
            username=self.user.username, password="test"))
        response = self.client.get('/')
        self.assertEquals(response.template_name[0], "main/facilitator.html")
        self.assertEquals(response.status_code, 200)
        self.assertFalse('Log In' in response.content)
        self.assertTrue('Log Out' in response.content)
        self.assertTrue('Dashboard' in response.content)


class LoginTest(TestCase):

    def test_login_get(self):
        response = self.client.get('/accounts/login/')
        self.assertEquals(response.status_code, 405)

    def test_login_post_noajax(self):
        response = self.client.post('/accounts/login/',
                                    {'username': self.user.username,
                                     'password': 'test'})
        self.assertEquals(response.status_code, 405)

    def test_login_post_ajax(self):
        response = self.client.post('/accounts/login/',
                                    {'username': '',
                                     'password': ''},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['error'], True)

        response = self.client.post('/accounts/login/',
                                    {'username': self.user.username,
                                     'password': 'test'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)
        the_json = json.loads(response.content)
        self.assertTrue(the_json['next'], "/")
        self.assertTrue('error' not in the_json)


class LogoutTest(TestCase):

    def test_logout_user(self):
        self.client.login(username=self.user.username, password="test")

        response = self.client.get('/accounts/logout/?next=/', follow=True)
        self.assertEquals(response.template_name[0], "main/splash.html")
        self.assertEquals(response.status_code, 200)
        self.assertTrue('Log In' in response.content)
        self.assertFalse('Log Out' in response.content)


class ReportViewTest(TestCase):

    def test_access_denied(self):
        url = reverse('report-view')

        # not logged in
        response = self.client.get(url)
        self.assertEquals(response.status_code, 405)

        # as participant
        self.login_participant()
        response = self.client.get(url)
        self.assertEquals(response.status_code, 405)

    def test_user(self):
        url = reverse('report-view')

        # facilitator
        self.client.login(username=self.user.username, password="test")
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
