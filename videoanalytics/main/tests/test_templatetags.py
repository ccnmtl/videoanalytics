from django.test.client import RequestFactory
from django.test.testcases import TestCase
from pagetree.models import Hierarchy, Section
from pagetree.tests.factories import UserFactory, ModuleFactory, \
    UserPageVisitFactory
from quizblock.models import Quiz, Submission, Response, Question, Answer
from quizblock.tests.test_templatetags import MockNodeList
from videoanalytics.main.templatetags.accessible import AccessibleNode
from videoanalytics.main.templatetags.quizsummary import IfQuizCompleteNode


class TestAccessible(TestCase):

    def setUp(self):
        self.user = UserFactory(is_superuser=True)

        ModuleFactory("one", "/pages/one/")
        self.hierarchy = Hierarchy.objects.get(name='one')

        self.section_one = Section.objects.get(slug='one')

        self.hierarchy.get_root().add_child_section_from_dict({
            'label': 'Page Four',
            'slug': 'page-four',
            'pageblocks': [{
                'label': 'Content',
                'css_extra': '',
                'block_type': 'Quiz',
                'body': 'random text goes here',
                'description': 'a description',
                'rhetorical': False,
                'questions': [{
                    'question_type': 'short text',
                    'text': 'a question',
                    'explanation': 'an explanation',
                    'intro_text': 'intro text',
                    'answers': []
                }]
            }]
        })
        self.section_four = Section.objects.get(slug='page-four')

        self.request = RequestFactory().get('/pages/%s/' % self.hierarchy.name)
        self.request.user = self.user

    def test_render_no_pageblocks(self):
        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.section_one)
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertTrue(nlTrue.rendered)
        self.assertFalse(nlFalse.rendered)

    def test_render_quizblock_novisits(self):
        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.section_four)
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertFalse(nlTrue.rendered)
        self.assertTrue(nlFalse.rendered)

    def test_render_quizblock_visits_and_nosubmissions(self):
        UserPageVisitFactory(user=self.user,  status='complete',
                             section=self.hierarchy.get_root())
        for section in self.hierarchy.get_root().get_descendants():
            UserPageVisitFactory(
                user=self.user,  status='complete', section=section)

        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.section_four)
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertFalse(nlTrue.rendered)
        self.assertTrue(nlFalse.rendered)

    def test_issubmitted_quizblock_visits_and_submissions(self):
        UserPageVisitFactory(user=self.user, status='complete',
                             section=self.hierarchy.get_root())
        for section in self.hierarchy.get_root().get_descendants():
            UserPageVisitFactory(
                user=self.user,  status='complete', section=section)

        quiz = Quiz.objects.all()[0]
        question = quiz.question_set.all()[0]
        s = Submission.objects.create(quiz=quiz, user=self.user)
        Response.objects.create(question=question, submission=s, value="a")

        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.section_four)
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertTrue(nlTrue.rendered)
        self.assertFalse(nlFalse.rendered)


class FakeRequest(object):
    pass


class IfQuizCompleteTest(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.quiz = Quiz.objects.create()
        self.request = FakeRequest()

    def assert_render_true(self):
        nl1 = MockNodeList()
        nl2 = MockNodeList()

        node = IfQuizCompleteNode('quiz', nl1, nl2)
        self.request.user = self.user
        context = dict(request=self.request, quiz=self.quiz)
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertTrue(nl1.rendered)
        self.assertFalse(nl2.rendered)

    def assert_render_false(self):
        nl1 = MockNodeList()
        nl2 = MockNodeList()
        node = IfQuizCompleteNode('quiz', nl1, nl2)
        self.request.user = self.user
        context = dict(request=self.request, quiz=self.quiz)
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertFalse(nl1.rendered)
        self.assertTrue(nl2.rendered)

    def test_quiz_complete(self):
        ques1 = Question.objects.create(quiz=self.quiz, text="question_one",
                                        question_type="single choice")
        Answer.objects.create(question=ques1, label="a",
                              value="a", correct=True)
        Answer.objects.create(question=ques1, label="b", value="b")

        ques2 = Question.objects.create(quiz=self.quiz, text="question_two",
                                        question_type="multiple choice")
        Answer.objects.create(question=ques2, label="a",
                              value="a", correct=True)
        Answer.objects.create(question=ques2, label="b", value="b")
        Answer.objects.create(question=ques2, label="c",
                              value="c", correct=True)

        # No submission
        self.assert_render_false()

        # Empty submission
        s = Submission.objects.create(quiz=self.quiz, user=self.user)
        self.assert_render_false()

        # ques1 response (single choice)
        Response.objects.create(question=ques1, submission=s, value="a")
        self.assert_render_false()

        # ques2 response - 1 answer
        Response.objects.create(question=ques2, submission=s, value="a")
        self.assert_render_true()

        # ques2 response - 2 answers
        Response.objects.create(question=ques2, submission=s, value="b")
        self.assert_render_true()

        # ques2 response - 3 answers
        Response.objects.create(question=ques2, submission=s, value="b")
        self.assert_render_true()
