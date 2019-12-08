# coding=utf-8
import sys, logging, json

from django.db import transaction

from applications.activity.models import Ranks
from applications.activity.share import is_activity_owner
from applications.common.services import area_name
from applications.score.models import Score, FinalScore
from applications.score.rule import JudgeRule
from applications.team.models import TeamExpert, Team
from utils.const_def import REVIEW_RULE_1, REVIEW_RULE_2, TRUE_INT, FALSE_INT, FALSE_STR, WORK_STATUS_HAVE_REVIEWED, INPUT_NUM, INPUT_TEXTAREA, INPUT_LIST
from utils.const_err import ERR_SCORE_ONLY_LEADER_FINAL_SCORE, ERR_USER_AUTH, ERR_SCORE_SUBMITTED, ERR_TEAM_LEADER_NOT_EXIST
from utils.utils_except import BusinessException

logger = logging.getLogger(__name__)


class LeaderRule(JudgeRule):
    code = REVIEW_RULE_1
    id = None
    activity_id = None
    max_score = 0
    expert_num = 0

    def __init__(self, id=None, activity_id=None, code=None, content=None):
        JudgeRule.__init__(self)
        d = json.loads(content)
        self.id = int(id)
        self.activity_id = int(activity_id)
        self.max_score = int(d['max'])
        self.expert_num = int(d['judge_count'])

    def get_ranks(self, is_creator=FALSE_INT, **kwargs):
        from applications.activity.models import Ranks
        qs_rank = Ranks.objects.filter(activity__id=self.activity_id).order_by('sn')
        if not is_creator:
            qs_rank = qs_rank.filter(all_allowed=TRUE_INT)
        rank_list = [{'rank_id':str(each.id), 'rank_desc':each.name} for each in qs_rank]
        return rank_list

    def get_score(self, work, team_expert=None, ranks=[], account=None):
        def score_item(rule, team_expert=None, status=FALSE_INT, is_final=FALSE_INT,
                       ranks=[], score_id='', score='', rank='', comment=''):
            return {
                'rule': str(REVIEW_RULE_1),
                'score_id': str(score_id) if score_id else '',
                'expert_id': str(team_expert.expert.id) if team_expert else '',
                'team_expert_id': str(team_expert.id) if team_expert else '',
                'expert_name': str(team_expert.expert.account.name) if team_expert else '',
                'expert_area_name_full': area_name(team_expert.expert.area.id) if team_expert else '',
                'expert_area_name_simple': area_name(team_expert.expert.area.id, full=False) if team_expert else '',
                'status': str(status),
                'is_final': str(is_final),
                'items': [
                    {'name': 'score', 'value': str(score), 'desc': u'得分', 'type': INPUT_NUM,
                     'range_min': '1', 'range_max': str(rule.max_score), 'enum': []},
                    {'name': 'rank', 'value': str(rank), 'desc': u'等级', 'type': INPUT_LIST,
                     'range_min': '', 'range_max': '', 'enum': ranks},
                    {'name': 'comment', 'value': str(comment), 'desc': u'评语', 'type': INPUT_TEXTAREA,
                     'range_min': '', 'range_max': '', 'enum': []},
                ]
            }

        qs_score = Score.objects.filter(work=work)
        qs_final_score = FinalScore.objects.filter(work=work)

        result = {
            'score':[],
            'final_score': []
        }
        if team_expert:
            s = qs_score.filter(team_expert=team_expert).first()
            fs = qs_final_score.filter(team_expert=team_expert).first()
            if team_expert.is_leader == TRUE_INT:
                fs_id = str(fs.id) if fs else ''
                fs_status = str(fs.status) if fs else FALSE_STR
                fs_score = str(fs.score) if fs else ''
                fs_rank = fs.rank.name if fs and fs.rank else ''
                fs_comment = fs.comments if fs else ''
                result['final_score'].append(score_item(self,
                    team_expert=team_expert, status=fs_status, is_final=TRUE_INT, ranks=ranks, score_id=fs_id, score=fs_score, rank=fs_rank, comment=fs_comment))
            s_id = str(s.id) if s else ''
            s_status = str(s.status) if s else FALSE_STR
            s_score = str(s.score) if s else ''
            s_rank = s.rank.name if s and s.rank else ''
            s_comment = s.comments if s else ''
            result['score'].append(score_item(self,
                    team_expert=team_expert, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
        else:
            # 只有赛事创建者和该组组长可以抓取本作品的所有评分
            if not is_activity_owner(work.activity, account):
                if not TeamExpert.objects.filter(team=work.team, expert__del_flag=FALSE_INT,
                                                 expert__account=account, is_leader=TRUE_INT).exists():
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
                            team_expert=each, status=s_status, is_final=FALSE_INT, ranks=ranks,
                            score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
            leader = qs_te.filter(is_leader=TRUE_INT).first()
            fs = qs_final_score.filter(team_expert=leader).first() if leader else None
            fs_id = str(fs.id) if fs else ''
            fs_status = str(fs.status) if fs else FALSE_STR
            fs_score = str(fs.score) if fs else ''
            fs_rank = fs.rank.name if fs and fs.rank else ''
            fs_comment = fs.comments if fs else ''
            result['final_score'].append(score_item(self,
                        team_expert=leader, status=fs_status, is_final=TRUE_INT,
                        ranks=ranks, score_id=fs_id, score=fs_score, rank=fs_rank, comment=fs_comment))
        return result

    @transaction.atomic()
    def score(self, work, data, commit, expert=None, account=None):
        data = json.loads(data)
        te = TeamExpert.objects.filter(expert=expert, expert__del_flag=FALSE_INT, team=work.team).first() if expert else None
        if te:
            logger.info('expert %s try to score work %s' % (expert.id, work.id))
        else:
            logger.info('activity(%s) creator try to score work %s' % (work.activity.id, work.id))
        '''
            {   "score_id": "xxx",
                "is_final": "0",
                "score": "90",
                "rank_id": "3",
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

                s.score = int(data['score']) if 'score' in data else None
                s.rank = Ranks.objects.filter(id=int(data['rank_id'])).first() if 'rank_id' in data else None
                s.comments = data['comment'] if 'comment' in data else ''
                s.status = int(commit)
                s.save()
            else:
                fs = FinalScore.objects.filter(id=int(id)).first()
                if not fs:
                    raise BusinessException(ERR_USER_AUTH)
                if te:
                    if te.is_leader == FALSE_INT:
                        raise BusinessException(ERR_SCORE_ONLY_LEADER_FINAL_SCORE)  # 只有组长或者赛事创建者可以打最终得分
                    if fs.status == TRUE_INT:
                        raise BusinessException(ERR_SCORE_SUBMITTED)  # 已提交的分数不能再修改
                    if fs.team_expert != te:
                        raise BusinessException(ERR_USER_AUTH)  # 只能修改自己打的分
                else:  # 超管替组长打分
                    leader_assigned = TeamExpert.objects.filter(team=work.team, expert__del_flag=FALSE_INT, is_leader=TRUE_INT).first()
                    if not leader_assigned:
                        raise BusinessException(ERR_TEAM_LEADER_NOT_EXIST)
                    te = leader_assigned

                fs.team_expert = te
                fs.score = int(data['score']) if 'score' in data else None
                fs.rank = Ranks.objects.filter(id=int(data['rank_id'])).first() if 'rank_id' in data else None
                fs.comments = data['comment'] if 'comment' in data else ''
                fs.status = int(commit)
                fs.save()
                # 组长评审完毕后作品状态变为“已评审”
                self.update_work_status(work)
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
                        rank=Ranks.objects.filter(id=int(data['rank_id'])).first() if 'rank_id' in data else None,
                        comments=data['comment'] if 'comment' in data else '',
                    )
                )
            else:
                if te:
                    if not te.is_leader:
                        raise BusinessException(ERR_SCORE_ONLY_LEADER_FINAL_SCORE)
                    if FinalScore.objects.filter(work=work, team_expert=te, status=TRUE_INT).exists():
                        raise BusinessException(ERR_SCORE_SUBMITTED)
                else:
                    leader_assigned = TeamExpert.objects.filter(team=work.team, expert__del_flag=FALSE_INT, is_leader=TRUE_INT).first()
                    if not leader_assigned:
                        raise BusinessException(ERR_TEAM_LEADER_NOT_EXIST)
                    te = leader_assigned
                    commit = TRUE_INT  # 活动创建者如果修改最终评分则直接生效

                FinalScore.objects.update_or_create(  # 防止重复打分
                    work=work, team_expert=te, del_flag=FALSE_INT,
                    defaults=dict(
                        status=int(commit),
                        score=int(data['score']) if 'score' in data else None,
                        rank=Ranks.objects.filter(id=int(data['rank_id'])).first() if 'rank_id' in data else None,
                        comments=data['comment'] if 'comment' in data else '',
                    )
                )
                # 更新work表状态
                self.update_work_status(work)

    def update_work_status(self, work):
        fs = FinalScore.objects.filter(work=work, status=TRUE_INT).first()
        if fs:
            work.status = WORK_STATUS_HAVE_REVIEWED[0]
            work.final_score = fs.score
            work.ranks = fs.rank
            work.save()

    def expert_count(self):
        return int(self.expert_num)

    def dimention(self):
        return 3, ('score', 'rank', 'comments')

    def display_judge(self, score_obj=None):
        return '%s / %s' % (
                    str(score_obj.score) if score_obj and score_obj.score else '',
                    score_obj.rank.name if score_obj and score_obj.rank else ''
        )
