#!/usr/bin/env python
# encoding: utf-8

import uuid
import hashlib
import time
from datetime import datetime, timedelta
try:
    from cdecimal import getcontext, Decimal, ROUND_HALF_UP
except:
    from decimal import getcontext, Decimal, ROUND_HALF_UP
from itertools import chain, groupby
from operator import setitem
from os import path
from math import ceil
import logging, logging.config
from contextlib import closing

logging.config.fileConfig('log4p.conf')

from apps.outlet_layer.settings import cache, mc_pool, cache_pool, redis_conn

try:
    import ujson as json
except:
    import json
from pprint import pprint
import umemcache

from base.frontend.common import conver_date_string_to_timestamp
from base.frontend.uploader import (
    save_photo, unzip_and_save_file, save_binary, save_icon_image,
    save_capture_image,new_save_photo, save_offerwall_icon,
    save_offerwall_apk_screenshot, save_android_package,
    save_testin_app
)
from base.wgs2gcj import wgs2gcj
from base.common import Ip2Int
from base import config
from base.utils import (
    RuntimeCache, bulk_up, dict_swap,
    object_id, bulk_object_id, get_object_id,
    safe_str, safe_int, safe_float, to_basestring, to_unicode,
    timestamp_to_datetime, datetime_to_timestamp, today, to_timezone,
    get_timezone, timedelta, native_str, set_checked, weighted_random,
    as_timezone
)
from model.data.definition import (
    User, UserType, App, AppStatus, AppUploadInfo, ApplicationLanguage,
    ApplicationType, AppCategory,
    PropertyGender, PropertyAge, PropertyCareer, PropertyTradingArea,
    Platform, Category, TimeRange, Carrier, BrandMobile, BusinessCircle,
    BudgetType, PaymentType, ShowType, AdvertStatus, Budget,AdvertTag,
    AdvertContent, Advert, IPDatabase, RegionDatabase, AdvertLevel,
    AdvertLevelLog, TrackLog, TrackLogType, User, VerificationMessage,
    ReportAdvertLog, Transaction, ClickAction, AdvertSeries, AdvertGroup,
    SerialNum, DisplayManner, AdvertIdea, NetworkType, UserAdFilter,
    Weekday, ShanPaiTrackLog, OfferWallTrackLogType, CommonSetting,
    OfferWallDeveloperSetting, IdealMoneyType, OfferWallTrackLogAndroidRule,
    OfferWallUser, OfferWallCenter, OfferWallAppTypes, OfferWallTaskLogState,
    CarrierNetworkType,AdvertGroupOrder, CPATrackLogType
)
from apps.outlet_layer.services import trading_area, mailing
from proto import data_pb2

from base.pubsub.toolkit import pub_region_invalidate
from base.pubsub.pub import send_msg

__ = config.get("api.static_url", None)
if __ is None:
    raise ValueError("Missing configuration option `api.static_url`.")


#---------------------------------------------------------------------
#                   Property
#
# So bad we have no universal naming convertion here :`(
#---------------------------------------------------------------------
class _Property(RuntimeCache):
    region_list = None
    regions_value = None
    provinces = None
    cities = None

    @cache.region('long_term')
    def _platforms(self, *args, **kwargs):
        return list(Platform.query())

    @cache.region('long_term')
    def _categories(self, *args, **kwargs):
        return list(Category.query())

    @cache.region('long_term')
    def _app_categories(self, *args, **kwargs):
        return list(AppCategory.query())

    @cache.region('long_term')
    def _languages(self, *args, **kwargs):
        return list(ApplicationLanguage.query())

    @cache.region('long_term')
    def _business_models(self, *args, **kwargs):
        return list(ApplicationType.query())

    @cache.region('long_term')
    def _publisher_statuses(self, *args, **kwargs):
        return list(AppStatus.query())

    @cache.region('long_term')
    def _genders(self, *args, **kwargs):
        return list(PropertyGender.query())

    @cache.region('long_term')
    def _ages(self, *args, **kwargs):
        return list(PropertyAge.query())

    @cache.region('long_term')
    def _careers(self, *args, **kwargs):
        return list(PropertyCareer.query())

    @cache.region('long_term')
    def _time_ranges(self, *args, **kwargs):
        return list(TimeRange.query())

    @cache.region('long_term')
    def _carriers(self, *args, **kwargs):
        return list(Carrier.query())

    @cache.region('long_term')
    def _brands(self, *args, **kwargs):
        return list(BrandMobile.query())

    @cache.region('long_term')
    def _areas(self, *args, **kwargs):
        return list(PropertyTradingArea.query())

    def _regions(self, *args, **kwargs):
        if self.region_list is None:
            self.region_list = list(RegionDatabase.query().sort('province',1))
        return self.region_list

    def regions_by_value_to__id(self):
        if self.regions_value is None:
            __ = {}
            for r in self._regions():
                __[r['value']] = str(r['_id'])

            self.regions_value = __

        return  self.regions_value

    def regions_by_province_code_to__id(self):
        if self.provinces is None:
            __ = {}
            regions = filter(lambda x: x['city_code'] == '' and x['province_code'] != '', self._regions())
            for r in regions:
                __[r['province_code']] = str(r['_id'])

            self.provinces = __

        return self.provinces

    def regions_by_city_code_to__id(self):
        if self.cities is None:
            __ = {}
            regions = filter(lambda x: x['city_code'] != '' and x['province_code'] != '', self._regions())
            for r in regions:
                if not r['province_code'] in __:
                    __[r['province_code']] = {}

                __[r['province_code']][r['city_code']] =  str(r['_id'])
                # __["%s-%s" % (r['province_code'], r['city_code'])] = str(r['_id'])

            self.cities = __

        return self.cities

    @cache.region('long_term')
    def _offer_apptypes(self, *args, **kwargs):
        return list(OfferWallAppTypes.query().sort('subject_type'))

    @cache.region('long_term')
    def _task_log_state(self, *args, **kwargs):
        return list(OfferWallTaskLogState.query())

    @cache.region('long_term')
    def _budget_types(self, *args, **kwargs):
        return list(BudgetType.query())

    @cache.region('long_term')
    def _payment_types(self, *args, **kwargs):
        return list(PaymentType.query())

    @cache.region('long_term')
    def _show_types(self, *args, **kwargs):
        return list(ShowType.query())

    @cache.region('long_term')
    def _campaign_statuses(self, *args, **kwargs):
        return list(AdvertStatus.query())

    @cache.region('long_term')
    def _cpm_levels(self, *args, **kwargs):
        return list(AdvertLevel.query(payment_type_code="cpm"))

    @cache.region('long_term')
    def _cpc_levels(self, *args, **kwargs):
        return list(AdvertLevel.query(payment_type_code="cpc"))

    @cache.region('long_term')
    def _cpa_levels(self, *args, **kwargs):
        return list(AdvertLevel.query(payment_type_code="cpa"))

    @cache.region('long_term')
    def _track_types(self, *args, **kwargs):
        return list(TrackLogType.query())

    @cache.region('long_term')
    def _advert_group_orders(self, *args, **kwargs):
        return list(AdvertGroupOrder.query())

    @cache.region('long_term')
    def _user_types(self, *args, **kwargs):
        return list(UserType.query())

    @cache.region('long_term')
    def _advert_tags(self, *args, **kwargs):
        return list(AdvertTag.query())

    # add in 2014/2/27
    @cache.region('long_term')
    def _clickactions(self, *args, **kwargs):
        return list(ClickAction.query())

    @cache.region('long_term')
    def _display_manner(self, *args, **kwargs):
        return list(DisplayManner.query())

    @cache.region('long_term')
    def _advert_idea(self, *args, **kwargs):
        return list(AdvertIdea.query())

    @cache.region('long_term')
    def _network_types(self, *args, **kwargs):
        return list(NetworkType.query())

    @cache.region('long_term')
    def _weekdays(self, *args, **kwargs):
        return list(Weekday.query())

    @cache.region('long_term')
    def _offer_wall_track_log_types(self, *args, **kwargs):
        return list(OfferWallTrackLogType().query())

    @cache.region('long_term')
    def _ideal_money(self, *args, **kwargs):
        return list(IdealMoneyType().query())

    @cache.region('long_term')
    def _carrier_network_type(self, *args, **kwargs):
        return list(CarrierNetworkType().query())

    @cache.region('long_term')
    def _cpa_track_log_type(self, *args, **kwargs):
        return list(CPATrackLogType().query())

Property = _Property()
# init
Property.regions_by_value_to__id()
Property.regions_by_province_code_to__id()
Property.regions_by_city_code_to__id()

#---------------------------------------------------------------------
#                   Publisher
#---------------------------------------------------------------------

def transform_formdata_publisher_edit(forms):
    # create / edit form.
    d = {}
    d["name"] = safe_str(forms.get("app_name"))
    d["description"] = safe_str(forms.get("app_desc"))
    d['keyword'] = safe_str(forms.get("app.keywords"))
    d["platform"] = Property.platforms_by_value_to__id().get(safe_int(forms.get("app_platform")))
    values = Property.categories_by_value_to__id()
    d["categories"] = map(lambda x: values.get(safe_int(x), None), forms.getall("app.appCate"))
    values = Property.languages_by_value_to__id()
    d["languages"] = map(lambda x: values.get(safe_int(x), None), forms.getall("app.language"))
    d["business_model"] = Property.business_models_by_value_to__id().get(safe_int(forms.get("app.isfee")))
    d["target_gender"] = Property.genders_by_value_to__id().get(safe_int(forms.get("app.sex")))
    values = Property.ages_by_value_to__id()
    if forms.get("appAgesRadio") == "0":
        d["target_ages"] = values.values()[1:]
    else:
        d["target_ages"] = map(lambda x: values.get(safe_int(x), None), forms.getall("app.ages"))
    values = Property.careers_by_value_to__id()
    if forms.get("appJobsRadio") == "0":
        d["target_careers"] = values.values()[1:]
    else:
        d["target_careers"] = map(lambda x: values.get(safe_int(x), None), forms.getall("app.jobs"))
    return d


def transform_formdata_publisher_update_info(forms, files):
    # upload app form
    d = {}
    __ = files.get("icon_image")
    if __:
        d["icon"] = save_icon_image(__.file)
    else:
        d["icon"] = None
    d["capture"] = map(lambda x: save_capture_image(x.file),
                       files.getall("Filedatas[]"))
    __ = files.get("APPdatas[]")
    if __:
        d["binary"] = save_binary(__.file, __.filename.decode("utf8"))
    d['market_url'] = forms.get("app.marketUrl")
    d['version'] = forms.get("app.ver")
    d['description'] = forms.get("app.adPosNote")
    return d


def gen_api_key_and_secret():
    return uuid.uuid1().hex, hashlib.md5(uuid.uuid1().hex).hexdigest()


def save_publisher(name, description, keyword, platform, categories,
                   languages, business_model, target_gender, target_ages,
                   target_careers, creator, status="verifying",
                   **kwargs):
    defaults = kwargs.pop("defaults", {})
    if "_id" in defaults:
        d = App.get_one(object_id(defaults["_id"]))
    else:
        d = App()
        d["name"] = name
        d["user"] = get_object_id(creator)
        d["api_key"], d["api_secret"] = gen_api_key_and_secret()
    d["description"] = description
    d["keyword"] = keyword
    d["platform"] = object_id(platform)
    if d["platform"] is None:
        raise ValueError("Argument `platform` must can be transform to ObjectId.")
    d["category"] = bulk_object_id(categories)
    d["app_language"] = bulk_object_id(languages)
    d["app_type"] = object_id(business_model)
    if d["app_type"] is None:
        raise ValueError("Argument `business_model` must can be transform to ObjectId.")
    d["target_gender"] = object_id(target_gender)
    if not target_ages:
        target_ages = [Property.ages_list()[0]]
    if not isinstance(target_ages, list):
        raise ValueError(
            "Parameter `target_ages` should be list of ObjectId.")
    d["target_ages"] = bulk_object_id(target_ages)
    if not target_careers:
        target_careers = [Property.careers_list()[0]]
    d["target_careers"] = bulk_object_id(target_careers)
    statuses = Property.publisher_statuses_by_code_to__id()
    if status is not None:
        d["status"] = object_id(statuses.get(status))
        if d["status"] is None:
            raise ValueError("Argument `status` should be one of " % map(lambda x: "`%s`" % x, statuses.keys()))
    if kwargs.get("persist", True):
        d.save()
        # 保存时创建默认的广告设置
        count = OfferWallDeveloperSetting.count({'app_id': d['_id']})
        if count == 0:
            dev_setting = OfferWallDeveloperSetting()
            dev_setting['app_id'] = d['_id']
            dev_setting.save()

    return d


def save_publisher_upload_info(record, icon, capture, binary,
                               market_url, version, description,
                               **kwargs):
    _id, oid = object_id(record["_id"]), None
    app = App.get_one(_id)
    if app["upload_info"]:
        oid = app["upload_info"]
        d = AppUploadInfo.get_one(oid)
    else:
        d = AppUploadInfo()
    d["version"] = version
    d["description"] = description
    d["market_url"] = market_url
    d['app_advert_type_list']=kwargs.pop('app_advert_type_list')
    if icon:
        d["icon"] = icon
    if capture:
        d["capture"] = capture
    if binary:
        d["binary"] = binary
    d.save()
    status = Property.publisher_statuses_by_code_to__id()["verifying"]
    App.update({"_id": _id}, {"$set": {
        "upload_info": d["_id"],
        "status": object_id(status)
    }})


def set_publisher_level(publisher, cpm_level=None, cpc_level=None,
                        cpa_level=None, **kwargs):
    """ 更改指定应用的应用等级。

        `cpm_level`, `cpc_level`, `cpa_level` 分别对应 CPM, CPC, CPA
        的等级，使用 `CPM-A`, `CPC-B`, `CPM-E` 这样的字面量字符串即可。

        `variable` 为浮动值。假设应用的应用等级是 CPM-C, CPC-B, CPA-A,
        分别对应 CPM 最低出价 ￥2.5，CPC 最低出价 ￥4.0，CPA 最低出价
        ￥10.0；CPM 开发者分成 ￥1.0，CPC 开发者分成 ￥2.0，CPA 开发者
        分成 ￥5.0。如果浮动值是 0.5，那么该应用的 CPM 开发者分成为
        ￥0.5，CPC 开发者分成为 ￥1.5，CPA 开发者分成为 ￥4.5。如果浮
        动值为 -0.5，那么该应用的 CPM 开发者分成为 ￥1.5，CPC 开发者分
        成为 ￥2.5，CPA 开发者分成为 ￥5.5。**浮动值不影响对应应用等级的
        最低出价**，但这一等式必需恒等成立：

        应用等级最低出价 = 开发者分成 + 平台分成 + 浮动值

        可选参数 `status` 用于同时设定应用的运行状态，这一参数的值是
        应用状态的 `code` 值，例如：`running`, `paused`。
    """
    #新的创建level_log
    print "="*30
    print "eval cpm_level",eval(cpm_level)
    print "="*30
    cpm_level = cpm_level and eval(cpm_level) or {"banner":{"lvl":"CPM-E","vab":"0.0"},"full_screen":{"lvl":"CPM-E","vab":"0.0"},"popup":{"lvl":"CPM-E","vab":"0.0"},"open_screen":{"lvl":"CPM-E","vab":"0.0"}}
    cpc_level = cpc_level and eval(cpc_level) or {"banner":{"lvl":"CPC-E","vab":"0.0"},"full_screen":{"lvl":"CPC-E","vab":"0.0"},"popup":{"lvl":"CPC-E","vab":"0.0"},"open_screen":{"lvl":"CPC-E","vab":"0.0"}}
    cpa_level = cpa_level and eval(cpa_level) or {"banner":{"lvl":"CPA-E","vab":"0.0"},"full_screen":{"lvl":"CPA-E","vab":"0.0"},"popup":{"lvl":"CPA-E","vab":"0.0"},"open_screen":{"lvl":"CPA-E","vab":"0.0"}}
    for i in cpm_level:
        cpm_level[i]['lvl'] = Property.cpm_levels_by_code(cpm_level[i]['lvl'])
    for i in cpc_level:
        cpc_level[i]['lvl'] = Property.cpc_levels_by_code(cpc_level[i]['lvl'])
    for i in cpa_level:
        cpa_level[i]['lvl'] = Property.cpa_levels_by_code(cpa_level[i]['lvl'])
    created_at = today(utc=True)
    logs = []
    print "="*30
    print  "cpm_level", cpm_level
    print "="*30
    for type_code, d_dict in (("cpm", cpm_level), ("cpc", cpc_level), ("cpa", cpa_level)):
        for show_type in d_dict:
            d = d_dict[show_type]
            nd = AdvertLevelLog()
            total, variable = Decimal(d['lvl']["total"]), Decimal(d['vab'])
            ds, ps = Decimal(d['lvl']["developer"]), Decimal(d['lvl']["platform"])
            print "="*15,__file__,"="*15
            import sys
            print sys._getframe().f_lineno," Line NO:"
            print ds,variable,type(ds),type(variable)
            print "="*15,__file__,"="*15
            ds = ds - variable
            if ds <= 0:
                raise ValueError("Variable mades invalid developer sharing.")
            ps = ps + variable
            if ps <= 0:
                raise ValueError("Variable mades invalid platform sharing.")
            nd["total"] = float(total)
            nd["developer"] = float(ds)
            nd["platform"] = float(ps)
            nd["variable"] = float(variable)
            nd["name"] = d['lvl']["name"]
            nd["code"] = d['lvl']["code"]
            nd["show_type"] = show_type
            nd["date_start"] = created_at
            _id = Property.payment_types_by_code_to__id(type_code)
            nd["payment_type"] = object_id(_id)
            logs.append(nd)
    #print logs
    #print "pulisher_id",publisher["_id"]
    AdvertLevelLog().collection.insert(logs)
    d = {"level_log": map(lambda x: x["_id"], logs)}
    __ = Property.publisher_statuses_by_code_to__id(kwargs.pop("status", ""))
    if __:
        d["status"] = object_id(__)

    # 2014-06-19 添加任务分成的记录
    if kwargs.has_key('payment_rate') and kwargs['payment_rate'] is not None:
        d['payment_rate'] = kwargs['payment_rate']

    App.update({"_id": publisher["_id"]}, {"$set": d})


def set_publisher_status(publisher, status_code,lock=False):
    statuses = Property.publisher_statuses_by_code_to__id()
    if status_code not in statuses:
        raise ValueError("Invalid status code: %s" % status_code)
    oid = object_id(statuses[status_code])
    statuslocked = False
    if status_code == 'paused' and lock:
        statuslocked = True
    App.update({"_id": object_id(publisher["_id"])},
               {"$set": {"status": oid,'statuslocked':statuslocked}})
    purge_app(publisher)


def _publisher_transform_app(d):
    nd = {}
    nd["_id"] = str(d["_id"])
    if "name" in d:
        nd["name"] = d["name"]
    if "description" in d:
        nd["description"] = d["description"]
    if "keyword" in d:
        nd["keyword"] = to_unicode(d["keyword"])
    if "api_key" in d:
        nd["api_key"] = d["api_key"]
    if "api_secret" in d:
        nd["api_secret"] = d["api_secret"]
    if "platform" in d:
        nd["platform"] = str(d["platform"])
    if "category" in d:
        nd["category"] = map(str, d["category"])
    if "app_language" in d:
        nd["languages"] = map(str, d["app_language"])
    if "app_type" in d:
        nd["business_model"] = str(d["app_type"])
    if "target_gender" in d:
        nd["target_gender"] = str(d["target_gender"])
    if "target_ages" in d:
        nd["target_ages"] = map(str, d["target_ages"])
    if "target_careers" in d:
        nd["target_careers"] = map(str, d["target_careers"])
    if "status" in d:
        nd["status"] = str(d["status"])
    if "statuslocked" in d:
        nd["statuslocked"] = [d["statuslocked"],nd['_id']]
    else:
        nd["statuslocked"] = ['',nd['_id']]
    if "user" in d:
        nd["user"] = str(d["user"])
    if "upload_info" in d:
        nd["upload_info"] = str(d["upload_info"])
    if "level_log" in d:
        nd["levels"] = map(str, d["level_log"])
    if "verification_message" in d:
        __ = map(str, d["verification_message"])
        if len(__) > 0:
            nd["verification_message"] = __[-1]
    if 'payment_rate' in d:
        nd['payment_rate'] = d['payment_rate']
    return nd


@bulk_up
def publisher_transform_app(lst):
    ret = map(_publisher_transform_app, lst)
    ret = dict_swap(ret, _publisher_transform_app_swap,
                    "platform", "category", "languages", "business_model",
                    "user", "status", "target_careers", "target_ages",
                    "target_gender", "levels", "verification_message")
    payment_types = Property.payment_types_by__id_to_code()
    defaults = {
        "cpm": Property.cpm_levels(raw=True),
        "cpc": Property.cpc_levels(raw=True),
        "cpa": Property.cpa_levels(raw=True)
    }
    for d in ret:
        levels = d.pop("levels", [])

        #print "="*15,__file__,"="*15
        #import sys
        #print "LineNO:",sys._getframe().f_lineno

        #print d
        #print "="*15,__file__,"="*15

        #print "="*15,__file__,"="*15
        #import sys
        #print "LineNO:",sys._getframe().f_lineno

        #print levels
        #print "="*15,__file__,"="*15

        # When AdvertLevelLog record for App record has exists.
        for lvl in levels:
            #print lvl
            ptcode = payment_types[str(lvl["payment_type"])]
            if ptcode not in d :
                d[ptcode] = {}
            if 'show_type' in lvl and lvl['show_type'] and str(lvl['show_type'])!= '':
                if 'banner' in lvl['show_type']:
                    lvl['show_type'] = 'banner'
                d[ptcode][lvl['show_type']] = lvl
            else:
                for i in ['banner','popup','full_screen','open_screen','shanpai']:
                    if i not in d[ptcode]:
                        d[ptcode][i] = lvl
        # Fill default AdvertLevel for App.
        for k in ("cpm", "cpc", "cpa"):
            if k not in d:
                d[k] = {}
                # TODO Should not this case.
            for j in ['banner','popup','full_screen','open_screen','shanpai']:
                if j not in d[k]:
                    d[k][j] = defaults[k][-1].copy()
                    d[k][j]["variable"] = 0.0
    return ret


def _publisher_transform_app_swap(platform, category, languages,
                                  business_model, status, target_careers,
                                  user, target_ages, target_gender, levels,
                                  verification_message,
                                  *args, **kwargs):
    users = {}
    if user:
        users = dict(map(lambda x: (str(x["_id"]), x), User.query({
            "_id": {"$in": bulk_object_id(user)},
            }, fields={'pending_transactions': False})))
    levels = list(chain(*levels))
    if levels:
        levels = bulk_object_id(levels)
        levels = AdvertLevelLog.query({"_id": {"$in": levels}})
        levels = dict([(str(d["_id"]), d) for d in levels])
    msg = VerificationMessage.query({"_id": {"$in": bulk_object_id(verification_message)}})
    msg = dict([(str(d["_id"]), d) for d in msg])
    return {
        "platform": Property.platforms_by__id(),
        "category": dict(Property.categories_by__id(), **Property.app_categories_by__id()),
        "languages": Property.languages_by__id(),
        "business_model": Property.business_models_by__id(),
        "status": Property.publisher_statuses_by__id(),
        "target_careers": Property.careers_by__id(),
        "target_ages": Property.ages_by__id(),
        "target_gender": Property.genders_by__id(),
        "user": users,
        "levels": levels,
        "verification_message": msg,
    }


@bulk_up
def publisher_transform_app_view(lst):
    ret = map(_publisher_transform_app, lst)
    ret = dict_swap(ret, _publisher_transform_app_view_swap,
                    "platform", "category", "languages",
                    "business_model", "target_gender", "target_ages",
                    "target_careers", "status","statuslocked", "user", "upload_info",
                    "verification_message")
    # mixed some `None` data, remove it.
    for i in ret:
        if "target_ages" in i:
            i["target_ages"] = filter(lambda x: x, i["target_ages"])
        # 2014-01-02: for `target_gender`, transfer to None if `dict`.
        if "target_gender" in i and not isinstance(i["target_gender"], dict):
            i["target_gender"] = None
    return ret


def _publisher_transform_app_view_swap(platform, category, languages,
                                       business_model, target_gender,
                                       target_ages, target_careers,
                                       status,statuslocked, user, upload_info,
                                       verification_message):
    props = globals()["Property"]
    f = lambda y: dict(map(lambda x: (str(x["_id"]), x), y))
    users, infos = {}, {}
    if user:
        pass
    if upload_info:
        infos = dict(map(lambda x: (str(x["_id"]), x), AppUploadInfo.query({
            "_id": {"$in": bulk_object_id(upload_info)},
        })))
        prefix = config.get("api.static_url")

        icon_url = config.get("api.icon_url")
        capture_url = config.get("api.capture_url")
        binary_url = config.get("api.binary_url")

        for k in upload_info:
            if k not in infos:
                infos[k] = AppUploadInfo()
            else:
                v = infos[k]
                if v["binary"]:
                    #v["binary"] = prefix + "/binary/" + v["binary"]
                    v["binary"] = binary_url + v["binary"]
                else:
                    v["binary"] = ""
                if v["icon"]:
                    #v["icon"] = prefix + "/icon/" + v["icon"]
                    v["icon"] = icon_url + v["icon"]
                else:
                    v["icon"] = ""
                #v["capture"] = map(lambda x: prefix + "/capture/" + x, v["capture"])
                v["capture"] = map(lambda x:capture_url + x, v["capture"])
                infos[k] = v
    msg = VerificationMessage.query({"_id": {"$in": bulk_object_id(verification_message)}})
    msg = dict([(str(d["_id"]), d) for d in msg])
    statuslocked = dict([(d[1],d[0]) for d in statuslocked])
    return {
        "platform": f(props.platforms(raw=True)),
        "category": f(props.categories(raw=True)),
        "languages": f(props.languages(raw=True)),
        "business_model": f(props.business_models(raw=True)),
        "target_gender": f(props.genders(raw=True)),
        "target_ages": f(props.ages(raw=True)),
        "target_careers": f(props.careers(raw=True)),
        "status": f(props.publisher_statuses(raw=True)),
        "statuslocked": statuslocked,
        "user": users,
        "upload_info": infos,
        "verification_message": msg,
    }


def prepare_publisher_form(app=None):
    d = {}
    if app and "category" in app:
        checked = map(lambda x: x["_id"], app["category"])
    else:
        checked = ()
    d["categories"] = set_checked(Property.categories(raw=True), "_id", checked)
    if app and "platform" in app:
        checked = [app["platform"]["_id"]]
    else:
        checked = ()
    d["platforms"] = set_checked(Property.platforms(raw=True), "_id", checked)
    if app and "languages" in app:
        checked = map(lambda x: x["_id"], app["languages"])
    else:
        checked = ()
    d["languages"] = set_checked(Property.languages(raw=True)[1:], "_id", checked)
    if app and "business_model" in app:
        checked = [app["business_model"]["_id"]]
    else:
        checked = ()
    d["business_models"] = set_checked(Property.business_models(raw=True)[1:], "_id", checked)
    if app and "target_gender" in app:
        checked = [app["target_gender"]["_id"]]
    else:
        checked = ()
    d["genders"] = set_checked(Property.genders(raw=True), "_id", checked)
    ages = Property.ages(raw=True)
    if app and "target_ages" in app:
        checked = map(lambda x: x["_id"], app["target_ages"])
    else:
        checked = ()
    d["ages"] = set_checked(ages[1:], "_id", checked)
    d["ages_checked_all"] = ages[0]["_id"] in checked or not checked
    careers = Property.careers(raw=True)
    if app and "target_careers" in app:
        checked = map(lambda x: x["_id"], app["target_careers"])
    else:
        checked = ()
    d["careers"] = set_checked(careers[1:], "_id", checked)
    d["careers_checked_all"] = careers[0]["_id"] in checked or not checked
    return d


#---------------------------------------------------------------------
#                   Campaign
#---------------------------------------------------------------------

def transform_formdata_campaign_by_request(forms, files):
    # For legacy form data transform.
    d = {}
    d["check_code"] = forms.get("check_code","")
    d["check_click_code"] = forms.get("check_click_code","")
    d["double_click"] = forms.get("double_click",0)
    d["name"] = safe_str(forms.get("name"))
    categories = Property.categories_by_value_to__id()
    d["app_categories"] = map(lambda x: categories.get(safe_int(x), None), forms.getall("app.Cate"))

    #标签，优先级
    d['priority'] = int(forms.get('priority',0))
    d['tag'] = Property.advert_tags_by_code_to__id()[forms.get('tag','sell')]


    # 广告类别
    d["category"] = categories.get(safe_int(forms.get("category")), None)

    # 上网方式
    network_types = Property.network_types_by_value_to__id()
    d["network"] = filter(lambda x: x, map(lambda x: network_types.get(safe_int(x), None), forms.getall("network")))
    if len(d["network"]) == 0:
        d["network"] = [network_types[0]]

    # 投放日
    weekdays = Property.weekdays_by_value_to__id()
    d["weekday_launch"] = filter(lambda x: x, map(lambda x: weekdays.get(safe_int(x), None), forms.getall("weekday_launch")))
    if len(d["weekday_launch"]) == 0:
        d["weekday_launch"] = [weekdays[0]]

    # 投放频次
    interval = safe_int(forms.get("frequency.interval", 0))
    times = safe_int(forms.get("frequency.times", 0))
    if interval > 0 and times > 0:
        d["frequency"] = {"interval": interval, "times": times}
    else:
        d["frequency"] = None

    # 摇一摇
    shake = safe_int(forms.get('shake'), 0)
    if shake == 1:
        d["shake"] = 'on'
    elif shake == 0:
        d['shake'] = 'off'
    # 刮一刮
    shave = safe_int(forms.get('shave'), 0)
    if shave == 1:
        d['shave'] = 'on'
    elif shave == 0:
        d['shave'] = 'off'
    # 吹一吹
    shave = safe_int(forms.get('blow'), 0)
    if shave == 1:
        d['blow'] = 'on'
    elif shave == 0:
        d['blow'] = 'off'

    # 广告回调地址
    ad_callback_url = forms.get('ad_activavtion_callback', '')

    # 如果是安卓应用，获取试玩时间(存储的单位是毫秒）
    cpa_apk_timeout = safe_int(forms.get('ad_android_playtime', '0'), 0) * 1000


    # d["category"] = categories.get(safe_int(forms.get("category")), None)
    #
    click_actions = Property.clickactions_by_value_to__id()
    d["click_action"] = click_actions.get(safe_int(forms.get("ad_click_action")), None)

    d['phone'] = safe_str(forms.get("phone"))
    d['message'] = safe_str(forms.get("message"))
    d['map_address'] = safe_str(forms.get("map_address"))

    # 设置回调地址
    d['cpa_callback_url'] = ad_callback_url

    # 设置Android相关的参数
    if safe_int(forms.get("platform", 0)) == 1:
        d['cpa_apk_timeout'] = cpa_apk_timeout

    # advert group
    d["group"] = safe_str(forms.get("group"))

    # @FIXME unknown: what timezone the timestamp computing base on.
    __ = []
    for i in (forms.get("startTime"), forms.get("endTime")):
        try:
            parsed = datetime.strptime(i, "%Y-%m-%d")
            __.append(to_timezone(parsed, "Asia/Shanghai"))
        except Exception, err:
            __.append(None)
    d["date_start"], d["date_end"] = __
    now = today(zero_time=True)
    if d["date_start"] < now:
        d["date_start"] = now
    if d["date_end"] is not None and d["date_end"] <= d["date_start"]:
        d["date_end"] = d["date_start"] + timedelta(days=10)
    d["description"] = safe_str(forms.get("description"))
    # campaign type
    budget_types = Property.budget_types_by_value_to__id()
    selected = safe_int(forms.get("budget_type", 0))
    d["budget_type"] = selected in budget_types and budget_types[selected] or budget_types[0]
    if selected == 1:
        d["budget_amount"] = safe_float(forms.get("daily_budget"))
    elif selected == 2:
        d["budget_amount"] = safe_float(forms.get("total_budget"))
    else:
        d["budget_amount"] = 0.0
    payment_types = Property.payment_types_by_value_to__id()
    selected = safe_int(forms.get("payment_type"))
    d["payment_type"] = selected in payment_types and payment_types[selected] or None  # should fail.
    d["cpc_url"], d["cpa_zip"], d["cpa_url"] = "", "", ""
    if selected == 0:    # CPC
        d["cpc_url"] = safe_str(forms.get("ad_redirect_url"))
    elif selected == 2:  # CPA
        f = files.get("ad_cap_zip_file")
        if f:
            __ = unzip_and_save_file(f.file, f.filename)
            d["cpa_zip"] = __ + ".zip"
            d["cpa_url"] = __ + "/index.html"
    d["premium_price"] = safe_float(forms.get("premium_price"))
    show_types = Property.show_types_by_value_to__id()
    selected = safe_int(forms.get("ad_banner_type", 0))
    d["show_type"] = selected in show_types and show_types[selected] or None
    # add in 2014.3.28
    if forms.get("ad_banner_text",None):
        display_manner_list = Property.display_manner_by_value_to__id()
        text_manner = display_manner_list.get(safe_int(forms.get('text_display_manner')),None)
        advert_idea_list = Property.advert_idea_by_value_to__id()
        advert_idea = advert_idea_list.get(safe_int(forms.get('advert_idea')))
        d["show_text"] = {'text': safe_str(forms.get("ad_banner_text")), 'advert_idea':advert_idea, 'display_manner': text_manner}
    elif forms.get("rich_media_url", None):
        rich_media_url = forms.get("rich_media_url")
        d["show_text"] = {'rich_media_url': rich_media_url}
    else:
        d["show_text"] = {}
    # print 'show_text', d["show_text"]
    d["show_images"] = []
    display_manner_list = Property.display_manner_by_value_to__id()
    req_keys = forms.keys()

    filelist = list(files)

    for li in filelist:
        if 'manner_' + li in req_keys:
            if files.get(li):
                img_info = new_save_photo(files.get(li).file)
                display_manner = display_manner_list.get(safe_int(forms.get('manner_'+li)))
                img_info['display_manner'] = display_manner
                img_info['id'] = li
                d["show_images"].append(img_info)
        else:
            img_info = new_save_photo(files.get(li).file)
            img_info['id'] = li
            d["show_images"].append(img_info)
    deletepicids =[i for i in  forms.get('deletepic','').split(',') if i]
    d['deletepic'] = []
    for k in deletepicids:
        if k not in filelist:
            d['deletepic'].append(k)

    # d["show_images"] = map(lambda x: save_photo(x.file), files.getall("Filedatas[]"))
    # d["show_text"] = safe_str(forms.get("ad_banner_text"))
    # 出现方式


    # 添加点击交互行为字段
    d["click_action_type"] = safe_str(forms.get("ad_click_action"))
    # save `Budget` and `AdvertContent`.
    # ----------------
    # targetting
    # ----------------
    # platform. @FIXME Current it is multiple select
    platforms = Property.platforms_by_value_to__id()
    selected = safe_int(forms.get("platform", 0))
    d["platform"] = selected in platforms and platforms[selected] or None
    values = Property.genders_by_value_to__id()
    d["gender"] = values.get(safe_int(forms.get("gender")), values[0])
    values = Property.ages_by_value_to__id()
    d["ages"] = map(lambda x: values.get(safe_int(x)), forms.getall("ages"))
    values = Property.careers_by_value_to__id()
    d["careers"] = map(lambda x: values.get(safe_int(x)), forms.getall("careers"))
    # time ranges
    time_ranges = Property.time_ranges_by_value_to__id()
    selected = map(safe_int, forms.getall("put_in_time"))
    d["time_ranges"] = filter(lambda x: x, map(lambda y: time_ranges.get(y), selected))
    if len(d["time_ranges"]) == 0:
        d["time_ranges"] = time_ranges.values()
    # regions
    regions = Property.regions_by_value_to__id()
    selected = map(safe_int, forms.getall("put_in_area"))
    if 0 in selected and len(selected) > 1:
        selected.pop(0)
    d["regions"] = filter(lambda x: x, map(lambda y: regions.get(y), selected))
    if len(d["regions"]) == 0:
        d["regions"] = [regions[0]]
    # areas
    # @FIXME How about ALL areas?
    areas = Property.areas_by__id_to__id()
    selected = map(safe_str, forms.getall("circle"))
    d["areas"] = filter(lambda x: x, map(lambda y: areas.get(y), selected))
    # brands
    brands = Property.brands_by_value_to__id()
    selected = map(safe_int, forms.getall("phone_brands"))
    if 0 in selected and len(selected) > 1:
        selected.pop(0)
    d["brands"] = filter(lambda x: x, map(lambda y: brands.get(y), selected))
    if len(d["brands"]) == 0:
        d["brands"] = [brands[0]]
    # languages
    languages = Property.languages_by_value_to__id()
    selected = map(safe_int, forms.getall("app_language"))
    if 0 in selected and len(selected) > 1:
        selected.pop(0)
    d["languages"] = filter(lambda x: x, map(lambda y: languages.get(y), selected))
    if len(d["languages"]) == 0:
        d["languages"] = [languages[0]]
    # business_model
    business_models = Property.business_models_by_value_to__id()
    selected = safe_int(forms.get("application_type", 0))
    d["business_model"] = selected in business_models and business_models[selected] or business_models[0]
    # carriers
    carriers = Property.carriers_by_value_to__id()
    selected = map(safe_int, forms.getall("carrier_type"))
    if 0 in selected and len(selected) > 1:
        selected.pop(0)
    d["carriers"] = filter(lambda x: x, map(lambda y: carriers.get(y), selected))
    if len(d["carriers"]) == 0:
        d["carriers"] = [carriers[0]]
    return d


def save_campaign(name, description, date_start, date_end,
                  payment_type, premium_price, cpc_url, cpa_zip, cpa_url,
                  show_type, show_images, show_text,
                  budget_type, budget_amount,
                  category, platform, time_ranges, regions, areas,tag,priority,
                  brands, languages,check_code,check_click_code,double_click,
                  business_model, carriers, gender, ages, careers,
                  creator, click_action_type, click_action, phone, message, shake,
                  shave, blow, map_address, cpa_callback_url, cpa_apk_timeout=None,
                  group=None, status="verifying", **kwargs):
    defaults = kwargs.pop("defaults", {})
    deletepic = kwargs.pop("deletepic", {})
    # 1. budget
    if "budget" in defaults:
        budget = Budget.get_one(object_id(defaults["budget"]))
    else:
        budget = Budget()
    budget["type"] = object_id(budget_type)
    budget["amount"] = budget_amount
    # 2. advert content
    if "content" in defaults:
        content = AdvertContent.get_one(object_id(defaults["content"]))
    else:
        content = AdvertContent()
    if show_type is None:
        raise ValueError("`show_type` can not set to `None`.")
    content["new_word"] = show_text
    imgs = []
    for img in content['new_images']:
        if img['id'] not in deletepic:
            imgs.append(img)
    content['new_images'] = imgs

    if len(content.get("new_images", [])) == 0 or show_images:
        if len(content.get("new_images", [])) == 0:
            content["new_images"] = show_images
        elif 'show_type' in content and str(content['show_type'])!=str(show_type):
            content["new_images"] = show_images
        else:
            chanids = []
            news = []
            for i in range(len(show_images)):
                newimg = show_images[i]
                same = 0
                for k in range(len(content["new_images"])):
                    oldimg = content["new_images"][k]
                    if newimg['id'] == oldimg['id']:
                        same= 1
                        chanids.append((k,i))
                        break
                if same == 0:
                    news.append(show_images[i])

            #print chanids,news
            for p in chanids:
                content["new_images"][p[0]] = show_images[p[1]]
            content["new_images"]+=news

    content["show_type"] = object_id(show_type)
    if "zip" not in content or cpa_zip:
        content["zip"] = cpa_zip
    if "url" not in content or cpa_url:
        content["url"] = cpa_url
    # 3. advert
    if "_id" in defaults:
        advert = Advert.get_one(object_id(defaults["_id"]))
    else:
        advert = Advert()
    advert["name"] = name
    advert["description"] = description
    advert["show_type"] = object_id(show_type)
    advert["redirect_url"] = cpc_url
    advert["premium_price"] = premium_price
    advert["date_start"] = date_start
    advert["date_end"] = date_end
    advert["payment_type"] = object_id(payment_type)
    advert["check_code"] = check_code
    advert["check_click_code"] = check_click_code
    advert["double_click"] = int(double_click)

    # click action
    if click_action:
        advert["click_action"] = object_id(click_action)
    else:
        advert["click_action"] = None
    advert["phone"] = phone
    advert["message"] = message
    advert["map_address"] = map_address
    advert["shake"] = shake
    advert["tag"] = object_id(tag)
    advert["priority"] = priority

    advert['shave'] = shave
    advert['blow'] = blow

    # activation callback
    advert['cpa_callback_url'] = cpa_callback_url
    if cpa_apk_timeout:
        advert['cpa_apk_timeout'] = cpa_apk_timeout

    # advert group
    if group:
        advert["group"] = object_id(group)

    if "advert_code" in defaults:
        advert["advert_code"] = defaults["advert_code"]
    else:
        advert["advert_code"] = "A%04d" % SerialNum.get_next_number("advert_seq")

    # targetting
    advert["category"] = object_id(category)

    app_categories = kwargs.pop('app_categories', [])
    advert["app_categories"] =  bulk_object_id(app_categories)

    advert["platform"] = [object_id(platform)]
    # targgetting: time ranges
    if not time_ranges:
        time_ranges = Property.time_ranges_list()
    advert['time_range'] = bulk_object_id(time_ranges)
    # targetting: regions
    values = Property.regions_list()
    if not regions:
        regions = [values[0]]
    else:
        regions = list(set(regions))
        if values[0] in regions:
            regions.pop(values[0])
    advert["region_launch"] = bulk_object_id(regions)
    # targetting: brands
    if not brands:
        brands = [object_id(Property.brands_list()[0])]
    advert["brand_mobile"] = bulk_object_id(brands)
    # targetting: languages
    if not languages:
        languages = [Property.languages_list()[0]]
    advert["app_language"] = bulk_object_id(languages)
    # targetting: business model
    if business_model is None:
        business_model = Property.business_models_list()[0]
    advert["app_type"] = object_id(business_model)
    # carriers
    values = Property.carriers_list()
    if not carriers:
        carriers = [values[0]]
    else:
        carriers = bulk_object_id(carriers)
        carriers = filter(lambda x: x in values, carriers)
    if values[0] in carriers and len(carriers) > 1:
        carriers.pop(values[0])
    advert["carrier"] = carriers
    # gender
    if not gender:
        gender = Property.genders_list()[0]
    advert["gender"] = object_id(gender)
    # trading areas
    advert["trading_areas"] = list(set(bulk_object_id(areas)))
    # ages
    values = Property.ages_list()
    if not ages:
        ages = [values[0]]
    else:
        ages = bulk_object_id(ages)
        ages = filter(lambda x: x in values, ages)
    if values[0] in ages and len(ages) > 1:
        ages.pop(values[0])
    advert["ages"] = list(set(ages))
    # careers
    values = Property.careers_list()
    if not careers:
        careers = [values[0]]
    else:
        careers = bulk_object_id(careers)
        careers = filter(lambda x: x in values, careers)
    if values[0] in careers and len(careers) > 1:
        careers.pop(values[0])
    advert["careers"] = list(set(careers))
    # user & status
    advert["user"] = object_id(creator["_id"])
    # NOTE You should specified status when update campaign record, `None`
    # means not change. By default `status` will reset to `verifying` when
    # update.
    if status is not None:
        statuses = Property.campaign_statuses_by_code_to__id()
        if status not in statuses:
            raise ValueError("Unknown campaign status `%s`." % status)
        advert["status"] = object_id(statuses[status])
    budget.save()
    content.save()
    advert["budget"] = object_id(budget["_id"])
    advert["content"] = object_id(content["_id"])
    if "media_type" in advert:  # clean up.
        del advert["media_type"]

    # 上网方式
    network = kwargs.pop("network", [])
    if len(network) > 0:
        advert["network"] = bulk_object_id(network)

    # 投放日
    weekday_launch = kwargs.pop("weekday_launch", [])
    if len(weekday_launch) > 0:
        advert["weekday_launch"] = bulk_object_id(weekday_launch)

    # 投放频次
    frequency = kwargs.pop("frequency", None)
    advert["frequency"] = frequency

    advert.save()
    return advert


@bulk_up
def campaign_transform_advert(lst):
    ret = map(_campaign_transform_advert, lst)
    ret = dict_swap(ret, _campaign_transform_advert_swap,
                    "status", "payment_type",
                    "budget", "content",
                    "user", "languages", "business_model", "ages",
                    "brands", "careers", "carriers", "category", "gender",
                    "platform", "regions", "time_ranges", "areas",'tag',
                    "verification_message", "budget_balance","click_action", "group", "network", "weekday_launch", "app_categories")

    lst = []
    for i in ret:
        regions = ''
        for region in i['regions']:
            regions += region['country']+region['province']+region['city']+' '
        i['regions_str'] = regions
        if i['content']:
            if 'new_word' in i['content']:
                if i['content']['new_word'] and 'display_manner' in i['content']['new_word']:
                    i['content']['new_word']['display_manner'] = Property.display_manner_by__id_to_value(str(i['content']['new_word']['display_manner']))
            if 'new_images' in  i['content']:
                for img in i['content']['new_images']:
                    #img['img_name'] = '/upload/' +img['img_name']
                    if 'display_manner' in img:
                        img['display_manner'] = Property.display_manner_by__id_to_value(str(img['display_manner']))
        if i["payment_type"]["code"] == "cpc":
            if i['content'] and 'url' in i['content']:
                i["content"]["url"] = i["redirect_url"]
        lst.append(i)
    return lst


def _campaign_transform_advert(d):
    nd = {}
    nd["removed"] = d["removed"]
    if "check_code" in d:
        nd["check_code"] = d["check_code"]
    else:
        nd["check_code"] = ""
    if "check_click_code" in d:
        nd["check_click_code"] = d["check_click_code"]
    else:
        nd["check_click_code"] = ""
    if "double_click" in d:
        nd["double_click"] = d["double_click"]==1 and '开启'.decode('utf-8') or '关闭'.decode('utf-8')
    else:
        nd["double_click"] = "关闭".decode('utf-8')
    # 摇一摇
    if "shake" in d:
        nd["shake"] = str(d["shake"]) == 'on' and '开启'.decode('utf-8') or '关闭'.decode('utf-8')
    else:
        nd["shake"] = "关闭".decode('utf-8')
    # 刮一刮
    if "shave" in d:
        nd["shave"] = str(d["shave"]) == 'on' and '开启'.decode('utf-8') or '关闭'.decode('utf-8')
    else:
        nd["shave"] = "关闭".decode('utf-8')
    # 吹一吹
    if "blow" in d:
        nd["blow"] = str(d["blow"]) == 'on' and '开启'.decode('utf-8') or '关闭'.decode('utf-8')
    else:
        nd["blow"] = "关闭".decode('utf-8')
    # 回调地址
    if 'cpa_callback_url' in d:
        nd['cpa_callback_url'] = d['cpa_callback_url']
    else:
        nd['cpa_callback_url'] = ''
    # Android 专用项目设置
    if 'cpa_apk_timeout' in d:
        nd['cpa_apk_timeout'] = d['cpa_apk_timeout']

    nd['show_type'] = Property.show_types_by__id()[str(d['show_type'])]

    # 添加点击交互功能
    if "click_action" in d and d["click_action"]:
        nd["click_action"] = str(d["click_action"])
    else:
        nd["click_action"] = None

    if "phone" in d and d["phone"]:
        nd["phone"] = str(d["phone"])
    else:
        nd["phone"] = None

    if "message" in d and d["message"]:
        nd["message"] = d["message"]
    else:
        nd["message"] = None

    if "map_address" in d and d["map_address"]:
        nd["map_address"] = d["map_address"]
    else:
        nd["map_address"] = None
    #----
    nd["_id"] = d["_id"]
    nd["name"] = d["name"]
    nd["description"] = d["description"]
    nd["budget_balance"] = "budget-%s" % d["_id"]
    if "budget" in d:
        nd["budget"] = str(d["budget"])
    if "payment_type" in d:
        nd["payment_type"] = str(d["payment_type"])
    if "premium_price" in d:
        nd["premium_price"] = d["premium_price"]
    if "redirect_url" in d:
        nd["redirect_url"] = d["redirect_url"]
    if "status" in d:
        nd["status"] = str(d["status"])
    if "content" in d:
	nd["content"] = str(d["content"])
    nd["tag"] = str(d["tag"])
    if "priority" in d:
        nd["priority"] = d["priority"]
    if "date_creation" in d:
        nd["date_creation"] = d["date_creation"]
    if "date_start" in d:
        nd["date_start"] = d["date_start"]
    if "date_end" in d:
        nd["date_end"] = d["date_end"]
    nd["is_endless"] = nd.get("date_end") is None or nd["date_end"].year > 2099
    if "date_verifier" in d:
        nd["date_verifier"] = d["date_verifier"]
    # targetting arguments.
    if "app_language" in d:
        nd["languages"] = map(str, d["app_language"])
    else:
        nd["languages"] = []
    if "app_type" in d:
        nd["business_model"] = str(d["app_type"])
    if "ages" in d:
        nd["ages"] = map(str, d["ages"])
    else:
        nd["ages"] = []
    if "brand_mobile" in d:
        nd["brands"] = map(str, d["brand_mobile"])
    else:
        nd["brands"] = []
    if "careers" in d:
        nd["careers"] = map(str, d["careers"])
    else:
        nd["careers"] = []
    if "carrier" in d:
        nd["carriers"] = map(str, d["carrier"])
    else:
        nd["carriers"] = []
    if "category" in d:
        nd["category"] = str(d["category"])
    if "gender" in d:
        nd["gender"] = str(d["gender"])
    else:
        nd["gender"] = str(Property.genders_by_code_to__id()["unlimited"])
    if "platform" in d:
        nd["platform"] = map(str, d["platform"])
    else:
        nd["platform"] = []
    if "region_launch" in d:
        nd["regions"] = map(str, d["region_launch"])
    else:
        nd["regions"] = []
    if "time_range" in d:
        nd["time_ranges"] = map(str, d["time_range"])
    else:
        nd["time_ranges"] = []
    if "trading_areas" in d:
        nd["areas"] = map(str, d["trading_areas"])
    else:
        nd["areas"] = []
    if "user" in d: nd["user"] = str(d["user"])
    if "budget" in d:
        nd["budget"] = str(d["budget"])
    if "date_start" in d:
        nd["date_start"] = to_timezone(to_timezone(d["date_start"], "UTC"), "Asia/Shanghai")
    if "date_end" in d:
        if d["date_end"] is None:
            nd["date_end"] = None
        else:
            nd["date_end"] = to_timezone(to_timezone(d["date_end"], "UTC"), "Asia/Shanghai")
    if "user" in d:
        nd["user"] = str(d["user"])
    if "verification_message" in d:
        __ = map(str, d["verification_message"])
        if len(__) > 0:
            nd["verification_message"] = __[-1]

    if "group" in d:
        nd["group"] = str(d["group"])
    else:
        nd["group"] = None

    if "advert_code" in d:
        nd["advert_code"] = d["advert_code"]
    else:
        nd["advert_code"] = None

    if "network" in d:
        nd["network"] = map(str, d["network"])

    if "weekday_launch" in d:
        nd["weekday_launch"] = map(str, d["weekday_launch"])

    if "frequency" in d:
        nd["frequency"] = d["frequency"]
    else:
        nd["frequency"] = None

    if "app_categories" in d:
        nd["app_categories"] = map(str, d["app_categories"])
    else:
        nd["app_categories"] = []
    nd['show_type'] = Property.show_types_by__id()[str(d['show_type'])]
    return nd


def _campaign_transform_advert_swap(status, payment_type, budget, content,
                                    user, languages, business_model, ages,
                                    brands, careers, carriers, category,
                                    gender, platform, regions,
                                    time_ranges, areas,
                                    verification_message, budget_balance,
                                    click_action, group,
                                    **kwargs):
    f = lambda y: dict(map(lambda x: (str(x["_id"]), x), y))
    budgets = list(Budget.query(_id={"$in": bulk_object_id(budget)}))
    __ = Property.budget_types_by__id()
    for budget in budgets:
        budget["type"] = __[str(budget["type"])]
    show_types = Property.show_types_by__id()
    contents = []
    __ = AdvertContent.query(_id={"$in": bulk_object_id(content)})
    prefix = config.get("api.static_url")
    base_dir = config.get("env.html_file_path")

    html_url = config.get("api.html_url")
    upload_url = config.get("api.upload_url")

    for d in __:
        d["_id"] = str(d["_id"])
        d["zip"] = ""  # Always set to blank
        if "url" in d and d["url"]:
            d["cpa_index_file"] = path.join(base_dir, d["url"])
            if not path.exists(d["cpa_index_file"]):
                d["cpa_index_file"] = ""
                # FIXME should log notice?
            #d["url"] = prefix + "/html/" + d["url"]
            d["url"] = html_url + d["url"]
            d["url_base"] = path.dirname(d["url"]) + "/"
        else:
            d["cpa_index_file"] = d["url"] = d["url_base"] = ""
        if d["new_images"]:

            for nu in range(len(d["new_images"])):
                #d["new_images"][nu]['img_name'] = prefix + "/upload/" + d["new_images"][nu]['img_name']
                d["new_images"][nu]['img_name'] = upload_url + d["new_images"][nu]['img_name']

        d["show_type"] = show_types[str(d["show_type"])]
        contents.append((d["_id"], d))

    # 转换广告组信息
    groups = []
    if group:
        groups = list(AdvertGroup.query({
            "_id": {"$in": bulk_object_id(group)},
            }))

    users = {}
    if user:
        users = dict(map(lambda x: (str(x["_id"]), x), User.query({
            "_id": {"$in": bulk_object_id(user)},
            }, fields={'pending_transactions': False})))
    msg = VerificationMessage.query({"_id": {"$in": bulk_object_id(verification_message)}})
    msg = dict([(str(d["_id"]), d) for d in msg])
    # budget balance, from memcache
    ret = {}
    try:
        with mc_pool.reserve() as mc:
            ret = mc.get_multi(budget_balance)
    except Exception:
        pass

    __ = dict(((k, float(v) / 1000) for k, v in ret.items()))
    for k in budget_balance:
        if k not in __:
            __[k] = float(0)
    budget_balance = __
    return {
        "status": f(Property.campaign_statuses(raw=True)),
        "payment_type": f(Property.payment_types(raw=True)),
        "budget": f(budgets),
        "content": dict(contents),
        "user": users,
        "languages": f(Property.languages(raw=True)),
        "business_model": f(Property.business_models(raw=True)),
        "ages": f(Property.ages(raw=True)),
        "brands": f(Property.brands(raw=True)),
        "careers": f(Property.careers(raw=True)),
        "carriers": f(Property.carriers(raw=True)),
        "category": f(Property.categories(raw=True)),
        "gender": f(Property.genders(raw=True)),
        "platform": f(Property.platforms(raw=True)),
        "regions": f(Property.regions(raw=True)),
        "tag": f(Property.advert_tags(raw=True)),
        "time_ranges": f(Property.time_ranges(raw=True)),
        "areas": f(Property.areas(raw=True)),
        "verification_message": msg,
        "budget_balance": budget_balance,
        "click_action": f(Property.clickactions(raw=True)),
        "group": f(groups),
        "network": f(Property.network_types(raw=True)),
        "weekday_launch": f(Property.weekdays(raw=True)),
        "app_categories": f(Property.categories(raw=True)),
    }


@bulk_up
def campaign_transform_api_advert(lst):
    #pprint(lst[0])
    nl = map(_campaign_transform_api_advert, lst)
    nl = dict_swap(nl, _campaign_transform_api_advert_swap,
                    "content", "show_type", "type")
    ret = []
    for d in nl:
        #pprint(d)
        # 2014-01-01: Added Session ID to advert ID.
        id_bk = d["_id"]
        d["_id"] = "%s%s" % (d["_id"], uuid.uuid4().hex)
        # transform content for APIAdvertContent.
        showtype = d.pop('show_type')
        d['content']['show_type'] = showtype
        d["content"]["word"] = d["content"]["new_word"]
        del d["content"]["new_word"]
        d["content"]["images"] = d["content"]["new_images"]
        del d["content"]["new_images"]

        if d["type"] == "cpm":
            d["content"]["zip"] = ""
            d["content"]["url"] = ""
        elif d["type"] == "cpc":
            d["content"]["zip"] = ""
            d["content"]["url"] = ""
            # 添加点击交互动作
            #click_action_id = Advert.get_one(id_bk)['click_action']
            #d['click_action'] = ClickAction.get_one(click_action_id)['code']
            d['click_action'] = str(Property.clickactions_by__id_to_value()[d["click_action"]])

        elif d["type"] == "cpa":
            d["redirect_url"] = d["content"]["url"]
            d["content"]["zip"] = ""
            d["content"]["url"] = ""
            d["click_action"] = '3'
        ret.append(d)
        # ret.append(data_pb2.APIAdvert().from_dict(d))
    return ret


def _campaign_transform_api_advert(d):
    nd = {}
    nd["_id"] = str(d["_id"])
    nd["content"] = nd["show_type"] = str(d["content"])
    nd["redirect_url"] = d["redirect_url"]
    nd["type"] = str(d["payment_type"])
    nd["click_action"] = str(d["click_action"])
    nd["check_code"] = d["check_code"]
    nd["check_click_code"] = d["check_click_code"]
    nd["double_click"] = d["double_click"]

    return nd


def _campaign_transform_api_advert_swap(content, show_type, type):
    ids = bulk_object_id(content)
    contents = list(AdvertContent.query({"_id": {"$in": ids}}))
    show_types = Property.show_types_by__id()
    lst_contents = []
    lst_show_types = []
    prefix = config.get("api.static_url")
    html_url = config.get("api.html_url")
    for d in contents:
        d["_id"] = str(d["_id"])
        d["zip"] = ""  # Always set to blank
        if "url" in d and d["url"]:
            #d["url"] = prefix + "/html/" + d["url"]
            d["url"] = html_url + d["url"]
        else:
            d["url"] = ""
        # if d["images"]:
        #     d["images"] = map(lambda x: prefix + "/upload/" + x, d["images"])
        _id = str(d["show_type"])
        lst_contents.append((d["_id"], d))
        lst_show_types.append((d["_id"], show_types[_id]))
    return {
        "content": dict(lst_contents),
        "show_type": dict(lst_show_types),
        "type": Property.payment_types_by__id_to_code(),
    }


def campaign_set_status(oid, status):
    statuses = Property.campaign_statuses_by_code_to__id()
    if status not in statuses:
        return False
    Advert.update({"_id": object_id(oid)}, {"$set": {"status": object_id(statuses[status])}})
    purge_advert(oid)


def prepare_campaign_form(advert=None, request=None):
    d = {}
    d["advert_click_action_array"] = Property.clickactions(raw=True)
    # 检查被选中的广告类型
    if advert and "app_categories" in advert:
        checked = map(lambda x: x["_id"], advert["app_categories"])
    else:
        checked = ()
    d["advert_category_array"] = set_checked(Property.categories(raw=True), "_id", checked)

    d["media_type_array"] = []  # NOTE Removed.
    d["ad_platform_array"] = Property.platforms(raw=True)
    d["time_range_array"] = Property.time_ranges(raw=True)
    d["ad_payment_type_array"] = Property.payment_types(raw=True)
    d["ad_budget_type_array"] = Property.budget_types(raw=True)
    d["application_language_array"] = Property.languages(raw=True)
    d["application_type_array"] = Property.business_models(raw=True)
    d["brand_mobile_array"] = Property.brands(raw=True)
    d["carrier_array"] = Property.carriers(raw=True)
    d["circle_list"] = trading_area.find_all_trading_areas()
    f1 = lambda x: (str(x["value"]), {"n": " ".join((x["province"], x["city"]))})
    f2 = lambda x: x["value"] > 0
    d["city_data"] = json.dumps(dict(map(f1, filter(f2, Property.regions(raw=True)))))
    selected_ages = (0, )
    selected_careers = (0, )
    selected_gender = 0
    # NOTE Both `city_data` and `cityData_y` dumps in JSON.

    user_id = None
    series_id = None
    group_id = None
    group_list_array = []
    series_list_array = []
    if advert:
        d["date_start"] = advert["date_start"].strftime("%Y-%m-%d")
        if advert["date_end"]:
            d["date_end"] = advert["date_end"].strftime("%Y-%m-%d")
        d["cityData_y"] = json.dumps(dict(map(f1, filter(f2, advert["regions"]))))
        if advert["ages"]:
            selected_ages = map(lambda x: x["value"], advert["ages"])
        if advert["careers"]:
            selected_careers = map(lambda x: x["value"], advert["careers"])
        if advert["gender"]:
            selected_gender = advert["gender"]["value"]
        if advert["group"]:
            group_id = advert["group"]["_id"]
            series_id = advert["group"]["series"]
        if advert["user"]:
            user_id = advert["user"]["_id"]
    else:
        d['date_start'] = today("%Y-%m-%d")
        d["cityData_y"] = "{}"
    d["ages"] = Property.ages(raw=True)
    map(lambda x: setitem(x, "checked", x["value"] in selected_ages), d["ages"])
    d["careers"] = Property.careers(raw=True)
    map(lambda x: setitem(x, "checked", x["value"] in selected_careers), d["careers"])
    d["genders"] = Property.genders(raw=True)
    map(lambda x: setitem(x, "checked", x["value"] == selected_gender), d["genders"])

    if request:
        if group_id is None:
            group_id = object_id(request.params.get('group_id', ''))

        if user_id is None:
            user_id = object_id(request.params.get('user_id', ''))

            if not user_id:
                user_id = request.session_id


    if series_id is None and group_id is not None:
        advert_group = AdvertGroup.get_one(_id=group_id)
        if advert_group:
            series_id = advert_group['series']

    if series_id:
        group_list_array = list(AdvertGroup.query(series=series_id, removed=False).sort("date_creation", -1))

    if user_id:
        series_list_array = get_advert_series_by_user(object_id(user_id))

    d['group_list_array'] = group_list_array
    d['series_list_array'] = series_list_array
    d['series_id'] = series_id
    d['group_id'] = group_id

    d['network_type_array'] = Property.network_types(raw=True)
    d['weekday_array'] = Property.weekdays(raw=True)

    return d


def set_campaign_status(campaign, status_code, reject_reason=""):
    statuses = Property.campaign_statuses_by_code_to__id()
    if status_code not in statuses:
        raise ValueError("Invalid status code `%s`." % status_code)
    d = {"$set": {"status": object_id(statuses[status_code])}}
    if status_code == "rejected":
        if not reject_reason:
            raise ValueError("You should give a reason when set rejected to a advert.")
        msg = VerificationMessage()
        msg["content"] = reject_reason
        msg.save()
        d["$push"] = {"verification_message": msg["_id"]}
    Advert.update({"_id": object_id(campaign["_id"])}, d)
    purge_advert(campaign["_id"])


#---------------------------------------------------------------------
#           Targetting & Ranking, process to advert request
#---------------------------------------------------------------------

#publishers = {}

@cache.region('in_memory')
def get_publisher(api_key):
   status = Property.publisher_statuses_by_code_to__id()["running"]
   res = App.get_one(api_key=api_key, status=object_id(status), removed=False)

   if res:
      res = publisher_transform_app(res)

   return res

#publishers = {}

@cache.region('in_memory')
def get_all_status_publisher(api_key):
    res = App.get_one(api_key=api_key, removed=False)

    statuses = Property.publisher_statuses_by_code_to__id()
    allowedstatus = [object_id(statuses['running']),object_id(statuses['not verified']),object_id(statuses['verifying']),object_id(statuses['rejected'])]
    res = App.get_one(api_key=api_key, removed=False,status={'$in':allowedstatus})
    
    if res:
        res = publisher_transform_app(res)

   
    return res


#campaigns = {}

@cache.region('in_memory')
def get_campaign(id):

    #status = Property.campaign_statuses_by_code_to__id()["running"]

    #advert = Advert.get_one(_id=object_id(id), removed=False,
    #                        status=object_id(status))

    advert = get_advert(id)

    if advert:
       advert = campaign_transform_advert(advert)

    return advert

@bulk_up
def purge_advert(lst):
    for id in lst:
        pub_region_invalidate(get_campaign, "in_memory", str(id))
        pub_region_invalidate(get_advert, "in_memory", str(id))
        send_msg('purge_advert', str(id))

def purge_app(publisher):
    if not hasattr(publisher, "api_key"):
        publisher = get_app(publisher["_id"])

    pub_region_invalidate(get_publisher, "in_memory", publisher["api_key"])
    pub_region_invalidate(get_app, "in_memory", str(publisher["_id"]))
    send_msg('purge_app', str(publisher["_id"]))
    send_msg('purge_app', publisher["api_key"])


def build_target_query(msg, *args, **kwargs):
    """ Build target query for database querying and rank score computing.

        `msg` must a protobuf message `APIAdvertShow` from client.
    """
    d = {}
    log = {}
    log['api_key'] = msg.api_key
    # When App is NOT running OR api_key NOT matched...
    #status = Property.publisher_statuses_by_code_to__id()["running"]
    #res = App.get_one(api_key=msg.api_key, status=object_id(status), removed=False)
    res = get_all_status_publisher(msg.api_key)
    print res['status']['code']
    if res is None or res['status']['code'] not in ['running','verifying','not verified','rejected']:
        return False
    # Platform compare: expected and API request.
    #publisher = publisher_transform_app(res)
    publisher = res
    #print(publisher)
    x, y = publisher["platform"]["code"].lower(), msg.device_info.platform.lower()
    log['platform'] = y
    if x != y:
        return False
    d['status'] = publisher['status']['code']
    d["platform"] = publisher["platform"]["_id"]
    show_types = Property.show_types_by_value_to__id()

    if msg.show_type_value == 100:
        d["show_type"] = [show_types[1], show_types[2], show_types[3]]
    else:
        d["show_type"] = [show_types[msg.show_type_value]]
        #全屏
        if msg.show_type_value == 4:
            ds = OfferWallDeveloperSetting.get_without_id({'app_id':object_id(res['_id'])})
            if ds:
                d['duration_show'] = ds.get('enable_duration',False) and ds.get('fullscreen_duration_show',5) or 0
                d['duration_show'] = float(d['duration_show'])
        #插屏
        elif msg.show_type_value == 5:
            ds = OfferWallDeveloperSetting.get_without_id({'app_id':object_id(res['_id'])})
            if ds:
                d['duration_show'] = ds.get('enable_duration',False) and ds.get('duration_show',5) or 0
                d['duration_show'] = float(d['duration_show'])

    log['show_type'] = msg.show_type_value

    # TODO Time-based check: all request time should larger than current UTC timestamp.
    # NOTE When client set illegal thing, we can assume it's evil.
    send_at, now = 0, today(True, utc=True)
    if hasattr(msg, "date_creation"):
        sent_at = safe_int(msg.date_creation) / 1000.0
    if send_at < (now - 600):
        sent_at = now
    d["utc_request_sent"] = timestamp_to_datetime(sent_at)
    #d["utc_request_received"] = today(utc=True)
    times = Property.time_ranges_by_code_to__id()
    h = str(to_timezone(d["utc_request_sent"], "Asia/Shanghai").hour)
    d["time"] = object_id(times.get(h))
    # IP-based region detection.
    log['ip_address'] = msg.device_info.ip_address
    #ip_int = Ip2Int(msg.device_info.ip_address)
    # Optimize for query speed:
    # based on sampling, start with small range (matched in 99% cases)
    #ip_region = IPDatabase.get_one({
    #    "ip_start": {"$lte": ip_int, "$gte": ip_int - 65536},
    #    "ip_end": {"$gte": ip_int, "$lte": ip_int + 65536}
    #})
    #if not ip_region:
    #    ip_region = IPDatabase.get_one({
    #        "ip_start": {"$lte": ip_int, "$gte": ip_int - 4194303},
    #        "ip_end": {"$gte": ip_int, "$lte": ip_int + 4194303}
    #    })
    #__ = [{"value": 0}]
    #if ip_region is not None:
    #    __.append({"province": ip_region["province"], "city": ""})
    #    if ip_region["city"] != "":
    #        __.append({"city": ip_region["city"]})

    __ = [Property.regions_by_value_to__id()[0]]

    region = kwargs.pop("region", None)
    city = kwargs.pop("city", None)
    province_to__id = Property.regions_by_province_code_to__id()
    city_to__id = Property.regions_by_city_code_to__id()

    if region:
        region = region.lower()
        if region in province_to__id:
           __.append(province_to__id[region])

        if city:
           city = city.lower()
           if region in city_to__id and city in city_to__id[region]:
               __.append(city_to__id[region][city])

    d["regions"] = bulk_object_id(__)

    # Trading areas.
    log['longitude'] = msg.device_info.longitude
    log['latitude'] = msg.device_info.latitude
    point = wgs2gcj(msg.device_info.longitude, msg.device_info.latitude)
    areas = trading_area.get_trading_areas_by_point(point)
    d["areas"] = map(lambda d: d["_id"], areas)
    # d["categories"] = bulk_object_id((x["_id"] for x in publisher["category"]))
    carriers = Property.carriers_by_code_to__id()
    d["carriers"] = [carriers["all"]]
    imsi = msg.device_info.imsi
    log['imsi'] = imsi
    if imsi in ("46000", "46002"):
        d["carriers"].append(carriers["cmcc"])
    elif imsi == "46001":
        d["carriers"].append(carriers["unicom"])
    elif imsi == "46003":
        d["carriers"].append(carriers["cmnet"])
    else:
        d["carriers"].append(carriers["other"])
    d["carriers"] = bulk_object_id(d["carriers"])
    # TODO also check msg.device_info
    d["languages"] = map(lambda d: d["_id"], publisher["languages"])
    d["languages"].append(object_id(Property.languages_list()[0]))
    # brands
    brands = Property.brands_by_code_to__id()
    d["brands"] = [brands["all"]]
    brand_name = msg.device_info.device_brand
    log['brand_name'] = brand_name
    if brand_name in brands:
        d["brands"].append(brands[brand_name])
    d["brands"] = bulk_object_id(d["brands"])
    # genders
    genders = Property.genders_by_code_to__id()
    d["genders"] = [genders["unlimited"]]
    if "target_gender" in publisher:
        d["genders"].append(publisher["target_gender"]["_id"])
    d["genders"] = bulk_object_id(set(d["genders"]))
    # ages
    ages = Property.ages_by_code_to__id()
    d["ages"] = [ages["unlimited"]]
    unlimited = str(ages["unlimited"])
    if "target_ages" in publisher:
        if unlimited in publisher["target_ages"]:
            d["ages"].extend(ages)
        else:
            d["ages"].extend(map(lambda d: d!=None and d["_id"] or None,
                                 publisher["target_ages"]))
    d["ages"] = bulk_object_id(set(d["ages"]))
    # careers
    careers = Property.careers_by_code_to__id()
    d["careers"] = [careers["unlimited"]]
    unlimited = str(careers["unlimited"])
    if "target_careers" in publisher:
        if unlimited in publisher["target_careers"]:
            d["careers"].extend(careers)
        else:
            d["careers"].extend(map(lambda d: d["_id"],
                                    publisher["target_careers"]))
    d["careers"] = bulk_object_id(set(d["careers"]))
    # business models / application type
    business_models = Property.business_models_by_code_to__id()
    d["business_models"] = [business_models["all"], publisher["business_model"]["_id"]]
    d["business_models"] = bulk_object_id(d["business_models"])
    # base price
    if d['status']!='running':
        d["base_price"] = 0
    else:
        show_types = Property.show_types_by_value()
        if msg.show_type_value == 100:
            show_type_code = 'banner'
        else:
            show_type_code = show_types[msg.show_type_value]['code']
        d["base_price"] = min((publisher[d][show_type_code]["total"] for d in ("cpm", "cpc", "cpa")))
    d["category"] = map(lambda x: x["_id"], publisher["category"])

    # 上网方式
    network = msg.device_info.net.upper()
    d['network'] = [Property.network_types_by_value_to__id()[0]]
    if network in Property.network_types_by_code_to__id():
        d['network'].append(Property.network_types_by_code_to__id()[network])

    # 周日
    weekday = d["utc_request_sent"].isoweekday()
    d['weekday_launch'] = [Property.weekdays_by_value_to__id()[0]]
    if weekday in Property.weekdays_by_value_to__id():
        d['weekday_launch'].append(Property.weekdays_by_value_to__id()[weekday])

    # d["sdk_version"] = msg.device_info.sdk_version.split('.')[0]

    log['open_udid'] =  msg.device_info.openudid
    log['mac'] =  msg.device_info.mac_address

    d['udid'] = check_udid(msg)
    #logger = logging.getLogger('advertLog')
    #logger.info('api_key: %(api_key)s, platform: %(platform)s, brand_name: %(brand_name)s, imsi: %(imsi)s, show_type: %(show_type)s, ip_address: %(ip_address)s, longitude: %(longitude)s, latitude: %(latitude)s, open_udid: %(open_udid)s, mac: %(mac)s' % log)
    return d


SCORE_FACTORS = {
    "platforms": Decimal(1),
    "category": Decimal(1),
    "times": Decimal(1),
    "regions": Decimal(5),
    "areas": Decimal(1),
    "carriers": Decimal(1),
    "brands": Decimal(1),
    "languages": Decimal(1),
    "genders": Decimal(1),
    "ages": Decimal(1),
    "careers": Decimal(1),
    "business_models": Decimal(1),
    "biguser": Decimal(1),
    "cpa": Decimal(1.2),
    "cpc": Decimal(1.1),
    "cpm": Decimal(1),
    "frequency": Decimal(1.5)
}

getcontext().prec = 6


def _is_fine_accuracy(lst, wildscard=None):
    if len(lst) == 0:
        return False
    if len(lst) == 1 and lst[0]["code"] == wildscard:
        return False
    return True

def _is_frequency(ad_id,ad_frequency,udid):

    if not ad_frequency:
        return True
    key = '{0}-{1}'.format(str(ad_id), str(udid))
    times = int(ad_frequency['times'])
    with mc_pool.reserve() as mc:
        res = mc.get(key)
        if res:
            res = int(res)
            if res < times:
                return True
            else:
                return False
        else:
            return True

def check_frequency(mc,ad,udid):
    # 更新广告的频次信息

    if ad["frequency"] is None:
        return

    else:
        key = '{0}-{1}'.format(str(ad['_id']), str(udid))
        times = ad['frequency']['times']
        interval = int(ad['frequency']['interval']) * 3600
        with mc_pool.reserve() as mc:
            res = mc.get(key)
            if res:
                mc.incr(key)
                return
            else:
                mc.set(key,1,interval)
                return

def check_udid(msg):
    device_info = msg.device_info
    if device_info.openudid:
        return device_info.openudid
    elif device_info.imei:
        return device_info.imei
    elif device_info.mac_address:
        return device_info.mac_address
    elif device_info.ip_address:
        return device_info.ip_address
    raise ValueError("Not ID for audience.")


def get_score(campaign,query,udid):
    final = Decimal(1)
    # # ----------------------------------------------------------------
    # # For targetting, fine accuracy get high score than coarse one.
    # if _is_fine_accuracy(campaign["ages"], "unlimited"):
    #     final += SCORE_FACTORS["ages"]
    # if _is_fine_accuracy(campaign["languages"], "all"):
    #     final += SCORE_FACTORS["languages"]
    # if _is_fine_accuracy(campaign["brands"], "all"):
    #     final += SCORE_FACTORS["brands"]
    # if _is_fine_accuracy(campaign["careers"], "unlimited"):
    #     final += SCORE_FACTORS["careers"]
    # if _is_fine_accuracy(campaign["carriers"], "unlimited"):
    #     final += SCORE_FACTORS["carriers"]
    # if campaign["gender"]["code"] == "unlimited":
    #     final += SCORE_FACTORS["genders"]
    # if len(campaign["time_ranges"]) != 24:
    #     final += SCORE_FACTORS["times"]

    if _is_frequency(campaign['_id'],campaign['frequency'],udid):
        # final += SCORE_FACTORS["frequency"]
        pass
    else:
        final = -2

    # # ----------------------------------------------------------------
    # # Payment type based weightting.
    # final += SCORE_FACTORS[campaign["payment_type"]["code"]]
    # # ----------------------------------------------------------------
    # # Added score significantly if campaign owner is big user.
    # types = Property.user_types_by__id_to_code()
    # if types.get(str(campaign["user"]["type"])) == "advertiser_massive":
    #     final += SCORE_FACTORS["biguser"]
    # # ----------------------------------------------------------------
    # regions and areas: nothing match or match any.
    areas_matched = regions_matched = True
    __ = campaign["regions"]
    if len(__) == 1 and __[0]["value"] == 0:
        regions_matched = 2
    elif any((x["value"] == 0 for x in __)):
        regions_matched = 2
    elif any((x["_id"] in query["regions"] for x in __)):
        # final += SCORE_FACTORS["regions"]
        pass
    else:
        regions_matched = False
    if len(campaign["areas"]) > 0:
        areas_matched = False
        if regions_matched == 2:
            regions_matched = False
        if any((x["_id"] in query["areas"] for x in campaign["areas"])):
            # final += SCORE_FACTORS["areas"]
            areas_matched = True
    elif len(campaign["areas"]) == 0 and areas_matched:
        areas_matched = False
    if not areas_matched and not regions_matched:
        final = -1
    # ----------------------------------------------------------------
    # TODO fill rate
    return final

def get_campaign_budget_balance(id):
    key = "budget-%s" % id
    try:
        with mc_pool.reserve() as mc:
            ret = mc.get(key)
            if ret:
                return float(ret) / 1000.0
            else:
                return None
    except Exception:
        return None

# @TODO Removed?
def intersect_ratio(subset, universe):
    s, u = set(subset), set(universe)
    i = u.intersection(s)
    return Decimal(len(i)) / Decimal(len(universe))

def campaign_transform_advert_with_cache(lst):

    __ = []
    for id in lst:
        advert = get_campaign(id)
        __.append(advert)

    return __


def get_adverts_by_api_request(query, count=10, score_rank=True, region=None, city=None):

    udid = query.pop('udid', '')
    status = Property.campaign_statuses_by_code_to__id()["running"]
    now = query["utc_request_sent"].replace(minute=0, second=0, microsecond=0)
    # 重构sdk

    if query["show_type"]:
        show_type = {'$in': bulk_object_id(query["show_type"])}

    args = {
        "status": object_id(status),
        "date_start": {"$lte": now},
        #"$or": [{"date_end": {"$gt": now}},
        #        {"date_end": None}],
        "premium_price": {"$gte": query["base_price"]},
        # current `show_type` NOT apply.
        "show_type": show_type,
        # "show_type": object_id(query["show_type"]),
        "removed": False,
    }
    tags = Property.advert_tags_by_code_to__id()
    if query['status'] != 'running':
        args['tag'] = object_id(tags['test'])
    else:
        args['tag'] = {'$in':[object_id(tags['fill']),object_id(tags['sell'])]}
 
    # args["category"] = {"$in": query["categories"]}
    args["platform"] = {"$in": [query["platform"]]}
    args["time_range"] = {"$in": [query["time"]]}
    #if query["regions"]:
    #    args["region_launch"] = {"$in": query["regions"]}
        #args["$or"].append({"region_launch": {"$in": query["regions"]}})
    #if query["areas"]:
    #    args["$or"] = [{"trading_areas": {"$size": 0}}]
    #    args["$or"].append({"trading_areas": {"$in": query["areas"]}})
    if query["brands"]:
        args["brand_mobile"] = {"$in": query["brands"]}
    if query["languages"]:
        args["app_language"] = {"$in": query["languages"]}
    if query["business_models"]:
        args["app_type"] = {"$in": query["business_models"]}
    if query["carriers"]:
        args["carrier"] = {"$in": query["carriers"]}
    if query["genders"]:
        args["gender"] = {"$in": query["genders"]}
    if query["ages"]:
        args["ages"] = {"$in": query["ages"]}
    if query["careers"]:
        args["careers"] = {"$in": query["careers"]}
    if query["category"]:
        args["app_categories"] = {"$in": query["category"]}

    # 上网方式
    if query["network"]:
        args['network'] = {"$in": bulk_object_id(query["network"])}

    if query['weekday_launch']:
        args['weekday_launch'] = {"$in": bulk_object_id(query['weekday_launch'])}
   # adverts = Advert.query(**args)
    adverts = query_advert(args)
   # cursor.sort("premium_price", -1)
    adverts = dict(((str(i["_id"]), i) for i in adverts))
    ## @TODO fill budget plan; some ad should drop by budget limit.
    if len(adverts) > 0:
        #__ = campaign_transform_advert(adverts.values())

        __ = campaign_transform_advert_with_cache(adverts.keys())

        #fn = lambda x: x["premium_price"]
        #query["upper_price"] = max(__, key=fn)["premium_price"]
        #query["lower_price"] = min(__, key=fn)["premium_price"]
        adverts = map(lambda x: (get_score(x, query,udid), x["premium_price"], x["budget"]["amount"],
                                 str(x["_id"]),x['priority']), __)
        adverts = filter(lambda x: x[0] > 0, adverts)
        #adverts.sort(reverse=True)

        adverts = filter_overbudget(adverts)

        #adverts = [adverts[i[-1]] for i in sorted(ids, reverse=True)]
        #adverts = adverts[:count]
    if adverts:
        # FIXME Now just weighted random choice here.
        if len(adverts) > 1:
            choice = weighted_random(adverts, lambda x: float(x[-1]))
            result = [get_advert(choice[-2])]
        else:
            result = [get_advert(c[-2]) for c in adverts]
        # result[0]['duration_show'] = query.get('duration_show',15.0)
        return result, query.get('duration_show',15.0)
    else:
        # @FIXME No ad matching, fill some ads?
        return [],'not matched'

@cache.region("advert_query_cache")
def query_advert(args):
    return list(Advert.query(fields={'_id': True}, **args))


def filter_overbudget(adverts):
    adverts = dict(map(lambda x: (x[-1], x), adverts))
    try:
        with mc_pool.reserve() as mc:
            ret = mc.get_multi(adverts.keys(), key_prefix="budget-")
            for k, v in ret.iteritems():
                if not float(v) / 1000.0 < adverts[k][2]:
                    # over budget, remove ad from the list
                    del adverts[k]

    except Exception, ex:
        print ex


    return adverts.values()

#---------------------------------------------------------------------
#           CPA preview handler.
#---------------------------------------------------------------------


def get_cpa_preview_html(advert):
    padding = "\n".join((
        "<head>",
        '<base href="{0}" />'.format(advert["content"]["url_base"]),
        '<script src="/js/cpa/sdk.testing.js"></script>',
    ))
    with open(advert["content"]["cpa_index_file"]) as f:
        content = to_unicode(f.read())
        content = content.replace("<head>", padding)
        return content


#---------------------------------------------------------------------
#           Campaign Summary
#---------------------------------------------------------------------

@bulk_up
def transform_campaign_summary(lst):
    lst = map(_transform_campaign_summary, lst)
    lst = dict_swap(lst, _transform_campaign_summary_swap, "payment_name",
                    "payment_type", "payment_name", "status",
                    "impressions",  "clicks", "actions", "CTR",
                    "balance")
    return lst


def _transform_campaign_summary(d):
    nd = {"_id": d["_id"]}
    nd["impressions"] = nd["clicks"] = nd["actions"] = nd["CTR"] = nd["balance"] = str(d["_id"])
    if "name" in d:
        nd["name"] = to_unicode(d["name"])
    else:
        nd["name"] = ""
    if "payment_type" in d:
        nd["payment_type"] = nd["payment_name"] = str(d["payment_type"])
    else:
        nd["payment_type"] = nd["payment_name"] = ""
    if "premium_price" in d:
        nd["premium_price"] = float(d["premium_price"])
    else:
        nd["premium_price"] = 0.0
    if "date_start" in d:
        nd["date_start"] = d["date_start"]
    else:
        nd["date_start"] = ""
    if "date_end" in d:
        nd["date_end"] = d["date_end"]
    else:
        nd["date_end"] = None
    if "status" in d:
        nd["status"] = str(d["status"])
    else:
        nd["status"] = ""
    return nd


def _transform_campaign_summary_swap(payment_name, payment_type, status,
                                     impressions, clicks, actions, CTR,
                                     balance):
    ret = {
        "payment_name": Property.payment_types_by__id_to_name(),
        "payment_type": Property.payment_types_by__id_to_code(),
        "status": Property.campaign_statuses_by__id_to_name(),
        "impressions": {},
        "clicks": {},
        "actions": {},
        "CTR": {},
        "balance": {},
    }
    ids = bulk_object_id(set(impressions))
    __ = ReportAdvertLog.query({"advert": {"$in": ids}}).sort("advert", 1)
    for _id, logs in groupby(__, lambda x: x["advert"]):
        _id = str(_id)
        logs = list(logs)
        ret["impressions"][_id] = sum(x["number_show"] for x in logs)
        ret["clicks"][_id] = sum(x["number_click"] for x in logs)
        ret["actions"][_id] = sum(x["number_action"] for x in logs)
        if ret["clicks"][_id] > 0:
            ctr = Decimal(ret["clicks"][_id]) / Decimal(ret["impressions"][_id]) * 100
            ctr = ctr.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        else:
            ctr = 0
        ret["CTR"][_id] = "%.2f%%" % ctr
        ret["balance"][_id] = sum(x["cost_total"] for x in logs)
    for _id in impressions:
        if _id not in ret["impressions"]:
            ret["impressions"][_id] = 0
            ret["clicks"][_id] = 0
            ret["actions"][_id] = 0
            ret["CTR"][_id] = "-"
            ret["balance"][_id] = 0
    return ret


#---------------------------------------------------------------------
#           Track Log Processor and Balancing
#---------------------------------------------------------------------

def seconds_to_daily_end():
    now = today()
    seconds = today(zero_time=True) + timedelta(days=1) - now
    return int(ceil(seconds.total_seconds()))


def get_memcache():
    mc = umemcache.Client(config.get("env.memcache_url"))
    mc.connect()
    return closing(mc)


def mc_timeout(mc, key, timeout):
    key = str(key)
    if mc.get(key):
        return False
    mc.set(key, str(today("%s")), timeout)
    return True


def mc_incr_float(mc, key, value, upper=None, daily=False):
    rec = mc.get(key)
    incr = int(value * 1000.0)
    if rec:
        ret = float(rec) / 1000.0
        if upper is None or ret < upper:
            mc.incr(key, incr)
            ret += value
        return ret
    if daily:
        mc.set(key, str(incr), seconds_to_daily_end())
    else:
        mc.set(key, str(incr))
    return value


class TrackLogRecord(object):
    def __init__(self, msg):
        if not self.set_campaign(msg.advert_id):
            raise ValueError("Invalid campaign (_id: %s)." % msg.advert_id)
        if not self.set_publisher(msg.api_key):
            raise ValueError("Invalid publisher (api_key: %s)." % msg.api_key)
        if not self.set_track_type(msg.value):
            raise ValueError("Invalid track type (value: %s)." % msg.value)
        self.raw = msg
        self.reason = ""
        self.ad_source = msg.ad_source
        self.value = msg.value
        self.audience = check_udid(msg)

    def valid(self):
        level_log, cost, share = self._get_billing()
        self.level_log = level_log
        self.cost = cost
        self.share = share
        with mc_pool.reserve() as mc:
            if self.value == 1:
                check_frequency(mc,self.campaign,self.audience)
            if cost == 0:
                return True
            if self._is_freeze(mc):
                self.reason = "freezed"
                return False
            if self._reach_budget_deal(mc, cost):
                return False
            if not self._balancing(mc, cost, share):
                self.reason = "balancing_failure"
                return False
        return True

    def save(self):
        now = today()
        periodic = now.strftime('%Y%m%d%H')

        hset = 'periodical_log_%s' % periodic
        key = '%s-%s-%s' % (self.campaign["_id"], self.publisher["_id"], self.track_type["code"])
        try:
            pipe  = redis_conn.pipeline()
            pipe.hincrby(hset, key, 1)

            if  self.cost > 0 and self.share > 0:
                hset = 'periodical_balance_%s' % periodic
                consumption_key = '%s-cost' % self.campaign["_id"]
                pipe.hincrbyfloat(hset, consumption_key, self.cost)

                share_key = '%s-%s-share' % (self.campaign["_id"], self.publisher["_id"])
                pipe.hincrbyfloat(hset, share_key, self.share)

                benefit_key = '%s-%s-benefit' % (self.campaign["_id"], self.publisher["_id"])
                pipe.hincrbyfloat(hset, benefit_key, self.cost - self.share)

            pipe.execute()

        except Exception, err:
            print(err)

        #log = TrackLog()
        #log["type"] = object_id(self.track_type["_id"])
        #log["advert"] = object_id(self.campaign["_id"])
        #log["app"] = object_id(self.publisher["_id"])
        #log["session_id"] = self.session_token
        #log["level_log"] = self.level_log
        # 增加标识广告来源字段
        #log['ad_source'] = self.ad_source
        #log["date_creation"] = now  # @FIXME parse timestamp from client?
        #log.save()

        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        ip_addr = self.raw.device_info.ip_address
        mac = self.raw.device_info.mac_address
        net = self.raw.device_info.net
        open_udid = self.raw.device_info.openudid
        longitude = self.raw.device_info.longitude
        latitude = self.raw.device_info.latitude
        brand = self.raw.device_info.device_brand
        platform = self.raw.device_info.platform
        sdk_version = self.raw.device_info.sdk_version
        model = self.raw.device_info.model
        imei = self.raw.device_info.imei
        imsi = self.raw.device_info.imsi
        logger = logging.getLogger('advertLog')
        logger.info('>>\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (timestamp, ip_addr, mac, open_udid, longitude, latitude, platform, net, brand, sdk_version, self.campaign["_id"], self.publisher["_id"], self.track_type["code"], self.ad_source, self.session_token, model, imei, imsi))


    # ------------------------------------------------------------
    # Accessors.

    #@property
    #def audience(self):
    #    device_info = self.raw.device_info
    #    if device_info.platform == "iOS":
    #        return device_info.openudid
    #    elif device_info.mac_address:
    #        return device_info.mac_address
    #    elif device_info.ip_address:
    #        return device_info.ip_address
    #    raise ValueError("Not ID for audience.")

    @property
    def developer(self):
        if not hasattr(self, "_publisher"):
            self._init_developer_and_advertiser_record()
        return self._developer

    @property
    def advertiser(self):
        if not hasattr(self, "_advertiser"):
            self._init_developer_and_advertiser_record()
        return self._advertiser

    # ------------------------------------------------------------
    # Protected methods: internal use ONLY, we don't need invoke
    # by hand in generally.
    # -----------------------------

    def set_campaign(self, advert_id):
        advert_id, session_token = advert_id[:24], advert_id[25:]
        #status = Property.campaign_statuses_by_code_to__id()["running"]
        #__ = Advert.get_one(_id=object_id(advert_id), removed=False,
        #                    status=object_id(status))
        __ = get_campaign(advert_id)
        if __ is None or __["status"]["code"] != "running" or __["removed"]:
            return False
        #self.campaign = campaign_transform_advert(__)

        self.campaign = __
        self.set_showtype(self.campaign['content']['show_type']['code'])
        self.session_token = session_token
        return True

    def set_publisher(self, publisher_api_key):
        #status = Property.publisher_statuses_by_code_to__id()["running"]
        #__ = App.get_one(api_key=publisher_api_key, removed=False,
        #                 status=object_id(status))

        __ = get_all_status_publisher(publisher_api_key)
        if not __:
            return False
        #self.publisher = publisher_transform_app(__)

        self.publisher = __
        return True

    def set_track_type(self, type_value):
        rec = Property.track_types_by_value().get(type_value)
        if not rec:
            return False
        self.track_type = rec
        return True

    def _get_billing(self):
        payment_type = self.campaign["payment_type"]["code"]
        price = self.campaign["premium_price"]
        type_code = self.track_type["code"]
        if self.publisher['status']['code'] == 'running':
            cpm_level = self.publisher["cpm"][self.show_type]
            cpc_level = self.publisher["cpc"][self.show_type]
            cpa_level = self.publisher["cpa"][self.show_type]
            if payment_type == "cpm" and type_code == "show":
                cost = float(Decimal(price) / Decimal(1000))
                share = float(Decimal(cpm_level["developer"]) / Decimal(1000))
                return (cpm_level["_id"], cost, share)
            elif payment_type == "cpc" and type_code == "click":
                return (cpc_level["_id"], price, cpc_level["developer"])
            elif payment_type == "cpa" and type_code == "action":
                return (cpa_level["_id"], price, cpa_level["developer"])
        return (None, 0, 0)

    def _init_developer_and_advertiser_record(self):
        ids = map(object_id, (self.publisher["user"]["_id"],
                              self.campaign["user"]["_id"]))
        cursor = User.query(_id={"$in": ids})
        if cursor.count() != 2:
            raise AssertionError("Publisher or advertiser not exists: [%s, %s]"
                                 % publisher, advertiser)
        developer, advertiser = list(cursor)
        if advertiser["_id"] == self.publisher["user"]["_id"]:
            developer, advertiser = advertiser, developer
        self._developer = developer
        self._advertiser = advertiser

    def _is_freeze(self, mc):
        """ Freeze time: default is 10 seconds, setup in config.ini:

        - `campaign.cpm_unfreeze_seconds`: CPM unfreeze time, in seconds.
        - `campaign.cpc_unfreeze_seconds`: CPC unfreeze time, in seconds.
        - `campaign.cpa_unfreeze_seconds`: CPA unfreeze time, in seconds.
        """
        payment_type = self.campaign["payment_type"]["code"]
        # timeout = config.getint("campaign.%s_unfreeze_seconds" % payment_type,
        #                         10)
        if payment_type == 'cpc' or payment_type == 'cpa':
            key = "freeze-%s-%s" % (self.audience, self.campaign["_id"])
            return not mc_timeout(mc, key, seconds_to_daily_end())

        return False

    def _reach_budget_deal(self, mc, cost):
        key = "budget-%s" % self.campaign["_id"]
        budget_type = self.campaign["budget"]["type"]["code"]
        upper = self.campaign["budget"]["amount"]
        if budget_type == "daily":
            ret = mc_incr_float(mc, key, cost, upper, daily=True)
            if ret >= upper:
                self.reason = "reach_daily_budget_deal"
                return True
        elif budget_type == "all":
            ret = mc_incr_float(mc, key, cost, upper)
            if ret >= upper:
                # When reach total budget deal, end the campaign and send mailing.
                campaign_set_status(self.campaign["_id"], "ended")
                mail = mailing.get_mail("notify_campaign_finished")
                mail.send(self.advertiser["email"],
                          receiver=self.advertiser,
                          advert=self.campaign)
                self.reason = "reach_total_budget_deal"
                return True
        return False

    def set_showtype(self,showtype):
        if 'banner' in showtype:
            showtype = 'banner'
        self.show_type = showtype
    def _balancing(self, mc, cost, share):
        advertiser, developer = self.advertiser, self.developer
        if advertiser["balance"] < cost:
            campaign_set_status(self.campaign["_id"], "paused")
            mail = mailing.get_mail("notify_campaign_paused_by_outaged")
            mail.send(advertiser["email"], receiver=advertiser, advert=self.campaign)
            return False

        # Transaction is emulating by two phase commits, may not precisely enough.
        # @see http://docs.mongodb.org/manual/tutorial/perform-two-phase-commits/
        #
        # The transaction implementation here is for potential underflow for advertiser,
        # if MongoDB server down when processing transaction, or process crash dealing
        # transaction, we do NOTHING for those cases.
        transaction = begin_transaction(advertiser["_id"], developer["_id"], cost, share)
        set_transaction_state(transaction, "pending")
        User.update({"_id": advertiser["_id"],
                    # "pending_transactions": {"$ne": transaction},
                    },
                    {"$inc": {"balance": -cost},
                     "$push": {"pending_transactions": transaction}
                    })
        User.update({"_id": developer["_id"],
                     #"pending_transactions": {"$ne": transaction},
                    },
                    {"$inc": {"balance": share},
                     "$push": {"pending_transactions": transaction}
                    })
        # Valiadation: is every thing ok after balancing?
        current = User.get_one(advertiser["_id"], fields={"balance": 1})["balance"]
        if current < 0:  # :`( - underflow, rollback.
            set_transaction_state(transaction, "canceling")
            User.update({"_id": advertiser["_id"],
                        # "pending_transactions": {"$ne": transaction},
                        },
                        {"$inc": {"balance": cost},
                         "$pull": {"pending_transactions": transaction}
                        })
            User.update({"_id": developer["_id"],
                        # "pending_transactions": {"$ne": transaction},
                        },
                        {"$inc": {"balance": -share},
                         "$pull": {"pending_transactions": transaction}
                        })
            set_transaction_state(transaction, "cenceled")
            return False
        # Congratulate!
        set_transaction_state(transaction, "committed")
        User.update({"_id": {"$in": (advertiser["_id"], developer["_id"])}},
                    {"$pull": {"pending_transactions": transaction}}, multi=True)
        set_transaction_state(transaction, "done")

        # Post-balancing: compute daily earned or daily consumed for user.
        #self._init_developer_and_advertiser_record()
        developer, advertiser = self.developer, self.advertiser

        balance = mc_incr_float(mc, "daily-earned-%s" % developer["_id"], share,
                                daily=True)
        if check_threshold(balance, developer.get("notify_daily_balance")):
            # Only sent once per day.
            key = "daily-earned-notify-%s" % developer["_id"]
            if not mc.get(key):
                mail = mailing.get_mail("notify_daily_income")
                mail.send(developer["email"], receiver=developer, balance=balance)
                mc.set(key, today("%s"), seconds_to_daily_end())
        key = "developer_balance_threshold_%s" % developer["_id"]
        last = mc.get(key)
        threshold = developer.get("notify_total_balance", 0)
        if threshold > 0 and developer["balance"] > threshold and not last:
            mail = mailing.get_mail("notify_developer_balancing")
            mail.send(developer["email"], receiver=developer)
            mc.set(key, str(int(developer["balance"] * 1000)))
        if last and developer["balance"] < (float(last) / 1000.0):
            mc.delete(key)

        balance = mc_incr_float(mc, "daily-consumed-%s" % advertiser["_id"], cost,
                                daily=True)
        if check_threshold(balance, advertiser.get("notify_daily_balance")):
            # Only sent once per day.
            key = "daily-consumed-notify-%s" % advertiser["_id"]
            if not mc.get(key):
                mail = mailing.get_mail("notify_daily_outgo")
                mail.send(developer["email"], receiver=advertiser)
                mc.set(key, today("%s"), seconds_to_daily_end())
        key = "advertiser_balance_threshold_%s" % advertiser["_id"]
        last = mc.get(key)
        threshold = advertiser.get("notify_total_balance", 0)
        if threshold > 0 and advertiser["balance"] < threshold and not last:
            mail = mailing.get_mail("notify_advertiser_balancing")
            mail.send(advertiser["email"], receiver=advertiser)
            mc.set(key, str(int(advertiser["balance"] * 1000)))
        if last and advertiser["balance"] > (float(last) / 1000.0):
            mc.delete(key)
        return True

# --- dsp track log ---------------------------------------------------------------
class DspTrackLogRecord(TrackLogRecord):
    def __init__(self, msg):
        if not self.set_publisher(msg.api_key):
            raise ValueError("Invalid publisher (api_key: %s)." % msg.api_key)
        if not self.set_track_type(msg.value):
            raise ValueError("Invalid track type (value: %s)." % msg.value)
        self.raw = msg
        self.reason = ""
        self.advert_id = msg.advert_id
        self.ad_source = msg.ad_source
        self.value = msg.value
        self.audience = check_udid(msg)

    def valid(self):
        level_log, share = self._get_billing()
        self.level_log = level_log
        self.share = share
        with mc_pool.reserve() as mc:
            # if self.value == 1:
            #     check_frequency(mc,self.campaign,self.audience)
            if self.value != 0:
                return True
            if self._is_freeze(mc):
                self.reason = "freezed"
                return False
            if not self._balancing(mc, share):
                self.reason = "balancing_failure"
                return False
        return True

    def _init_developer_and_advertiser_record(self):
        cursor = User.query(_id=self.publisher["user"]["_id"])
        if cursor.count() == 0:
            raise AssertionError("Publisher or advertiser not exists: [%s]"
                                 % str(self.publisher["user"]["_id"]))
        developer= list(cursor)[0]
        self._developer = developer

    def _is_freeze(self, mc):
        payment_type = ''
        #timeout = config.getint("campaign.%s_unfreeze_seconds" % payment_type,10)
        key = "freeze-%s-%s" % (self.audience, self.advert_id)
        #print key,timeout,mc_timeout(mc, key, seconds_to_daily_end())
        return not mc_timeout(mc, key, seconds_to_daily_end())

    def save(self):
        now = today()
        periodic = now.strftime('%Y%m%d%H')

        hset = 'dsp_periodical_log_%s' % periodic
        dsp = self.advert_id.split('||')[0]
        key = '%s-%s-%s-%s' % (dsp, self.publisher["_id"], self.track_type["code"], self.show_type)
        try:
            pipe  = redis_conn.pipeline()
            pipe.hincrby(hset, key, 1)

            if  self.share > 0:
                hset = 'dsp_periodical_balance_%s' % periodic

                share_key = '%s-%s-%s-share' % (dsp, self.show_type, self.publisher["_id"])
                pipe.hincrbyfloat(hset, share_key, self.share)


            pipe.execute()

        except Exception, err:
            print(err)

        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        ip_addr = self.raw.device_info.ip_address
        mac = self.raw.device_info.mac_address
        net = self.raw.device_info.net
        open_udid = self.raw.device_info.openudid
        longitude = self.raw.device_info.longitude
        latitude = self.raw.device_info.latitude
        brand = self.raw.device_info.device_brand
        platform = self.raw.device_info.platform
        sdk_version = self.raw.device_info.sdk_version
        model = self.raw.device_info.model
        imei = self.raw.device_info.imei
        imsi = self.raw.device_info.imsi
        logger = logging.getLogger('advertLog')
        logger.info('>>\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' % (timestamp, ip_addr, mac, open_udid, longitude, latitude, platform, net, brand, sdk_version, self.advert_id, self.show_type,self.publisher["_id"], self.track_type["code"], self.ad_source, '', model, imei, imsi))


    def _get_billing(self):
        #print self.show_type
        type_code = self.track_type["code"]
        cpc_level = self.publisher["cpc"][self.show_type]
        #print cpc_level
        if  type_code == "click":
            return (cpc_level["_id"], cpc_level["developer"])
        else:
            return (None, 0)

    def _balancing(self, mc, share):
        developer = self.developer

        User.update({"_id": developer["_id"],
                     #"pending_transactions": {"$ne": transaction},
                    },
                    {"$inc": {"balance": share},
                    })
        developer= self.developer

        balance = mc_incr_float(mc, "daily-earned-%s" % developer["_id"], share,
                                daily=True)
        if check_threshold(balance, developer.get("notify_daily_balance")):
            # Only sent once per day.
            key = "daily-earned-notify-%s" % developer["_id"]
            if not mc.get(key):
                mail = mailing.get_mail("notify_daily_income")
                mail.send(developer["email"], receiver=developer, balance=balance)
                mc.set(key, today("%s"), seconds_to_daily_end())
        key = "developer_balance_threshold_%s" % developer["_id"]
        last = mc.get(key)
        threshold = developer.get("notify_total_balance", 0)
        if threshold > 0 and developer["balance"] > threshold and not last:
            mail = mailing.get_mail("notify_developer_balancing")
            mail.send(developer["email"], receiver=developer)
            mc.set(key, str(int(developer["balance"] * 1000)))
        if last and developer["balance"] < (float(last) / 1000.0):
            mc.delete(key)

        return True


# ---闪拍track log
class ShanPaiTrackLogRecord(TrackLogRecord):
    def __init__(self, msg):
        super(ShanPaiTrackLogRecord,self).__init__(msg)

    def save(self):
        log = ShanPaiTrackLog()
        log["type"] = object_id(self.track_type["_id"])
        log["advert"] = object_id(self.campaign["_id"])
        log["app"] = object_id(self.publisher["_id"])
        log["session_id"] = self.session_token
        log["level_log"] = self.level_log
        # 增加标识广告来源字段
        log['ad_source'] = self.ad_source
        log["date_creation"] = today()  # @FIXME parse timestamp from client?
        log.save()
# ---------------

# -----------------------------------------------------------
# ------------------- CPA Track log START -------------------
# -----------------------------------------------------------
class CPATrackLogRecord(TrackLogRecord):

    def __init__(self, msg):
        self.publisher, self.track_type = None, -1
        if not self.set_campaign(msg.advert_id):
            raise ValueError("Invalid campaign (_id: %s)." % msg.advert_id)
        if not self.set_publisher(msg.api_key):
            raise ValueError("Invalid publisher (api_key: %s)." % msg.api_key)
        if not self.set_track_type(msg.value):
            raise ValueError("Invalid track type (value: %s)." % msg.value)

        self.is_clz_callback = msg.value == 6
        self.raw = msg
        self.ad_close_time = 0
        self.ad_click_position = ''
        self.advert_id = msg.advert_id
        self.ad_source = msg.ad_source
        self.value = msg.value
        self.audience = check_udid(msg)

        if self.is_clz_callback:
            self.latitude = msg.device_info.latitude
            self.longitude = msg.device_info.longitude
            self.close_time = msg.date_creation

    def set_track_type(self, type_value):
        rec = Property.cpa_track_log_type_by_value().get(type_value)
        if not rec:
            return False
        self.track_type = rec
        return True

    def valid(self):
        if self.is_clz_callback:
            return self.__close_track_log_valid()
        else:
            return self.__cpa_track_log_valid()

    def save(self):
        # 如果是关闭落地页，不需要写DB
        if self.is_clz_callback:
            self.__close_track_log_save()
        else:
            self.__cpa_track_log_save()

    @classmethod
    def create_ios_activation(cls, advert_id, session_id, device_info):
        from model.data.definition import CPAActivationRecord
        _advert_id = object_id(advert_id)

        if CPAActivationRecord.count({'advert_id': _advert_id, 'session_id': session_id}) != 0:
            print '--- the activation info is exists:' + advert_id + session_id
            return
        else:
            record = CPAActivationRecord()
            record['advert_id'] = _advert_id
            record['session_id'] = session_id
            record['status'] = 0
            record['device_info'] = device_info
            try:
                record.save()
                print '--- save activation info success:' + advert_id + session_id
            except Exception, e:
                print '>> [SAVE ERROR]' + str(e)

    @classmethod
    def save_cpa_activation(cls, record):
        # 保存信息到redis里面
        now = today()
        periodic = now.strftime('%Y%m%d%H')

        hset = 'periodical_log_%s' % periodic
        key = '%s-%s-action' % (record.campaign["_id"], record.publisher["_id"])

        try:
            pipe = redis_conn.pipeline()
            pipe.hincrby(hset, key, 1)
            pipe.execute()

        except Exception, err:
            print(err)

        # 写日志
        CPATrackLogRecord.to_advert_logger(record, now=now, track_type='action')

    @classmethod
    def save_ad_click(cls, advert_id, data):
        # 缓存时间半小时
        AD_CLICK_CACHE_TIME = 30*60
        start_timestamp = safe_int(data['date_creation'], int(time.time()))
        # 记录点击事件
        with mc_pool.reserve() as mc:
            k_for_click = '%s_click_ad_clz' % advert_id
            k_for_pos = '%s_click_ad_pos' % advert_id
            click_position = '%s,%s' % (data['clk_pos_x'], data['clk_pos_y'])
            print '-- advert_id of click has been set: %s', k_for_click
            print '-- position of %s click has been set: %s' % (advert_id, click_position)
            mc.set(k_for_click, start_timestamp, AD_CLICK_CACHE_TIME)
            mc.set(k_for_pos, click_position, AD_CLICK_CACHE_TIME)

    @classmethod
    def has_ad_click(cls, advert_id):
        key_for_click = '%s_click_ad_clz' % advert_id
        key_for_position = '%s_click_ad_pos' % advert_id
        click_time = None
        click_position = None
        with mc_pool.reserve() as mc:
            print '>> the ad_click cache id is: %s' % key_for_click
            data = mc.get(key_for_click)
            pos = mc.get(key_for_position)
            if data:
                click_time = data
                # 清除缓存
                mc.delete(key_for_click)
            if pos:
                click_position = pos
                mc.delete(key_for_position)
            print '>> ad_click has found:', data

        return click_time is not None, click_time, click_position

    @classmethod
    def to_advert_logger(cls, record, *args, **kw):
        now = ('now' in kw and kw['now']) or today()

        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        ip_addr = record.raw.device_info.ip_address
        mac = record.raw.device_info.mac_address
        net = record.raw.device_info.net
        open_udid = record.raw.device_info.openudid
        longitude = record.raw.device_info.longitude
        latitude = record.raw.device_info.latitude
        brand = record.raw.device_info.device_brand
        platform = record.raw.device_info.platform
        sdk_version = record.raw.device_info.sdk_version
        model = record.raw.device_info.model
        imei = record.raw.device_info.imei
        imsi = record.raw.device_info.imsi

        advert_id = ('advert_id' in kw and kw['advert_id']) or record.raw.advert_id
        show_type = ('show_type' in kw and kw['show_type']) or record.show_type
        publisher = ('publisher' in kw and kw['publisher']) or record.publisher["_id"]
        ad_source = ('ad_source' in kw and kw['ad_source']) or record.ad_source
        track_type = ('track_type' in kw and kw['track_type']) or record.track_type["code"]

        logger = logging.getLogger('advertLog')

        logger_template = '>>\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s'
        logger_content = [timestamp, ip_addr, mac, open_udid, longitude, latitude, platform, net, brand, sdk_version, advert_id, show_type, publisher, track_type, ad_source, '', model, imei, imsi]
        if len(args) > 0:
            logger_template += len(args) * '\t%s'
            logger_content += args

        print logger_template
        print logger_content
        logger.info(logger_template % tuple(logger_content))


    # Android 应用需要验证之前执行的步骤
    def __look_before_step(self, track_log_type):
        android_cpa_types = CPATrackLogType.android_types()

        # cpa_type ==> ('name', value)
        # 从第一步开始检查过程，检查到cpa_type[1] == track_log_type 结束
        prev, prev_name = -1, ''
        with mc_pool.reserve() as mc:
            for cpa_type in android_cpa_types:
                if cpa_type[1] == track_log_type:
                    break
                else:
                    prev, prev_name = cpa_type[1], cpa_type[0]

            k = '%s_cpa_step' % self.advert_id
            # 如果是第一个（Download）的话，则不检查直接保存
            if track_log_type != android_cpa_types[0][1]:
                data = mc.get(k)
                if not data:
                    return False, 'cannot found the previos activation steps'
                if data != prev:
                    return False, 'previous step[%s] is not exists' % prev_name

            mc.set(k, track_log_type)

        return True, 'Success'

    # 验证关闭
    def __close_track_log_valid(self):
        exists, click_time, click_pos = CPATrackLogRecord.has_ad_click(self.raw.advert_id)
        if not exists:
            self.reason = 'the track log of [click] is missing'
            return False
        else:
            now = self.raw.date_creation
            # ad_close_time 为时间戳
            self.ad_close_time = str(now - click_time)
            self.ad_click_position = click_pos
            return True

    # CPA 回调验证
    def __cpa_track_log_valid(self):
        track_log_type = self.value
        sdk_platform = self.raw.device_info.platform.lower()

        if sdk_platform == 'android':
            # Android 需要检查之前的步骤
            ok, self.reason = self.__look_before_step(track_log_type)
            return ok
        elif sdk_platform != 'ios':
            # android/ios 以外的平台
            self.reason = 'invalid platform: %s' % sdk_platform
            return False
        else:
            self.reason = 'iOS do not support this activation process'
            return False

    # 落地页广告关闭track log记录
    def __close_track_log_save(self):
        CPATrackLogRecord.to_advert_logger(self, self.ad_close_time, self.ad_click_position)

    # cpa回调track_log记录
    def __cpa_track_log_save(self):
        track_log_type = self.value
        sdk_platform = self.raw.device_info.platform.lower()

        # only support android
        if sdk_platform != 'android':
            return
        # 当前步骤完成了写logger
        CPATrackLogRecord.to_advert_logger(self)

        # 如果完成所有步骤的话，则写redis和logger
        if track_log_type == CPATrackLogType.Try:
            print '>> OK, Android CPA Track Log Success:' + self.advert_id
            CPATrackLogRecord.save_cpa_activation(self)


# ---------------------------------------------------------
# ------------------- CPA Track log END -------------------
# ---------------------------------------------------------


def begin_transaction(source, destination, source_balance, destination_balance):
    transaction = Transaction()
    transaction["source"] = source
    transaction["source_balance"] = source_balance
    transaction["destination"] = destination
    transaction["destination_balance"] = destination_balance
    transaction["state"] = "initial"
    transaction.save()
    return transaction["_id"]


def set_transaction_state(transaction_id, state):
    Transaction.update({"_id": transaction_id}, {"$set": {"state": state}})


def check_threshold(value, threshold):
    if threshold and value > threshold:
        return True
    return False

def get_advert_series_by_user(user):
    return list(AdvertSeries.query(user=object_id(user), removed=False).sort("date_creation", -1))

def transform_advert_series(lst):
    return map(_transform_advert_series, lst)

def _transform_advert_series(s):
    groups = map(lambda x : x['_id'], list(AdvertGroup.query(fields=['_id'], series=s['_id'], removed=False)))
    s['groups'] = groups
    s['group_count'] = len(groups)
    s['advert_count'] = Advert.count({"group": {"$in": bulk_object_id(groups)}, "removed": False})
    return s

def transform_advert_group(lst):
    return map(_transform_advert_group, lst)

def _transform_advert_group(g):
    g['advert_count'] = Advert.count(group=g['_id'], removed=False)
    g['group_order'] = Property.advert_group_orders_by__id().get(str(g['group_order']),{})
    return g

def prepare_advert_total_info(user_id):
    user = User.get_one(user_id)
    cursor = Advert.query(user=user['_id'], removed=False)
    total = cursor.count()
    __ = object_id(Property.campaign_statuses_by_code_to__id()["running"])
    running = Advert.count(user=user['_id'], status=__, removed=False)
    return dict(total_advertiser_counts=total,
        total_running_advertiser_counts=running,
        total_stop_advertiser_counts=(total - running),
        # @deprecated  Rework financing and balance
        advertiser_balance=user["balance"],
        )


#adverts = {}

@cache.region('in_memory')
def get_advert(id):

    advert = Advert.get_one(_id=object_id(id))
    return advert


@cache.region('in_memory')
def get_app(id):

    app = App.get_one(_id=object_id(id))
    return app

#---------------------------------
#   积分墙广告
#---------------------------------
from model.data.definition import OfferWallAdvert

# 获取积分墙相关设置（预留利润，利率）
@cache.region('offer_wall_memcached')
def get_offerwall_setting(code):
    commons = CommonSetting.get_one({'code': code})
    if commons:
        return commons['value']
    else:
        return None

# 清除设置里面的某项数据的缓存
def reset_offerwall_setting_cache(code):
    cache.region_invalidate(get_offerwall_setting, 'offer_wall_memcached', code)


# 设置积分墙广告的状态
def set_offerwall_status(offerwall, status_code, reject_reason=""):
    statuses = Property.campaign_statuses_by_code_to__id()
    if status_code not in statuses:
        raise ValueError("Invalid status code `%s`." % status_code)
    d = {"$set": {"status": object_id(statuses[status_code])}}
    if status_code == "rejected":
        if not reject_reason:
            raise ValueError("You should give a reason when set rejected to a advert.")
        msg = VerificationMessage()
        msg["content"] = reject_reason
        msg.save()

        # TODO: 是否需要？
        # d["$push"] = {"verification_message": msg["_id"]}
    OfferWallAdvert.update({"_id": object_id(offerwall["_id"])}, d)


# 獲取积分用戶列表，并且带上相关的积分余额信息
#---------------------------------------------------
def prepare_offerwall_user_manage(cursor):
    if not cursor:
        return None
    datalist = list(cursor)
    id_list = []
    for item in datalist:
        id_list.append(item['_id'])

    reduce_function = """
        function reduce_to(cur, obj) {
            obj.remain_score += cur.score;
        }
    """

    score_list = OfferWallCenter.group(
        key=['user_id'],
        condition={'user_id': {'$in': id_list}},
        initial={'remain_score': 0},
        reduce=reduce_function
    )
    if not score_list:
        for data in datalist:
            data['remain_score'] = 0
        return datalist

    score_dict = dict(zip([x['user_id'] for x in score_list], [x['remain_score'] for x in score_list]))

    for data in datalist:
        if data['_id'] in score_dict:
            data['remain_score'] = score_dict[data['_id']]
        else:
            data['remain_score'] = 0

    return datalist

# 获取积分用户管理的单个用户的任务详情
#---------------------------------------------------
def prepare_offerwall_one_user_tasklist(cursor):
    tasks = list(cursor)
    task_log_state = Property.task_log_state_by_value_to_code()
    id_list = [x['advert_id'] for x in tasks]

    ad_list = OfferWallAdvert.query({'_id': {'$in': id_list}})
    if not ad_list:
        return tasks

    ad_list = dict(map(lambda x: (x['_id'], x), ad_list))
    for t in tasks:
        t['name'] = ad_list[t['advert_id']]['name']
        t['state_name'] = task_log_state[t['state']]
    return tasks


# 获取积分用户管理的单个用户信息及其余额统计
#---------------------------------------------------
def prepare_offerwall_one_user_view(one):
    if not one:
        return None

    reduce_function = """
        function reduce_to(cur, obj) {
            obj.remain_score += cur.score;
        }
    """

    score_result = OfferWallCenter.group(
        key=['user_id'],
        condition={'user_id': object_id(one['_id'])},
        initial={'remain_score': 0},
        reduce=reduce_function
    )

    output = {}
    output.update(one)
    output['remain_score'] = (score_result and float(score_result[0]['remain_score'])) or 0

    return output


# 整理积分墙管理页面的一些常用缓存
def prepare_offerwall_manage_status():
    status = Property.campaign_statuses_by__id()
    budgetType = Property.budget_types_by__id_to_name()
    platformType = Property.platforms_by__id_to_name()
    appTypes = Property.offer_apptypes(raw=True)
    return status, budgetType, platformType, appTypes

# 整理积分墙审核界面的一些输出数据
def prepare_offerwall_verified(cursor, accountingModule):
    ad_list = list(cursor)
    ad_status_refer = Property.campaign_statuses_by__id_to_name()
    ad_platform_refer = Property.platforms_by__id_to_name()
    ad_budget_refer = Property.budget_types_by__id_to_name()

    for ad in ad_list:
        d_start, d_end = ad['start_date'], ad['end_date']
        ad['status_name'] = ad_status_refer[str(ad['status'])]
        ad['start_date'] = to_timezone(as_timezone(d_start, 'UTC'), 'Asia/Shanghai').date()
        ad['end_date'] = to_timezone(as_timezone(d_end, 'UTC'), 'Asia/Shanghai').date()
        ad['budget_name'] = ad_budget_refer[str(ad['budget'])]
        ad['platform_name'] = ad_platform_refer[str(ad['platform'])]

        u = accountingModule.transform_user(accountingModule.get_user(ad["user_id"]))
        ad['user_name'] = u['full_name']

    return ad_list

def prepare_offerwall_addedit_form(data_input=None, obj_id=None):
    data_input = data_input or {}
    data_input['app_types'] = Property.offer_apptypes(raw=True)
    data_input['budget_types'] = Property.budget_types(raw=True)
    data_input['budget_value'] = 0    # defaults to 0
    data_input['all_platform'] = Property.platforms(raw=True)
    data_input['car_net_list'] = []
    data_input['advert_tag_obj'] = None
    profit = get_offerwall_setting('offerwall_exchange_profit')
    if profit:
        data_input['profit'] = profit

    if obj_id:
        forms = OfferWallAdvert.get_one(obj_id)
        if not forms:
            data_input['has_ad'] = False
            return data_input
        else:
            data_input['has_ad'] = True


            # 应用图标
            icon_url = forms['icon']
            if icon_url:
                offerwall_url = config.get('api.offerwall_icon_url')
                forms['icon'] = offerwall_url + icon_url

            # android的apk
            apk_url = forms['app_apk_url']
            if apk_url and apk_url.find('//') < 0:
                # 如果已经是一个url，则直接输出，否则拼接输出
                offerwall_apk_url = config.get('api.offerwall_apk_url')
                forms['app_apk_url'] = offerwall_apk_url + apk_url

            # android的截图
            apk_screenshots = None
            _screenshots = forms['app_apk_screenshot']
            if _screenshots:
                apk_screenshots = []
                for scr in _screenshots:
                    apk_screenshots.append(config.get('api.offerwall_apk_screenshot_url') + scr)
                forms['app_apk_screenshot'] = apk_screenshots

            forms['task_steps'] = json.dumps(forms['task_steps'])
            d_start, d_end = forms['start_date'], forms['end_date']
            forms['start_date'] = to_timezone(as_timezone(d_start, 'UTC'), 'Asia/Shanghai').date()
            forms['end_date'] = to_timezone(as_timezone(d_end, 'UTC'), 'Asia/Shanghai').date()
            data_input['advert_tag_obj'] = Property.advert_tags_by__id(str(forms['tag']))

            data_input.update(forms)
            data_input['budget_value'] = Property.budget_types_by__id_to_value(str(forms['budget']))
            data_input['real_price'] = (profit and (1-profit) * forms['price']) or forms['price']

            car_net_all = Property.carrier_network_type_by__id()
            data_input['car_net_list'] = [car_net_all.get(str(i))
                                           for i in forms.get('carrier_network', [])]

            data_input['ad_channel'] = forms['channel']

        return data_input


def transform_formdata_offerwall(params, files, user, objid=None):
    forms = {}
    forms.update(params)
    budget_effect = 0
    if int(forms['ad_budget_type']) == 1:
        budget_effect = safe_int(forms['ad_effect_day'])
    elif int(forms['ad_budget_type']) == 2:
        budget_effect = safe_int(forms['ad_effect_total'])

    # 获取缓存里面的应用类型列表
    app_type_cache = Property.offer_apptypes_by__id()

    # 获取解释任务详情
    if 'ad_taskdetail' in forms:
        if forms['ad_taskdetail'] == '':
            detail_steps = []
        else:
            detail_steps = json.loads(forms['ad_taskdetail'])
    else:
        detail_steps = []

    # 检查这个是否一条Android的积分广告
    platform_cache = Property.platforms_by_name_to__id()
    is_android = False
    android_forms = {}

    if object_id(platform_cache['Android']) == object_id(forms['ad_platform']):
        is_android = True
        apk_post_type = (forms['ad_apk'] and safe_int(forms['ad_apk'])) or 0
        # 处理应用上传
        apk = files.get('ad_apk_upload')
        if apk_post_type == 0 and apk:
            uri_apk = save_android_package(apk.file, apk.filename)
            android_forms['app_apk_url'] = uri_apk
            # 通过file获取应用名
            android_forms['app_apk_filename'] = apk.filename
        else:
            apk_url = forms['ad_apk_uri'] or ''
            prefix = config.get('api.offerwall_apk_url')
            # 如果url是当前配置的前缀，则不修改,反之则修改
            if not apk_url.startswith(prefix):
                android_forms['app_apk_url'] = apk_url
            # 如果选择的是网址，则通过文本框显示
            android_forms['app_apk_filename'] = forms['ad_apk_filename']

        android_forms['app_apk_size'] = forms['ad_apk_size'] and safe_float(forms['ad_apk_size'], 0.0)
        android_forms['app_apk_ver'] = forms['ad_apk_version'] or ''
        android_forms['app_apk_pkgname'] = forms['ad_apk_pkgname']

        # Android平台可能会需要计时器，判断
        if 'ad_apk_use_timeout' in forms and safe_int(forms['ad_apk_use_timeout'], 0) == 1:
            if 'ad_apk_timeout' in forms and safe_int(forms['ad_apk_timeout'], -1) > 0:
                # 时间数值正确则保存为以毫秒为准的数值
                android_forms['app_apk_timeout'] = safe_int(forms['ad_apk_timeout']) * 60 * 1000
            else:
                android_forms['app_apk_timeout'] = -1
        else:
            android_forms['app_apk_timeout'] = -1

        # TODO:截图删除的处理
        upload_screens = files.getall('screens[]')
        if upload_screens:
            screenshots = map(lambda x: save_offerwall_apk_screenshot(x.file), upload_screens)
            android_forms['app_apk_screenshot'] = screenshots
        elif not objid:
            # 如果没有上传图片，并且没有objid，则给一个空的数组，如果有objectid但是没有上传则不处理
            android_forms['app_apk_screenshot'] = []

    # 修正日期，如果结束时间小于等于开始时间，则修改为开始时间的下一天(主要防止恶意提交）
    start_date = datetime.strptime(forms['ad_startat'].strip(), '%Y-%m-%d')
    end_date = datetime.strptime(forms['ad_endat'].strip(), '%Y-%m-%d')
    if end_date <= start_date:
        end_date = start_date + timedelta(days=1)

    # 创建插入的数据
    offer_wall = {
        'platform': object_id(forms['ad_platform']),
        'name': forms['ad_name'],
        'word': forms['ad_text'],
        'task_name': forms['ad_tasksummary'],
        'task_steps': detail_steps,
        'budget': object_id(forms['ad_budget']),
        'budget_effect': budget_effect,
        'channel': int(forms['ad_channel']),
        'is_api': int(forms['ad_isapi']),
        'price': safe_float(forms['ad_price']),
        'start_date':  start_date,
        'end_date': end_date,
        # app infomation
        'app_name': forms['ad_appname'],
        'app_market_url': forms['ad_market'],
        'app_type': object_id(forms['ad_apptype']),
        'app_activation_url': forms['ad_callbackurl'],
        'app_info': forms['ad_appdesc'],
        'app_author': forms['ad_appauthor']
    }

    # 只有创建的广告才会有user_id
    if user:
        offer_wall['user_id'] = user

    # 设置应用的主类型（应用or游戏）
    _app_type_id = forms['ad_apptype']
    offer_wall['app_main_type'] = app_type_cache[_app_type_id]['subject_type']

    #广告标签
    offer_wall['tag'] = object_id(Property.advert_tags_by_value_to__id(int(params.get('advert_tag'))))
    # 处理时区问题
    offer_wall['start_date'] = to_timezone(offer_wall['start_date'], "Asia/Shanghai")
    offer_wall['end_date'] = to_timezone(offer_wall['end_date'], "Asia/Shanghai")

    # 如果是android类型，则先插入相关的数据
    if is_android:
        offer_wall.update(android_forms)

    # 处理icon的上传
    icon = files.get('ad_icon')
    if icon:
        offer_wall['icon'] = save_offerwall_icon(icon.file)

    # 上网方式
    net_work_types = params.getall('car_nets')
    if not net_work_types:
        offer_wall['carrier_network'] = [object_id(Property.carrier_network_type_by_value_to__id(CarrierNetworkType.all_all))]
    else:
        offer_wall['carrier_network'] = [object_id(Property.carrier_network_type_by_value_to__id(int(i)))
                                         for i in net_work_types]

    ad = None
    if objid:
        ad = OfferWallAdvert().get_one(objid)
        if not ad:
            return None
    else:
        if not user:
            return 'user id not exists'
        ad = OfferWallAdvert()
        # 新建广告默认为未审核
        ad_status = Property.campaign_statuses_by_value_to__id()
        ad['status'] = object_id(ad_status[2])  # 2 for 审核中

    # for k in offer_wall.keys():
    #     ad[k] = offer_wall[k]
    ad.dict_update(offer_wall)

    return ad


#------------------------------------------------------
#   Testin 相关
#------------------------------------------------------

#-------------- 构建 sig 参数 ----------------

def __sort_the_inner_array(arr):
    wrapper = '{%s}'
    content = ''
    for e in arr:
        if type(e) is int or type(e) is float:
            content += str(e)
        elif type(e) is str or type(e) is unicode:
            content += '"%s"' % e
        elif type(e) is tuple or type(e) is list:
            content += __sort_the_inner_array(e)
        elif type(e) is dict:
            content += __sort_the_inner_dict(e)
        else:
            continue
        content += ','
    return wrapper % content[:len(content)-1]


def __sort_the_inner_dict(d):
    wrapper ='{%s}'
    content = ''
    items = d.items()
    items.sort(key=lambda x: x[0])
    for it in items:
        k = '"%s"' % it[0]
        v = it[1]
        if type(v) is int or type(v) is float:
            v = str(v)
        elif type(v) is str or type(v) is unicode:
            v = '"%s"' % v
        elif type(v) is list or type(v) is tuple:
            v = __sort_the_inner_array(v)
        elif type(v) is dict:
            v = __sort_the_inner_dict(v)
        else:
            continue
        content += '%s:%s,' % (k, v)

    return wrapper % content[:len(content)-1]


def prepare_testin_sig(d, SECRET):
    items = d.items()
    items.sort(key=lambda x: x[0])
    rs = ''
    for it in items:
        if type(it[1]) is list or type(it[1]) is tuple:
            rs += u'%s=%s' % (it[0], __sort_the_inner_array(it[1]))
        elif type(it[1]) is dict:
            rs += u'%s=%s' % (it[0], __sort_the_inner_dict(it[1]))
        elif type(it[1]) is int or type(it[1]) is float:
            rs += u'%s=%s' % (it[0], str(it[1]))
        else:
            if type(it[1]) == str:
                rs += u'%s=%s' % (it[0], it[1].decode('utf8'))
            elif type(it[1]) == unicode:
                rs += u'%s=%s' % (it[0], it[1])

    rs += SECRET
    return hashlib.md5(rs.encode('utf8')).hexdigest()

#--------------  构建 sig end ------------------

from base import app_analyze

def transform_formdata_testin_upload(files):
    app_file = files.get('app_file')
    app_filename = app_file.filename.lower()

    surfix = app_filename.split('.')[-1]
    if surfix not in ('apk', 'ipa'):
        return {'ok': False, 'msg': u'不支持应用格式'}

    icon_dir = config.get('env.testin_logo_path')
    app_name, app_localpath = save_testin_app(app_file.file, surfix)

    if surfix == 'apk':
        ok, info = app_analyze.parse_app_package(app_localpath, 'android', icon_dir)
    else:
        ok, info = app_analyze.parse_app_package(app_localpath, 'ios', icon_dir)

    if ok:
        info['app_file'] = app_name
        return {'ok': True, 'data': info}
    else:
        # 解析失败需要删除应用包
        import os
        os.remove(app_localpath)
        return {'ok': False, 'msg': u'无法解析应用包'}
