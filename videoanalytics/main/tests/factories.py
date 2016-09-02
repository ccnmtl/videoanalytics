from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test.client import Client
from django.test.testcases import TestCase
import factory
from pagetree.models import Hierarchy
from pagetree.tests.factories import UserFactory, ModuleFactory
import simplejson

from videoanalytics.main.models import QuizSummaryBlock, YouTubeBlock


class PagetreeTestCase(TestCase):
    def setUp(self):
        super(PagetreeTestCase, self).setUp()

        ModuleFactory("en", "/pages/en/")
        ModuleFactory("es", "/pages/es/")

        self.hierarchy_en = Hierarchy.objects.get(name='en')
        self.hierarchy_es = Hierarchy.objects.get(name='es')


class QuizSummaryBlockFactory(factory.DjangoModelFactory):
    class Meta:
        model = QuizSummaryBlock
    quiz_class = "quiz class"


class YouTubeBlockFactory(factory.DjangoModelFactory):
    class Meta:
        model = YouTubeBlock
    video_id = 'abcdefg'
    title = 'Sample Title'
