# coding=utf-8
import collections

from django.db.models import Q

from applications.activity.share import expert
from applications.common.services import area_name
from applications.user.models import Area
from applications.work.models import Work
from applications.work.share import struct_work
from utils.const_def import TRUE_INT, FALSE_INT, WORK_SHOW_STATUS_SUBJUDGE_DONE, WORK_SHOW_STATUS_SUBJUDGE_DOING
from utils.utils_type import str2bool


def struct_subjudge_expert(subjudge, e):
    raw = expert(e)
    raw['subjudge_id'] = str(subjudge.id)
    return raw


def struct_work_subjudge(work, subjudge_status, subjudge_score, subjudge_team, subjudge_rule):
    result = collections.OrderedDict()
    result.update(struct_work(work, None))
    result['subjudge_score_id'] = str(subjudge_score.id) if subjudge_score else ''
    result['subjudge_score_display'] = subjudge_rule.parse_rule().display_judge(score_obj=subjudge_score) if subjudge_score else '/'
    result['subjudge_status'] = subjudge_status
    result['subjudge_team_id'] = str(subjudge_team.id)
    result['subjudge_team_name'] = subjudge_team.name
    return result


def struct_work_subjudge_leader(
        subjudge_rule, work, judge_status, subjudge_score, subjudge_team, expert_count, expert_judge):
    result = collections.OrderedDict()
    result.update(struct_work_subjudge(work, judge_status, subjudge_score, subjudge_team, subjudge_rule))

    expert_score_list = list()
    for i in xrange(expert_count):
        if i in expert_judge:
            expert_score_list.append(subjudge_rule.parse_rule().display_judge(score_obj=expert_judge[i])
                            if expert_judge[i] else '-')
        else:
            expert_score_list.append('-')
    result['subjudge_expert_score_list'] = expert_score_list
    return result