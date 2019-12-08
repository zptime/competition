#!/usr/bin/env python
# coding=utf-8

import json
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from applications.activity.models import Rule
from applications.activity.share import is_activity_owner
from applications.expert.models import Expert
from utils.const_def import *
from utils.const_err import *
from utils.public_fun import is_1
from utils.utils_except import BusinessException
from models import Score, FinalScore
from ..work.models import Work
from ..team.models import TeamExpert


logger = logging.getLogger(__name__)


def is_super_ops(activity, account, expert=None):
    if activity.user.account == account:
        return True
    else:
        if not expert:
            raise BusinessException(ERR_EXPERT_NOT_EXIST)
        return False


def _perm_can_judge_work(work, expert):
    if not expert:
        raise BusinessException(ERR_USER_AUTH)
    if work.activity.stage != ACTIVITY_STAGE_REVIEW:
        raise BusinessException(ERR_INVALID_PHASE)
    work_team = work.team
    if not work_team:
        raise BusinessException(ERR_TEAM_WORK_NOT_EXIST)
    if not TeamExpert.objects.filter(team=work.team, expert=expert, expert__del_flag=FALSE_INT).exists():
        raise BusinessException(ERR_USER_AUTH)


def score(account, work, data, commit):
    rule = Rule.objects.filter(activity=work.activity).first().parse_rule()
    expert = Expert.objects.filter(del_flag=FALSE_INT, account=account).first()
    # 权限校验
    is_super = is_activity_owner(work.activity, account)
    if not is_super:
        _perm_can_judge_work(work, expert)
    rule.score(work, data, commit, expert=expert, account=account)


def get_score(account, work):
    rule = Rule.objects.filter(activity=work.activity).first().parse_rule()
    expert = Expert.objects.filter(account=account, del_flag=FALSE_INT).first()
    te = TeamExpert.objects.filter(expert=expert, expert__del_flag=FALSE_INT, team=work.team, team__del_flag=FALSE_INT).first()
    if not expert or not te:
        raise BusinessException(ERR_EXPERT_NOT_EXIST)
    # # 权限校验
    # _perm_can_judge_work(work, expert)
    return rule.get_score(work, team_expert=te, ranks=rule.get_ranks(is_creator=False), account=account)


def load_all_score(account, work):
    rule = Rule.objects.filter(activity=work.activity).first().parse_rule()
    expert = Expert.objects.filter(account=account, del_flag=FALSE_INT).first()
    # 权限校验
    if not is_activity_owner(work.activity, account):
        return rule.get_score(work, team_expert=None, ranks=rule.get_ranks(is_creator=FALSE_INT), account=account)
    else:
        return rule.get_score(work, team_expert=None, ranks=rule.get_ranks(is_creator=TRUE_INT), account=account)


def submit_score(account, activity, expert, work_list, is_final):
    rule = Rule.objects.filter(activity=activity).first().parse_rule()
    if is_1(is_final):
        qs = FinalScore.objects.filter(status=FALSE_INT, work__in=work_list, work__activity=activity, team_expert__expert=expert)
    else:
        qs = Score.objects.filter(status=FALSE_INT, work__in=work_list, work__activity=activity, team_expert__expert=expert)

    succ_count = 0
    for each in qs:
        if not is_activity_owner(activity, account):   # 非活动创建者则只能提交自己的得分
            if each.team_expert.expert.account != account:
                logger.info('account %s try to hack submit work %s score, but it is not his/her score'
                                    % (account.id, each.work.id))
                continue
        each.status = TRUE_INT
        each.save()
        succ_count += 1
        rule.update_work_status(each.work)   # 更新每一个被提交得分的作品

    fail_count = len(work_list) - succ_count

    msg1 = (u'%d个作品提交分数成功. ' % succ_count) if succ_count > 0 else ''
    msg2 = (u'%d个作品提交分数失败, 可能还未评审或已提交, 或者您没有权限提交此作品' % fail_count) if fail_count > 0 else ''
    return dict(c=SUCCESS[0], m=SUCCESS[1], d=msg1 + msg2)



