# coding=utf-8
import logging
import jieba
from django.core.cache import cache
from django.utils.datastructures import MultiValueDict
from applications.user.models import Area, LEVEL_PROVINCE, LEVEL_CITY, LEVEL_COUNTY, LEVEL_INSTITUTION
from utils.const_def import FALSE_INT, TRUE_INT, BIG

logger = logging.getLogger(__name__)

KEY = 'guess_area'
TIMEOUT = 60 * 30  # sec

# 可能的模糊后缀
PROV = (u'自治区', u'省', u'市', u'', )
CITY = (u'自治州', u'市', u'林区', u'地区', u'', )
ZONE = (u'经济技术开发区', u'技术开发区', u'经开区', u'高新区', u'工业区', u'自治县',
        u'特区', u'新区', u'管理区', u'地区', u'区', u'县', u'市', u'', )

POSTFIX_MAP = {
    LEVEL_PROVINCE: PROV,
    LEVEL_CITY: CITY,
    LEVEL_COUNTY: ZONE,
}


class GuessArea():
    RESULT_STATUS_FIND = 1  # 发现一个区域
    RESULT_STATUS_FIND_DIRECT = 2  # 发现一个直属区域
    RESULT_STATUS_FIND_NEW_DIRECT = 3  # 新定义一个直属区域
    RESULT_STATUS_NOT_FIND = 4   # 未发现

    area_map = None
    guess_dictionary = None

    @staticmethod
    def _strip_and_compose(self, name, postfix_list=list()):
        pure = name
        for postfix in postfix_list:
            if name.endswith(postfix):
                pure = name[:name.rfind(postfix)]
                break
        return map(lambda x: pure+x, postfix_list)

    @staticmethod
    def _parent_area_names(self, area):
        result = [area.area_name, ]
        scaner = area.parent
        while scaner:
            if scaner.manage_direct != TRUE_INT:
                if scaner.area_level in POSTFIX_MAP:
                    name_list = GuessArea._strip_and_compose(
                        self, scaner.area_name, postfix_list=POSTFIX_MAP[scaner.area_level])
            map(lambda x: result.append(x), name_list)
            scaner = scaner.parent
        return result

    def _build(self):
        """
            构建用于模糊匹配的区域词典
        """
        result = MultiValueDict()
        qs = Area.objects.filter(del_flag=FALSE_INT).all()
        for each in qs:
            if each.manage_direct == TRUE_INT:
                # 直属不做任何处理
                result.appendlist(each.area_name, each.id)
            else:
                if each.area_level in POSTFIX_MAP:
                    name_list = GuessArea._strip_and_compose(
                                self, each.area_name, postfix_list=POSTFIX_MAP[each.area_level])
                    map(lambda x: result.appendlist(x, each.id), name_list)
                else:
                    # 机构和学校不做任何处理
                    result.appendlist(each.area_name, each.id)
        return result, [k for k in result]

    @staticmethod
    def _determine_by_score(self, d):
        winner = None
        winner_score = None
        for each in d:
            if not winner:
                winner = each
                winner_score = d[each]
            else:
                if d[each] < winner_score:
                    winner = d
                    winner_score = d[each]
        return winner

    def __init__(self):
        if not cache.get(KEY):
            area_map, guess_dictionary = self._build()
            cache.set(KEY, {
                'area_map': area_map,
                'guess_dictionary': guess_dictionary,
            }, timeout=TIMEOUT)
            # 将系统中的区域名称注入jieba词典
            for each in guess_dictionary:
                jieba.add_word(each)
        self.area_map = cache.get(KEY)['area_map']
        self.guess_dictionary = cache.get(KEY)['guess_dictionary']

    def guess(self, raw):
        candidate = list()

        cut_result = jieba.cut(raw)
        sgmt = [each for each in cut_result]
        logger.info('jieba cut "%s" as: ' % raw + '/'.join(sgmt))
        sgmt.reverse()
        for i, each in enumerate(sgmt):
            if each in self.area_map:
                find = self.area_map.getlist(each)
                if len(find) > 1:
                    match_score = {}
                    for f in find:
                        # match_score[find] = BIG  # 如果某关键词发现了多个匹配area，必须要有其他佐证，否则视为不匹配
                        a = Area.objects.filter(id=f).first()
                        if not a:
                            continue
                        parent_names = GuessArea._parent_area_names(self, a)
                        for j, last in enumerate(sgmt):
                            if j <= i:
                                continue  # 从其他分片中寻找佐证
                            if last in parent_names:
                                match_score[f] = j
                                break
                    if match_score:
                        most_match_find = GuessArea._determine_by_score(self, match_score)
                        candidate.append(most_match_find)
                elif len(find) == 1:
                    candidate.append(find[0])
                else:
                    # this keyword not find proper area
                    continue

        # 从发现的全部候选结果中，选取最精准的区域
        if candidate:
            winner = None
            for each in candidate:
                area_obj = Area.objects.filter(id=each).first()
                if not winner:
                    winner = area_obj
                elif winner.manage_direct==TRUE_INT:
                    if area_obj.manage_direct==TRUE_INT and area_obj.area_level < winner.area_level:
                        winner = area_obj
                else:
                    if area_obj.area_level < winner.area_level:
                        winner = area_obj
            logger.info('AI guess "%s" means area ID:%s, name:%s' %(raw, winner.id, winner.area_name))
            if winner.manage_direct == TRUE_INT:
                return GuessArea.RESULT_STATUS_FIND_DIRECT, winner.parent, winner.area_name
            else:
                return GuessArea.RESULT_STATUS_FIND, winner, None
        else:
            logger.info('AI can not guess "%s" as an area' % raw)
            return GuessArea.RESULT_STATUS_NOT_FIND, None, None




