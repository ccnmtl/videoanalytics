from django.contrib import admin
from videoanalytics.main.models import UserProfile, UserVideoView
from pagetree.models import Hierarchy, UserLocation, UserPageVisit

admin.site.register(Hierarchy)
admin.site.register(UserLocation)


class UserPageVisitAdmin(admin.ModelAdmin):
    class Meta:
        model = UserPageVisit

    search_fields = ("user__username",)
    list_display = ("user", "section", "status", "first_visit", "last_visit")

admin.site.register(UserPageVisit, UserPageVisitAdmin)


class UserVideoViewAdmin(admin.ModelAdmin):
    class Meta:
        model = UserVideoView

    search_fields = ("user__username",)
    list_display = ("user", "video_id", "video_duration", "seconds_viewed")

admin.site.register(UserVideoView, UserVideoViewAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    class Meta:
        model = UserProfile

    search_fields = ("user__username",)
    list_display = ("user", "created")

admin.site.register(UserProfile, UserProfileAdmin)
