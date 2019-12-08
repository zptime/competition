#!/usr/bin/env python
# coding=utf-8

from django.db import transaction

from models import News,NewsType
from utils.const_def import *
from utils.const_err import *
import datetime
import json

from utils.file_fun import get_image_url
from utils.public_fun import str_p_datetime

DEFAULT_NEWSTYPE_NAME = u'新闻'


def check_user_permission_news(user):
    if user.is_anonymous() or not user.activity_mask > 0:
        dict_resp = dict(c=ERR_NEWS_PERMISSION_DENIED[0], m=ERR_NEWS_PERMISSION_DENIED[1], d=[])
    else:
        dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
    return dict_resp


def get_newstypename_byid(area_id, newstype_id):
    ret = ''
    tmp_list = NewsType.objects.all()
    if area_id:
        tmp_list = tmp_list.filter(area_id=area_id)
    tmp_list = tmp_list.values("id", "type_name")
    newstype_list = list(tmp_list)
    # list2 = list(filter(lambda x: x["id"] == newstype_id, newstype_list))
    list2 = [x for x in newstype_list if x["id"] == newstype_id]
    if len(list2) > 0:
        newstype = list2[0]
        ret = newstype["type_name"]
    return ret


def list_newstype(user, area_id):
    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        newstype_list = NewsType.objects.filter(del_flag=DEL_FLAG_NO)
        if area_id:
            newstype_list = newstype_list.filter(area_id=area_id)
        newstype_list = newstype_list.values("id", "area_id", "type_name", "edit_flag")
        # def_list = newstype_list.filter(type_name=DEFAULT_NEWSTYPE_NAME, edit_flag=FLAG_NO)
        def_list = newstype_list.filter()
        if len(def_list) <= 0:
            add_res = add_newstype(user, area_id, DEFAULT_NEWSTYPE_NAME, FLAG_NO)
            if SUCCESS[0] != add_res["c"]:
                return add_res
        newstype_list = list(newstype_list)
        dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=newstype_list)
        return dict_resp
    else:
        return check_result


def add_newstype(user, area_id, type_name, edit_flag=FLAG_YES):
    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        today = datetime.datetime.today()
        old_samename_newstype = NewsType.objects.filter(area_id=area_id, type_name=type_name, del_flag=FALSE_INT)
        if old_samename_newstype:
            raise Exception(u"已存在同名的新闻类型")
        NewsType.objects.create(area_id=area_id, type_name=type_name, create_time=today, update_time=today, edit_flag=edit_flag)
        dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
        return dict_resp
    else:
        return check_result


def update_newstype(user, newstype_id, type_name):
    if not newstype_id:
        raise Exception(u"新闻类型ID不能为空")
    elif not type_name:
        raise Exception(u"新闻类型名称不能为空")

    old_samename_newstype = NewsType.objects.filter(type_name=type_name, del_flag=FALSE_INT)
    if old_samename_newstype:
        raise Exception(u"已存在同名的新闻类型")

    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        newstype = NewsType.objects.get(id=newstype_id, del_flag=DEL_FLAG_NO)
        if type_name != newstype.type_name:
            newstype.type_name = type_name
        newstype.save()
        dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
        return dict_resp
    else:
        return check_result


def delete_newstype(user, newstype_id_list):
    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        list = json.loads(newstype_id_list)
        for newstype_id in list:
            newstype = NewsType.objects.get(id=newstype_id, del_flag=DEL_FLAG_NO)
            if newstype:
                newstype.del_flag = DEL_FLAG_YES
                newstype.save()
        dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
        return dict_resp
    else:
        return check_result


def list_news(user, area_id, verbose):
    news = News.objects.filter(del_flag=DEL_FLAG_NO)
    if area_id:
        news = news.filter(area_id=area_id)
    # 默认列出已发布的新闻
    if not verbose or "1" == verbose:
        news = news.filter(status=FLAG_YES)
    else:
        news = news.filter(status=FLAG_NO)
    news_info = news.order_by('-is_top', "-status", "-public_time", "-id").\
        values("id", "title", 'news_type_id', 'is_top', 'status', 'public_time', "del_flag", "image__url", "is_home_image_show", "read")
    news_info = list(news_info)
    news_len = len(news_info)

    for index, item in enumerate(news_info):
        item["public_time"] = item["public_time"].strftime('%Y-%m-%d') if item["public_time"] else ""
        item["image_url"] = get_image_url(item["image__url"]) if item["image__url"] else ""
        item.pop("image__url")
        item["is_home_image_show"] = item["is_home_image_show"] if item["is_home_image_show"] else "0"
        if item["news_type_id"]:
            item["news_type_name"] = get_newstypename_byid(area_id, item["news_type_id"])
        if 0 == index:
            item["previous"] = ""
            item["previous_title"] = ''
            if news_len > index+1:
                item["next"] = str(news_info[index+1]["id"])
                item["next_title"] = news_info[index+1]["title"]
            else:
                item["next"] = ""
                item["next_title"] = ''
        elif news_len-1 == index:
            item["previous"] = str(news_info[index-1]["id"])
            item["previous_title"] = news_info[index-1]["title"]
            item["next"] = ""
            item["next_title"] = ''
        else:
            item["previous"] = str(news_info[index-1]["id"])
            item["previous_title"] = news_info[index-1]["title"]
            item["next"] = str(news_info[index+1]["id"])
            item["next_title"] = news_info[index+1]["title"]
    dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=news_info)
    return dict_resp


@transaction.atomic
def add_news(user, title, content, news_type_id, is_top, status, area_id, image_id, is_home_image_show):
    check_result = check_user_permission_news(user)
    if not image_id and is_home_image_show == TRUE_STR:
        raise Exception(u"未上传封面图片，不能设置新闻首页轮播图显示")

    if is_home_image_show:
        is_home_image_show = int(is_home_image_show)
    else:
        is_home_image_show = 0

    if SUCCESS[0] == check_result["c"]:
        if not title:
            dict_resp = dict(c=ERR_NEWS_INFO_INCOMPLETE[0], m=ERR_NEWS_INFO_INCOMPLETE[1], d=[])
            return dict_resp
        else:
            if News.objects.filter(title=title, del_flag=DEL_FLAG_NO).exists():
                dict_resp = dict(c=ERR_NEWS_TITLE_CONFLICT[0], m=ERR_NEWS_TITLE_CONFLICT[1], d=[])
                return dict_resp
            else:
                if status:
                    status = int(status)
                    if FLAG_YES == status:
                        today = datetime.datetime.today()
                        News.objects.create(title=title, content=content, news_type_id=int(news_type_id), is_top=int(is_top),
                                            status=status, area_id=area_id, public_time=today, publisher_id=user.id,
                                            image_id=image_id, is_home_image_show=is_home_image_show)
                    else:
                        News.objects.create(title=title, content=content, news_type_id=int(news_type_id), is_top=int(is_top),
                                            status=status, area_id=area_id, publisher_id=user.id,
                                            image_id=image_id, is_home_image_show=is_home_image_show)
                    dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
                    return dict_resp
    else:
        return check_result


def detail_news(user, news_id, area_id=None):
    if not news_id:
            raise Exception(u"新闻ID不能为空")
    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        news_info = News.objects.filter(id=news_id, del_flag=DEL_FLAG_NO).\
            values("id", "area_id", "title", 'content', 'news_type_id', 'is_top', 'publisher_id', 'status', 'public_time', 'image__url', 'is_home_image_show', 'read')
    else:
        news_info = News.objects.filter(id=news_id, del_flag=DEL_FLAG_NO, status=FLAG_YES).\
            values("id", "area_id", "title", 'content', 'news_type_id', 'is_top', 'publisher_id', 'status', 'public_time', 'image__url', 'is_home_image_show', 'read')
    if not news_info:
        dict_resp = dict(c=ERR_NODATA_FOUND[0], m=ERR_NODATA_FOUND[1], d=[])
    else:
        list_result = list_news(user, area_id=area_id, verbose=None)
        list_info = list_result["d"]
        news_info = list(news_info)[0]
        if news_info["public_time"]:
            news_info["public_time"] = news_info["public_time"].strftime('%Y-%m-%d') if news_info["public_time"] else ""
        if news_info["news_type_id"]:
            news_info["news_type_name"] = get_newstypename_byid(news_info["area_id"], news_info["news_type_id"])
        news_info["image_url"] = get_image_url(news_info["image__url"]) if news_info["image__url"] else ""
        news_info.pop("image__url")
        news_info["is_home_image_show"] = news_info["is_home_image_show"] if news_info["is_home_image_show"] else "0"
        for item in list_info:
            if item["id"] == news_info["id"]:
                news_info["previous"] = item["previous"]
                news_info["previous_title"] = item["previous_title"]
                news_info["next"] = item["next"]
                news_info["next_title"] = item["next_title"]
                news_info["read"] = item["read"]
        dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[news_info])

    # 阅读量加1
    cur_news = News.objects.get(id=news_id)
    cur_news.read = cur_news.read + 1 if cur_news.read else 1
    cur_news.save()
    return dict_resp


@transaction.atomic
def update_news(user, news_id,  title, content, news_type_id, is_top, status, image_id, is_home_image_show):
    if not news_id:
        raise Exception(u"新闻ID不能为空")
    if not image_id and is_home_image_show == TRUE_STR:
        raise Exception(u"未上传封面图片，不能设置新闻首页轮播图显示")
    news_id = int(news_id)
    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        news = News.objects.get(id=news_id, del_flag=DEL_FLAG_NO)
        if not title:
            dict_resp = dict(c=ERR_NEWS_INFO_INCOMPLETE[0], m=ERR_NEWS_INFO_INCOMPLETE[1], d=[])
            return dict_resp
        else:
            if title == news.title:
                pass
            else:
                if News.objects.filter(title=title, del_flag=DEL_FLAG_NO).exclude(id=news_id).exists():
                    dict_resp = dict(c=ERR_NEWS_TITLE_CONFLICT[0], m=ERR_NEWS_TITLE_CONFLICT[1], d=[])
                    return dict_resp
                else:
                    news.title = title
            if content != news.content:
                news.content = content
            if news_type_id != news.news_type_id:
                news.news_type_id = news_type_id
            if int(is_top) != news.is_top:
                news.is_top = int(is_top)
            status = int(status)
            if status != news.status:
                news.status = status
            if status == FLAG_YES:
                today = datetime.datetime.today()
                news.public_time = today
                news.publisher_id = user.id
            else:
                news.public_time = None
            news.image_id = image_id if image_id else None
            news.is_home_image_show = is_home_image_show if is_home_image_show else 0
            news.save()
            dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
            return dict_resp
    else:
        return check_result


@transaction.atomic
def operate_news(user, news_id, news_operation):
    if not news_id:
        raise Exception(u"新闻ID不能为空")
    news_id = int(news_id)
    check_result = check_user_permission_news(user)
    if SUCCESS[0] == check_result["c"]:
        news = News.objects.filter(id=news_id, del_flag=DEL_FLAG_NO).all()
        if not news:
            dict_resp = dict(c=ERR_NODATA_FOUND[0], m=ERR_NODATA_FOUND[1], d=[])
            return dict_resp
        else:
            news_operation = int(news_operation)
            if NEWS_OPERATION_DELETE == news_operation:
                news.update(del_flag=DEL_FLAG_YES)
            elif NEWS_OPERATION_UNDO == news_operation:
                news.update(status=FLAG_NO, public_time=None)
            elif NEWS_OPERATION_TOP == news_operation:
                news.update(is_top=FLAG_YES)
            elif NEWS_OPERATION_UNTOP == news_operation:
                news.update(is_top=FLAG_NO)
            elif NEWS_OPERATION_PUBLIC == news_operation:
                today = datetime.datetime.today()
                news.update(status=FLAG_YES, publisher_id=user.id, public_time=today)
            dict_resp = dict(c=SUCCESS[0], m=SUCCESS[1], d=[])
            return dict_resp
    else:
        return check_result


def api_list_focusnews(numbers):
    # 查询焦点新闻列表，只显示最新的几条
    result = dict()
    if not numbers:
        numbers = 5
    else:
        numbers = int(numbers)

    news = News.objects.filter(is_home_image_show=TRUE_INT, del_flag=FALSE_INT).order_by('-public_time')[:numbers]
    news_list = list()
    for each_news in news:
        news_dict = {
            "public_time": each_news.public_time.strftime('%Y-%m-%d') if each_news.public_time else "",
            "image_url": get_image_url(each_news.image.url) if each_news.image else "",
            "id": each_news.id,
            "title": each_news.title,
            "content": each_news.content,
            "publisher": each_news.publisher.name,
        }
        news_list.append(news_dict)
        result['news_list'] = news_list
        result['count'] = len(news_list)

    return dict(c=SUCCESS[0], m=SUCCESS[1], d=result)
