#!/usr/bin/env python
# coding=utf-8


from django.contrib import admin
from models import Score, FinalScore


class ScoreAppAdmin(admin.ModelAdmin):
    list_display = ["id", "work_id", "team_expert", "score", "rank", "status", "del_flag"]
    list_filter = ["id", "work_id", "team_expert", "status", "del_flag"]

admin.site.register(Score, ScoreAppAdmin)


class FinalScoreAppAdmin(admin.ModelAdmin):
    list_display = ["id", "work_id", "team_expert", "score", "rank", "status", "del_flag"]
    list_filter = ["id", "work_id", "team_expert", "status", "del_flag"]

admin.site.register(FinalScore, FinalScoreAppAdmin)
