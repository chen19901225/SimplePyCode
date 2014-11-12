#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import
import random
from os import urandom
from datetime import datetime, timedelta
from functools import partial
try:
    from cdecimal import Decimal
except:
    from decimal import Decimal

from faker import Faker
from faker.providers import BaseProvider
from faker.providers.internet import Provider as provider_internet

from base.utils import (
    today, timestamp_to_datetime, datetime_to_timestamp, is_string,
    md5sum, object_id,
)
from model.data.definition import App
from proto import data_pb2
from .campaign import Property, publisher_transform_app
from .trading_area import find_all_trading_areas


#---------------------------------------------------------------------
#                   Custom Faker Provider
#
# Generate data for testing.
#---------------------------------------------------------------------
class BalinProvider(BaseProvider):
    @classmethod
    def random_list(cls, array=('a', 'b', 'c'), lower=None, upper=None):
        array = list(array)
        length = len(array)
        if lower is None:
            lower = 0
        if upper is not None:
            length = min(upper, length)
        return [cls.random_element(array) for __ in range(random.randint(lower, length))]

    @classmethod
    def random_list_not_empty(cls, array=('a', 'b', 'c'), upper=None):
        array = list(array)
        length = len(array)
        return cls.random_list(array, lower=1)

    @classmethod
    def mac_address(cls, manufacturer=None):
        # https://github.com/diogomonica/py-MACtool/blob/master/MACtool.py
        # NOTE Current only generate fake mac address without manufacturer.
        if manufacturer is None:
            prefix = [0x00]
        for __ in range(6 - len(prefix)):
            prefix.append(random.randint(0x00, 0x7f))
        return ":".join("%02x" % x for x in prefix)

    # https://github.com/LazyZhu/myblog/blob/06af685703f71a5d94dcd3051a0bdc7471c8ae23/imei-generator/js/imei-generator.js
    # http://www.esoftnetonline.com/cellphones.htm
    RBI = ("01", "10", "30", "33", "35", "44", "45", "49", "50", "51", "52", "53", "54", "86", "91", "98", "99")
    PA = ("02", "20", "08", "80", "01", "10", "00", "13")

    @classmethod
    def imei(cls):
        imei = map(int, random.choice(cls.RBI))
        for __ in range(12):
            imei.append(random.randrange(0, 10))
        imei[6:8] = map(int, random.choice(cls.PA))
        offset, checksum = (15 + 1) % 2, 0
        for i in range(14):
            if (i + offset) % 2:
                t = imei[i] * 2
                if t > 9:
                    t -= 9
                checksum += t;
            else:
                checksum += imei[i]
        imei.append((10 - (checksum % 10)) % 10)
        return "".join(map(str, imei))[:15]

    @classmethod
    def uri_image(cls, size=None):
        use_real_image = False
        if is_string(size) and "x" in size:
            try:
                __ = map(int, size.split("x"))
                use_real_image = True
            except:
                pass
        if use_real_image:
            return "http://dummyimage.com/%s/000/fff" % size
        else:
            return provider_internet.uri_path() + ".jpg"

    @classmethod
    def ipv4(cls, lower=None, upper=None):
        lower = lower is None and -2147483648 or lower
        upper = upper is None and 2147483647 or upper
        return ".".join(map(lambda n: str(random.randint(lower, upper) >> n & 0xff), [24, 16, 8, 0]))


    @classmethod
    def imsi(cls, prefer=None):
        lst = ("46000", "46001", "46002", "46003")
        if prefer not in lst:
            return cls.random_element(lst)
        return prefer

    @classmethod
    def random_float(cls, lower=0.0, upper=10.0, prec=6):
        lower = int(lower * prec)
        upper = int(upper * prec)
        n = random.randint(lower, upper)
        return float(Decimal(n) / Decimal(prec))

    #---------------------------------------------------------------------
    # Get random record from production database.
    #---------------------------------------------------------------------
    PUBLISHER_CACHE=None

    @classmethod
    def publisher(cls, clean_cache=False):
        if clean_cache:
            BalinProvider.PUBLISHER_CACHE = []
        # TODO Generator fake publisher.
        cache = BalinProvider.PUBLISHER_CACHE
        if not cache:
            status = Property.publisher_statuses_by_code_to__id()["running"]
            res = App.query(status=object_id(status))
            cache = BalinProvider.PUBLISHER_CACHE = publisher_transform_app(list(res))
        return random.choice(cache)

    @classmethod
    def budget_type(cls):
        return cls.random_element(Property.budget_types_list())

    @classmethod
    def show_type(cls):
        return cls.random_element(Property.show_types_list())

    @classmethod
    def payment_type(cls):
        return cls.random_element(Property.payment_types_list())

    @classmethod
    def target_category(cls):
        return cls.random_element(Property.categories_list())

    @classmethod
    def target_categories(cls, lower=None, upper=None):
        return cls.random_list(Property.categories_list(), lower, upper)

    @classmethod
    def target_platform(cls):
        return cls.random_element(Property.platforms_list())

    @classmethod
    def target_time_ranges(cls, lower=None, upper=None):
        return cls.random_list(Property.time_ranges_list(), lower, upper)

    @classmethod
    def target_regions(cls, lower=None, upper=None):
        values = Property.regions_list()
        if cls.random_digit() % 2:
            return [values[0]]
        else:
            return cls.random_list(values[1:], lower, upper)

    @classmethod
    def target_areas(cls):
        return find_all_trading_areas()

    @classmethod
    def target_brands(cls):
        values = Property.brands_list()
        if cls.random_digit() % 2:
            return [values[0]]
        else:
            return cls.random_list(values[1:])

    @classmethod
    def target_languages(cls, lower=None, upper=None):
        values = Property.languages_list()
        if cls.random_digit() % 2:
            return [values[0]]
        else:
            return cls.random_list(values[1:])

    @classmethod
    def target_carriers(cls, lower=None, upper=None):
        return cls.random_list(Property.carriers_list(), lower, upper)

    @classmethod
    def target_gender(cls):
        return cls.random_element(Property.genders_list())

    @classmethod
    def target_ages(cls, lower=None, upper=None):
        return cls.random_list(Property.ages_list(), lower, upper)

    @classmethod
    def target_careers(cls, lower=None, upper=None):
        values = Property.careers_list()
        if cls.random_digit() % 2:
            return [values[0]]
        else:
            return cls.random_list(values[1:], lower, upper)

    @classmethod
    def target_business_model(cls, targetting=True):
        values = Property.business_models_list()
        if targetting:
            if cls.random_digit() % 2:
                return values[0]  # unlimited business model.
            else:
                return cls.random_element(values[1:])
        else:
            return cls.random_element(values[1:])

# We init the faker as global instance for later use.
faker = Faker()
faker.add_provider(BalinProvider)


def set_or_random(kwargs, key, multiple, fn, mapping_key="code"):
    if key in kwargs:
        if kwargs[key] is None:
            if multiple:
                return []
            else:
                return None
        else:
            if key == "platform":
                fn = "platforms_by_%s_to__id" % mapping_key
            elif key == "category":
                fn = "categories_by_%s_to__id" % mapping_key
            elif key == "business_model":
                fn = "business_models_by_%s_to__id" % mapping_key
            elif key == "payment_type":
                fn = "payment_types_by_%s_to__id" % mapping_key
            else:
                fn = key + "_by_%s_to__id" % mapping_key
            values = getattr(Property, fn)()
            if isinstance(kwargs[key], (tuple, list)):
                ret = filter(lambda x: x in values, kwargs[key])
                ret = map(lambda x: values[x], kwargs[key])
                if multiple:
                    return ret
                else:
                    return ret[0]
            if kwargs[key] not in values:
                raise ValueError("Invalid code `%s` for property %s." %
                                 kwargs[key], key)
            if multiple:
                return [values[kwargs[key]]]
            else:
                return values[kwargs[key]]
    else:
        return fn()


#---------------------------------------------------------------------
#                   Mocking data generators
#---------------------------------------------------------------------
def Campaign(**kwargs):
    # TODO custom field value by `kwargs`.
    d = {}
    # base advert properties.
    d["name"] = faker.name()
    d["description"] = faker.sentence()
    if "date_start" in kwargs:
        if type(kwargs["date_start"]) is datetime:
            d["date_start"] = kwargs["date_start"]
        elif is_string(kwargs["date_start"]):
            # expected string like `2013-12-19`
            d["date_start"] = datetime.strptime(kwargs["date_start"],
                                                "%Y-%m-%d")
    if "date_start" not in d:
        d["date_start"] = today(utc=True) - timedelta(days=1)
    if "date_end" in kwargs:
        if type(kwargs["date_end"]) is datetime:
            d["date_end"] = kwargs["date_end"]
        elif is_string(kwargs["date_end"]):
            # expected string like `2013-12-19`
            d["date_end"] = datetime.strptime(kwargs["date_end"],
                                              "%Y-%m-%d")
    if "date_end" not in d:
        d["date_end"] = today(utc=True) + timedelta(days=7)
    if d["date_end"] <= d["date_start"]:
        d["date_end"] = d["date_start"] + timedelta(days=7)
    # campaign type.
    d["payment_type"] = set_or_random(kwargs, "payment_type", False,
                                      faker.payment_type)
    d["premium_price"] = kwargs.pop("premium_price",
                                    faker.random_float(0.7, 10.0))
    d["cpc_url"] = faker.url()
    d["cpa_zip"] = "/" + faker.uri_path() + ".zip"  # @TODO generate real things for interactive test.
    d["cpa_url"] = "/" + faker.uri_path()  # @TODO generate real things for interactive test.
    d["show_type"] = faker.show_type()
    d["show_images"] = ["/" + faker.uri_image(bool(kwargs.get("image_size", None)))
                        for i in range(random.randint(3, 5))]
    d["show_text"] = faker.sentence()
    # budget.
    d["budget_type"] = faker.budget_type()
    d["budget_amount"] = float(faker.random_number())
    # targetting
    keys = ("category", "platform", "gender", "business_model")
    for k in keys:
        d[k] = None
    keys = ("areas", "brands", "languages", "time_ranges", "regions",
            "carriers", "ages", "careers")
    for k in keys:
        d[k] = []
    positive = kwargs.get("implicated_target", True)
    if positive or "category" in kwargs:
        d["category"] = set_or_random(kwargs, "category", False,
                                      faker.target_category)
    if positive or "platform" in kwargs:
        d["platform"] = set_or_random(kwargs, "platform", False,
                                      faker.target_platform)
    if positive or "time_ranges" in kwargs:
        d["time_ranges"] = set_or_random(kwargs, "time_ranges", True,
                                         faker.target_time_ranges)
    if positive or "regions" in kwargs:
        upper = random.randint(3, 7)
        d["regions"] = set_or_random(kwargs, "regions", True,
                                     partial(faker.target_regions,
                                             upper=upper), "value")
    if positive or "areas" in kwargs:
        d["areas"] = set_or_random(kwargs, "areas",
                                   True, faker.target_areas, "_id")
    if positive or "brands" in kwargs:
        d["brands"] = set_or_random(kwargs, "brands",
                                    True, faker.target_brands)
    if positive or "languages" in kwargs:
        d["languages"] = set_or_random(kwargs, "languages", True,
                                       faker.target_languages)
    if positive or "business_model" in kwargs:
        d["business_model"] = set_or_random(kwargs, "business_model",
                                            False,
                                            faker.target_business_model)
    if positive or "carriers" in kwargs:
        d["carriers"] = set_or_random(kwargs, "carriers", True,
                                      faker.target_carriers)
    if positive or "genders" in kwargs:
        d["gender"] = set_or_random(kwargs, "genders", False,
                                    faker.target_gender)
    if positive or "ages" in kwargs:
        d["ages"] = set_or_random(kwargs, "ages", True, faker.target_ages)
    if positive or "careers" in kwargs:
        d["careers"] = set_or_random(kwargs, "careers", True,
                                     faker.target_careers)
    return d


def Publisher(**kwargs):
    # TODO custom field value by `kwargs`.
    d = {}
    d["name"] = faker.name()
    d["description"] = faker.sentence()
    d["keyword"] = ", ".join([faker.word() for __ in range(random.randint(0, 4))])
    d["platform"] = set_or_random(kwargs, "platform", False,
                                  faker.target_platform)
    d["categories"] = set_or_random(kwargs, "category", True,
                                    partial(faker.target_categories,
                                            lower=1))
    fn = partial(faker.target_languages, lower=1)
    d["languages"] = set_or_random(kwargs, "languages", True, fn)
    fn = partial(faker.target_business_model, targetting=False)
    d["business_model"] = set_or_random(kwargs, "business_models", False, fn)
    d["target_gender"] = set_or_random(kwargs, "genders", False,
                                       faker.target_gender)
    d["target_ages"] = set_or_random(kwargs, "ages", True,
                                     faker.target_ages)
    d["target_careers"] = set_or_random(kwargs, "careers", True,
                                        faker.target_careers)
    return d


def User(user_type=None, passwd=None, **kwargs):
    user_types = ("advertiser", "developer", "biguser", "admin")
    if user_type is not None and user_type not in user_types:
        user_type = None
    if passwd:
        gen_pwd = lambda: passwd
    else:
        # NOT reliable password generation algorithm, DO NOT USE in reality.
        gen_pwd = lambda: md5sum(urandom(10))
    if user_type:
        gen_user_type = lambda: user_type
    else:
        gen_user_type = lambda: random.choice(user_types)
    d = {
        "email": faker.email(),
        "password": gen_pwd(),
        "user_type": gen_user_type(),
        "user_name": faker.name(),
        "phone_num": faker.phone_number(),
    }
    return d


def APIAdvertShow(publisher=None, **kwargs):
    msg = data_pb2.APIAdvertShow()
    if publisher is None:
        publisher = faker.publisher()
    msg.api_key = publisher["api_key"]
    msg.show_type_value = random.randrange(1, 6)
    kwargs["platform"] = publisher.get("platform")
    d = APIAdvertDeviceInfo(**kwargs)
    d = d.to_dict()
    for k in d:
        setattr(msg.device_info, k, d[k])
    if "date_creation" in kwargs:
        t = kwargs["date_creation"]
    else:
        t = today(utc=True)
    msg.date_creation = datetime_to_timestamp(t) * 1000
    return msg


def APIAdvertDeviceInfo(**kwargs):
    msg = data_pb2.APIAdvertDeviceInfo()
    msg.imei = faker.imei()
    msg.mac_address = faker.mac_address()
    if "ip_range" in kwargs:
        lower, upper = kwargs["ip_range"]
        msg.ip_address = faker.ipv4(lower, upper)
    else:
        # NOTE `ipv4` from Faker is unpredictable, sometime will generated values that broken the test.
        msg.ip_address = "127.0.0.1"
    platform = kwargs.get("platform")
    if isinstance(platform, dict) and "code" in platform:
        platform = platform["code"].lower()
    if platform not in ("ios", "android") or not platform:
        platform = random.choice(("ios", "android"))
    msg.platform = platform
    if msg.platform == "android":
        msg.os_version = random.choice(("1.5", "1.6", "2.0", "2.1", "2.2", "2.3", "3.0", "4.0", "4.1"))
        msg.device_brand = random.choice(("nokia", "samsung", "sharp"))
    elif msg.platform == "ios":
        msg.os_version = random.choice(("3.1.3", "4.2.1", "5.1.1", "6.1.3", "6.1.5", "7.0.4", "7.1 beta2"))
        msg.device_brand = "apple"
    if "longitude" in kwargs:
        msg.longitude = float(kwargs["longitude"])
    else:
        msg.longitude = float(faker.longitude())
    if "latitude" in kwargs:
        msg.latitude = float(kwargs["latitude"])
    else:
        msg.latitude = float(faker.latitude())
    msg.sdk_version = "1.0"  # @FIXME
    msg.imsi = faker.imsi(prefer=kwargs.get("imsi"))
    # TODO new fields.
    return msg
