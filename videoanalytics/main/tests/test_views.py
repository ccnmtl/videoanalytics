from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from pagetree.helpers import get_hierarchy
from pagetree.tests.factories import UserFactory


class BasicTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_root(self):
        response = self.client.get("/")
        self.assertEquals(response.status_code, 302)

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
        r = self.client.get("/pages/a/section-1/")
        self.assertEqual(r.status_code, 302)

    def test_edit_page(self):
        r = self.client.get("/pages/a/edit/section-1/")
        self.assertEqual(r.status_code, 302)


class PagetreeViewTestsLoggedIn(TestCase):
    def setUp(self):
        self.client = Client()

        self.hierarchy = get_hierarchy("a", "/pages/a/")
        self.root = self.hierarchy.get_root()
        self.root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

        self.hierarchy_b = get_hierarchy("b", "/pages/b/")
        root = self.hierarchy_b.get_root()
        root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

        self.user = UserFactory()
        self.client.login(username=self.user.username, password="test")

        self.superuser = UserFactory(is_superuser=True)

    def test_page(self):
        r = self.client.get("/pages/a/section-1/")
        self.assertEqual(r.status_code, 200)

        r = self.client.get('/pages/b/section-1', follow=True)
        self.assertEqual(r.status_code, 200)
        self.assertEquals(r.redirect_chain,  [('/pages/a/section-1/', 302)])

    def test_edit_page(self):
        # you must be a superuser to edit pages
        r = self.client.get("/pages/a/edit/section-1/")
        self.assertEqual(r.status_code, 302)

        self.client.login(username=self.superuser.username, password="test")
        r = self.client.get("/pages/a/edit/section-1/")
        self.assertEqual(r.status_code, 200)


class ChangePasswordTest(TestCase):

    def test_logged_out(self):
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 302)

    def test_user(self):
        user = UserFactory()
        self.assertTrue(self.client.login(
            username=user.username, password="test"))
        response = self.client.get('/accounts/password_change/')
        self.assertEquals(response.status_code, 200)


class IndexViewTest(TestCase):

    def test_anonymous_user(self):
        response = self.client.get('/', follow=True)
        self.assertTrue('Get Started' in response.content)
        self.assertFalse('Log Out' in response.content)
        self.assertEquals(response.status_code, 200)

    def test_user(self):
        hierarchy = get_hierarchy("a", "/pages/a/")
        root = hierarchy.get_root()
        root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

        user = UserFactory()
        self.assertTrue(self.client.login(
            username=user.username, password="test"))
        response = self.client.get('/')
        self.assertEquals(response.status_code, 302)


class ReportViewTest(TestCase):

    def test_access_denied(self):
        url = reverse('report-view')

        # not logged in
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

        user = UserFactory()
        self.client.login(username=user.username, password="test")
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

    def test_user(self):
        user = UserFactory(is_superuser=True, is_staff=True)
        self.client.login(username=user.username, password="test")
        url = reverse('report-view')

        # facilitator
        self.client.login(username=user.username, password="test")
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
