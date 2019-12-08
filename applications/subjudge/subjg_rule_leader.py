# coding=utf-8
import sys, logging, json

from django.db import transaction

from applications.common.services import area_name
from applications.subjudge.models import SubJudgeRule, SubJudgeScore, SubJudgeTeamExpert, SubJudgeRank, SubJudgeTeamWork
from applications.subjudge.subjg_rule import SubJudgeRuleDef
from utils.const_def import REVIEW_RULE_1, TRUE_INT, FALSE_INT, FALSE_STR, TRUE_STR, INPUT_NUM, INPUT_LIST, INPUT_TEXTAREA
from utils.const_err import ERR_SCORE_ONLY_LEADER_FINAL_SCORE, ERR_USER_AUTH, ERR_SCORE_SUBMITTED, ERR_SCORE_INFO_INCOMPLETE, ERR_TEAM_LEADER_NOT_EXIST
from utils.utils_except import BusinessException

logger = logging.getLogger(__name__)


class SubJudgeLeaderRule(SubJudgeRuleDef):
    code = REVIEW_RULE_1
    subjudge = None
    max_score = 0
    expert_num = 0

    def __init__(self, subjudge=None, code=None, content=None):
        SubJudgeRuleDef.__init__(self)
        d = json.loads(content)
        self.subjudge = subjudge
        self.max_score = int(d['max'])
        self.expert_num = int(d['judge_count'])

    def get_score(self, subjudge_team_work, subjudge_team_expert=None, ranks=[], account=None):
        def score_item(rule, subjudge_team_expert, status=FALSE_INT, is_final=FALSE_INT,
                       ranks=[], score_id='', score='', rank='', comment=''):
            return {
                'rule': str(REVIEW_RULE_1),
                'score_id': str(score_id),
                'expert_id': str(subjudge_team_expert.expert.id) if subjudge_team_expert else '',
                'team_expert_id': str(subjudge_team_expert.id) if subjudge_team_expert else '',
                'expert_name': str(subjudge_team_expert.expert.account.name) if subjudge_team_expert else '',
                'expert_area_name_full': area_name(subjudge_team_expert.expert.area.id) if subjudge_team_expert else '',
                'expert_area_name_simple': area_name(subjudge_team_expert.expert.area.id, full=False) if subjudge_team_expert else '',
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

        qs_score = SubJudgeScore.objects.filter(subjudge_team_work=subjudge_team_work)

        result = {
            'score': [],
            'final_score': []
        }
        if subjudge_team_expert:
            s = qs_score.filter(subjudge_team_expert=subjudge_team_expert, is_leader=FALSE_INT).first()
            fs = qs_score.filter(subjudge_team_expert=subjudge_team_expert, is_leader=TRUE_INT).first()
            if subjudge_team_expert.is_leader == TRUE_INT:
                fs_id = str(fs.id) if fs else ''
                fs_status = str(fs.status) if fs else FALSE_STR
                fs_score = str(fs.score) if fs else ''
                fs_rank = fs.rank.name if fs and fs.rank else ''
                fs_comment = fs.comment if fs else ''
                result['final_score'].append(score_item(self,
                    subjudge_team_expert, status=fs_status, is_final=TRUE_INT, ranks=ranks, score_id=fs_id, score=fs_score, rank=fs_rank, comment=fs_comment))
            s_id = str(s.id) if s else ''
            s_status = str(s.status) if s else FALSE_STR
            s_score = str(s.score) if s else ''
            s_rank = s.rank.name if s and s.rank else ''
            s_comment = s.comment if s else ''
            result['score'].append(score_item(self,
                    subjudge_team_expert, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
        else:
            qs_te = SubJudgeTeamExpert.objects.filter(expert__del_flag=FALSE_INT, subjudge_team=subjudge_team_work.subjudge_team).order_by('sn')
            for each in qs_te:
                s = qs_score.filter(subjudge_team_expert=each).first()
                s_id = str(s.id) if s else ''
                s_status = str(s.status) if s else FALSE_INT
                s_score = str(s.score) if s else ''
                s_rank = s.rank.name if s and s.rank else ''
                s_comment = s.comment if s else ''
                result['score'].append(score_item(self,
                    each, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))

            leader_te = SubJudgeTeamExpert.objects.filter(expert__del_flag=FALSE_INT,
                                subjudge_team=subjudge_team_work.subjudge_team, is_leader=TRUE_INT).first()
            fs = qs_score.filter(subjudge_team_expert=leader_te, is_leader=TRUE_INT).first() if leader_te else None
            fs_id = str(fs.id) if fs else ''
            fs_status = str(fs.status) if fs else FALSE_INT
            fs_score = str(fs.score) if fs else ''
            fs_rank = fs.rank.name if fs and fs.rank else ''
            fs_comment = fs.comment if fs else ''
            result['final_score'].append(score_item(self,
                        leader_te, status=fs_status, is_final=TRUE_INT, ranks=ranks, score_id=fs_id, score=fs_score, rank=fs_rank, comment=fs_comment))
        return result

    def _update_work_status(self, subjudge_team_work):
        final_score = SubJudgeScore.objects.filter(
                            subjudge_team_work=subjudge_team_work, status=TRUE_INT, is_leader=TRUE_INT).first()
        if final_score:
            subjudge_team_work.subjudge_status = TRUE_INT
            subjudge_team_work.final_score = final_score.score
            subjudge_team_work.final_rank = final_score.rank
            subjudge_team_work.final_comment = final_score.comment
            subjudge_team_work.save()

    @transaction.atomic()
    def score(self, subjudge_team_work, data, commit, expert=None):
        data = json.loads(data)
        te = SubJudgeTeamExpert.objects.filter(
                expert=expert, expert__del_flag=FALSE_INT, subjudge_team=subjudge_team_work.subjudge_team).first() if expert else None
        '''
            {   "score_id": "x",
                "is_final": "0",
                "score": "85",
                "rank_id": "x",
                "comment": "xxxxxx",  }
        '''
        id = data['score_id'] if 'score_id' in data else None
        is_final = str(data['is_final']) if 'is_final' in data else FALSE_STR
        # 修改得分
        if id:
            if is_final == FALSE_STR:
                s = SubJudgeScore.objects.filter(id=int(id), is_leader=FALSE_INT).first()
                if not s:
                    raise BusinessException(ERR_USER_AUTH)
                if expert and te:
                    if s.status == TRUE_INT:
                        raise BusinessException(ERR_SCORE_SUBMITTED)  # 已提交的分数不能再修改
                    if s.subjudge_team_expert != te:
                        raise BusinessException(ERR_USER_AUTH)  # 只能修改自己打的分

                s.score = int(data['score']) if 'score' in data else None
                rk = SubJudgeRank.objects.filter(id=int(data['rank_id'])).first() if 'rank_id' in data else None
                if not rk:
                    raise BusinessException(ERR_SCORE_INFO_INCOMPLETE)
                s.rank = rk
                s.comment = data['comment'] if 'score' in data else ''
                s.status = int(commit)
                s.save()
            else:
                fs = SubJudgeScore.objects.filter(id=int(id), is_leader=TRUE_INT).first()
                if not fs:
                    raise BusinessException(ERR_USER_AUTH)
                if te:
                    if te.is_leader == FALSE_INT:
                        raise BusinessException(ERR_SCORE_ONLY_LEADER_FINAL_SCORE)  # 只有组长可以打最终得分
                    if fs.status == TRUE_INT:
                        raise BusinessException(ERR_SCORE_SUBMITTED)  # 已提交的分数不能再修改
                    if fs.subjudge_team_expert != te:
                        raise BusinessException(ERR_USER_AUTH)  # 只能修改自己打的分
                else:  # 子级评审创建者替组长打分
                    leader_assigned = SubJudgeTeamExpert.objects.filter(expert__del_flag=FALSE_INT,
                                subjudge_team=subjudge_team_work.subjudge_team, is_leader=TRUE_INT).first()
                    if not leader_assigned:
                        raise BusinessException(ERR_TEAM_LEADER_NOT_EXIST)
                    te = leader_assigned

                fs.subjudge_team_expert = te
                fs.score = int(data['score']) if 'score' in data else None
                rk = SubJudgeRank.objects.filter(id=int(data['rank_id'])).first() if 'rank_id' in data else None
                if not rk:
                    raise BusinessException(ERR_SCORE_INFO_INCOMPLETE)
                fs.rank = rk
                fs.comment = data['comment'] if 'comment' in data else ''
                fs.status = int(commit)
                fs.save()

                self._update_work_status(subjudge_team_work)
                return id

        # 新增得分
        else:
            rank = SubJudgeRank.objects.filter(id=int(data['rank_id'])).first() if data['rank_id'] else None
            if not rank:
                raise BusinessException(ERR_SCORE_INFO_INCOMPLETE)

            if is_final == FALSE_STR:
                if not te:
                    # 暂时不允许创建者直接替非组长打分
                    raise BusinessException(ERR_USER_AUTH)
                if SubJudgeScore.objects.filter(subjudge_team_work=subjudge_team_work,
                                    subjudge_team_expert=te, is_leader=FALSE_INT, status=TRUE_INT).exists():
                    raise BusinessException(ERR_SCORE_SUBMITTED)
            else:
                if te:
                    if not te.is_leader:
                        raise BusinessException(ERR_SCORE_ONLY_LEADER_FINAL_SCORE)
                    if SubJudgeScore.objects.filter(subjudge_team_work=subjudge_team_work,
                                    subjudge_team_expert=te, is_leader=TRUE_INT, status=TRUE_INT).exists():
                        raise BusinessException(ERR_SCORE_SUBMITTED)
                else:
                    leader_assigned = SubJudgeTeamExpert.objects.filter(expert__del_flag=FALSE_INT,
                                subjudge_team=subjudge_team_work.subjudge_team, is_leader=TRUE_INT).first()
                    if not leader_assigned:
                        raise BusinessException(ERR_TEAM_LEADER_NOT_EXIST)
                    te = leader_assigned
                    commit = TRUE_INT  # 子级评审创建者如果修改最终评分则直接生效

            new_score, is_new_create = SubJudgeScore.objects.update_or_create(
                    subjudge_team_work=subjudge_team_work,
                    subjudge_team=subjudge_team_work.subjudge_team,
                    subjudge_team_expert=te,
                    is_leader=int(is_final),
                    defaults=dict(
                        rank=rank, comment=data['comment'], score=int(data['score']), status=int(commit)
                    )
            )
            self._update_work_status(subjudge_team_work)
            return new_score.id

    def update_work_status(self, subjudge_team_work):
        fs = SubJudgeScore.objects.filter(
                subjudge_team_work=subjudge_team_work, status=TRUE_INT, is_leader=TRUE_INT).first()
        if fs:
            subjudge_team_work.subjudge_status = TRUE_INT
            subjudge_team_work.final_score = fs.score
            subjudge_team_work.final_rank = fs.rank
            subjudge_team_work.final_comment = fs.comment
            subjudge_team_work.save()

    def expert_count(self):
        return int(self.expert_num)

    def get_judge_progress(self, work):
        subjg_work = SubJudgeTeamWork.objects.filter(subjudge=self.subjudge, work=work).first()
        if not subjg_work:
            return False, '', ''
        qs_leader = SubJudgeScore.objects.filter(subjudge_team_work=subjg_work, status=TRUE_INT, is_leader=TRUE_INT)
        qs_normal = SubJudgeScore.objects.filter(subjudge_team_work=subjg_work, status=TRUE_INT, is_leader=FALSE_INT)
        is_finish = False
        progress = ''
        final = ''
        if qs_leader.exists():
            is_finish = False
            final = self.display_judge(score_obj=qs_leader.first())
            progress = '100%'
        else:
            progress = '%s / %s' % (qs_normal.count(), self.expert_num+1)
        return is_finish, final, progress

    def display_judge(self, score_obj=None):
        return ('%s / %s' % (str(score_obj.score), score_obj.rank.name if score_obj.rank else '')) if score_obj else ''

    def dimention(self):
        return 3, ('score', 'rank', 'comment')

