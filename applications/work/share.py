# coding=utf-8
import collections

from django.db.models import Q

from applications.activity.models import Role
from applications.user.models import Area
from applications.work.models import Work, WorkFlow
from utils.const_def import TRUE_INT, FALSE_INT, WORK_SHOW_STATUS_SUBJUDGE_DONE, WORK_SHOW_STATUS_SUBJUDGE_DOING, WORK_SHOW_STATUS_NOT_EXAMINE, WORK_SHOW_STATUS_EXAMINED, \
    WORK_STATUS_NOT_SUBMIT, WORKFLOW_SUBMIT, WORKFLOW_REJECT, WORKFLOW_APPROVE, TRUE_STR, FALSE_STR
from utils.utils_type import str2bool, bool2str


def get_user(activity, account):
    role = Role.objects.filter(activity=activity, user__account=account).first()
    return (role.user, role) if role else (None, None)


def is_work_owner(work, user):
    return work.uploader == user


def struct_work_judge(work, judge_status, score, team, rule):
    result = collections.OrderedDict()
    result.update(struct_work(work, None))
    result['judge_status'] = str(judge_status)
    result['score_id'] = str(score.id) if score else ''
    result['score_display'] = rule.parse_rule().display_judge(score_obj=score) if score else '/'
    result['team_id'] = str(team.id)
    result['team_name'] = team.name
    return result


def struct_work_judge_leader(work, judge_status, score, team, expert_count, rule, expert_judge):
    from applications.activity.models import Rule
    rule = Rule.objects.filter(activity=team.activity).first()
    result = collections.OrderedDict()
    result.update(struct_work_judge(work, judge_status, score, team, rule))

    expert_score_list = list()
    for i in xrange(expert_count):
        if i in expert_judge:
            expert_score_list.append(rule.parse_rule().display_judge(score_obj=expert_judge[i]) if expert_judge[i] else '/')
        else:
            expert_score_list.append('-')
    result['expert_score_list'] = expert_score_list
    return result


def struct_work_upload(work, pov, commit_status):
    result = collections.OrderedDict()
    result.update(struct_work(work, pov))
    result['commit_status'] = str(commit_status)
    return result


def struct_work_approve(work, pov, approve_status, need_subjudge, subjudge_progress, subjudge_is_finish, subjudge_final):
    result = collections.OrderedDict()
    result.update(struct_work(work, pov))
    result['approve_status'] = str(approve_status)

    if need_subjudge:
        result['need_subjudge'] = bool2str(need_subjudge)
        # 专家评审是否完成
        result['subjudge_is_finish'] = TRUE_STR if subjudge_is_finish else FALSE_STR

        result['subjudge_progress'] = subjudge_progress
        result['subjudge_final'] = subjudge_final if subjudge_is_finish else WORK_SHOW_STATUS_SUBJUDGE_DOING
    else:
        result['need_subjudge'] = bool2str(need_subjudge)
        result['subjudge_is_finish'] = ''
        result['subjudge_progress'] = ''
        result['subjudge_final'] = ''
    return result


def struct_work_super(work, pov):
    from utils.public_fun import const_main_status
    result = collections.OrderedDict()
    result.update(struct_work(work, pov))
    result['main_status'] = const_main_status().dictionary()[work.status]
    return result


def struct_work(work, pov):
    from utils.file_fun import get_file_url
    from utils.file_fun import get_image_url
    from applications.common.services import area_name
    result = collections.OrderedDict()
    result['id'] = str(work.id)
    result['name'] = work.name
    result['rar_url'] = get_file_url(work.rar_file.url) if work.rar_file else ''
    result['img_url'] = get_image_url(work.img_file.url) if work.img_file else ''
    result['no'] = work.no
    result['sub_activity'] = work.sub_activity
    result['phase'] = work.phase
    result['project'] = work.project
    result['subject'] = work.subject
    result['status'] = str(work.status)
    result['authors'] = work.authors
    result['star'] = str(work.like)
    result['pv'] = str(work.pv)
    result['final_rank'] = work.ranks.name if work.ranks else ''
    result['final_score'] = str(work.final_score)
    result['preview_status'] = str(work.preview_status)
    result['area_is_direct'] = str(work.area.manage_direct)
    result['area_id'] = str(work.area.id)
    result['area_name_full'] = area_name(work.area.id, pov=pov)
    result['area_name_simple'] = area_name(work.area.id, full=False, pov=pov)
    result['is_public'] = str(work.is_public) if work.is_public else '0'
    return result


def workflow(work):
   current_flow =  WorkFlow.objects.filter(work=work).order_by('-update_time').first()
   return current_flow


def pre_workflow(work):
    return workflow(work).pre_flow


LV_MAP = {
    3: 1,  # 校和机构级
    4: 2,  # 区县级
    5: 4,  # 市州级
    6: 8,  # 省级
}
LV_MAP_REVERSE = {LV_MAP[k] : k for k in LV_MAP}


# 某管理员提交/审核了多少作品
def how_many_approve(role):
    flow_list = list(WorkFlow.objects.filter(trigger=role, event__in=(WORKFLOW_SUBMIT[0], WORKFLOW_APPROVE[0])))
    reject = WorkFlow.objects.filter(trigger=role, event=WORKFLOW_REJECT[0], pre_flow__in=flow_list).count()
    return len(flow_list) - reject


# 作品的下一个状态
def next_place(work, current_area, handlers):
    if work.status == 1:
        return 2, current_area
    if work.status in (2, 3, 4, 5, ):
        current_role = Role.objects.filter(user=handlers[0], activity=work.activity).first()
        parent_area = current_role.parent_role.user.area
        parent_area_lv = parent_area.area_level
        next_status = ''
        if parent_area == work.activity.user.area:
            next_status = 7
        else:
            next_status = LV_MAP_REVERSE[parent_area_lv]
        return next_status, parent_area
    if work.status >= 6:
        return 7, work.activity.user.area


# 作品的上一个状态
def _pre_status(work, handlers):
    '''
        [1, u"未上传"]
        [2, u"未提交"]
        [3, u"学校审批中"]
        [4, u"区县审批中"]
        [5, u"市州审批中"]
        [6, u"省和直辖市审批中"]
        [7, u"未分组"]
    '''
    if work.status in (1, 2,):
        return 1
    if work.status in (2, 3, 4, 5, ):
        parent_role = [each.parent_role for each in handlers]
        parent_area_lv = parent_role[0].user.area.area_level
        return LV_MAP_REVERSE[parent_area_lv]
    if work.status >= 6:
        return 7


# 当前作品在哪一个层次, 由谁来处理
def work_current_place(work):
    from applications.activity.models import Role
    acti = work.activity
    w_user = work.uploader
    '''
        [1, u"未上传"]
        [2, u"未提交"]
        [3, u"学校审批中"]
        [4, u"区县审批中"]
        [5, u"市州审批中"]
        [6, u"省和直辖市审批中"]
        [7, u"未分组"]
    '''
    c_area = c_lv = None
    c_handlers = []   # ROLE
    if work.status in (1, 2,):
        c_area = w_user.area
        c_lv = w_user.area.area_level
        c_handlers = list(Role.objects.filter(activity=acti, user=w_user))
    elif work.status in (3, 4, 5, 6,):
        c_lv = LV_MAP[work.status]
        baseline_user = w_user
        loop_lv = None
        is_find = True
        count = 0
        while loop_lv != c_lv or count < 6:
            role = Role.objects.filter(activity=acti, user=baseline_user).first()
            parent = role.parent_role
            if not parent:
                is_find = False
                break
            loop_lv = parent.user.area.area_level
            baseline_user = parent.user
            count += 1
        if not is_find:
            raise Exception
        c_area = baseline_user.area
        # 找到这一地区的所有管理员
        c_handlers = list(Role.objects.filter(activity=acti, user__area=c_area))
    else:
        c_lv = acti.area.area_level
        c_area = acti.area
        c_handlers = list(Role.objects.filter(activity=acti, user=acti.user))
    return {
        'status': work.status,
        'current_area': c_area,
        'current_level': c_lv,
        'current_handler': c_handlers,
        'current_handler_name': [each.user.account.name for each in c_handlers],
    }


def works(activity, id_list=None, uploader=None, sub_activity=None, paragraph=None,
          paragraph_project=None, subject=None, keyword=None,
          area=None, ignore_area_id_list=None, direct_area=None, status_list=None,
          has_file=None, task_status_list=None):
    """
        查询作品列表（基础过滤版）
    """
    qs = Work.objects.filter(activity=activity).order_by('-commit_time', '-create_time')
    if id_list:
        qs = qs.filter(id__in=id_list)
    if uploader:
        qs = qs.filter(uploader=uploader)
    if sub_activity:
        qs = qs.filter(sub_activity=sub_activity)
    if paragraph:
        qs = qs.filter(phase=paragraph)
    if paragraph_project:
        qs = qs.filter(project=paragraph_project)
    if subject:
        qs = qs.filter(subject=subject)
    if keyword:
        qs = qs.filter(Q(no__contains=keyword) | Q(name__contains=keyword))
    if ignore_area_id_list:
        qs = qs.exclude(area__id__in=ignore_area_id_list)

    if direct_area:
        qs = qs.filter(area__manage_direct=TRUE_INT, area__parent=direct_area)
    else:
        if area:
            qs = qs.filter(area=area)

    if status_list:
        qs = qs.filter(status__in=status_list)
    if has_file:
        qs = qs.filter(rar_file__isnull=str2bool(str(has_file)))
    if task_status_list:
        qs = qs.filter(task_status__in=task_status_list)

    return qs


def is_sub_area(mother, child):
    stack = [child, ]
    p = child.parent
    while p != None:
        stack.append(p)
        if p == mother:
            return True, stack
        p = p.parent
    return False, stack


def works_manager_can_see(my_user, activity, sub_activity=None, phase=None, project=None, area=None,
                          direct_area=None, subject=None, keyword=None):
    qs = works(activity, sub_activity=sub_activity, paragraph=phase,
               paragraph_project=project, subject=subject, keyword=keyword,
               area=area, direct_area=direct_area)
    # 某一区域的参赛者可见子级上报的作品和自己上传的作品
    qs = qs.filter(Q(area=my_user.area) | Q(area__parent=my_user.area)).filter(status__gt=WORK_STATUS_NOT_SUBMIT[0])
    result = list()
    result_non_approve = list()
    for each in qs:
        current_flow = workflow(each)
        if current_flow:
            c_area = current_flow.area
            c_lv = current_flow.area.area_level
        else:
            # 兼容原有活动
            where = work_current_place(each)
            c_area = where['current_area']
            c_lv = where['current_level']

        yes_is_sub_area, _ = is_sub_area(c_area, my_user.area)

        if c_lv == my_user.area.area_level and c_area == my_user.area:
            result_non_approve.append({'work': each, 'approve_status': WORK_SHOW_STATUS_NOT_EXAMINE})
            result.append({'work': each, 'approve_status': WORK_SHOW_STATUS_NOT_EXAMINE})
        elif c_lv > my_user.area.area_level and yes_is_sub_area:
            result.append({'work': each, 'approve_status': WORK_SHOW_STATUS_EXAMINED})
        else:
            # work is not approved by sub user
            pass
    return result, result_non_approve
