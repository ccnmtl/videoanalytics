from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.db.models.signals import post_save
from django.utils import timezone
from pagetree.models import Hierarchy, UserPageVisit, PageBlock
from pagetree.reports import PagetreeReport, ReportableInterface, \
    StandaloneReportColumn, ReportColumnInterface
from quizblock.models import Submission

from videoanalytics.main.templatetags.quizsummary import \
    get_quizzes_by_css_class, get_quiz_summary_by_category


CONTROL_GROUP = 'a'
DIAGNOSTIC_GROUP = 'b'


class UserProfile(models.Model):
    user = OneToOneField(User, related_name='profile')
    research_group = models.CharField(max_length=1, default=CONTROL_GROUP)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    def is_participant(self):
        return not self.user.is_active

    def default_hierarchy(self):
        return Hierarchy.get_hierarchy(self.research_group)

    def in_control_group(self):
        return self.default_hierarchy().name == CONTROL_GROUP

    def default_location(self):
        return self.default_hierarchy().get_root()

    def first_access_formatted(self):
        upv = UserPageVisit.objects.filter(user=self.user).exclude(
            first_visit__isnull=True).order_by('first_visit').first()

        if upv:
            dt = timezone.localtime(upv.first_visit)
            return dt.strftime('%b %d, %Y %H:%M:%S')

        return ''

    def last_access_formatted(self):
        upv = UserPageVisit.objects.filter(user=self.user).exclude(
            last_visit__isnull=True).order_by('-last_visit').first()

        if upv:
            dt = timezone.localtime(upv.last_visit)
            return dt.strftime('%b %d, %Y %H:%M:%S')

        return ''

    def last_location_url(self):
        if self.percent_complete() == 0:
            hierarchy = Hierarchy.get_hierarchy(self.research_group)
            section = hierarchy.get_root().get_first_child()
        else:
            section = self.last_location()

        return section.get_absolute_url()

    def last_location(self):
        hierarchy = Hierarchy.get_hierarchy(self.research_group)
        upv = UserPageVisit.objects.filter(
            user=self.user, section__hierarchy=hierarchy).order_by(
            '-last_visit')
        if upv.count() < 1:
            return hierarchy.get_root()
        else:
            return upv[0].section

    def percent_complete(self):
        hierarchy = Hierarchy.get_hierarchy(self.research_group)
        pages = hierarchy.get_root().get_descendants().count()
        visits = UserPageVisit.objects.filter(
            user=self.user, section__hierarchy=hierarchy).count()
        if pages > 0:
            return int(visits / float(pages) * 100)
        else:
            return 0


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)


class UserVideoView(models.Model):
    user = models.ForeignKey(User)
    video_id = models.CharField(max_length=256)
    video_duration = models.IntegerField(default=0)
    seconds_viewed = models.IntegerField(default=0)

    def percent_viewed(self):
        rv = float(self.seconds_viewed) / self.video_duration * 100
        return rv

    class Meta:
        unique_together = (('user', 'video_id'),)


class QuizSummaryReportColumn(ReportColumnInterface):
    def __init__(self, topic):
        self.topic = topic

    def identifier(self):
        return self.topic

    def metadata(self):
        '''hierarchy, itemIdentifier', 'group', 'item type', 'item text' '''
        return ['', self.identifier(), 'Aggregate Quiz Score',
                '# correct', '']

    def user_value(self, user):
        if user.profile.in_control_group():
            return '-'

        if not Submission.objects.filter(user=user).exists():
            return ''

        blocks = get_quizzes_by_css_class(
            user.profile.default_hierarchy(), 'assessment')
        values = get_quiz_summary_by_category(blocks, user)

        if self.identifier() in values:
            return values[self.identifier()]['score']
        else:
            return ''


class QuizSummaryBlock(models.Model):
    pageblocks = GenericRelation(
        PageBlock, related_query_name='quiz_summary')
    template_file = 'main/quiz_summary_block.html'
    display_name = 'Quiz Summary Block'
    quiz_class = models.CharField(max_length=50)

    def pageblock(self):
        return self.pageblocks.all()[0]

    def __unicode__(self):
        return unicode(self.pageblock())

    @classmethod
    def add_form(self):
        return QuizSummaryForm()

    def edit_form(self):
        return QuizSummaryForm(instance=self)

    @classmethod
    def create(self, request):
        form = QuizSummaryForm(request.POST)
        return form.save()

    def edit(self, vals, files):
        form = QuizSummaryForm(data=vals, files=files, instance=self)
        if form.is_valid():
            form.save()

    def needs_submit(self):
        return False

    def unlocked(self, user):
        return True

    def as_dict(self):
        return dict(
            quiz_class=self.quiz_class
        )

    @classmethod
    def create_from_dict(cls, d):
        return cls.objects.create(
            quiz_class=d.get('quiz_class', '')
        )

    def report_metadata(self):
        return self.report_columns()

    def report_values(self):
        return self.report_columns()

    def report_columns(self):
        return [QuizSummaryReportColumn('thermodynamics'),
                QuizSummaryReportColumn('reaction_classes'),
                QuizSummaryReportColumn('redox_chemistry'),
                QuizSummaryReportColumn('mechanisms'),
                QuizSummaryReportColumn('paper_figures')]


class QuizSummaryForm(forms.ModelForm):
    class Meta:
        model = QuizSummaryBlock
        exclude = []

ReportableInterface.register(QuizSummaryBlock)


class YouTubeReportColumn(ReportColumnInterface):
    def __init__(self, hierarchy, video_id, title):
        self.hierarchy = hierarchy
        self.video_id = video_id
        self.title = title

    def identifier(self):
        return self.video_id

    def metadata(self):
        '''hierarchy, itemIdentifier', 'group', 'item type', 'item text' '''
        return [self.hierarchy.name, self.identifier(), 'YouTube Video',
                'percent viewed', '%s' % (self.title)]

    def user_value(self, user):
        try:
            view = UserVideoView.objects.get(user=user,
                                             video_id=self.identifier())
            return '{}'.format(view.percent_viewed())
        except UserVideoView.DoesNotExist:
            return 0


class YouTubeBlock(models.Model):
    pageblocks = GenericRelation(
        PageBlock, related_query_name='user_video')
    template_file = 'main/youtube_video_block.html'
    display_name = 'YouTube Video'

    video_id = models.CharField(max_length=256)
    title = models.TextField()

    def pageblock(self):
        return self.pageblocks.all()[0]

    def __unicode__(self):
        return unicode(self.pageblock())

    @classmethod
    def add_form(self):
        return YouTubeForm()

    def edit_form(self):
        return YouTubeForm(instance=self)

    @classmethod
    def create(self, request):
        form = YouTubeForm(request.POST)
        return form.save()

    def edit(self, vals, files):
        form = YouTubeForm(data=vals, files=files, instance=self)
        if form.is_valid():
            form.save()

    def needs_submit(self):
        return False

    def unlocked(self, user):
        return True

    def report_columns(self):
        return [YouTubeReportColumn(self.pageblock().section.hierarchy,
                                    self.video_id, self.title)]

    def report_metadata(self):
        return self.report_columns()

    def report_values(self):
        return self.report_columns()

    def as_dict(self):
        return dict(
            video_id=self.video_id,
            title=self.title
        )

    @classmethod
    def create_from_dict(cls, d):
        return cls.objects.create(
            video_id=d.get('video_id', ''),
            title=d.get('title', '')
        )


class YouTubeForm(forms.ModelForm):
    class Meta:
        model = YouTubeBlock
        widgets = {'title': forms.TextInput}
        exclude = []


ReportableInterface.register(YouTubeBlock)


class VideoAnalyticsReport(PagetreeReport):

    def users(self):
        users = User.objects.exclude(is_superuser=True).exclude(is_staff=True)
        return users.order_by('id')

    def standalone_columns(self):
        return [
            StandaloneReportColumn(
                'participant_id', 'profile', 'string',
                'Participant Id', lambda x: x.username),
            StandaloneReportColumn(
                'research_group', 'profile', 'string',
                'Research Group', lambda x: x.profile.research_group),
            StandaloneReportColumn(
                'percent_complete', 'profile', 'percent',
                '% of hierarchy completed',
                lambda x: x.profile.percent_complete()),
            StandaloneReportColumn(
                'first_access', 'profile', 'date string', 'first access date',
                lambda x: x.profile.first_access_formatted()),
            StandaloneReportColumn(
                'last_access', 'profile', 'date string', 'last access date',
                lambda x: x.profile.last_access_formatted())]
