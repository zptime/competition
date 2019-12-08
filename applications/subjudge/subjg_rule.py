# coding=utf-8
import logging, sys
from django.db import models
from utils.const_def import *
from django.core.cache import cache
from utils.public_fun import load_clazz

logger = logging.getLogger(__name__)


class SubjudgeRuleMethodNotImplementException(Exception):
    msg = ''
    def __init__(self, class_name, method_name):
        self.msg = 'method %s is not implement!' % method_name

    def __str__(self):
        return repr(self.msg)


class SubJudgeRuleDef:
    rule_map = {
        1: 'applications.subjudge.subjg_rule_leader.SubJudgeLeaderRule',
        2: 'applications.subjudge.subjg_rule_average.SubJudgeAverageRule',
    }

    def __init__(self):
        pass

    @staticmethod
    def get_rule(id, subjudge, code, content, force_update_cache=False):
        CACHE_KEY_PREFIX = 'subjdge_rule_'
        ''' 组长制
            {
                'code': 1,
                'judge_count': 6,
                'max': 100
            }
         OR 平均分制
            {
                'code': 2,
                'judge_count': 6,
                'max': 100
                'ignore_maxmin': 0
            }
        '''
        if (id not in cache) or force_update_cache:
            instance = load_clazz(SubJudgeRuleDef.rule_map[int(code)], subjudge=subjudge, code=code, content=content)
            cache.set(CACHE_KEY_PREFIX+str(id), instance)
        return cache.get(CACHE_KEY_PREFIX+str(id))

    def score(self, work, data, commit, **kwargs):
        # 打分
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'score')

    def get_score(self, work, **kwargs):
        # 评审专家获取自身的评分
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'get_score')

    def get_judge_status(self):
        # 获取评审状态和进度
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'get_judge_status')

    def update_work_status(self, subjg_team_work):
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'update_work_status')

    def get_ranks(self):
        from applications.subjudge.models import SubJudgeRank
        qs_rank = SubJudgeRank.objects.filter(subjudge=self.subjudge).order_by('sn')
        ranks = [{'rank_id': str(each.id), 'rank_desc': each.name} for each in qs_rank]
        return ranks

    def get_judge_progress(self, work):
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'get_judge_progress')

    def expert_count(self):
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'expert_count')

    def display_judge(self, score_obj=''):
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'display_judge')

    def dimention(self):
        raise SubjudgeRuleMethodNotImplementException(self.__class__.__name__, 'dimention')


