# coding=utf-8
import sys, logging, json

from django.db import transaction

from applications.common.services import area_name
from applications.subjudge.models import SubJudgeScore, SubJudgeTeamWork, SubJudgeTeamExpert, SubJudgeRank
from applications.subjudge.subjg_rule import SubJudgeRuleDef
from utils.const_def import REVIEW_RULE_1, REVIEW_RULE_2, FALSE_INT, TRUE_INT, FALSE_STR, WORK_STATUS_HAVE_REVIEWED, INPUT_NUM, INPUT_TEXTAREA, INPUT_LIST
from utils.const_err import ERR_SCORE_SUBMITTED, ERR_USER_AUTH
from utils.utils_except import BusinessException
from utils.utils_type import str2bool

logger = logging.getLogger(__name__)


class SubJudgeAverageRule(SubJudgeRuleDef):
    code = REVIEW_RULE_2
    subjudge = None
    max_score = 0
    expert_num = 0
    is_ignore_maxmin = False

    def __init__(self, subjudge=None, code=None, content=None):
        SubJudgeRuleDef.__init__(self)
        d = json.loads(content)
        self.subjudge = subjudge
        self.max_score = int(d['max'])
        self.expert_num = int(d['judge_count'])
        self.is_ignore_maxmin = str2bool(str(d['ignore_maxmin'])) if 'ignore_maxmin' in d else False

    def get_score(self, subjudge_team_work, subjudge_team_expert=None, ranks=[], account=None):
        def score_item(rule, subjudge_team_expert, status=FALSE_INT, is_final=FALSE_INT,
                       ranks=[], score_id='', score='', rank='', comment=''):
            result = {
                'rule': str(REVIEW_RULE_2),
                'score_id': str(score_id),
                'expert_id': str(subjudge_team_expert.expert.id) if subjudge_team_expert and subjudge_team_expert.expert else '',
                'subjudge_team_expert_id': str(subjudge_team_expert.id) if subjudge_team_expert else '',
                'expert_name': subjudge_team_expert.expert.account.name if subjudge_team_expert and subjudge_team_expert.expert else '',
                'expert_area_name_full': area_name(subjudge_team_expert.expert.area.id)
                                        if subjudge_team_expert and subjudge_team_expert.expert else '',
                'expert_area_name_simple': area_name(subjudge_team_expert.expert.area.id, full=False)
                                        if subjudge_team_expert and subjudge_team_expert.expert else '',
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

        qs_score = SubJudgeScore.objects.filter(subjudge_team_work=subjudge_team_work)

        result = {
            'score': [],
            'final_score': []
        }
        if subjudge_team_expert:
            s = qs_score.filter(subjudge_team_expert=subjudge_team_expert).first()
            s_id = s.id if s else ''
            s_status = s.status if s else FALSE_INT
            s_score = s.score if s else ''
            s_rank = s.rank.name if s else ''
            s_comment = s.comment if s else ''
            result['score'].append(score_item(self,
                subjudge_team_expert, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
        else:
            # 只有评审创建者可以抓取本作品子级评审的所有评分
            if subjudge_team_work.subjudge.user != account:
                raise BusinessException(ERR_USER_AUTH)
            qs_te = SubJudgeTeamExpert.objects.filter(subjudge_team=subjudge_team_work.subjudge_team).order_by('sn')
            for each in qs_te:
                s = qs_score.filter(subjudge_team_expert=each).first()
                s_id = s.id if s else ''
                s_status = s.status if s else FALSE_INT
                s_score = s.score if s else ''
                s_rank = s.rank.name if s and s.rank else ''
                s_comment = s.comment if s else ''
                result['score'].append(score_item(self,
                    each, status=s_status, is_final=FALSE_INT, ranks=ranks, score_id=s_id, score=s_score, rank=s_rank, comment=s_comment))
            # 平均分
            final_status = TRUE_INT if subjudge_team_work.final_score else FALSE_INT
            result['final_score'].append(score_item(self,
                subjudge_team_expert, status=final_status, is_final=TRUE_INT, ranks=ranks,
                score_id='', score=str(subjudge_team_work.final_score if subjudge_team_work.final_score else ''),
                rank=str(subjudge_team_work.final_rank.id), comment=subjudge_team_work.final_comment))
        return result

    def update_work_status(self, subjg_team_work):
        expert_in_team = SubJudgeTeamExpert.objects.filter(subjudge_team=subjg_team_work.subjudge_team)
        qs = SubJudgeScore.objects.filter(subjudge_team_work=subjg_team_work,
                            subjudge_team_expert__in=expert_in_team).order_by('score')
        score_count = qs.count()
        if score_count == len(expert_in_team):
            # 所有专家都已经评分，可计算平均分
            total = reduce(lambda a,b: a+b, [sc.score for sc in qs])
            if self.is_ignore_maxmin and score_count >= 5:
                total = total - list(qs)[0].score - list(qs)[-1].score
            average = total / score_count
            subjg_team_work.final_score = average
            # 子级评审状态变为“已评审”
            subjg_team_work.subjudge_status = TRUE_INT
            subjg_team_work.save()

    @transaction.atomic()
    def score(self, subjudge_team_work, data, commit, expert=None):
        data = json.loads(data)
        te = SubJudgeTeamExpert.objects.filter(
                expert=expert, subjudge_team=subjudge_team_work.subjudge_team).first()
        '''
            {   'score_id': '2',
                'is_final': '0',
                'score': '97',
                'comment': 'xxxxxx',  }
            {   'score_id': '',
                'is_final': '1',
                'score': '97',
                'rank_id': '3',
                'comment': 'xxxxxx',  }                
        '''
        id = data['score_id'] if 'score_id' in data else None
        is_final = str(data['is_final']) if 'is_final' in data else FALSE_STR
        # 修改得分
        if id:
            s = SubJudgeScore.objects.filter(id=int(id)).first()
            # 已提交的分数不能再修改
            if expert and s.status == TRUE_INT:
                raise BusinessException(ERR_SCORE_SUBMITTED)
            s.subjudge_team_expert = te
            s.score = int(data['score'])
            s.rank = SubJudgeRank.objects.filter(id=int(data['rank_id'])).first()
            s.comment = data['comment']
            s.status = int(commit)
            s.save()
            if int(commit) == TRUE_INT:
                self.update_work_status(subjudge_team_work)
            return id

        # 新增得分
        else:
            rank = SubJudgeRank.objects.filter(id=int(data['rank_id'])).first() if data['rank_id'] else None
            if is_final == FALSE_STR:
                new_score = SubJudgeScore.objects.create(
                        subjudge_team_work=subjudge_team_work, subjudge_team_expert=te,
                        subjudge_team=subjudge_team_work.subjudge_team,
                        score=int(data['score']),
                        rank=rank,
                        comment=data['comment'], status=int(commit))
                self.update_work_status(subjudge_team_work)
                return new_score
            else:
                # 平均分模式下评审创建者只能修改等级和评语
                subjudge_team_work.final_rank = rank
                subjudge_team_work.final_comment = data['comment']
                subjudge_team_work.save()
                return None

    def get_judge_progress(self, work):
        t_w = SubJudgeTeamWork.objects.filter(subjudge=self.subjudge, work=work).first()
        finish = False
        progress = ''
        final = ''
        if t_w:
            max = SubJudgeTeamExpert.objects.filter(subjudge=self.subjudge, subjudge_team=t_w.subjudge_team).count()
            exist = SubJudgeScore.objects.filter(subjudge_team_work=t_w)
            if max == exist:
                finish = True
                final = '%s' % t_w.final_score
            progress = '%s / %s' % (exist, max)
        return progress, finish, final

    def expert_count(self):
        return int(self.expert_num)

    def display_judge(self, score_obj=None):
        return str(score_obj.score) if score_obj else ''

    def dimention(self):
        return 2, ('score', 'comment')

