from apps.timemarkers.models import TimeMarker
from django.contrib import admin


@admin.register(TimeMarker)
class TimeMarkerAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]

    list_filter = [
        "name",
    ]

    search_fields = [
        "name",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]
