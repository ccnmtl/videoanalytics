import factory
from videoanalytics.main.models import QuizSummaryBlock, YouTubeBlock


class QuizSummaryBlockFactory(factory.DjangoModelFactory):
    class Meta:
        model = QuizSummaryBlock
    quiz_class = "quiz class"


class YouTubeBlockFactory(factory.DjangoModelFactory):
    class Meta:
        model = YouTubeBlock
    video_id = 'abcdefg'
    title = 'Sample Title'
