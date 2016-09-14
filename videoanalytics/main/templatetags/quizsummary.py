from django import template
from django.contrib.contenttypes.models import ContentType
from pagetree.models import PageBlock
from quizblock.models import Quiz


register = template.Library()


@register.assignment_tag
def is_user_correct(user, question):
    return question.is_user_correct(user)


def get_quizzes_by_css_class(hierarchy, cls):
    ctype = ContentType.objects.get_for_model(Quiz)
    blocks = PageBlock.objects.filter(content_type__pk=ctype.pk)
    blocks = blocks.filter(css_extra__contains=cls)
    blocks = blocks.filter(section__hierarchy=hierarchy)
    return blocks


class GetQuizSummary(template.Node):
    def __init__(self, user, quiz_class, var_name):
        self.user = user
        self.quiz_class = quiz_class
        self.var_name = var_name

    def render(self, context):
        u = context[self.user]
        cls = context[self.quiz_class]

        blocks = get_quizzes_by_css_class(u.profile.default_hierarchy(), cls)

        topics = {}
        for b in blocks:
            for question in b.content_object.question_set.all():
                if question.css_extra not in topics:
                    topics[question.css_extra] = {
                        'title': question.css_extra,
                        'explanation': question.explanation,
                        'score': 0,
                        'passed': 0
                    }

                if question.is_user_correct(u):
                    topics[question.css_extra]['score'] += 1
                    topics[question.css_extra]['passed'] = \
                        1 if topics[question.css_extra]['score'] > 1 else 0

        values = topics.values()
        values.sort(key=lambda x: x['passed'])
        context[self.var_name] = values

        return ''


@register.tag('get_quiz_summary')
def quizsummary(parser, token):
    user = token.split_contents()[1:][0]
    quiz_class = token.split_contents()[1:][1]
    var_name = token.split_contents()[1:][3]
    return GetQuizSummary(user, quiz_class, var_name)


def is_question_complete(question, user):
    answers = question.correct_answer_values()
    if len(answers) == 0:
        # No "correct" values for this question
        return True

    responses = question.user_responses(user)
    return len(responses) > 0


def is_quiz_complete(quiz, user):
    complete = True
    for question in quiz.question_set.all():
        complete = complete and is_question_complete(question, user)
    return complete


class IfQuizCompleteNode(template.Node):
    def __init__(self, quiz, nodelist_true, nodelist_false=None):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.quiz = quiz

    def render(self, context):
        quiz = context[self.quiz]
        user = context['request'].user

        if is_quiz_complete(quiz, user):
            return self.nodelist_true.render(context)
        elif self.nodelist_false is not None:
            return self.nodelist_false.render(context)
        else:
            return ''


@register.tag('ifquizcomplete')
def IfQuizComplete(parser, token):
    quiz = token.split_contents()[1:][0]
    nodelist_true = parser.parse(('else', 'endifquizcomplete'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifquizcomplete',))
        parser.delete_first_token()
    else:
        nodelist_false = None
    return IfQuizCompleteNode(quiz, nodelist_true, nodelist_false)
