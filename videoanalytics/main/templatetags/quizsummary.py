from django import template
from django.contrib.contenttypes.models import ContentType
from pagetree.models import PageBlock
from quizblock.models import Response, Submission, Quiz


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

        results = []
        for b in blocks:
            for question in b.content_object.question_set.all():
                results.append({
                    'question': question,
                    'user_correct': question.is_user_correct(u)
                })

        context[self.var_name] = results
        return ''


@register.tag('get_quiz_summary')
def quizsummary(parser, token):
    user = token.split_contents()[1:][0]
    quiz_class = token.split_contents()[1:][1]
    var_name = token.split_contents()[1:][3]
    return GetQuizSummary(user, quiz_class, var_name)
