# coding=utf-8
from django.conf.urls import url
from templates.html import *

urlpatterns = [

    url(r'^version$', get_version),
    url(r'^logout/', page_logout),


    #################################### 后台管理 begin ####################################

    #首页
    url(r'^backStage/index$', backStage_activityCenter_center),

    #活动中心
    url(r'^backStage/activityCenter/center$', backStage_activityCenter_center),
    url(r'^backStage/activityCenter/edit$', backStage_activityCenter_edit),
    url(r'^backStage/activityCenter/edit/preview$', backStage_activityCenter_preview),
    url(r'^backStage/activityCenter/history$', backStage_activityCenter_history),

    #精选作品
    url(r'^backStage/goodWorks/main$', backStage_goodWorks_main),
    url(r'^backStage/goodWorks/control$', backStage_goodWorks_control),

    #新闻中心
    url(r'^backStage/newsCenter/main$', backStage_newsCenter_main),
    url(r'^backStage/newsCenter/editorNews$', backStage_newsCenter_editorNews),
    url(r'^backStage/newsCenter/addNews$', backStage_newsCenter_addNews),
    url(r'^backStage/newsCenter/draftList$', backStage_newsCenter_draftList),
    url(r'^backStage/newsCenter/newslist$', backStage_newsCenter_newlist),

    #专家风采中心
    url(r'^backStage/professorCenter/add$', backStage_professorCenter_add),
    url(r'^backStage/professorCenter/edit$', backStage_professorCenter_edit),

    #用户中心
    url(r'^backStage/userCenter/user', backStage_userCenter_user),
    url(r'^backStage/userCenter/expert', backStage_userCenter_expert),

    #管理具体的一次竞赛
    url(r'^backStage/oneActivity$', backStage_oneActivity),   
    url(r'^backStage/oneActivity/index$', backStage_oneActivity_index),
    url(r'^backStage/oneActivity/user/viewAll$', backStage_oneActivity_user_viewAll),
    url(r'^backStage/oneActivity/work/viewWork$', backStage_oneActivity_work_viewWork),
    url(r'^backStage/oneActivity/work/editWork$', backStage_oneActivity_work_editWork),
    url(r'^backStage/oneActivity/work/editScore$', backStage_oneActivity_work_editScore),
    url(r'^backStage/oneActivity/work/viewAllWork$', backStage_oneActivity_work_viewAllWork),
    url(r'^backStage/oneActivity/team/assignWork$', backStage_oneActivity_team_assignWork),
    url(r'^backStage/oneActivity/team/assignExpert$', backStage_oneActivity_team_assignExpert),
    url(r'^backStage/oneActivity/team/assignWorkDetails$', backStage_oneActivity_team_assignWorkDetails),

    #################################### 后台管理 end ####################################


    #根
    # url(r'^$', page_root),
    url(r'^$', page_pc),
    url(r'^weixin/', page_pc),
    url(r'^portal/', page_pc),
    url(r'^test/', page_pc),
    url(r'^handle/', page_pc),
    url(r'^competition/', page_pc),
    url(r'^operation/', page_pc),


    url(r'^area/(?P<area_id>\w{0,50})$', page_visitors_homepage),
    url(r'^oneActivity$', page_oneActivity),

    #活动中心
    url(r'^logged/activityCenter$', page_logged_activityCenter),
    #用户中心
    url(r'^logged/userCenter$', page_logged_userCenter),

    url(r'^common/workdetail$', page_common_workdetail),
    url(r'^common/newsdetail$', page_common_newsdetail),

    #区域
    url(r'^page/layer/area$', page_layer_area),
    #选人
    url(r'^page/layer/user$', page_layer_user),


    #模板
    url(r'^page/template/manage$', page_template_manage),

    #游客
    url(r'^visitors/activityIntroduction$', page_visitors_activityIntroduction),
    url(r'^visitors/activityGoodWorks_his$', page_visitors_activityGoodWorks_his),
    url(r'^visitors/activityIntroduction_his$', page_visitors_activityIntroduction_his),
    url(r'^visitors/homepage$', page_visitors_homepage),
    url(r'^visitors/history$', page_visitors_history),
    url(r'^visitors/newslist$', page_visitors_newslist),
    url(r'^visitors/goodWorks$', page_visitors_goodWorks),
   
    #用户
    url(r'^page/user/index$', page_user_index),
    url(r'^page/user/upload/uploadWork$', page_user_upload_uploadWork),
    url(r'^page/user/upload/uploadWorkAll$', page_user_upload_uploadWorkAll),
    url(r'^page/user/upload/uploadWorkRar$', page_user_upload_uploadWorkRar),
    url(r'^page/user/upload/associateRarToWork', page_user_associateRarToWork),
    url(r'^page/user/upload/viewWork', page_user_upload_viewWork),
    url(r'^page/user/review/viewWork$', page_user_review_viewWork),
    url(r'^page/user/review/editWork$', page_user_review_editWork),

    #专家
    url(r'^page/expert/index$', page_expert_index),
    url(r'^page/expert/crew/reviewWork$', page_expert_crew_reviewWork),
    url(r'^page/expert/leader/reviewWork$', page_expert_leader_reviewWork),

    url(r'^page/test_resumable$', page_test_resumable),


    ]