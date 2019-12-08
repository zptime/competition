#!/usr/bin/env python
# coding=utf-8


from django.contrib import admin
from models import Team, TeamExpert


class TeamAppAdmin(admin.ModelAdmin):
    list_display = ["id", "activity_id", "name", "work_count", "del_flag"]
    list_filter = ["id", "name", "activity_id", "del_flag"]

admin.site.register(Team, TeamAppAdmin)


class TeamExpertAppAdmin(admin.ModelAdmin):
    list_display = ["id", "team_id", "expert_id", "sn", "is_leader", 'del_flag']
    list_filter = ["id", "team_id", "is_leader", "del_flag"]

admin.site.register(TeamExpert, TeamExpertAppAdmin)
