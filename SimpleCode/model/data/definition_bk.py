# coding=UTF-8


# from mongokit import Document, CustomType
from mongokit import *
from bson.objectid import InvalidId

import datetime

from base import config

from base.backend.model import datamanager

MongoDB_Default_Database = config.get('mongodb.database')

#try:
#    from apps.data_layer.settings import MongoDB_Default_Database
#except Exception, e:
#    from settings import MongoDB_Default_Database


def object_id(obj_id):
    if type(obj_id) is ObjectId:
        return obj_id
    try:
        return ObjectId(obj_id)
    except InvalidId:
        return None


class ModelBase(Document):
    __database__ = MongoDB_Default_Database
    __collection__ = ''
    __manager__ = ''
    # use_autorefs = True

    structure = {
        'removed': bool,
        'date_creation': datetime.datetime,
    }

    default_values = {
        'removed': False,
        #'date_creation': datetime.datetime.utcnow(),
    }

    indexes = [
        {
            'fields':['removed', 'date_creation']
        }
    ]

    def set_removed(self):
        self['removed'] = True

    def save(self, *args, **kwargs):
        if self.get('date_creation') is None:
            self['date_creation'] = datetime.datetime.utcnow()
        return Document.save(self, *args, **kwargs)

    @property
    def manager(self):
        # print(self.__manager__)
        return self.__manager__

    def __init__(self, doc=None, gen_skel=True, collection=None, lang='en', fallback_lang='en'):
        if collection is None:
            collection = datamanager.connection_global[self.__database__][self.__collection__]
        super(ModelBase, self).__init__(doc, gen_skel, collection, lang, fallback_lang)
        self._obj_class = self.__class__

    def upsert(self, fields=None, uuid=False, validate=None, safe=True, *args, **kwargs):
        if not isinstance(fields, (tuple, list)):
            raise ValueError("Argument `fields` should be tuple or list.")
        query = dict(((k, self.get(k)) for k in fields))
        if validate is True or (validate is None and self.skip_validation is False):
            self.validate(auto_migrate=False)
        else:
            if self.use_autorefs:
                self._make_reference(self, self.structure)
        if '_id' not in self:
            if uuid:
                self['_id'] = unicode("%s-%s" % (self.__class__.__name__, uuid4()))
        self._process_custom_type('bson', self, self.structure)
        self.collection.update(query, self, upsert=True, safe=safe, *args, **kwargs)
        self._process_custom_type('python', self, self.structure)

    def insertIfNotExists(self, fields):
        if not isinstance(fields, (tuple, list)):
            raise ValueError("Argument `fields` should be tuple or list.")
        query = dict(((k, self.get(k)) for k in fields))
        if self.find(query).count() == 0:
            self.save()
            return True

    @classmethod
    def update(cls, *args, **kwargs):
        return cls().collection.update(*args, **kwargs)

    @classmethod
    def query(cls, query=None, fields=None, cursor=True, **kwargs):
        if query is None:
            query = kwargs
        elif not isinstance(query, dict):
            query = {"_id": object_id(query)}
        if not cursor:
            return query
        return cls().find(query, fields=fields)

    @classmethod
    def get_id(cls, query=None, **kwargs):
        """ Retrieve first document match query, than return `_id`.
        """
        cursor = cls.query(query, fields={"_id": 1}, **kwargs)
        if cursor.count() == 1:
            return cursor.next()["_id"]
        raise ValueError("Invalid query: %s" % query)

    @classmethod
    def get_one(cls, query=None, **kwargs):
        cursor = cls.query(query, **kwargs)
        if cursor.count() > 0:
            return cursor.next()
        return None

    @classmethod
    def count(cls, query=None, **kwargs):
        cursor = cls.query(query, **kwargs)
        return cursor.count()

    @classmethod
    def exists(cls, query=None, **kwargs):
        return cls.count(query, **kwargs) > 0

    @classmethod
    def set_removed(cls, query=None, **kwargs):
        return cls().collection.update(cls.query(query, cursor=False, **kwargs),
                                       {"$set": {"removed": True}}, multi=True)

    @classmethod
    def remove(cls, query=None, **kwargs):
        return cls().collection.remove(cls.query(query, cursor=False, **kwargs))

    def __getstate__(self):
        return dict(self)

class ModelTypeBase(ModelBase):
    __collection__ = ''

    structure = {
        'name': basestring,
        'code': basestring,
        'value': int
    }

    required_fields = ['name', 'value', 'code']


class Property(ModelBase):
    """ DO NOT USE DIRECTLY, SUBCLASS FIRST!!
    """
    structure = {
        "code": basestring,
        "name": basestring,
        "value": int,
    }
    required_fields = ['name', 'value', 'code']

    @classmethod
    def import_fixture(cls):
        j, items = 0, []
        for i in cls.fixtures:
            rec = cls()
            rec["value"] = j
            rec["code"], rec["name"] = i
            j += 1
            items.append(rec)
        cls().collection.insert(items)


class PropertyGender(Property):
    __collection__ = 'property_genders'
    __manager__ = 'ManagerFinanceLogSource'
    fixtures = (
        ("unlimited", u"不限性别"),
        ("male", u"男性为主"),
        ("female", u"女性为主"),
    )


class PropertyAge(Property):
    __collection__ = 'property_ages'
    __manager__ = 'ManagerFinanceLogSource'
    fixtures = (
        ("unlimited", u"不限年龄"),
        ("under_18", u"18岁以下"),
        ("between_18_to_25", u"18-25岁"),
        ("between_25_to_35", u"25-35岁"),
        ("between_35_to_40", u"35-40岁"),
        ("older_40", u"40岁以上"),
    )


class PropertyCareer(Property):
    __collection__ = "property_careers"
    __manager__ = 'ManagerFinanceLogSource'
    fixtures = (
        ("unlimited", u"不限职业"),
        ("students", u"学生"),
        ("government_employees", u"政府/国企人员"),
        ("enterprise_employees", u"私企职员"),
        ("foreign_employees", u"外企职员"),
        ("workers", u"工人"),
        ("attendants", u"服务业人员"),
        ("freelancers", u"自由职业"),
        ("farmers", u"农民工"),
    )


class PropertyTradingArea(ModelBase):
    __collection__ = "property_trading_areas"
    __manager__ = "ManagerPropertyTradingArea"

    structure = {
        "name": basestring,
        "coordinates": [(float, float)],
        "province": basestring,
        "city": basestring,
    }

    required_fields = ["name", "coordinates"]


# USER_TYPE = [u'developer', u'advertiser']
# USER_STATUS = [u'pending', u'not verified', u'verifying', u'verified']


class FinanceLogSource(ModelTypeBase):
    __collection__ = 'finance_log_source'
    __manager__ = 'ManagerFinanceLogSource'

class FinanceLogStatus(ModelTypeBase):
    __collection__ = 'finance_log_status'
    __manager__ = 'ManagerFinanceLogStatus'

class FinanceLogOperation(ModelTypeBase):
    __collection__ = 'finance_log_operation'
    __manager__ = 'ManagerFinanceLogOperation'

class FinanceLog(ModelBase):
    __collection__ = 'finance_log'
    __manager__ = 'ManagerFinanceLog'

    structure = {
        'title': basestring,
        'amount': float,

        'source': FinanceLogSource,
        'status': FinanceLogStatus,
        'operation': FinanceLogOperation
    }




class VerificationMessage(ModelBase):
    __collection__ = 'verification_message'
    __manager__ = 'ManagerVerificationMessage'

    structure = {
        'content': basestring,
    }





class UserVerificationType(ModelTypeBase):
    __collection__ = 'user_verification_type'
    __manager__ = 'ManagerUserVerificationType'

class UserVerification(ModelBase):
    __collection__ = 'user_verification'
    __manager__ = 'ManagerUserVerification'

    structure = {
        'bank_account': basestring,
        'bank_name': basestring,

        'company_name': basestring,
        'company_license_image': basestring,

        'personal_id_number': basestring,
        'personal_name': basestring,
        'personal_id_front_image': basestring,
        'personal_id_back_image': basestring,

        'verification_type': UserVerificationType,
    }


class UserStatus(ModelTypeBase):
    __collection__ = 'user_status'
    __manager__ = 'ManagerUserStatus'

class UserType(ModelTypeBase):
    __collection__ = 'user_type'
    __manager__ = 'ManagerUserType'


class UserProfile(ModelBase):
    __collection__ = 'user_profile'
    __manager__ = 'ManagerUserProfile'

    structure = {
        'contact_name': basestring,
        'contact_phone': basestring,
        'contact_address': basestring,
        'qq_number': basestring,
        'province': basestring,
        'city': basestring,
        'company_name': basestring,
    }


class Transaction(ModelBase):
    __collection__ = "transation"
    __manager__ = "ManagerTransation"

    structure = {
        "source": ObjectId,
        "source_balance": float,
        "destination": ObjectId,
        "destination_balance": float,
        "state": basestring
    }


class User(ModelBase):
    __collection__ = 'user'
    __manager__ = 'ManagerUser'

    structure = {
        'full_name': basestring,
        'phone': basestring,
        'email': basestring,
        'password': basestring,

        'type': UserType,
        'status': UserStatus,

        'verification': UserVerification,
        'profile': UserProfile,
        'finance_log': [FinanceLog],
        'balance': float,

        'verification_message': [VerificationMessage],

        'notify_daily_balance': float,
        'notify_total_balance': float,

        'pending_transactions': [Transaction],

        'managed_by': basestring,
    }

    required_fields = ['email', 'password']

    default_values = {
        'balance': 0.0,
        'notify_daily_balance': 0.0,
        'notify_total_balance': 0.0,
    }


class Company(ModelBase):
    __collection__ = 'company'
    __manager__ = 'ManagerCompany'

    structure = {
        'name': basestring,
        'address': [basestring],
        'phone_number': [basestring]
    }


# APP_STATUS = [u'running', u'paused', u'verifying', u'stopped', u'ended']
# APP_PLATFORM = [u'ios', u'android']

class AppStatus(ModelTypeBase):
    __collection__ = 'app_status'
    __manager__ = 'ManagerAppStatus'



class AppSetting(ModelBase):
    __collection__ = 'app_setting'
    __manager__ = 'ManagerAppStatus'

    structure = {

    }


class Category(ModelTypeBase):
    __collection__ = 'category'
    __manager__ = 'ManagerCategory'


class MediaType(ModelTypeBase):
    __collection__ = 'media_type'
    __manager__ = 'ManagerMediaType'


class TimeRange(ModelTypeBase):
    __collection__ = 'time_range'
    __manager__ = 'ManagerTimeRange'


class Platform(ModelTypeBase):
    __collection__ = 'platform'
    __manager__ = 'ManagerPlatform'


# LOG_TYPE = ['ios', 'android']


class AdvertType(ModelBase):
    # 广告条 插屏广告 浮层广告

    __collection__ = 'advert_type'
    __manager__ = 'ManagerAdvertType'

    structure = {
        'name': basestring,
    }

    required_fields = ['name']


class PaymentType(ModelTypeBase):
    # CPC CPM 激活

    __collection__ = 'payment_type'
    __manager__ = 'ManagerPaymentType'

    structure = {
        'description': basestring,
    }


class BudgetType(ModelTypeBase):
    # ‘每天限额 总额 无预算

    __collection__ = 'budget_type'
    __manager__ = 'ManagerBudgetType'

    structure = {
        'description': basestring,
    }


class Budget(ModelBase):
    __collection__ = 'budget'
    __manager__ = 'ManagerBudget'

    structure = {
        'amount': float,
        'type': BudgetType
    }

    required_fields = ['amount', 'type']


class HourlySlice(ModelBase):
    __collection__ = 'hourly_slice'
    __manager__ = 'ManagerHourlySlice'

    structure = {
        'start': datetime.datetime,
        'end': datetime.datetime
    }

    required_fields = ['start', 'end']


class Region(ModelBase):
    __collection__ = 'region'
    __manager__ = 'ManagerRegion'

    structure = {
        'country': basestring,
        'province': basestring,
        'city': basestring,
        'district': basestring,
    }

    required_fields = ['country']

    default_values = {
        'country': '中国'
    }

class RegionLaunch(ModelBase):
    __collection__ = 'region_launch'
    __manager__ = 'ManagerRegionLaunch'

    structure = {
        'name': basestring,
        'value': int
    }

    required_fields = ['name', 'value']


class DeviceBrand(ModelBase):
    __collection__ = 'device_brand'
    __manager__ = 'ManagerDeviceBrand'

    structure = {
        'name' : basestring
    }

    required_fields = ['name']


class Language(ModelBase):
    __collection__ = 'language'
    __manager__ = 'ManagerLanguage'

    structure = {
        'name' : basestring
    }

    required_fields = ['name']


# ADVERT_STATUS = [u'running', u'paused', u'verifying', u'stopped', u'ended']

class AdvertStatus(ModelTypeBase):
    __collection__ = 'advert_status'
    __manager__ = 'ManagerAdvertStatus'

    fixtures = (
        ("paused", u"暂停"),
        ("not verified", u"未审核"),
        ("verifying", u"审核中"),
        ("verified", u"通过审核"),
        ("rejected", u"未通过审核"),
        ("running", u"运行中"),
        ("ended", u"结束"),
    )

    @classmethod
    def import_fixture(cls):
        items = []
        for i, j in enumerate(cls.fixtures):
            code, name = j
            rec = cls()
            rec["code"] = code
            rec["name"] = name
            rec["value"] = i
            rec.upsert(("name", ))

class ApplicationLanguage(ModelTypeBase):
    __collection__ = 'application_language'
    __manager__ = 'ManagerApplicationLanguage'

class ApplicationType(ModelTypeBase):
    __collection__ = 'application_type'
    __manager__ = 'ManagerApplicationType'

class BrandMobile(ModelTypeBase):
    __collection__ = 'brand_mobile'
    __manager__ = 'ManagerBrandMobile'

    structure = {
        'name': basestring,
        'code': basestring,
        'value': int,
        'english_name': basestring,
    }

    fixtures = (
        ("全部", "all", "all"),
        ("索尼爱立信", "Sony", "Sony"),
        ("摩托罗拉", "Motorola", "motorola"),
        ("三星", "Samsung", "samsung"),
        ("LG", "LG", "lge"),
        ("夏普", "Sharp", "sharp"),
        ("联想", "Lenovo", "Lenovo"),
        ("魅族", "Meizi", "Meizu"),
        ("小米", "Xiaomi", "Xiaomi"),
        ("天语", "Tianyu", "K-TOUCH"),
        ("OPPO", "OPPO", "OPPO"),
        ("酷派", "Coolpad", "Coolpad"),
        ("华为", "Huawei", "Huawei"),
        ("HTC", "HTC", "HTC"),
        ("宏碁", "Acer", "Acer"),
        ("中兴", "ZTE", "ZTE"),
        ("步步高", "vivo", "vivo"),
        ("苹果", "Apple", "apple"),
        ("其他", "other", "other"),
    )

    @classmethod
    def import_fixture(cls):
        items = []
        for i, j in enumerate(cls.fixtures):
            cname, ename, code = j
            rec = cls()
            rec["code"] = code
            rec["name"] = cname
            rec["english_name"] = ename
            if ename == "other":
                i = 9999
            rec["value"] = i
            rec.upsert(("name", ))

# 出现方式
class DisplayManner(ModelTypeBase):
    __collection__ = 'display_manner'
    __manager__ = 'ManagerDisplayManner'

# 广告创意
class AdvertIdea(ModelTypeBase):
    __collection__ = 'advert_idea'
    __manager__ = 'ManagerAdvertIdea'

# 上网方式
class NetworkType(ModelTypeBase):
    __collection__ = 'network_type'


# 投放日
class Weekday(ModelTypeBase):
    __collection__ = 'weekday'


class Carrier(ModelTypeBase):
    __collection__ = 'carrier'
    __manager__ = 'ManagerCarrier'

class ShowType(ModelTypeBase):
    __collection__ = 'show_type'
    __manager__ = 'ManagerShowType'

class AdvertContent(ModelBase):
    __collection__ = 'advert_content'
    __manager__ = 'ManagerAdvertContent'

    structure = {
        'word': basestring,
        'images': [basestring],
        'show_type': ShowType,
        'new_word': dict,
        'new_images': [dict],
        'zip': basestring,
        'url': basestring
    }


class AdvertLevel(ModelBase):
    __collection__ = 'advert_level'
    __manager__ = 'ManagerAdvertLevel'

    structure = {
        'name': basestring,
        'code': basestring,
        'developer': float,
        'platform': float,
        'total': float,
        'payment_type_code': basestring
    }

    fixtures = (
        # code / 初始化名称, 开发者分成，平台分成，最低出价
        ("CPM-A", 1.1, 2.5, 3.6),
        ("CPM-B", 0.7, 2.0, 2.7),
        ("CPM-C", 0.5, 1.3, 1.8),
        ("CPM-D", 0.3, 0.6, 0.9),
        ("CPM-E", 0.15, 0.35, 0.5),
        ("CPC-A", 1.1, 2.5, 3.6),
        ("CPC-B", 0.7, 2.0, 2.7),
        ("CPC-C", 0.5, 1.3, 1.8),
        ("CPC-D", 0.3, 0.6, 0.9),
        ("CPC-E", 0.15, 0.35, 0.5),
        ("CPA-A", 1.1, 2.5, 3.6),
        ("CPA-B", 0.7, 2.0, 2.7),
        ("CPA-C", 0.5, 1.3, 1.8),
        ("CPA-D", 0.3, 0.6, 0.9),
        ("CPA-E", 0.15, 0.35, 0.5),
    )

    @classmethod
    def import_fixture(cls, upsert=False):
        items = []
        for i in cls.fixtures:
            code, developer_share, platform_share, cost = i
            rec = cls()
            rec["code"] = rec["name"] = code
            rec["developer"] = developer_share
            rec["platform"] = platform_share
            rec["total"] = cost
            rec["payment_type_code"] = code.split("-")[0].lower()
            if upsert:
                rec.upsert(("name", ))
            else:
                items.append(rec)
        if items:
            cls().collection.insert(items)


class AdvertLevelLog(ModelBase):
    __collection__ = 'advert_level_log'
    __manager__ = 'ManagerAdvertLevel'

    structure = {
        'name': basestring,
        'developer': float,
        'platform': float,
        'variable': float,
        'total': float,
        'code': basestring,
        'payment_type': PaymentType,
        'date_start': datetime.datetime
    }


class IPDatabase(ModelBase):
    __collection__ = 'ip_database'
    __manager__ = 'ManagerIPDatabase'

    structure = {
        'value': int,
        'ip_start': int,
        'ip_end': int,
        'country': basestring,
        'province': basestring,
        'city': basestring,
        'district': basestring,
        'carrier': basestring,
        'zip_code': int
    }

class RegionDatabase(ModelBase):
    __collection__ = 'region_database'
    __manager__ = 'ManagerRegionDatabase'

    structure = {
        'value': int,
        'country': basestring,
        'province': basestring,
        'city': basestring,
    }

# add in 2014/2/27
class ClickAction(ModelTypeBase):
    __collection__ = 'click_action'
    __manager__ = 'ManagerClickAction'



class Advert(ModelBase):
    __collection__ = 'advert'
    __manager__ = 'ManagerAdvert'

    structure = {
        'name': basestring,
        'description': basestring,
        'show_type': ShowType,

        'category': Category,

        'app_categories': [Category],

        'platform': [Platform],
        #'media_type': [MediaType],

        'date_start': datetime.datetime,
        'date_end': datetime.datetime,
        'date_verifier': datetime.datetime,
        # 'date_start': basestring,
        # 'date_end': basestring,

        'status': AdvertStatus,

        'budget': Budget,
        'time_range': [TimeRange],
        #'region_launch': [RegionLaunch],
        'region_launch': [RegionDatabase],
        'carrier': [Carrier],
        'brand_mobile': [BrandMobile],
        'app_language': [ApplicationLanguage],
        'app_type': ApplicationType,
        # new targetting properties, added @ 2013-12-19
        'trading_areas': [PropertyTradingArea],
        'gender': PropertyGender,
        'ages': [PropertyAge],
        'careers': [PropertyCareer],

        # 'budget_type': int,
        'premium_price': float,

        'payment_type': PaymentType,

        'redirect_url': basestring,

        'content': AdvertContent,
        'user': User,

        'verification_message': [VerificationMessage],

        # 为点击交互行为增加字段
        'click_action': ClickAction,
        'phone': basestring,
        'message' :basestring,
        'map_address': basestring,

        # 广告组
        'group': ObjectId,
        # 广告ID
        'advert_code': basestring,
        # 上网方式
        'network': [NetworkType],
        # 投放日
        'weekday_launch': [Weekday],
        # 投放频次
        'frequency': None,
        # 摇一摇
        'shake':basestring
    }

    required_fields = ['name', 'date_start', 'status', 'platform', 'user']


class AppUploadInfo(ModelBase):
    __collection__ = 'app_upload_info'
    __manager__ = 'ManagerAppUploadInfo'

    structure = {
        'icon': basestring,
        'capture': [basestring],

        'binary': basestring,

        'market_url': basestring,
        'version': basestring,
        'description': basestring,
    }

    required_fields = ['icon', 'capture', 'binary', 'market_url']


class App(ModelBase):
    __collection__ = 'app'
    __manager__ = 'ManagerApp'

    structure = {
        'name': basestring,
        'api_key': basestring,
        'api_secret': basestring,

        'status': AppStatus,

        'description': basestring,
        'keyword': basestring,
        'platform': Platform,

        'app_language': [ApplicationLanguage],
        'app_type': ApplicationType,

        'category': [Category],
        'setting': AppSetting,

        'date_verifier': datetime.datetime,

        'upload_info': AppUploadInfo,
        'user': User,
        'level_log': [AdvertLevelLog],

        'verification_message': [VerificationMessage],

        "target_gender": PropertyGender,
        "target_ages": [PropertyAge],
        "target_careers": [PropertyCareer],
    }

    required_fields = ['name', 'api_key', 'user']







class TrackLogType(ModelTypeBase):
    __collection__ = 'track_log_type'
    __manager__ = 'ManagerTrackLogType'


class TrackLog(ModelBase):
    __collection__ = 'track_log'
    __manager__ = 'ManagerTrackLog'

    structure = {
        # 'name': basestring,
        'type': TrackLogType,
        'app': App,
        'advert': Advert,
        'level_log': AdvertLevelLog,
        'session_id': basestring,
        'ad_source': basestring,
    }

    required_fields = ['type', 'advert']

    indexes = [
        {
            'fields':['type', 'app', 'advert']
        }
    ]

# 闪拍track log
class ShanPaiTrackLog(TrackLog):
    __collection__ = 'shanpai_track_log'
    __manager__ = 'ManagerShanPaiTrackLog'


class ReportAdvertLog(ModelBase):
    __collection__ = 'report_advert_log'
    __manager__ = 'ManagerReportAdvertLog'

    structure = {
        'date_start': datetime.datetime,
        'date_end': datetime.datetime,
        'advert': Advert,

        'number_request': int,
        'number_show': int,
        'number_click': int,
        'number_action': int,
        'cost_show': float,
        'cost_click': float,
        'cost_action': float,
        'cost_total': float,
    }

    indexes = [
        {'fields': ['date_start', 'date_end']},
        {'fields': ['advert']}
    ]


class PeriodicalAdvertLog(ReportAdvertLog):
    __collection__ = 'periodical_advert_log'


class ReportAppLog(ModelBase):
    __collection__ = 'report_app_log'
    __manager__ = 'ManagerAppReportLog'

    structure = {
        'date_start': datetime.datetime,
        'date_end': datetime.datetime,
        'app': App,

        'number_request': int,
        'number_show': int,
        'number_click': int,
        'number_action': int,
        'cost_show': float,
        'cost_click': float,
        'cost_action': float,
        'cost_total': float,
    }

    indexes = [
        {'fields': ['date_start', 'date_end']},
        {'fields': ['app']},
    ]


class PeriodicalAppLog(ReportAppLog):
    __collection__ = 'periodical_app_log'


class ReportPlatformLog(ModelBase):
    __collection__ = "report_platform_log"
    __manager__ = "ManagerReportPlatformLog"

    structure = {
        'date_start': datetime.datetime,
        'date_end': datetime.datetime,
        'group_name': basestring,

        'requests': int,
        'impressions': int,
        'clicks': int,
        'actions': int,
        'revenue': float,
    }

    indexes = [
        {'fields': ['date_start', 'date_end']},
    ]


class PeriodicalPlatformLog(ReportPlatformLog):
    __collection__ = 'periodical_platform_log'


class BusinessCircle(ModelBase):
    __collection__ = 'business_circle'
    __manager__ = 'ManagerBusinessCircle'

    structure = {
        'name': basestring,
        'coordinate': basestring,
        # 'coordinate': [{
        #     'lat': float,
        #     'lon': float
        # }]
    }

    # indexes = [
    #     {
    #         'coordinate': [('location', '2d'), ],
    #     }
    # ]


class Privilege(ModelBase):
    __collection__ = "privilege"
    __manager__ = "ManagerPrivilege"

    structure = {
        "user_id": basestring,
        "privilege_name": basestring,
        "group_id": basestring,
    }

    required_fields = ["user_id", "privilege_name"]


class Group(ModelBase):
    __collection__ = "group"
    __manager__ = "ManagerGroup"

    structure = {
        "name": basestring,
        "chief": basestring,
        "privileges": [basestring],
        "users": [basestring],
    }

    required_fields = ["name"]


class PasswordReset(ModelBase):
    __collection__ = "password_reset"
    __manager__ = "ManagerPasswordReset"

    structure = {
        "user": User,
        "token": basestring,
        "exhausted": bool,
    }

class AdvertSeries(ModelBase):
    __collection__ = 'advert_series'

    structure = {
        "user": ObjectId,
        "series_name": basestring,
        "series_code": basestring,
    }

class AdvertGroup(ModelBase):
    __collection__ = 'advert_group'

    structure = {
        "user": ObjectId,
        "group_name": basestring,
        "group_code": basestring,
        "series": ObjectId,
    }

class SerialNum(ModelBase):
    '''
    用于生成序列号
    '''
    __collection__ = 'serial_num'

    structure = {
        "type": basestring,
        "current_pos": long,
    }

    @classmethod
    def get_next_number(cls, type, try_times=5):
        serial_num = cls()
        next_num = None
        criteria = dict(type=type)
        for i in range(0, try_times):
            s = serial_num.find_one(criteria)
            if s is not None:
                query = dict(criteria)
                current_pos = s.get('current_pos', 0)
                query['current_pos'] = current_pos
                current_pos = current_pos + 1
                d = serial_num.find_and_modify(query, {'$set': {'current_pos': current_pos}})
                if d is not None:
                    next_num = current_pos
                else:
                    continue
            else:
                next_num = 1l
                serial_num.collection.insert({'current_pos': next_num, 'type': type})

            break

        if next_num is None:
            raise ValueError('Cannot get the next sequence')

        return next_num
