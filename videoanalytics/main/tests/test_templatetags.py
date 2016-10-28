from django.test.client import RequestFactory
from django.test.testcases import TestCase
from pagetree.models import Hierarchy, Section
from pagetree.tests.factories import UserFactory, ModuleFactory, \
    UserPageVisitFactory
from quizblock.models import Quiz, Submission, Response, Question, Answer
from quizblock.tests.test_templatetags import MockNodeList

from videoanalytics.main.templatetags.accessible import AccessibleNode
from videoanalytics.main.templatetags.quizsummary import IfQuizCompleteNode, \
    GetQuizSummary


class TestAccessible(TestCase):

    def setUp(self):
        self.user = UserFactory(is_superuser=True)

        ModuleFactory('one', '/pages/one/')
        self.hierarchy = Hierarchy.objects.get(name='one')

        self.sections = self.hierarchy.get_root().get_descendants()

        self.request = RequestFactory().get('/pages/%s/' % self.hierarchy.name)
        self.request.user = self.user

    def test_render_first_page(self):
        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.sections[0])
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertTrue(nlTrue.rendered)
        self.assertFalse(nlFalse.rendered)

    def test_render_no_visits(self):
        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.sections[1])
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertFalse(nlTrue.rendered)
        self.assertTrue(nlFalse.rendered)

    def test_render_incomplete_visit(self):
        UserPageVisitFactory(user=self.user, section=self.sections[0])

        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.sections[1])
        out = node.render(context)
        self.assertEqual(out, None)
        self.assertFalse(nlTrue.rendered)
        self.assertTrue(nlFalse.rendered)

    def test_render_complete_visit(self):
        UserPageVisitFactory(
            user=self.user, section=self.sections[0], status='complete')

        nlTrue = MockNodeList()
        nlFalse = MockNodeList()

        node = AccessibleNode('section', nlTrue, nlFalse)
        context = dict(request=self.request, section=self.sections[1])
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
        ques1 = Question.objects.create(quiz=self.quiz, text='question_one',
                                        question_type='single choice')
        Answer.objects.create(question=ques1, label='a',
                              value='a', correct=True)
        Answer.objects.create(question=ques1, label='b', value='b')

        ques2 = Question.objects.create(quiz=self.quiz, text='question_two',
                                        question_type='multiple choice')
        Answer.objects.create(question=ques2, label='a',
                              value='a', correct=True)
        Answer.objects.create(question=ques2, label='b', value='b')
        Answer.objects.create(question=ques2, label='c',
                              value='c', correct=True)

        # No submission
        self.assert_render_false()

        # Empty submission
        s = Submission.objects.create(quiz=self.quiz, user=self.user)
        self.assert_render_false()

        # ques1 response (single choice)
        Response.objects.create(question=ques1, submission=s, value='a')
        self.assert_render_false()

        # ques2 response - 1 answer
        Response.objects.create(question=ques2, submission=s, value='a')
        self.assert_render_true()

        # ques2 response - 2 answers
        Response.objects.create(question=ques2, submission=s, value='b')
        self.assert_render_true()

        # ques2 response - 3 answers
        Response.objects.create(question=ques2, submission=s, value='b')
        self.assert_render_true()


class QuizSummaryTest(TestCase):

    def setUp(self):
        self.user = UserFactory()
        self.user.profile.research_group = 'one'
        self.user.profile.save()

        self.quiz = Quiz.objects.create()

        ModuleFactory('one', '/pages/one/')
        section = Section.objects.get(slug='one')
        section.append_pageblock('Q', 'assessment', content_object=self.quiz)

        self.ques1 = Question.objects.create(
            quiz=self.quiz, text='one', question_type='single choice',
            css_extra='t1', explanation='a')
        Answer.objects.create(question=self.ques1, label='a',
                              value='a', correct=True)
        Answer.objects.create(question=self.ques1, label='b', value='b')

        self.ques2 = Question.objects.create(
            quiz=self.quiz, text='two', question_type='single choice',
            css_extra='t1', explanation='a')
        Answer.objects.create(
            question=self.ques2, label='a', value='a', correct=True)
        Answer.objects.create(question=self.ques2, label='b', value='b')

        self.ques3 = Question.objects.create(
            quiz=self.quiz, text='three', question_type='single choice',
            css_extra='t1', explanation='a')
        Answer.objects.create(
            question=self.ques3, label='a', value='a', correct=True)
        Answer.objects.create(question=self.ques3, label='b', value='b')

        ques4 = Question.objects.create(
            quiz=self.quiz, text='four', question_type='single choice',
            css_extra='t2', explanation='b')
        Answer.objects.create(
            question=ques4, label='a', value='a', correct=True)
        Answer.objects.create(question=ques4, label='b', value='b')

    def test_no_submission(self):
        ctx = {'user': self.user, 'cls': 'assessment'}

        # No submission
        GetQuizSummary('user', 'cls', 'results').render(ctx)
        self.assertTrue('results' in ctx)
        self.assertEquals(len(ctx['results']), 2)

        self.assertEquals(ctx['results'][0]['title'], 't1')
        self.assertEquals(ctx['results'][0]['explanation'], 'a')
        self.assertEquals(ctx['results'][0]['score'], 0)
        self.assertFalse(ctx['results'][0]['passed'])

        self.assertEquals(ctx['results'][1]['title'], 't2')
        self.assertEquals(ctx['results'][1]['explanation'], 'b')
        self.assertEquals(ctx['results'][1]['score'], 0)
        self.assertFalse(ctx['results'][1]['passed'])

    def test_one_correct(self):
        ctx = {'user': self.user, 'cls': 'assessment'}
        s = Submission.objects.create(quiz=self.quiz, user=self.user)
        Response.objects.create(question=self.ques1, submission=s, value='a')
        Response.objects.create(question=self.ques2, submission=s, value='b')
        Response.objects.create(question=self.ques3, submission=s, value='b')

        GetQuizSummary('user', 'cls', 'results').render(ctx)
        self.assertEquals(ctx['results'][0]['title'], 't1')
        self.assertEquals(ctx['results'][0]['score'], 1)
        self.assertFalse(ctx['results'][0]['passed'])

    def test_two_correct(self):
        ctx = {'user': self.user, 'cls': 'assessment'}
        s = Submission.objects.create(quiz=self.quiz, user=self.user)
        Response.objects.create(question=self.ques1, submission=s, value='a')
        Response.objects.create(question=self.ques2, submission=s, value='a')
        Response.objects.create(question=self.ques3, submission=s, value='b')

        GetQuizSummary('user', 'cls', 'results').render(ctx)
        self.assertEquals(ctx['results'][0]['title'], 't2')
        self.assertEquals(ctx['results'][1]['title'], 't1')
        self.assertEquals(ctx['results'][1]['score'], 2)
        self.assertTrue(ctx['results'][1]['passed'])

    def test_all_correct(self):
        ctx = {'user': self.user, 'cls': 'assessment'}
        s = Submission.objects.create(quiz=self.quiz, user=self.user)
        Response.objects.create(question=self.ques1, submission=s, value='a')
        Response.objects.create(question=self.ques2, submission=s, value='a')
        Response.objects.create(question=self.ques3, submission=s, value='a')

        GetQuizSummary('user', 'cls', 'results').render(ctx)
        self.assertEquals(ctx['results'][0]['title'], 't2')
        self.assertEquals(ctx['results'][1]['title'], 't1')
        self.assertEquals(ctx['results'][1]['score'], 3)
        self.assertTrue(ctx['results'][1]['passed'])
