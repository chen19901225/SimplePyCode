#!/usr/bin/env python
# encoding: utf-8

from functools import partial
from datetime import datetime
from operator import setitem
from itertools import chain
import uuid

from model.data.definition import (
    User, UserType, UserStatus, UserVerification, FinanceLog,
    FinanceLogSource, FinanceLogStatus, FinanceLogOperation,
    PasswordReset, Advert, AdvertStatus,
)
from base import config
from base.utils import (
    to_unicode, u, object_id, md5sum, dict_swap, bulk_up, safe_float,
    RuntimeCache, bulk_object_id, today, as_timezone, to_timezone
)


class _Property(RuntimeCache):
    def _user_types(self, *args, **kwargs):
        return list(UserType.query())

    def _finance_log_sources(self, *args, **kwargs):
        return list(FinanceLogSource.query())

    def _finance_log_statuses(self, *args, **kwargs):
        return list(FinanceLogStatus.query())

    def _finance_log_operations(self, *args, **kwargs):
        return list(FinanceLogOperation.query())

    def _campaign_statuses(self, *args, **kwargs):
        return list(AdvertStatus.query())


Property = _Property()


""" There are some additional collections related to collection `user`:

    - `user_profile`
    - `user_status`
    - `user_type`
    - `user_verification`
    - `user_verification_type`
    - `verification_message`

    This file should cover all methods direct operating on these collections.
"""

#
# User Type
#
# There are four types user:
# - `advertiser`, constant 0
# - `developer`, constant 1
# - `biguser`, constant 2
# - `admin`, constant 3
#
class UserTypeError(ValueError):
    pass


CACHE_USER_TYPES = {}
CACHE_USER_TYPE_CODES = {}

def init_user_type_cache():
    table = {u("advertiser"): "advertiser",
             u("developer"): "developer",
             u("advertiser_massive"): "biguser",
             u("manager"): "admin"}
    if len(CACHE_USER_TYPES) == 0:
        for i in UserType().collection.find():
            alias = to_unicode(table[i["code"]])
            d = {"name": i["name"], "code": i["code"], "_id": str(i["_id"]), "value": int(i["value"]), "alias": alias}
            CACHE_USER_TYPES[i["_id"]] = d
            CACHE_USER_TYPE_CODES[alias] = d


def get_user_type_by_id(user_type_id):
    init_user_type_cache()
    if user_type_id in CACHE_USER_TYPES:
        return CACHE_USER_TYPES[user_type_id]
    return None


def get_user_type_by_code(user_type_code):
    init_user_type_cache()
    user_type_code = to_unicode(user_type_code)
    if user_type_code in CACHE_USER_TYPE_CODES:
        return CACHE_USER_TYPE_CODES[user_type_code]
    return None


def is_valid_user_type(user_type, backward_compact=False):
    if backward_compact:
        # 0 - 广告主，1 - 开发者，2 - 大客户，3 - 管理员
        return user_type in (0, 1, 2, 3, "0", "1", "2", "3", "advertiser", "developer", "biguser", "admin")
    else:
        return user_type in ("advertiser", "developer", "biguser", "admin")


def translate_user_type(user_type):
    if not is_valid_user_type(user_type, True):
        raise UserTypeError("The value: `%s`" % user_type)
    if user_type in ("advertiser", "developer", "biguser", "admin"):
        user_type = {"advertiser": 0, "developer": 1, "biguser": 2, "admin": 3}[user_type]
    return user_type


#
# User Status
#
# There are five statuses for user:
# - `paused`, constant 0
# - `unverified`, constant 1
# - `in_verify`, constant 2
# - `verified`, constant 3
# - `rejected`, contant 4
#

def UserStatusError(ValueError):
    pass


CACHE_USER_STATUSES = {}
CACHE_USER_STATUS_CODES = {}

def init_user_status_cache():
    table = {u("paused"): "paused",
             u("not verified"): "unverified",
             u("verifying"): "in_verify",
             u("verified"): "verified",
             u("rejected"): "rejected",
            }
    if len(CACHE_USER_STATUSES) == 0:
        for i in UserStatus().collection.find():
            CACHE_USER_STATUSES[i["_id"]] = {"name": i["name"], "code": i["code"], "_id": str(i["_id"])}
            code = to_unicode(table[i["code"]])
            CACHE_USER_STATUS_CODES[code] = {"name": i["name"], "code": i["code"], "_id": str(i["_id"])}


def get_user_status_by_id(user_status_id):
    init_user_status_cache()
    if user_status_id in CACHE_USER_STATUSES:
        return CACHE_USER_STATUSES[user_status_id]
    return None


def get_user_status_by_code(user_status_code):
    init_user_status_cache()
    user_status_code = to_unicode(user_status_code)
    if user_status_code in CACHE_USER_STATUS_CODES:
        return CACHE_USER_STATUS_CODES[user_status_code]
    return None


def is_valid_user_status(user_status, backward_compact=False):
    if backward_compact:
        # 0 - 暂停，1 - 未审核，2 - 审核中，3 - 通过审核，4 - 未通过审核
        return user_type in (0, 1, 2, 3, 4, "0", "1", "2", "3", "4", "paused", "unverified", "verifying",
                             "verified", "rejected")
    else:
        return user_type in ("paused", "unverified", "verifying", "verified", "rejected")


def translate_user_status(user_status):
    if not is_valid_user_status(user_status, True):
        raise UserStatusError("The value: `%s`" % user_status)
    if user_status in ("paused", "unverified", "verifying", "verified", "rejected"):
        user_status = {"paused": 0, "unverified": 1, "verifying": 2, "verified": 3, "rejected": 4}[user_status]
    return user_status


#
# User Verification
#

def transform_verification(rec):
    d = {}
    d["_id"] = str(rec["_id"])
    d["company_name"] = rec["company_name"]
    # FIXME: more fields to deal with
    # bank_name, personal_id_number, personal_name, verification_type, personal_id_back_imge, company_license_image, personal_id_front_image, removed, data_creation, bank_account
    return d


#
# User
#
DEFAULT_TRANSFORMER = "python"

@bulk_up
def transform_user(rec, transformer=None):
    if transformer is None:
        transformer = DEFAULT_TRANSFORMER
    ret = map(partial(_transform_user, transformer=transformer), rec)
    ret = dict_swap(ret, _swap, "verification")
    return ret


def _swap(verification):
    verification = map(object_id, filter(lambda v: v, verification))
    __ = UserVerification().find({"_id": {"$in": verification}})
    __ = dict([str(v["_id"]), v] for v in map(transform_verification, __))
    return {"verification": __}


def _transform_user(rec, transformer):
    if "_id" in rec:
        rec["_id"] = to_unicode(str(rec["_id"]))
    if "type" in rec:
        rec["type"] = get_user_type_by_id(rec["type"])


    if rec["type"]["code"] == "advertiser":
        # 广告主统计广告数量
        rec["running_adverts"] = Advert.count(removed=False, user=object_id(rec["_id"]),
                                              status=object_id(Property.campaign_statuses_by_code_to__id()["running"]))
        rec["stopped_adverts"] = Advert.count(removed=False, user=object_id(rec["_id"]),
                                              status=object_id(Property.campaign_statuses_by_code_to__id()["paused"]))
    if "managed_by" in rec and rec["managed_by"]:
        # 获取管理员
        rec["managed_by"] = get_user(_id=object_id(rec["managed_by"]))

    if "status" in rec:
        rec["status"] = get_user_status_by_id(rec["status"])
    if "verification" in rec and rec["verification"] is not None:
        rec["verification"] = str(rec["verification"])
    if "date_creation" in rec:
        # date_creation in timestamp
        rec["ts_date_creation"] = float(rec["date_creation"].strftime("%s")) * 1000
    if transformer == "text":
        if "date_creation" in rec:
            rec["date_creation"] = rec["date_creation"].strftime("%Y-%m-%d %H:%M:%S")
    if "notify_total_balance" in rec:
        rec["notify_total_balance"] = float(rec["notify_total_balance"])
    else:
        rec["notify_total_balance"] = 0.0
    if "notify_daily_balance" in rec:
        rec["notify_daily_balance"] = float(rec["notify_daily_balance"])
    else:
        rec["notify_daily_balance"] = 0.0
    return rec


def add_user(email, password, user_type, user_name, phone_num,
             persist=True, **kwargs):
    # @FIXME Refactor later.
    user_type = translate_user_type(user_type)
    db_obj = User()
    if db_obj.find({"email": email}).count() > 0:
        raise ValueError("Duplicated Email.")
    db_obj["email"] = email
    # @FIXME stronger password encrypt algorithm.
    db_obj['password'] = encrypt_password(password)
    db_obj['type'] = UserType.get_id(value=user_type)
    status_code = kwargs.pop("status", "unverified")
    db_obj['status'] = object_id(get_user_status_by_code(status_code)["_id"])
    db_obj["full_name"] = user_name
    db_obj["phone"] = phone_num
    # optional fields.
    db_obj['balance'] = 0.0
    db_obj['verification'] = None
    db_obj['finance_log'] = []
    db_obj['verification_message'] = []
    db_obj['date_creation'] = datetime.utcnow()
    if persist:
        db_obj.save()
    return db_obj


def get_user(query=None, **kwargs):
    rec = User.get_one(query, **kwargs)
    if rec is None:
        raise ValueError("Query match nothing: %s" % query)
    return rec


def get_user_list(query=None, limit=30, page=1, with_counts=False, **kwargs):
    cursor = User.query(query, **kwargs).sort("date_creation", -1)
    count = cursor.count()
    if page > 1:
        cursor = cursor.skip((page - 1) * limit)
    cursor = cursor.limit(limit)
    if with_counts:
        return list(cursor), count
    return list(cursor)


def mock_user(count=1, user_type=None, passwd=None, save=True):
    """ This functions help generate a large numbers of users.

        DO NOT USE IN PRODUCTION.

    """
    # @NOTE please use `apps.outlet_layer.services.mocking.User` instead.
    users = []
    user_types = ("advertiser", "developer", "biguser", "admin")
    if user_type is not None and user_type not in user_types:
        raise ValueError("Invalid user type: %s" % user_type)
    from faker import Faker
    faker = Faker()
    if passwd:
        gen_pwd = lambda: passwd
    else:
        from os import urandom
        # NOT reliable password generation algorithm, DO NOT USE in reality.
        gen_pwd = lambda: md5sum(urandom(10))
    if user_type:
        gen_user_type = lambda: user_type
    else:
        from random import choice
        gen_user_type = lambda: choice(user_types)

    i = 0
    while i < count:
        try:
            u = {
                "email": faker.email(),
                "password": gen_pwd(),
                "user_type": gen_user_type(),
                "user_name": faker.name(),
                "phone_num": faker.phone_number(),
                "persist": False,
            }
            users.append(add_user(**u))
            i += 1
        except ValueError:
            pass

    if save:
        User().collection.insert(users)
    return users


def search_user(keyword, user_type=None, with_counts=False):
    """ Return a list of users which found keyword in `full_name` or `email`.

        Current we use the simplest solution, based on MongoDB's regex-based collection scan.

        The result only return three fields of user record:
            - `_id`
            - `full_name`
            - `email`
    """
    query = {"$or": [{"email": {"$regex": keyword}}, {"full_name": {"$regex": keyword}}]}
    query["removed"] = False
    if user_type is not None:
        query["type"] = UserType.get_id(value=translate_user_type(user_type))
    cursor = User().collection.find(query, fields={"full_name": 1, "email": 1, "type": 1})
    fetch = lambda x: map(transform_user, x.limit(20).to_array())
    if with_counts:
        total = cursor.count()
        return fetch(cursor), total
    else:
        return fetch(cursor)


def has_user(query=None, **kwargs):
    if "user_type" in kwargs:
        kwargs["type"] = object_id(get_user_type_by_code(kwargs["user_type"])["_id"])
        del kwargs["user_type"]
    return User.exists(query, **kwargs)


def set_notify_check(user, **kwargs):
    d = {}
    daily_balance = safe_float(kwargs.pop("daily_balance", 0))
    if daily_balance > 0:
        d["notify_daily_balance"] = daily_balance
    total_balance = safe_float(kwargs.pop("total_balance", 0))
    if total_balance > 0:
        d["notify_total_balance"] = total_balance
    if d:
        User.update({"_id": object_id(user["_id"])},
                    {"$set": d})


def get_withdrawal_log(user_ids=None, user_type=None, **kwargs):
    # NOTE because it is complex query, paging should go into here.
    # http://stackoverflow.com/a/15224544
    cond = {"finance_log.0": {"$exists": True}, "removed": False}
    if user_ids:
        if not isinstance(user_ids, (list, tuple)):
            user_ids = (user_ids, )
        user_ids = bulk_object_id(user_ids)
        cond["_id"] = {"$in": user_ids}
    if user_type:
        types = Property.user_types_by_code_to__id()
        if user_type in types:
            cond["type"] = object_id(types[user_type])
    __ = User.query(cond, fields={"finance_log": 1})
    mapping = ([(j, i["_id"]) for j in i["finance_log"]] for i in __)
    mapping = dict(chain(*mapping))
    query_grarms = {"_id": {"$in": mapping.keys()}}
    date_start = kwargs.pop("date_start", '')
    date_end = kwargs.pop("date_end", '')
    if date_start and date_end:
        query_grarms["date_creation"]= {"$gte": date_start, "$lt": date_end}
    cursor = FinanceLog.query(query_grarms)
    # TODO paging
    return transform_finance_log([setitem(i, "user", mapping[i["_id"]]) or i
                                  for i in cursor])


@bulk_up
def transform_finance_log(lst):
    lst = map(_transform_finance_log, lst)
    lst = dict_swap(lst, _transform_finance_log_swap, "user", "source",
                    "status", "operation")
    return lst


def _transform_finance_log(d):
    nd = {}
    if "_id" in d:
        nd["_id"] = d["_id"]
    if "user" in d:
        nd["user"] = str(d["user"])
    if "users" in d:
        nd["users"] = d["users"]
    if "source" in d:
        nd["source"] = str(d["source"])
    if "status" in d:
        nd["status"] = str(d["status"])
    if "operation" in d:
        nd["operation"] = str(d["operation"])
    if "amount" in d:
        nd["amount"] = d["amount"]
    if "tax" in d:
        nd["tax"] = d["tax"]
    if "title" in d:
        nd["title"] = to_unicode(d["title"])
    if "date_creation" in d:
        nd["date_creation"] = d["date_creation"]
    if "checktime" in d:
        nd["checktime"] = d["checktime"]
    return nd


def _transform_finance_log_swap(user, source, status, operation):
    users = {}
    if user:
        users = map(lambda x: (str(x["_id"]), x),
                    User.query({"_id": {"$in": bulk_object_id(user)}}))
        users = dict(users)
    return {
        "user": users,
        "source": Property.finance_log_sources_by__id(),
        "status": Property.finance_log_statuses_by__id(),
        "operation": Property.finance_log_operations_by__id(),
    }


def generate_password_reset_url(user):
    token = uuid.uuid4().hex
    url = "%s/reset?token=%s" % (config.get("api.static_url"), token)
    uid = object_id(user["_id"])
    cursor = PasswordReset.query({"user": uid, "exhausted": False})
    if cursor.count() > 0:
        PasswordReset.update({"user": uid}, {"$set": {"exhausted": True}})
    rec = PasswordReset()
    rec["user"] = uid
    rec["exhausted"] = False
    rec["token"] = token
    rec["date_creation"] = today()
    rec.save()
    return url


def check_password_reset_token(token):
    rec = PasswordReset.get_one({"token": token, "exhausted": False})
    if rec:
        created_at = as_timezone(rec["date_creation"], "UTC")
        elapsed = today() - created_at
        if elapsed.total_seconds() >= 3600 * 72:
            rec["exhausted"] = True
            rec.save()
            return False
        return True
    return False


def reset_password(token, password):
    rec = PasswordReset.get_one(token=token)
    PasswordReset.update({"token": token},
                         {"$set": {"exhausted": True}})
    pwd = encrypt_password(password)
    User.update({"_id": object_id(rec["user"])},
                {"$set": {"password": pwd}})
    u = User.get_one(rec["user"])
    u = transform_user(u)
    code = u["type"]["code"]
    if code in ("advertiser", "advertiser_massive", "biguser"):
        return "/login"
    elif code in ("admin", "manager"):
        return "/admin_login"
    elif code == "developer":
        return "/dev/login"


def encrypt_password(pwd):
    return md5sum(pwd)
