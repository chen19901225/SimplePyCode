# coding=UTF-8


# from mongokit import Document, CustomType

import collections
import datetime
from mongokit import *

from bson.objectid import InvalidId
import bson
from beaker.cache import cache_regions

from base.utils import parse, smart_region_invalidate
from base import config
from base.backend.model import datamanager
from apps.outlet_layer.settings import cache

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
    def group(cls, *args, **kwargs):
        print args, kwargs
        return cls().collection.group(*args, **kwargs)

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

    #--------整合--------
    def to_dict(self):
       return dict(self)

    def __getitem__(self, item):
        if not item in self:
            return None

        return Document.__getitem__(self, item)

    def get_by_id(self, id):
        "通过ID获取对象"

        oid = parse(id, bson.ObjectId)
        if oid:
            return self.find_one(spec_or_id=oid)

        return None

    def find_with_page(self, page, *args, **kwargs):
        start_pos = page.get('start_pos')
        page_size = page.get('page_size')
        result = self.find(*args, **kwargs).skip(start_pos).limit(page_size)
        page['total_rows'] = result.count()
        page['last_pos'] = start_pos + result.count(True)
        return result

    def __getstate__(self):
        return dict(self)


    #基类dict 的update函数被屏蔽了
    def dict_update(self, E=None, **F):
        super(ModelBase, self).update(E, **F)


class CacheModelBase(ModelBase):
    __region__ = 'offer_wall_memcached'

    @classmethod
    def is_shared_cache(cls):
        return cache_regions[cls.__region__]['type'] != 'memory'

    #---------------------------------- find one -----------------------------
    @classmethod
    def get_with_id(cls, _id):
        assert isinstance(_id, ObjectId)
        assert issubclass(cls, Document)
        return cls.__find_one_with_cache({'_id': _id})

    #find_one_id函数必须保证查询条件的唯一性，即该查询条件 只能匹配一条或0条数据
    # 所有not_found_remove为False都表示你要在新建条目的时候手动清除它
    @classmethod
    def find_one_id_with_cache(cls, condition, not_found_remove_level=1, *args, **kwargs):
        rst = cls.__find_one_with_cache(condition, {'_id': 1}, *args, **kwargs)
        if rst:
            return rst['_id']
        else:
            # 找不到则清除所对应的缓存
            not_found_remove_level = int(not_found_remove_level)
            if not_found_remove_level == 0:
                pass
            elif not_found_remove_level == 1:
                #因为只需要清自己相关的，无论如何都只是清一份
                cache.region_invalidate(
                    cls.create_func_find_one_with_cache(),
                    cls.__region__,
                    cls.__collection__,
                    condition,
                    {'_id': 1},
                    *args,
                    **kwargs
                )
            elif not_found_remove_level == 2:
                #如果缓存是非共享缓存，广播清缓存
                cls.remove_cache_with_find_one(condition, {'_id': 1}, *args, **kwargs)
            return None

    @classmethod
    def create_func_find_one_with_cache(cls):
        @cache.region(cls.__region__, cls.__collection__)
        def _find_one_with_cache(*args, **kwargs):
            return cls().find_one(*args, **kwargs)
        return _find_one_with_cache

    @classmethod
    def get_without_id(cls, *args, **kwargs):
        _id = cls.find_one_id_with_cache(*args, **kwargs)
        if _id:
            return cls.get_with_id(_id)
        return None

    @classmethod
    def __find_one_with_cache(cls, *args, **kwargs):
        return cls.create_func_find_one_with_cache()(*args, **kwargs)

    @classmethod
    def remove_cache_with_find_one(cls, *args):  # TODO待测试
        smart_region_invalidate(cls.create_func_find_one_with_cache(),
                                cls.__region__, cls.__collection__, *args)

    # @classmethod
    # def _remove_cache_with_find_one(cls, *args, **kwargs):
    #     return cache.region_invalidate(cls.create_func_find_one_with_cache(),
    #                                    cls.__region__, cls.__collection__, *args, **kwargs)

    #------------------- find --------------------------------

    @classmethod
    def find_id_with_cache(cls, condition, *args, **kwargs):
        rst = cls.__find_with_cache(condition, {'_id': 1}, *args, **kwargs)
        return [idd['_id'] for idd in rst]

    @classmethod
    def __find_with_cache(cls, *args, **kwargs):
        return cls.create_func_find_with_cache()(*args, **kwargs)

    @classmethod
    def create_func_find_with_cache(cls):
        @cache.region(cls.__region__, cls.__collection__)
        def _find_with_cache(*args, **kwargs):
            return list(cls().find(*args, **kwargs))
        return _find_with_cache

    @classmethod
    def remove_cache_with_find(cls, *args):  # TODO待测试
        smart_region_invalidate(cls.create_func_find_with_cache(),
                                cls.__region__, cls.__collection__, *args)

    # @classmethod
    # def _remove_cache_with_find(cls, *args, **kwargs):#TODO待测试
    #     return cache.region_invalidate(cls.create_func_find_with_cache(),
    #                                    cls.__region__, cls.__collection__, *args, **kwargs)

    #该函数最后一个参数对应的是 一个ModelBase的对象，则返回该对象， 否则返回该参数对应的值
    def get_element_with_nested(self, *args):
        assert(args is not [])

        _model_type = type(self)
        _model_data = self

        for _ele_key in args:
            ele_val = _model_data[_ele_key]
            sub_model_type = None
            if _ele_key in _model_type.structure:
                sub_model_type = _model_type.structure[_ele_key]
            if not sub_model_type or not issubclass(sub_model_type, ModelBase):  # 找不到就返回该值
                assert(_ele_key == args[-1])  # 必须是参数的最后一个值
                return ele_val
            if issubclass(sub_model_type, CacheModelBase):
                _model_data = sub_model_type.get_with_id(ele_val)
            else:
                _model_data = sub_model_type().get_by_id(ele_val)
            if _model_data is None:  # maybe id is None
                return None
            _model_type = sub_model_type
        return _model_data

    def save(self, uuid=False, validate=None, safe=True, *args, **kwargs):

        super(CacheModelBase, self).save(uuid=uuid, validate=validate, safe=safe, *args, **kwargs)
        if '_id' in self:
            self.remove_cache_with_find_one({'_id': self['_id']})

    #如果更新的关键字里面有_id会清除所对应get_with_id的缓存
    #若没有，则需要手动清除缓存
    @classmethod
    def update(cls, spec, *args, **kwargs):
        rst = super(CacheModelBase, cls).update(spec, *args, **kwargs)
        if '_id' in spec:
            cls.remove_cache_with_find_one({'_id': spec['_id']})
        return rst

    @classmethod
    def find_and_modify(cls, *args, **kwargs):
        target = super(CacheModelBase, cls()).find_and_modify(*args, **kwargs)
        if target:
            cls.remove_cache_with_find_one({'_id': target['_id']})
        return target




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

        'tax':float,
        'source': FinanceLogSource,
        'status': FinanceLogStatus,
        'operation': FinanceLogOperation,
        'users':[dict],
        'checktime':datetime.datetime
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

class Team(ModelBase):
    __collection__ = 'team'
    __manager__ = 'ManagerTeam'

    structure = {
        'creator': basestring,
        'teammates': [dict],
        'status':UserStatus,
        'taxcount':dict,
        'editrecord':dict
    }

    indexes = [
        {
            'fields': ['creator']
        }
    ]

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


class AppCategory(ModelTypeBase):
    __collection__ = 'app_category'
    __manager__ = 'ManagerAppCategory'


class AdvertCategory(ModelTypeBase):
    __collection__ = 'advert_category'
    __manager__ = 'ManagerAdvertCategory'


class MediaType(ModelTypeBase):
    __collection__ = 'media_type'
    __manager__ = 'ManagerMediaType'


class TimeRange(ModelTypeBase):
    __collection__ = 'time_range'
    __manager__ = 'ManagerTimeRange'


class Platform(ModelTypeBase):
    __collection__ = 'platform'
    __manager__ = 'ManagerPlatform'
    #------------define----------------
    ios = 0
    android = 1
    #-----------------------------------
    fixtures = (
        ("ios", u"iOS", ios),
        ("android", u"Android", android),
    )

    @classmethod
    def import_fixture(cls):
        for c, n, i in cls.fixtures:
            obj = cls()
            obj['code'] = c
            obj['name'] = n
            obj['value'] = i
            obj.upsert(('value',))
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
    __collection__ = 'budget_type'
    __manager__ = 'ManagerBudgetType'

    structure = {
        'description': basestring,
    }

    # ‘每天限额 总额 无预算
    #--------- define ----------
    none, daily, all = range(3)
    #---------------------------
    fixture = {
        (u'无预算', 'none', none),
        (u'日预算', 'daily', daily),
        (u'总预算', 'all', all),
    }

    @classmethod
    def import_fixture(cls):
        for n, c, v in cls.fixture:
            s = cls()
            s['name'] = n
            s['code'] = c
            s['value'] = v
            s['description'] = u""
            s.upsert(('value',))




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
        'new_word': dict,
        'new_images': [dict],
        'show_type': ShowType,
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
    __manager__ = 'ManagerAdvertLevelLog'

    structure = {
        'name': basestring,
        'developer': float,
        'platform': float,
        'variable': float,
        'total': float,
        'code': basestring,
        'payment_type': PaymentType,
        'show_type':basestring,

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




class AdvertTag(ModelTypeBase):
    __collection__ = 'advert_tag'
    __manager__ = 'ManagerAdvertTag'

    input_data = (
        (0, 'test', '测试'),
        (1, 'sell', '售出'),
        (2, 'fill', '填充')
    )
    @classmethod
    def import_fixture(cls):
        for v, c, n in cls.input_data:
            obj = cls()
            obj['value'] = v
            obj['code'] = c
            obj['name'] = n
            obj.upsert(('value', ))

class Advert(ModelBase):
    __collection__ = 'advert'
    __manager__ = 'ManagerAdvert'

    structure = {
        'name': basestring,
        'description': basestring,
        'show_type': ShowType,
        'check_code' : basestring,
        'check_click_code' : basestring,
        'double_click':int,
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
        'shake':basestring,
        # 优先级
        'priority': int,
        # 标签
        'tag':AdvertTag,
        # 刮一刮
        'shave': basestring,
        # 吹一吹
        'blow': basestring,

        # SDK 3.0 CPA Require
        'cpa_callback_url': basestring,      # 激活回调地址
        'cpa_app_name': basestring,
        'cpa_market_url': basestring,

        'cpa_unit_price': float,
        'cpa_apk_upload': bool,
        'cpa_apk_uri': basestring,
        'cpa_apk_package': basestring,
        'cpa_apk_size': float,
        'cpa_apk_type': int,
        'cpa_apk_version': basestring,
        'cpa_apk_word': basestring,
        'cpa_apk_desc': basestring,
        'cpa_apk_icon': basestring,
        'cpa_apk_screenshot': [basestring],

        'cpa_apk_timeout': int                # Android 专用，试玩时间, 0 表示不开启
    }

    required_fields = ['name', 'date_start', 'status', 'platform', 'user']

    default_values = {
        'cpa_apk_timeout': 0
    }


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
        'app_advert_type_list':[basestring]
    }

    required_fields = ['icon', 'capture', 'binary', 'market_url']


class App(CacheModelBase):
    __collection__ = 'app'
    __manager__ = 'ManagerApp'

    structure = {
        'name': basestring,
        'api_key': basestring,
        'api_secret': basestring,

        'status': AppStatus,
        'statuslocked':bool,

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

        "payment_rate": float,          # 任务
    }

    required_fields = ['name', 'api_key', 'user']

    default_values = {
        'statuslocked': False,
        'payment_rate': 1.0,
    }

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

        'dsp_platform': basestring,

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

    default_values = {
        'dsp_platform': 'o2omobi',
    }

class PeriodicalAppLog(ReportAppLog):
    __collection__ = 'periodical_app_log'

class ReportAppLogDetail(ModelBase):
    __collection__ = 'report_app_log_detail'
    __manager__ = 'ManagerReportAppLogDetail'

    structure = {
        'date_start': datetime.datetime,
        'date_end': datetime.datetime,
        'app': App,
        'advert':Advert,
        'show_type': basestring,

        'dsp_platform': basestring,

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

    default_values = {
        'dsp_platform': 'o2omobi',
    }

class PeriodicalAppLogDetail(ReportAppLogDetail):
    __collection__ = 'periodical_app_log_detail'


# 存放广告报表修改后的数据
class ReportAdvertLogEdit(ModelBase):
    __collection__ = 'report_advert_log_edit'
    __manager__ = 'ManagerReportAdvertLogEdit'

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

class ReportAppLogDownloadLog(ModelBase):
    __collection__ = 'report_app_log_download_log'
    __manager__ = 'ManagerReportAppDownloadLog'

    structure = {
        'date_start': datetime.datetime,
        'date_end': datetime.datetime,
        'app': [dict],
        'user': dict,
    }

    indexes = [
        {'fields': ['date_start', 'date_end']},
        {'fields': ['user']},
    ]

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
class AdvertGroupOrder(ModelBase):
    __collection__ = 'advert_group_order'

    structure = {
        "name":basestring,
        "code":basestring,
        "value":int,
    }

class AdvertGroup(ModelBase):
    __collection__ = 'advert_group'

    structure = {
        "user": ObjectId,
        "group_name": basestring,
        "group_code": basestring,
        "series": ObjectId,
        "group_order":AdvertGroupOrder,
        "group_order_number":basestring,
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
# ----------------
# 整合媒介
# ---------------
class ProvinceCity(ModelBase):
    __collection__ = 'province_city'

    structure = {
        'province_code': basestring,
        'province_name': unicode,
        'pinyin': basestring,
        'shortname': basestring,
        'cities': [
            {
                'city_code': basestring,
                'city_name': unicode,
                'pinyin': basestring,
                'shortname': basestring,
            }
        ],
    }

    @classmethod
    # @cache.region('long_term')
    def get_all_provinces(cls):
        ProvinceCity = cls()
        cur = ProvinceCity.find(sort=[('province_code', 1)], fields={'province_code': True, 'province_name': True, '_id': False})
        return collections.OrderedDict([(c['province_code'], c['province_name'])  for c in cur])

    @classmethod
    # @cache.region('long_term')
    def get_cities(cls, province_code):
        ProvinceCity = cls()
        if not province_code:
            return None
        cur = ProvinceCity.find_one({'province_code': province_code}, fields={'_id': False, 'cities': True})
        if 'cities' in cur:
            return collections.OrderedDict([(c['city_code'], c['city_name'])  for c in cur['cities']])
        else:
            return None


class Param(ModelBase):
    __collection__ = 'dict'

    structure = {
        'code': basestring,
        'value': unicode,
        'order': int,
        'type': basestring,
    }

    @classmethod
    # @cache.region('long_term')
    def get_params(cls, param_type):
        Param = cls()
        cur = Param.find(spec={'type': param_type}, fields={'_id': False, 'code': True, 'value': True}, sort=[('order', 1)])
        return collections.OrderedDict([(c['code'], c['value'])  for c in cur])

    @classmethod
    def get_values(cls, param_type, codes=[]):
        Param = cls()
        return map(Param.get_params(param_type).get, codes)



class Client(ModelBase):
    __collection__ = 'client'

    structure = {
        'client_id': long,       # 广告主ID
        'client_name': unicode, # 客户名称
        'department': unicode,  # 客户部门
        'higher_dept': unicode, # 上级单位
        'employee': basestring,    # 员工人数
        'client_source': basestring,    # 客户来源代码
        'client_state': basestring,     # 客户状态代码
        'client_level': basestring,     # 客户级别代码
        'client_website': basestring,  # 公司网址
        'first_contact': unicode,   # 首要联系人
        'mobile': basestring,   # 手机
        'office_phone': basestring, # 办公电话
        'qq': basestring,
        'email': basestring,
        'other_phone': basestring,  # 其他电话
        'province': basestring,     # 省份代码
        'city': basestring,         # 城市代码
        'address': unicode,         # 地址
        'zipcode': basestring,      # 邮编
        'bank_name': unicode,       # 银行名称
        'account': unicode,         # 开户名
        'account_no': basestring,   # 银行账号
        'credit': basestring,       # 信用额度
        'tax_no': basestring,       # 纳税号
        'pay_type': [basestring],     # 支付方式代码
        'remark': unicode,          # 备注
        'inactive': bool,             # 是否已停止合作
        'create_time': datetime.datetime,    # 创建时间
        'effective_date': datetime.datetime,    # 合同生效时间
        'incharge': unicode,    # 负责人
    }

    required_fields = ['client_id', 'client_name', 'client_source', 'client_state',
                       'client_level', 'first_contact', 'mobile', 'province', 'city',
                       'address', 'zipcode', 'bank_name', 'account', 'account_no',
                       'pay_type', 'inactive', 'create_time', 'effective_date', 'incharge']

    default_values = {
        'inactive': False,
        'create_time': datetime.datetime.now()
    }

    def get_sum_by_date(self, start_date, end_date=None):
        '''
        按日期汇总每日的客户数量
        如果传入时间段，则返回时间段内每日的客户数量
        如果传入单个日期，则只统计该日的客户数量
        '''
        match = {}
        results = []
        if isinstance(start_date, datetime.datetime) and isinstance(end_date, datetime.datetime):
            match['effective_date'] = {'$gte' : start_date, '$lte': end_date}

        elif isinstance(start_date, datetime.datetime):
            match['effective_date'] = start_date

        if len(match) > 0:
            pipeline = [{'$match': match}, {'$sort': {'effective_date': -1}}, \
                        {'$group': {'_id': '$effective_date', \
                                    'total': {'$sum': 1}}}]

            cur = self.collection.aggregate(pipeline)
            results = cur['result']

        return results

class Contact(ModelBase):
    __collection__ = 'contact'

    structure = {
        'client_objectid': bson.objectid.ObjectId,   # 客户对象id
        'client_name': unicode,     # 客户名称
        'name': unicode,       # 联系人名称
        'ename': basestring, # 联系人英文名
        'department': unicode,  # 部门
        'position': unicode, # 职位
        'first_contact': basestring,    # 首要联系人
        'office_phone': basestring,    # 办公室电话
        'mobile': basestring,     # 手机
        'home_phone': basestring,     # 家庭电话
        'other_phone': basestring,  # 其他电话
        'email': basestring,
        'birthdate': datetime.datetime,     # 生日
        'assistant_name': unicode,         # 助理姓名
        'assistant_phone': basestring,         # 助理电话
        'remark': unicode,          # 备注
        'create_time': datetime.datetime,    # 创建时间
        'incharge': unicode,    # 负责人
    }

    required_fields = ['client_objectid', 'client_name', 'name', 'first_contact', 'mobile', 'create_time', 'incharge']

    default_values = {
        'create_time': datetime.datetime.now()
    }

# -----媒介-----
class Media(ModelBase):
    __collection__ = 'media'

    structure = {
        'media_id': long,
        'media_category': [basestring],
        'media_name': basestring,
        'media_level': basestring,
        'company': basestring,
        'contactMan': basestring,
        'position': basestring,
        # 'groupId': basestring,
        # 'staffId': basestring,
        'staffName': basestring,
        'media_attr': basestring,
        'ad_postion': basestring,
        'isBanner': basestring,
        'isWall': basestring,
        'isPush': basestring,
        'isRichMedia': basestring,
        'isTablePlaque': basestring,
        'isVideo': basestring,
        'isImplant': basestring,
        'isTerminal': basestring,
        'isCarrier': basestring,
        'isOS': basestring,
        'isRegion': basestring,
        'isTime': basestring,
        'android_user_num': basestring,
        'ios_user_num': basestring,
        'day_active_rate': basestring,
        'day_pv_num': basestring,
        'day_uv_num': basestring,
        'day_cpa_num': basestring,
        'payment_way': basestring,
        'publish_price': basestring,
        'discount_price': basestring,
        'delivery': basestring,
        'app_desc': basestring,
        'docking_way': basestring,
        'other_desc': basestring,
        'isAudit': basestring, #是否审计
        'create_time': datetime.datetime,    # 创建时间
        'effective_date': datetime.datetime,    # 合同生效时间
        'isBlack': basestring,  #是否移入黑名单
        'audit_status': basestring,  #审计状态
        'attachment': [dict]
    }

    required_fields = ['media_id', 'media_category', 'media_name',
                       'media_level', 'effective_date']

    default_values = {
        'isAudit': "2", #1审核 2未审核
        'create_time': datetime.datetime.now(),
        'isBlack': "0"  #1黑名单 0 正常
    }

    @classmethod
    def get_medias(cls, page, *args, **kwargs):
        cursor = cls().find(*args, **kwargs).skip(page.getFirstResult()).limit(page.getPageSize())
        return cursor

    def get_sum_by_date(self, start_date, end_date=None):
        '''
        按日期汇总每日的媒介数量
        如果传入时间段，则返回时间段内每日的媒介数量
        如果传入单个日期，则只统计该日的媒介数量
        '''
        match = {}
        results = []
        if isinstance(start_date, datetime.datetime) and isinstance(end_date, datetime.datetime):
            match['effective_date'] = {'$gte' : start_date, '$lte': end_date}

        elif isinstance(start_date, datetime.datetime):
            match['effective_date'] = start_date

        if len(match) > 0:
            pipeline = [{'$match': match}, {'$sort': {'effective_date': -1}}, \
                        {'$group': {'_id': 'effective_date', \
                                    'total': {'$sum': 1}}}]

            cur = self.collection.aggregate(pipeline)
            results = cur['result']

        return results
# -----流量------
class FlowInfo(ModelBase):
    __collection__ = 'flowinfo'


    structure = {
                'date': datetime.datetime,
                'date_string':basestring,
                'hash_code':long,
                'cond_id':{
                'ex_media_id': basestring,
                'ex_media_name': basestring,
                'ad_id': basestring,
                'ad_name': basestring,
                'channel_id': basestring,
                'bd_name': basestring
                },
                'unit_price': float,
                'impact_count': int,
                'reduce_count': int,
                'commission': float,
                'profit': float
    }

    @classmethod
    def request_flow_info(cls, *dt):
        arg_num = len(dt)
        if arg_num == 0 or arg_num > 2:
            return
        if arg_num == 1:
            one_day = dt[0]
            query_string = {"date": one_day}
            result_cursor = cls().find(query_string).sort([('date', -1)])
            result = []

            for item in list(result_cursor):
                tmp = {}
                for thing in item:
                    if thing == 'cond_id':
                        tmp.update(item[thing])
                    else:
                        tmp[thing] = item[thing]
                    if tmp not in result:
                        result.append(tmp)
            return result

        elif arg_num == 2:

            if dt[0] < dt[1]:

                start_date = dt[0]
                end_date = dt[1]

                query_string = {"date": {"$gte": start_date, "$lte": end_date}}
                result_cursor = cls().find(query_string).sort([('date', -1)])

                result = []

                for item in list(result_cursor):
                    tmp = {}
                    for thing in item:
                        if thing == 'cond_id':
                            tmp.update(item[thing])
                        else:
                            tmp[thing] = item[thing]
                        if tmp not in result:
                            result.append(tmp)
                return result

            elif dt[0] > dt[1]:

                start_date = dt[1]
                end_date = dt[0]

                query_string = {"date": {"$gte": start_date, "$lte": end_date}}
                result_cursor = cls().find(query_string).sort([('date', -1)])
                result = []
                for item in list(result_cursor):
                    tmp = {}
                    for thing in item:
                        if thing == 'cond_id':
                            tmp.update(item[thing])
                        else:
                            tmp[thing] = item[thing]
                        if tmp not in result:
                            result.append(tmp)
                return result

            else:
                one_day = dt[0]
                query_string = {"date": one_day}
                result_cursor = cls().find(query_string).sort([('date', -1)])
                result = []

                for item in list(result_cursor):
                    tmp = {}
                    for thing in item:
                        if thing == 'cond_id':
                            tmp.update(item[thing])
                        else:
                            tmp[thing] = item[thing]
                        if tmp not in result:
                            result.append(tmp)
                return result

class FlowStat(ModelBase):
    __collection__ = 'flowstat'

    structure = {
        'search_id':{
                'ex_media_id': basestring,
                'ex_media_name': basestring,
                'ad_id': basestring,
                'ad_name': basestring,
                'channel_id': basestring,
                'bd_name':basestring
                },
        'hash_code': long
    }

# 平台流量
class AdvertiserList(ModelBase):
    '''
    keep records of signed advertiser amount
    '''

    __collection__ = 'traffic.advertiserlist'


    structure = {
        'ymd': datetime.datetime,   #
        'y': int,                   # the year
        'm': int,                   # the month
        'd': int,                   # the day
        'amount': int  # advertiser amount every day
    }

    required_fields = ['ymd', 'y', 'm','d','amount']

    @classmethod
    def gen_advertiserlist(cls,dt,amount):
        '''
        update the amount of signed advertiser in a given day
        '''
        #criteria = {'$and':[{'ymd':datetime.datetime(dt.year,dt.month,dt.day)},{'y':dt.year},{'m':dt.month},{'d':dt.day}]}
        criteria = {'ymd':datetime.datetime(dt.year,dt.month,dt.day),'y':dt.year,'m':dt.month,'d':dt.day}
        AdvertiserList = cls()
        AdvertiserList.find_and_modify(criteria,{'$set':{'amount':amount}},upsert=True)

    @classmethod
    def show_advertiserlist_dailyview(cls,fromDate,toDate):
        criteria = {'$and':[{'ymd':{'$gte':fromDate}},{'ymd':{'$lte':toDate}}]}
        AdvertiserList = cls()
        docs = AdvertiserList.find(criteria)

        return list(docs)

    @classmethod
    def show_advertiser_volume(cls):
        '''
        the aggregation equivalent:

db.traffic.advertiserlist.aggregate(
{'$match':{'ymd':{'$lte':ISODate('2014-01-23T00:00:00.000Z')}}},
{'$project':{'amount':1,'_id':0}},
{'$group':{'_id':{},'volume':{'$sum':'$amount'}}}
);

        '''
        now = datetime.datetime.now()
        criteria = {'$match':{'ymd':{'$lte':now}}},\
{'$project':{'amount':1,'_id':0}},\
{'$group':{'_id':{},'volume':{'$sum':'$amount'}}}
        AdvertiserList = cls()

        ret = AdvertiserList.collection.aggregate(criteria)

        print ret

        ##expect ret is like "{ "result" : [ { "_id" : { }, "volume" : 6 } ], "ok" : 1 }"
        #return ret['result'][0]['volume']
        #fix the issue:
        #if the reporting collection does not exist
        return ret['result'][0]['volume']  if ret['result'] else 0

class MList(ModelBase):
    '''
    keep records of media amount
    '''

    __collection__ = 'traffic.mlist'

    structure = {
        'ymd': datetime.datetime,   #
        'y': int,                   # the year
        'm': int,                   # the month
        'd': int,                   # the day
        'amount': int  # media amount every day
    }

    required_fields = ['ymd', 'y', 'm','d','amount']

    @classmethod
    def gen_mlist(cls,dt,amount):
        '''
        update the amount of signed advertiser in a given day
        '''
        #criteria = {'$and':[{'ymd':datetime.datetime(dt.year,dt.month,dt.day)},{'y':dt.year},{'m':dt.month},{'d':dt.day}]}
        criteria = {'ymd':datetime.datetime(dt.year,dt.month,dt.day),'y':dt.year,'m':dt.month,'d':dt.day}
        MList = cls()
        MList.find_and_modify(criteria,{'$set':{'amount':amount}},upsert=True)

    @classmethod
    def show_mlist_dailyview(cls,fromDate,toDate):
        criteria = {'$and':[{'ymd':{'$gte':fromDate}},{'ymd':{'$lte':toDate}}]}
        MList = cls()
        docs = MList.find(criteria)

        return list(docs)

    @classmethod
    def show_m_volume(cls):
        '''
        the aggregation equivalent:

db.traffic.mlist.aggregate(
{'$match':{'ymd':{'$lte':ISODate('2014-01-23T00:00:00.000Z')}}},
{'$project':{'amount':1,'_id':0}},
{'$group':{'_id':{},'volume':{'$sum':'$amount'}}}
);

        '''
        now = datetime.datetime.now()
        criteria = {'$match':{'ymd':{'$lte':now}}},\
{'$project':{'amount':1,'_id':0}},\
{'$group':{'_id':{},'volume':{'$sum':'$amount'}}}
        MList = cls()
        ret = MList.collection.aggregate(criteria)

        ##expect ret is like "{ "result" : [ { "_id" : { }, "volume" : 6 } ], "ok" : 1 }"
        #return ret['result'][0]['volume']
        #fix the issue:
        #if the reporting collection does not exist
        return ret['result'][0]['volume']  if ret['result'] else 0

class MediaList(ModelBase):
    '''
    The MediaList is intermedia between origianl channel traffic and total channel traffic per day/months.

    The MediaList is designed to be divide into year,months,day axis.
    '''
    __collection__ = 'traffic.medialist'

    structure = {
        'ymd': datetime.datetime,   # the format is yyyy-MM-dd
        'y': int,         # the year
        'm': int,         # the month
        'd': int,         # the day
        'med': [unicode]  # media name list
    }

    required_fields = ['ymd', 'y', 'm','d']

    @classmethod
    def gen_medialist(cls,year,month,day,medias):
        '''
        insert or update medialist
        for example:
        db.mls.insert({ymd:"20140105",y:2014,m:1,d:5});
        db.mls.update({y:2014,m:1,d:5},{$push:{med:"hive"}});
        db.mls.update({y:2014,m:1,d:5},{$push:{med:{$each:["pig","erop"]}}});
        '''
        if year is None or month is None or day is None:
            raise ValueError

        if not isinstance(year,int) \
            or not isinstance(month,int) \
            or not isinstance(day,int) \
            or not isinstance(medias,list):
            raise TypeError

        criteria = {'$and':[{'y':year},{'m':month},{'d':day}]}
        MediaList = cls()
        doc = MediaList.find_one(criteria)

        #eliminate the duplicate elements' value
        if doc is None:
            doc = MediaList

            doc['ymd']=datetime.datetime(year,month,day)
            doc['y']=year
            doc['m']=month
            doc['d']=day
            doc['med']=list(set(medias))
        else:
            doc['med'].extend(medias)
            doc['med']=list(set(doc['med']))
        doc.save()

    @classmethod
    def show_medialist_dailyview(cls,fromDate,toDate):
        '''
        equal aggregation framework expression:

        for example:compute media amount in between 2014.1.1,2014.1.5

        db.traffic.medialist.aggregate(
{'$match':{'$and':[{'ymd':{'$lte':ISODate('2014-01-31T06:15:33.035Z')}},{'ymd':{'$gte':ISODate('2013-12-01T06:15:33.035Z')}}]}},
{'$project':{'ymd':1,'med':1,'_id':0}},
{'$unwind':'$med'},
{'$group':{'_id':{'ymd':'$ymd'},'count':{'$sum':1}}},
{'$sort':{'_id':-1}}
);
        '''
        agg_expr = [\
{'$match':{'$and':[{'ymd':{'$lte':toDate}},{'ymd':{'$gte':fromDate}}]}},\
{'$project':{'ymd':1,'med':1,'_id':0}},\
{'$unwind':'$med'},\
{'$group':{'_id':{'ymd':'$ymd'},'count':{'$sum':1}}},\
{'$sort':{'_id':-1}}\
]

        MediaList = cls()
        ret = MediaList.collection.aggregate(agg_expr)

        return ret['result']

    @classmethod
    def show_medialist_monthlyview(cls,fromDate,toDate):
        '''
        equal aggregation framework expression:

        for example:compute media monthly amount between 2014.1
        The tricky thing is when you use $group,a operator is indispensable.We choose the "first" operator as a trick

        db.traffic.medialist.aggregate(
{'$match':{'$and':[{'ymd':{'$lte':ISODate('2014-01-31T06:15:33.035Z')}},{'ymd':{'$gte':ISODate('2013-12-01T06:15:33.035Z')}}]}},
{'$project':{'y':1,'m':1,'med':1,'_id':0}},
{'$unwind':'$med'},
{'$group':{'_id':{'y':'$y','m':'$m'},'count':{'$sum':1}}},
{'$sort':{'_id':-1}}
);
        '''
        agg_expr = [\
{'$match':{'$and':[{'ymd':{'$lte':toDate}},{'ymd':{'$gte':fromDate}}]}},\
{'$project':{'y':1,'m':1,'med':1,'_id':0}},\
{'$unwind':'$med'},\
{'$group':{'_id':{'y':'$y','m':'$m'},'count':{'$sum':1}}},\
{'$sort':{'_id':-1}}\
]
        MediaList = cls()

        ret = MediaList.collection.aggregate(agg_expr)

        return ret['result']


class UserAdFilter(ModelBase):
    __collection__ = 'user_ad_filter'

    structure = {
        'user': ObjectId,
        'categories': list,
    }

#====================== DSP 广告 ============================================

# DSP平台设置
#--------------------------------------------
class DspPlatformConfig(CacheModelBase):
    __collection__ = 'dsp_platform_config'

    structure = {
        'dsp_platform':         basestring,     # 平台标识，英文，类似code
        'dsp_platform_name':    basestring,     # 平台名称，类似name
        'dsp_timeout':          int,            # 超时时间
        'dsp_priority_level':   int,            # dsp平台的广告优先级
        'dsp_req_url':          basestring,     # dsp广告请求地址
        'dsp_report_url':       basestring,     # dsp广告报表请求地址
        'dsp_req_switch':       int,            # 平台请求开关（0：关， 1：开）
        'dsp_req_limited':      int             # 流量控制
    }

    default_values = {
        'dsp_timeout': 0,
        'dsp_priority_level': 0,
        'dsp_req_url': '',
        'dsp_report_url': '',
        'dsp_req_switch': 1,
        'dsp_req_limited': 0,
    }


class ReportLomark(ModelBase):
    __collection__ = 'report_lomark'

    structure = {
        'appid': basestring,            # 应用id
        'date': basestring,             # 日期，字符串，貌似是本地日期
        'adspacetype': basestring,      # 广告类型， banner，插屏，全屏
        'client': basestring,           # 设备类型，手机/平板
        'request': int,                 # 请求数
        'impression': int,              # 展示数
        'click': int                    # 点击数
    }


class CarrierNetworkType(ModelBase):
    __collection__ = 'carrier_network_type'

    all_all = 0

    structure = {
        'value': int,
        'carrier': basestring,
        'network': basestring,
        'car_name': basestring,
        'net_name': basestring,
    }

    carrier_index = (

        (0b1 << 16, u'cmcc', u'移动'),
        (0b11 << 16, u'unicom', u'联通'),
        (0b111 << 16, u'cmnet', u'电信'),
        (0b1111 << 16, u'other', u'其它'),
    )

    network_index = (
        (1, u'wifi', u'WiFi'),
        (2, u'2g', u'2G'),
        (3, u'3g', u'3G'),
        (4, u'4g', u'4G')
    )

    _index_compare = (
        (carrier_index[0], network_index),
        (carrier_index[1], network_index),
        (carrier_index[2], network_index),
        (carrier_index[3], network_index),
    )

    @classmethod
    def import_fixture(cls):
        all_obj = cls()
        all_obj['value'] = 0
        all_obj['carrier'] = 'all'
        all_obj['car_name'] = '全'
        all_obj['network'] = 'all'
        all_obj['net_name'] = '选'

        all_obj.upsert(('value', 'carrier', 'network'))

        for c, ns in cls._index_compare:
            for n in ns:
                obj = cls()
                obj['value'] = c[0] + n[0]
                obj['carrier'] = c[1]
                obj['car_name'] = c[2]
                obj['network'] = n[1]
                obj['net_name'] = n[2]
                print dict(obj)
                obj.upsert(('value', 'carrier', 'network'))




#====================== Offer Wall ============================================

class OfferWallTrackLogType(ModelTypeBase):
    __collection__ = 'offer_wall_track_log_type'
    #------------------data----------------------
    structure = {
        'is_show': bool,
    }
    #-----------------define---------------------+
    click = 1
    show = 2
    activation = 3
    sdk_exchange = 4
    #android的有效点击会在下载行为那一步记录
    effective_click = 5
    money = 6
    android = {
        'pos': 128,
        'attributes': ['download', 'downloaded', 'install', 'activation', 'experience']
    }
    android_action_len = len(android['attributes'])

    @classmethod
    def is_android_action_value(cls, value):
        pos = cls.android['pos']
        return pos <= value < pos + cls.android_action_len

    #--------------------------------------------
    fixtures = [
        #- ap/ad --- code - value - is show -----
        ('展示', 'show', show, True),
        ('点击', 'click', click, True),
        ('有效点击', 'effective click', effective_click, True),
        ('效果数', 'activation', activation, True),
        ('欧币', 'exchange', sdk_exchange, True),
        ('收入/成本', 'money', money, True)
    ]

    __fixtures = [
        ('android下载', 'click', android['pos'], False)
    ]


    @classmethod
    def import_fixture(cls):
        for n, c, v, is_show in cls.__fixtures + cls.fixtures:
            s = cls()
            s['name'] = n
            s['code'] = c
            s['value'] = v
            s['is_show'] = is_show
            s.upsert(('value',))


class OfferWallTrackLogAndroidRule(CacheModelBase):
    __collection__ = 'offer_wall_track_log_android_rule'
    structure = {
        'name': basestring,
        'code': basestring,
        'value': int,
        #该行为的生存周期，超过周期还没执行下一个行为则作废
        'life_cycle': int,
    }
    #----------------define------------------
    __values = OfferWallTrackLogType.android
    #----------------------------------------

    @classmethod
    def import_fixture(cls):
        for i in range(len(cls.__values['attributes']) - 1):
            s = cls()
            s['name'] = ""
            s['code'] = cls.__values['attributes'][i]
            s['value'] = i
            s.upsert(('value',))

    default_values = {
        'life_cycle': 3600,
    }


class OfferWallAppTypes(ModelTypeBase):
    __collection__ = 'offer_wall_app_types'

    Application = 1  # 应用大类
    Game = 2         # 游戏大类

    structure = {
        'subject_type': int
    }
    default_values = {
        'subject_type': Game
    }
    fixture = {
        # 应用类型
        (u'新闻', 'news', Application), (u'财经', 'financial', Application), (u'汽车', 'auto', Application),
        (u'生活', 'life', Application),(u'工具', 'tools', Application), (u'娱乐', 'entertainment', Application),
        (u'体育', 'sport', Application), (u'游戏', 'game', Application),
        (u'商旅', 'trip', Application), (u'教育', 'edu', Application),
        (u'阅读', 'reading', Application), (u'女性', 'lady', Application),
        # 游戏类型
        (u'角色扮演', 'rpg', Game), (u'动作格斗', 'ftg', Game), (u'体育竞技', 'spg', Game),
        (u'射击飞行', 'stg', Game), (u'策略回合', 'slg', Game), (u'冒险模拟', 'act', Game),
        (u'休闲趣味', 'funny', Game), (u'棋牌益智', 'chess', Game)
    }

    @classmethod
    def import_fixture(cls):
        i = 0
        for n, c, v in cls.fixture:
            s = cls()
            s['value'] = i
            s['subject_type'] = v
            s['name'] = n
            s['code'] = c
            s.upsert(('value',))
            i += 1


class OfferWallAdvert(CacheModelBase):
    __region__ = 'offer_wall_short'
    __collection__ = 'offer_wall_advert'
    structure = {
        'platform': Platform,               # 平台
        'user_id': User,                    # 积分广告所对应的用户
        'status': AdvertStatus,             # 积分广告的状态
        'name': basestring,                 # 广告名
        'word': basestring,                 # 推广文案
        'task_name': basestring,            # 任务名
        'task_steps': [basestring],         # 任务步骤
        'budget': BudgetType,               # 预算, 0:无预算，1:总预算，2:日预算
        'budget_effect': int,               # 预算效果数
        'channel': int,                     # 投放渠道，0:积分墙， 1:推荐墙
        'is_api': int,                      # 是否api对接, 0:false, 1:true
        'price': float,                     # 任务价格
        'icon': basestring,                 # 图标路径
        'start_date': datetime.datetime,    # 开始日期
        'end_date': datetime.datetime,      # 结束日期
        #app info
        'app_name': basestring,             # 应用名
        'app_market_url': basestring,       # 市场链接(跳转地址)
        'app_main_type': int,               # 应用的主要类型（目前，1表示应用，2表示游戏）
        'app_type': OfferWallAppTypes,      # 应用类型
        'app_activation_url': basestring,   # 激活地址
        'app_info': basestring,             # 应用描述
        'app_author': basestring,           # 应用作者

        'app_apk_url': basestring,           # (Android专用)apk的下载地址
        'app_apk_filename': basestring,      # (Android专用)apk的文件名
        'app_apk_pkgname': basestring,       # (Android专用)apk的包名
        'app_apk_size': float,               # (Android专用)大小
        'app_apk_ver': basestring,           # (Android专用)应用版本号
        'app_apk_screenshot': [basestring],  # (Android专用)应用截图，3张
        'app_apk_timeout': int,              # (Android专用)计时器字段，默认不开启（-1或0）

        'carrier_network': [CarrierNetworkType],  # 上网方式和手机卡
        'tag': AdvertTag,                      # 标示广告投放方式
    }

    android_apk_not_timeout = -1

    default_values = {
        'price': 0.0,
        'channel': 0,
        'budget_effect': 0,
        'app_apk_url': '',
        'app_apk_filename': '',
        'app_apk_pkgname': '',
        'app_apk_size': 0.0,
        'app_apk_ver': '0.0.0',
        'app_apk_screenshot': [],
        'app_main_type': OfferWallAppTypes.Application,
        'app_apk_timeout': android_apk_not_timeout,
    }
    channel_offer = 0
    channel_recommend = 1

class OfferWallUser(CacheModelBase):
    __collection__ = 'offer_wall_user'
    structure = {
        'openudid': basestring,  # 设备的唯一标示
        'mac': basestring,       # mac地址（预留）
        'ifa': basestring,       # ifa（预留）
        'udid': basestring,      # udid（预留）
    }

    default_values = {
        'mac': '',
        'ifa': '',
        'udid': ''
    }


class OfferWallTaskLogState(ModelTypeBase):
    __collection__ = 'offer_wall_task_log_state'
    #所有大于0的表示成功
    #所有小于0表示不成功
    #==============define==============
    not_activation = 0
    activation = 1
    failure = -1
    #==================================
    fixtures = {
        ("not activation", u"未激活", not_activation),
        ("activation", u"激活", activation),
        ("failure", u"失效", failure),
    }


    @classmethod
    def import_fixture(cls):
        for n, c, i in cls.fixtures:
            s = cls()
            s['name'] = n
            s['code'] = c
            s['value'] = i
            s.upsert(('value',))


class OfferWallTaskLog(CacheModelBase):
    __collection__ = 'offer_wall_task_log'
    structure = {
        'user_id': OfferWallUser,               # 对应OfferWallUser的_id
        'advert_id': OfferWallAdvert,           # 对应OfferWallAdvert的_id
        'app_id': App,                          # 对应App 的_id
        'score': float,                         # 获得的分数
        'state': int,                           # 任务状态0：未完成，1：完成，-1:失效
    }

    default_values = {
        'state': OfferWallTaskLogState.failure,
    }


class OfferWallConsumptionLog(CacheModelBase):
    __collection__ = 'offer_wall_consumption_log'
    structure = {
        'user_id': OfferWallUser,   # 对应OfferWallUser的_id
        'app_id': App,              # 对应App 的_id
        'score': float,             # 消费的分数
    }


class OfferWallCenter(CacheModelBase):#TODO
    __collection__ = 'offer_wall_center'
    structure = {
        'user_id': OfferWallUser,       #对应OfferWallUser的_id
        'app_id': App,                  #对应App 的_id
        'score': float,                 #记录用户总分
    }


class OfferWallCheck(CacheModelBase):
    __collection__ = 'offer_wall_check_log'
    structure = {
        'check_str': basestring,  # 校验url是否合法
        'task_log': OfferWallTaskLog,
        'extra_data': basestring,
    }
    default_values = {
        'extra_data': ''
    }


# 通用设置表
class CommonSetting(CacheModelBase):
    __collection__ = 'common_setting'
    structure = {
        'code': basestring,             # 积分兑换配置表的选项名
        'value': float,                 # 积分兑换配置表的值
        'description': basestring      # 相关描述
    }
    default_values = {
        'value': 0.0
    }
    #-----------------------
    fixtures = {
        ("offerwall_exchange_profit", u"积分墙预留利率", 0.2),
        ("offerwall_exchange_rate", u"积分墙汇率", 2.0),
        ("offerwall_task_limit", u"积分任务限制", 6),
    }

    @classmethod
    def import_fixture(cls):
        for c, n, i in cls.fixtures:
            s = cls()
            s['description'] = n
            s['code'] = c
            s['value'] = i
            s.update({'code': c}, dict(s), upsert=True)


# 应用虚拟货币类型
class IdealMoneyType(ModelTypeBase):
    __collection__ = 'ideal_money_type'

    fixtures = (
        ("score", u"积分", 1), ("golden", u"金币", 2), ("diamond", u"钻石", 3),
        ("energy", u"能量点", 4), ("books", u"书币", 5), ("exp", u"经验", 6),
        ("points", u"点数", 7), ("chip", u"筹码", 8), ("times", u"分钟", 9)
    )

    @classmethod
    def import_fixture(cls):
        for c, n, i in cls.fixtures:
            s = cls()
            s['name'] = n
            s['code'] = c
            s['value'] = i
            s.upsert(('value',))


# 开发者后台应用设置
class OfferWallDeveloperSetting(CacheModelBase):
    __region__ = 'short_term'
    __collection__ = 'offer_wall_developer_setting'
    structure = {
        'app_id': App,
        'show_offerwall': bool,
        'unit': basestring,
        'rate': float,
        'default_view': int,                # 前端显示的默认页面， 1表示应用，2表示游戏
        'callback_url': basestring,         # 服务端回调地址（激活用）
        'duration_show': float,             # 插屏广告时间，必须>=5
        'fullscreen_duration_show': float,  # 全屏广告时间，必须>=5
        'enable_duration': bool,            # 是否启用插屏或者全屏广告自动关闭
        'enable_double_click': int          # 是否启用二次点击 (  -1 未设置， 0 关闭， 1 开启）
    }

    default_values = {
        'show_offerwall': True,
        'unit': u'金币',
        'rate': 2.0,
        'default_view': OfferWallAppTypes.Game,
        'callback_url': '',
        'duration_show': 5.0,
        'fullscreen_duration_show': 5.0,
        'enable_duration': False,
        'enable_double_click': -1
    }

    #这个只是填充一下数据，如果app_id已经存在不会覆盖原有的数据
    @classmethod
    def import_fixture(cls):
        for app in App().find({'removed': False}, {'_id': 1}):
            if not cls().find_one({'app_id': app['_id']}):
                s = cls()
                s['app_id'] = app['_id']
                s.upsert(('app_id',))


#行为统计
class PeriodicalOfferWallAdvertLog(ModelBase):
    structure = {
        'advert': OfferWallAdvert,
        'date_start': datetime.datetime,
    }
    default_values = {
    }
    for widget in OfferWallTrackLogType.fixtures:
        c = widget[1]
        structure[c] = int
        default_values[c] = 0


class PeriodicalOfferWallAppLog(ModelBase):
    structure = {
        'app': App,
        'date_start': datetime.datetime,
    }
    default_values = {
    }
    for widget in OfferWallTrackLogType.fixtures:
        c = widget[1]
        structure[c] = int
        default_values[c] = 0


class PeriodicalOfferWallAdvertLogHour(PeriodicalOfferWallAdvertLog):
    __collection__ = 'periodical_offer_wall_advert_log_hour'


class PeriodicalOfferWallAppLogHour(PeriodicalOfferWallAppLog):
    __collection__ = 'periodical_offer_wall_app_log_hour'


class PeriodicalOfferWallAdvertLogDay(PeriodicalOfferWallAdvertLog):
    __collection__ = 'periodical_offer_wall_advert_log_day'


class PeriodicalOfferWallAppLogDay(PeriodicalOfferWallAppLog):
    __collection__ = 'periodical_offer_wall_app_log_day'


class PeriodicalRecommendWallAppLogHour(PeriodicalOfferWallAppLog):
    __collection__ = 'periodical_recommend_wall_app_log_hour'


class PeriodicalRecommendWallAppLogDay(PeriodicalOfferWallAppLog):
    __collection__ = 'periodical_recommend_wall_app_log_day'

class SdkVersionServer(CacheModelBase):  # TODO
    __collection__ = 'sdk_version_server'

    server = 0
    stop = 1
    structure = {
        'platform': int,
        'version': basestring,
        'status': int
    }

    default_values = {
        'status': server
    }

#-------------------------------------------------------------
#    Testin 测试相关功能
#-------------------------------------------------------------

# 提交到testin的数据
class TestinRecord(ModelBase):
    __collection__ = 'testin_record'
    structure = {
        'user_id': User,
        'sid': basestring,
        'client': basestring,
        'platform_code': int,           # 按照testin那边的值表示： 1. android, 2. ios
        'date': datetime.datetime,
        'pass_percent': float,
        'filepath': basestring,
        'is_upload': int,               # 表示当前测试的应用是上传的还是选择App的  0:表示选择app， 1：上传
        'app_logo': basestring,
        'app_name': basestring,
        'app_pkgname': basestring,
        'test_id': basestring,
        'test_details': basestring,
        'test_status':  int             # 0: 等待中， -1：失败， 1：已完成  2: 报告已经生成
    }

    default_values = {
        'pass_percent': 0.0,
        'filepath': '',
        'test_details': '',
        'is_upload': 1
    }

    def details(self):
        import json
        return json.loads(self['test_details'])

#-------------------------------------------------------------
#    SDK CPA 3.0 TrackLog
#-------------------------------------------------------------
# CPA的tracklog类型
class CPATrackLogType(ModelTypeBase):
    __collection__ = 'cpa_track_log_type'

    Download = 128              # 下载
    Download_Complete = 129     # 下载完成
    Install = 130               # 安装
    Activation = 131            # 激活
    Try = 132                   # 试玩
    Close = 6                   # 关闭落地页

    __type_list = []
    __android_cpa_types = []

    structure = {
        'is_show': bool,
    }

    fixtures = [
        #- ap/ad --- code - value - is show -----
        ('下载', 'download', Download, True),
        ('下载完成', 'download_complete', Download_Complete, True),
        ('安装', 'install', Install, True),
        ('激活', 'activation', Activation, True),
        ('试玩', 'try', Try, True),
        ('关闭落地页', 'close', Close, False)
    ]

    @classmethod
    def import_fixture(cls):
        for n, c, v, is_show in cls.fixtures:
            s = cls()
            s['name'] = n
            s['code'] = c
            s['value'] = v
            s['is_show'] = is_show
            s.upsert(('value',))

    @classmethod
    def types_list(cls):
        if len(cls.__type_list) == 0:
            cls.__type_list =  [c[2] for c in cls.fixtures]
        return cls.__type_list

    @classmethod
    def android_types(cls):
        if len(cls.__android_cpa_types) == 0:
            cls.__android_cpa_types = [(c[2], c[1]) for c in cls.fixtures if c[2] >= 128]
        return cls.__android_cpa_types


class CPAActivationRecord(CacheModelBase):
    __collection__ = 'cpa_activation_record'

    structure = {
        'advert_id': Advert,
        'session_id': basestring,
        'status': int,               # 0 表示未激活，1表示已经激活
        'device_info': dict          # 设备信息
    }