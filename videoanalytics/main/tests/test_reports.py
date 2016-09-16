from django.test import TestCase
from pagetree.helpers import get_hierarchy
from pagetree.models import UserPageVisit, Hierarchy
from pagetree.tests.factories import UserFactory, ModuleFactory
from videoanalytics.main.models import VideoAnalyticsReport, \
    YouTubeBlock, YouTubeReportColumn, UserVideoView


class YouTubeReportColumnTest(TestCase):

    def setUp(self):
        self.hierarchy_a = get_hierarchy("a", "/pages/a/")
        root = self.hierarchy_a.get_root()
        root.add_child_section_from_dict(
            {
                'label': 'Section 1',
                'slug': 'section-1',
                'pageblocks': [],
                'children': [],
            })

        super(YouTubeReportColumnTest, self).setUp()

        self.column = YouTubeReportColumn(self.hierarchy_a, 'avideo',
                                          'atitle')

        self.user = UserFactory()

    def test_identifier(self):
        self.assertEquals(self.column.identifier(), "avideo")

    def test_metadata(self):
        keys = ['a', 'avideo', 'YouTube Video',
                'percent viewed', 'atitle']
        self.assertEquals(self.column.metadata(), keys)

    def test_user_value(self):
        self.assertEquals(self.column.user_value(self.user), 0)

        view = UserVideoView.objects.create(user=self.user,
                                            video_id='avideo',
                                            video_duration=200)
        self.assertEquals(self.column.user_value(self.user),
                          '0.0% (0 seconds)')

        view.seconds_viewed = 100
        view.save()
        self.assertEquals(self.column.user_value(self.user),
                          '50.0% (100 seconds)')


class VideoAnalyticsReportTest(TestCase):

    def setUp(self):
        super(VideoAnalyticsReportTest, self).setUp()

        self.participant = UserFactory()
        self.participant2 = UserFactory()

        block = YouTubeBlock()
        block.video_id = 'avideo'
        block.language = 'a'
        block.title = 'Title'
        block.save()

        ModuleFactory("a", "/pages/a/")
        self.hierarchy_a = Hierarchy.objects.get(name='a')

        section = self.hierarchy_a.get_root().get_next()
        section.append_pageblock('Video 1', '', content_object=block)

        sections = self.hierarchy_a.get_root().get_descendants()
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[0],
                                     status="complete")
        UserPageVisit.objects.create(user=self.participant,
                                     section=sections[1],
                                     status="complete")

        UserVideoView.objects.create(user=self.participant,
                                     video_id='avideo',
                                     seconds_viewed=50,
                                     video_duration=200)

        self.report = VideoAnalyticsReport()

    def test_get_users(self):
        self.assertEquals(len(self.report.users()), 2)

    def test_metadata(self):
        rows = self.report.metadata([self.hierarchy_a])

        header = ['hierarchy', 'itemIdentifier', 'exercise type',
                  'itemType', 'itemText', 'answerIdentifier',
                  'answerText']
        self.assertEquals(rows.next(), header)

        self.assertEquals(rows.next(), "")

        # participant id
        self.assertEquals(rows.next(), ['', 'participant_id', 'profile',
                                        'string', 'Participant Id'])

        self.assertEquals(rows.next(), ['', 'research_group', 'profile',
                                        'string', 'Research Group'])

        # percent complete
        self.assertEquals(rows.next(), ['', 'percent_complete',
                                        'profile',
                                        'percent', '% of hierarchy completed'])

        # en last access
        self.assertEquals(rows.next(), ['', 'last_access',
                                        'profile', 'date string',
                                        'last access date'])

        # en time spent
        self.assertEquals(rows.next(), ['', 'time_spent',
                                        'profile', 'integer', 'minutes'])

        youtube_metadata = [u'a', u'avideo', 'YouTube Video',
                            'percent viewed', u'Title']
        self.assertEquals(rows.next(), youtube_metadata)

        try:
            rows.next()
        except StopIteration:
            pass  # expected

    def test_values(self):
        rows = self.report.values([self.hierarchy_a])
        header = ['participant_id', 'research_group',
                  'percent_complete', 'last_access',
                  'time_spent', 'avideo']
        self.assertEquals(rows.next(), header)

        row = rows.next()
        self.assertEquals(row[0], self.participant.username)
        self.assertEquals(row[1], 'a')
        self.assertEquals(row[2], 50)
        self.assertIsNotNone(row[3])
        self.assertTrue(row[4] > 0)
        self.assertEquals(row[5], '25.0% (50 seconds)')

        row = rows.next()
        self.assertEquals(row[0], self.participant2.username)
        self.assertEquals(row[1], 'a')
        self.assertEquals(row[2], 0)
        self.assertEquals(row[3], '')
        self.assertEquals(row[4], 0)
        self.assertEquals(row[5], 0)

        try:
            rows.next()
        except StopIteration:
            pass  # expected
