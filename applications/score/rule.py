# coding=utf-8
import sys
import logging
from django.core.cache import cache
from utils.const_def import REVIEW_RULE_1, REVIEW_RULE_2
from utils.public_fun import load_clazz

logger = logging.getLogger(__name__)


class RuleMethodNotImplementException(Exception):
    def __init__(self, class_name, method_name):
        logger.error('find un-implement method! class_name: %s, method_name: %s' % (class_name, method_name))

    def __str__(self):
        return repr(self.message)


class JudgeRule:
    rule_map = {
        REVIEW_RULE_1: 'applications.score.rule_leader.LeaderRule',
        REVIEW_RULE_2: 'applications.score.rule_average.AverageRule',
    }

    def __init__(self):
        pass

    @staticmethod
    def get_rule(id, activity_id, code, content, force_update_cache=False):
        CACHE_KEY_PREFIX = 'rule_'
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
        if not force_update_cache or id not in cache:
            instance = load_clazz(JudgeRule.rule_map[int(code)],
                                  id=id, activity_id=activity_id, code=code, content=content)
            cache.set(CACHE_KEY_PREFIX+str(id), instance)
        return cache.get(CACHE_KEY_PREFIX+str(id))

    def score(self, work, data, commit, **kwargs):
        # 打分
        raise RuleMethodNotImplementException(self.__class__.__name__, 'score')

    def get_score(self, work, **kwargs):
        # 评审专家获取自身的评分
        raise RuleMethodNotImplementException(self.__class__.__name__, 'get_score')

    def get_judge_status(self):
        # 获取评审状态和进度
        raise RuleMethodNotImplementException(self.__class__.__name__, 'get_judge_status')

    def update_work_status(self, work):
        raise RuleMethodNotImplementException(self.__class__.__name__, 'update_work_status')

    def get_ranks(self, **kwargs):
        raise RuleMethodNotImplementException(self.__class__.__name__, 'get_ranks')

    def display_judge(self, score_obj=None):
        raise RuleMethodNotImplementException(self.__class__.__name__, 'display_judge')

    def expert_count(self):
        raise RuleMethodNotImplementException(self.__class__.__name__, 'expert_count')

    def dimention(self):
        raise RuleMethodNotImplementException(self.__class__.__name__, 'dimention')







