# coding=utf-8
import sys, logging, json

from django.db import transaction

from applications.activity.models import Ranks
from applications.activity.share import is_activity_owner
from applications.common.services import area_name
from applications.score.models import Score, FinalScore
from applications.score.rule import JudgeRule
from applications.team.models import TeamExpert
from utils.const_def import REVIEW_RULE_1, REVIEW_RULE_2, FALSE_INT, TRUE_INT, FALSE_STR, WORK_STATUS_HAVE_REVIEWED, INPUT_NUM, INPUT_TEXTAREA, INPUT_LIST
from utils.const_err import ERR_SCORE_SUBMITTED, ERR_USER_AUTH, ERR_SCORE_AVERAGE_MODE_FORBID_CREATOR_CHANGE_SCORE
from utils.utils_except import BusinessException
from utils.utils_type import str2bool

logger = logging.getLogger(__name__)


class AverageRule(JudgeRule):
    code = REVIEW_RULE_2
    id = None
    activity_id = None
    max_score = 0
    expert_num = 0
    is_ignore_maxmin = False

    def __init__(self, id=None, activity_id=None, code=None, content=None):
        JudgeRule.__init__(self)
        d = json.loads(content)
        self.id = int(id)
        self.activity_id = int(activity_id)
        self.max_score = int(d['max'])
        self.expert_num = int(d['judge_count'])
        self.is_ignore_maxmin = str2bool(str(d['ignore_maxmin'])) if 'ignore_maxmin' in d else False

    def get_ranks(self, **kwargs):
        from applications.activity.models import Ranks
        qs_rank = Ranks.objects.filter(activity__id=self.activity_id).order_by('sn')
        rank_list = [{'rank_id': str(each.id), 'rank_desc': each.name} for each in qs_rank]
        return rank_list

    def get_score(self, work, team_expert=None, ranks=[], account=None):
        def score_item(rule, team_expert=None, status=FALSE_INT, is_final=FALSE_INT,
                       ranks=[], score_id='', score='', rank='', comment=''):
            result = {
                'rule': str(REVIEW_RULE_2),
                'score_id': str(score_id),
                'expert_id': str(team_expert.expert.id) if team_expert else '',
                'team_expert_id': str(team_expert.id) if team_expert else '',
                'expert_name': team_expert.expert.account.name if team_expert else '',
                'expert_area_name_full': area_name(team_expert.expert.area.id, joint='') if team_expert and team_expert.expert.area else '',
                'expert_area_name_simple': area_name(team_expert.expert.area.id, joint='', full=False) if team_expert and team_expert.expert.area else '',
                'status': str(status),
                'is_final': str(is_final),
                'items': [
                    {'name': 'score', 'value': str(score), 'desc': u'得分', 'type': INPUT_NUM,
                     'range_min': '1', 'range_max': str(rule.max_score), 'enum': []},
                    {'name': 'comment', 'value': str(comment), 'desc': u'评语', 'type': INPUT_TEXTAREA,
                     'range_min': '', 'range_max': '', 'enum': []},
                ]
            }
            if is_final == TRUE_INT:
                result['items'].insert(1, {'name': 'rank', 'value': str(rank), 'desc': u'等级', 'type': INPUT_LIST,
                                           'range_min': '', 'range_max': '', 'enum': ranks})
            return result

        qs_score = Score.objects.filter(work=work)
        qs_final_score = FinalScore.objects.filter(work=work)

        result = {
            'score': [],
            'final_score': []
        }
        if team_expert:
            s = qs_score.filter(team_expert=team_expert).first()
            s_id = str(s.id) if s else ''
            s_status = str(s.status) if s else FALSE_STR
            s_score = str(s.score) if s else ''
            s_rank = s.rank.name if s and s.rank else ''
            s_comment = s.comments if s else ''
            result['score'].append(score_item(self,
                    team_expert=team_expert, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
        else:
            # 只有赛事创建者可以抓取本作品的所有评分（平均分模式）
            if not is_activity_owner(work.activity, account):
                raise BusinessException(ERR_USER_AUTH)
            qs_te = TeamExpert.objects.filter(team=work.team, expert__del_flag=FALSE_INT).order_by('sn')
            for each in qs_te:
                s = qs_score.filter(team_expert=each).first()
                s_id = str(s.id) if s else ''
                s_status = str(s.status) if s else FALSE_STR
                s_score = str(s.score) if s else ''
                s_rank = s.rank.name if s and s.rank else ''
                s_comment = s.comments if s else ''
                result['score'].append(score_item(self,
                        team_expert=each, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
            # 平均分
            fs = qs_final_score.first()
            fs_id = str(fs.id) if fs else ''
            fs_status = str(fs.status) if fs else FALSE_STR
            fs_score = str(fs.score) if fs else ''
            fs_rank = fs.rank.name if fs and fs.rank else ''
            fs_comment = fs.comments if fs else ''
            result['final_score'].append(score_item(self,
                    team_expert=None, status=fs_status, is_final=TRUE_INT, ranks=ranks, score_id=fs_id, score=fs_score, rank=fs_rank, comment=fs_comment))
        return result

    def update_work_status(self, work):
        expert_in_team = TeamExpert.objects.filter(team=work.team, expert__del_flag=FALSE_INT)
        score_collected = list()
        for each_te in expert_in_team:
            score = Score.objects.filter(work=work, team_expert=each_te).first()
            if not score:
                return
            # 所有专家都已经评分，可计算平均分
            score_collected.append(int(score.score))
        if len(score_collected) >= 1:
            if self.is_ignore_maxmin and len(score_collected) >= 5:
                score_collected.sort()
                total = sum(score_collected) - score_collected[0] - score_collected[-1]
                average = total / (len(score_collected) - 2)
            else:
                total = sum(score_collected)
                average = total / len(score_collected)
            FinalScore.objects.update_or_create(
                work=work,
                defaults={"score": average, "status": TRUE_INT})
            # 作品状态变为“已评审”
            work.status = WORK_STATUS_HAVE_REVIEWED[0]
            work.final_score = average
            work.save()

    def display_judge(self, score_obj=None):
        return str(score_obj.score) if score_obj else ''

    @transaction.atomic()
    def score(self, work, data, commit, expert=None, account=None):
        data = json.loads(data)
        te = TeamExpert.objects.filter(expert=expert, expert__del_flag=FALSE_INT, team=work.team).first() if expert else None
        if te:
            logger.info('expert %s try to score work %s' % (expert.id, work.id))
        else:
            logger.info('activity(%s) creator try to score work %s' % (work.activity.id, work.id))
        '''
            {   "score_id": "2",
                "is_final": "0",
                "score": "95",
                "rank_id": "not used",
                "comment": "xxxxxx"  }               
        '''
        id = data['score_id'] if 'score_id' in data else None
        is_final = str(data['is_final']) if 'is_final' in data else FALSE_STR
        # 修改得分
        if id:
            if is_final == FALSE_STR:
                s = Score.objects.filter(id=int(id)).first()
                if not s:
                    raise BusinessException(ERR_USER_AUTH)
                if te:
                    if s.status == TRUE_INT:
                        raise BusinessException(ERR_SCORE_SUBMITTED)  # 已提交的分数不能再修改
                    if s.team_expert != te:
                        raise BusinessException(ERR_USER_AUTH)  # 只能修改自己打的分

                s.score = int(data['score'])
                # s.rank = Ranks.objects.filter(id=int(data['rank_id'])).first()  # 平均分模式下普通评分只能给分数
                s.comments = data['comment']
                s.status = int(commit)
                s.save()
                self.update_work_status(work)
            else:
                fs = FinalScore.objects.filter(id=int(id)).first()
                if not fs:
                    raise BusinessException(ERR_USER_AUTH)
                # 平均分模式下最终得分只能由活动创建者修改
                if not is_activity_owner(work.activity, account):
                    raise BusinessException(ERR_USER_AUTH)

                fs.team_expert = None
                if int(data['score']) != fs.score:
                    logger.warn('<average mode> activity creator try to modify score, OLD: %s, NEW: %s'
                                    % (fs.score, int(data['score'])))
                    raise BusinessException(ERR_SCORE_AVERAGE_MODE_FORBID_CREATOR_CHANGE_SCORE)
                fs.rank = Ranks.objects.filter(id=int(data['rank_id'])).first()
                fs.comments = data['comment']
                fs.status = TRUE_INT
                fs.save()
                work.status = WORK_STATUS_HAVE_REVIEWED[0]
                work.ranks = fs.rank
                work.save()
        # 新增得分
        else:
            if is_final == FALSE_STR:
                if not te:
                    # 暂时不允许创建者直接替非组长打分
                    raise BusinessException(ERR_USER_AUTH)
                if Score.objects.filter(work=work, team_expert=te, status=TRUE_INT).exists():
                    raise BusinessException(ERR_SCORE_SUBMITTED)
                Score.objects.update_or_create(  # 防止重复打分
                    work=work, team_expert=te, del_flag=FALSE_INT,
                    defaults=dict(
                        status=int(commit),
                        score=int(data['score']) if 'score' in data else None,
                        rank=None,
                        comments=data['comment'] if 'comment' in data else '',
                    )
                )
                self.update_work_status(work)
            else:
                # 平均分模式下最终得分只能由活动创建者修改
                if not is_activity_owner(work.activity, account):
                    raise BusinessException(ERR_USER_AUTH)

                # 平均分模式下最终成绩只能修改等级，不能修改得分
                if 'score' in data and data['score'] and str(data['score']) != '-1' and str(data['score']) != '0':
                    logger.warn('<average mode> activity creator try to give score: %s' % data['score'])
                    raise BusinessException(ERR_SCORE_AVERAGE_MODE_FORBID_CREATOR_CHANGE_SCORE)
                rk = Ranks.objects.filter(id=int(data['rank_id'])).first() if data['rank_id'] else None
                FinalScore.objects.update_or_create(  # 防止重复打分
                    work=work, del_flag=FALSE_INT,
                    defaults=dict(
                        status=TRUE_INT,
                        rank=rk,
                        comments=data['comment'] if 'comment' in data else '',
                    )
                )
                work.status = WORK_STATUS_HAVE_REVIEWED[0]
                work.ranks = rk
                work.save()

    def expert_count(self):
        return int(self.expert_num)

    def dimention(self):
        return 2, ('score', 'comments')


