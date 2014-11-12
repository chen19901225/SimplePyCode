#!/usr/bin/env python
# encoding: utf-8

from __future__ import division, absolute_import
from functools import partial
from itertools import imap, groupby, chain
from datetime import timedelta, datetime
from time import time

try:
    from cdecimal import Decimal
except:
    from decimal import Decimal

from base.utils import (
    should_be_list, dict_swap, isorted, object_id, native_str, bulk_up,
    today, to_timezone, as_timezone, get_default_timezone, bulk_object_id,
    set_default_timezone,
)
from model.data.definition import (
    TrackLog, TrackLogType, Advert, AdvertType, PaymentType, App,
    AdvertLevelLog, ReportAdvertLog, ReportAdvertLogEdit, ReportAppLog,ReportAppLogDetail, ReportPlatformLog, PeriodicalAppLog, PeriodicalAdvertLog, PeriodicalPlatformLog,
    PeriodicalOfferWallAdvertLogHour, PeriodicalOfferWallAppLogHour
)
from proto import data_pb2
from .campaign import Property

TZ_ASIA_SHANGHAI = timedelta(hours=8)


def sorted_groupby(lst, key_name):
    if hasattr(key_name, "__call__"):
        k = key_name
    else:
        k = lambda x: x[key_name]
    return groupby(sorted(lst, key=k), k)


# --------------------------------------------------------------------
# Transform advert records for aggregating. After transform, record
# should looks like:
#
# {
#   _id: "32d34007-7464-11e3-98ed-c82a1415e45d",
#   payment_type: "CPA",
#   price: Decimal(0),
#   show_type: "banner_word+icon"
# }
#
# The `payment_type` should one of follow: `CPM`, `CPC`, `CPA`.
#
# The `show_type` should be one of follows: `banner_word+icon`,
# `banner_image_static`, `banner_image_dynamic`, `full_screen`,
# `popup`.
# --------------------------------------------------------------------
def _transform_advert(d):
    nd = {}
    if "_id" in d:
        nd["_id"] = str(d["_id"])
    if "payment_type" in d:
        nd["payment_type"] = str(d["payment_type"])
    if "premium_price" in d:
        nd["price"] = Decimal(d["premium_price"])
    else:
        nd["price"] = Decimal(0)
    if "show_type" in d:
        nd["show_type"] = str(d["show_type"])
    if "user" in d:
        nd["user"] = str(d["user"])
    return nd


def _swap_advert(**swap):
    return {
        "payment_type": Property.payment_types_by__id_to_code(),
        "show_type": Property.show_types_by__id_to_code(),
    }


@bulk_up
def transform_advert(lst):
    lst = map(_transform_advert, lst)
    lst = dict_swap(lst, _swap_advert, "payment_type", "show_type")
    return lst


# --------------------------------------------------------------------
# Transform app records for aggregating. After transform, record
# should looks like:
#
# {
#   _id: "32d34007-7464-11e3-98ed-c82a1415e45d",
#   user: "32d34007-7464-11e3-98ed-c82a1415e45d",
#   cpm: {
#     developer: 0.15,
#     total: 0.5
#   },
#   cpc: {
#     developer: 0.15,
#     total: 0.5
#   },
#   cpa: {
#     developer: 0.15,
#     total: 0.5
#   }
# }
# --------------------------------------------------------------------
def _transform_app(d):
    nd = {}
    if "_id" in d:
        nd["_id"] = str(d["_id"])
    if "user" in d:
        nd["user"] = str(d["user"])
    if "level_log" in d:
        nd["levels"] = map(str, d["level_log"])
    return nd


def _swap_app(**swap):
    levels = list(chain(*swap.get("levels", [])))
    if levels:
        levels = bulk_object_id(levels)
        levels = AdvertLevelLog.query({"_id": {"$in": levels}})
        levels = dict([(str(d["_id"]), d) for d in levels])
    return {"levels": levels}


@bulk_up
def transform_app(lst):
    lst = map(_transform_app, lst)
    lst = dict_swap(lst, _swap_app, "levels")
    payment_types = Property.payment_types_by__id_to_code()
    defaults = {
        "cpm": Property.cpm_levels(raw=True),
        "cpc": Property.cpc_levels(raw=True),
        "cpa": Property.cpa_levels(raw=True),
    }
    for d in lst:
        levels = d.pop("levels", [])
        # When AdvertLevelLog record for App record has exists.
        #
        # NOTE Decimal(3.14) will get result like
        # Decimal('3.140000000000000124344978758017532527446746826171875')
        # so we transform to str first than wrap into Decimal.
        for lvl in levels:
            name = payment_types[str(lvl["payment_type"])]
            d[name] = {"sharing": Decimal(str(lvl["developer"])),
                       "base": Decimal(str(lvl["total"]))}
        # Fill default AdvertLevel for App.
        for k in ("cpm", "cpc", "cpa"):
            if k not in d:
                # TODO Should not this case.
                d[k] = defaults[k][-1].copy()
                d[k]["variable"] = 0.0
                d[k]["sharing"] = Decimal(str(d[k]["developer"]))
                d[k]["base"] = Decimal(str(d[k]["total"]))
    return lst


# --------------------------------------------------------------------
# Transform track log records for aggregating. After transform, record
# should looks like:
#
# {
#   _id: "32d34007-7464-11e3-98ed-c82a1415e45d",
#   action: 'click',
#   advert: [Advert Record after transform],
#   date_creation: datetime.datetime()
# }
# --------------------------------------------------------------------
def _transform_track_log(d):
    nd = {}
    if "_id" in d:
        nd["_id"] = str(d["_id"])
    if "date_creation" in d:
        nd["date_creation"] = to_timezone(as_timezone(d["date_creation"], "UTC"))
    if "type" in d:
        nd["action"] = str(d["type"])
    if "app" in d:
        nd["app"] = str(d["app"])
    if "advert" in d:
        nd["advert"] = str(d["advert"])
    return nd


def _swap_track_log(**swap):
    ids = bulk_object_id(Set(swap.get("app", [])))
    apps = list(App.query({"_id": {"$in": ids}}))
    apps = transform_app(apps)
    ids = bulk_object_id(Set(swap.get("advert", [])))
    adverts = list(Advert.query({"_id": {"$in": ids}}))
    adverts = transform_advert(adverts)
    log_types = list(TrackLogType().find())
    log_types = dict([(str(x["_id"]), native_str(x["code"]))
                      for x in log_types])
    f = lambda x: dict([(str(y["_id"]), y) for y in x])
    return {
        "action": log_types,
        "app": f(apps),
        "advert": f(adverts),
    }


@bulk_up
def transform_track_log(lst):
    lst = map(_transform_track_log, lst)
    lst = dict_swap(lst, _swap_track_log, "action", "app", "advert")
    return lst


# --------------------------------------------------------------------
#           Aggregator.
# --------------------------------------------------------------------
k_payment_type = lambda x: x["advert"]["payment_type"]
k_show_type = lambda x: x["advert"]["show_type"]
k_advert = lambda x: x["advert"]["_id"]
k_app = lambda x: x["app"]["_id"]


def count_action(action_code, lst):
    return len(filter(lambda x: x["action"] == action_code, lst))


def safe_rate(x, y):
    if x > 0 and y > 0:
        return round(x / y, 4)
    return 0


def parse_date_str(s, tz=None):
    try:
        return as_timezone(datetime.strptime(s, "%Y-%m-%d"))
    except Exception, err:
        #print err
        return None


def rotate_daily(lst, key="date_creation"):
    fn = lambda x: (x[key] + TZ_ASIA_SHANGHAI).strftime("%Y-%m-%d")
    return sorted_groupby(lst, fn)


def meaningful_float(i):
    if type(i) is not Decimal:
        try:
            i = Decimal(str(i))
        except Exception, err:
            print i
            raise err
    return float(i.quantize(Decimal(".01")))


def summarize_advert(advert, logs, base=None):
    d = {}
    d["requests"] = Decimal(count_action("request", logs))
    d["impressions"] = Decimal(count_action("show", logs))
    d["clicks"] = Decimal(count_action("click", logs))
    d["actions"] = Decimal(count_action("action", logs))
    if base is None:
        base = advert["price"]
    base = Decimal(str(base))
    if advert["payment_type"] == "cpm":
        d["balance"] = d["impressions"] / Decimal(1000) * base
    elif advert["payment_type"] == "cpc":
        d["balance"] = d["clicks"] * base
    elif advert["payment_type"] == "cpa":
        d["balance"] = d["actions"] * base
    return d


def aggregate_report_by_campaign(logs, fn_base):
    for app_id, lst1 in sorted_groupby(logs, k_app):
        lst1 = list(lst1)
        app = lst1[0]["app"]
        for advert_id, lst2 in sorted_groupby(lst1, k_advert):
            lst2 = list(lst2)
            advert = lst2[0]["advert"]
            if advert["payment_type"] in ("cpm", "cpc", "cpa"):
                base = fn_base(advert, app)
            else:
                raise ValueError("Unexpected payment type %s."
                                 % payment_type)
            yield (summarize_advert(advert, lst2, base), advert, app)


def aggregate_report_advert(logs):
    ret = []
    for __, lst in sorted_groupby(logs, k_advert):
        lst = list(lst)
        advert = lst[0]["advert"]
        report = summarize_advert(advert, lst)
        report["type"] = advert["payment_type"]
        ret.append((__, report))
    return ret


def aggregate_report_app(logs):
    fn = lambda advert, app: app[advert["payment_type"]]["sharing"]
    lst = []
    for (report, advert, app) in aggregate_report_by_campaign(logs, fn):
        lst.append((app["_id"], advert["payment_type"], report))
    ret = []
    for app_id, group in sorted_groupby(lst, lambda x: x[0]):
        group = list(group)
        report = {}
        report["requests"] = sum(i[-1]["requests"] for i in group)
        report["impressions"] = sum(i[-1]["impressions"] for i in group)
        report["clicks"] = sum(i[-1]["clicks"] for i in group)
        report["actions"] = sum(i[-1]["actions"] for i in group)
        report["cpm_balance"] = sum(i[-1]["balance"] for i in group if i[1] == "cpm")
        report["cpc_balance"] = sum(i[-1]["balance"] for i in group if i[1] == "cpc")
        report["cpa_balance"] = sum(i[-1]["balance"] for i in group if i[1] == "cpa")
        report["balance"] = report["cpm_balance"] + report["cpc_balance"] + report["cpa_balance"]
        ret.append((app_id, report))
    return ret


def aggregate_report_platform(logs):
    fn = lambda ad, app: ad["price"] - app[ad["payment_type"]]["sharing"]
    lst = []
    for (report, advert, app) in aggregate_report_by_campaign(logs, fn):
        lst.append((advert["payment_type"], report))
        lst.append((advert["show_type"], report))
    ret = []
    for key, group in sorted_groupby(lst, lambda x: x[0]):
        group, report = list(group), {}
        for k in group[0][1]:
            if not isinstance(group[0][1][k], Decimal):
                # Simple pass through first value is ok?
                report[k] = group[0][1][k]
                continue
            report[k] = sum(map(lambda x: x[1][k], group))
        ret.append((key, report))
    return ret


def aggregate_all(logs, date_start, date_end, buffer_only=False):
    ret = []
    # --------------------
    # Platform Report
    buffers = []
    total = ReportPlatformLog()
    total["date_start"] = date_start
    total["date_end"] = date_end
    total["group_name"] = "total"
    total["requests"] = []
    total["impressions"] = []
    total["clicks"] = []
    total["actions"] = []
    total["revenue"] = []
    for (group_name, report) in aggregate_report_platform(logs):
        d = ReportPlatformLog()
        d["date_start"] = date_start
        d["date_end"] = date_end
        d["group_name"] = group_name
        d["requests"] = int(report["requests"])
        d["impressions"] = int(report["impressions"])
        d["clicks"] = int(report["clicks"])
        d["actions"] = int(report["actions"])
        d["revenue"] = meaningful_float(report["balance"])
        if group_name in ("cpm", "cpc", "cpa"):
            total["requests"].append(report["requests"])
            total["impressions"].append(report["impressions"])
            total["clicks"].append(report["clicks"])
            total["actions"].append(report["actions"])
            total["revenue"].append(report["balance"])
        buffers.append(d)
    total["requests"] = int(sum(total["requests"]))
    total["impressions"] = int(sum(total["impressions"]))
    total["clicks"] = int(sum(total["clicks"]))
    total["actions"] = int(sum(total["actions"]))
    total["revenue"] = meaningful_float(sum(total["revenue"]))
    buffers.append(total)
    # @TODO upsert mode?
    if buffer_only:
        ret.append(buffers)
    else:
        ReportPlatformLog().collection.insert(buffers)
    # --------------------
    # Advert Report
    buffers = []
    for (advert_id, report) in aggregate_report_advert(logs):
        d = ReportAdvertLog()
        d["advert"] = object_id(advert_id)
        d["date_start"] = date_start
        d["date_end"] = date_end
        d["number_request"] = int(report["requests"])
        d["number_show"] = int(report["impressions"])
        d["number_click"] = int(report["clicks"])
        d["number_action"] = int(report["actions"])
        d["cost_show"] = d["cost_click"] = d["cost_action"] = d["cost_total"] = 0.0
        balance = meaningful_float(report["balance"])
        if report["type"] == "cpm":
            d["cost_show"] = d["cost_total"] = float(balance)
        elif report["type"] == "cpc":
            d["cost_click"] = d["cost_total"] = float(balance)
        elif report["type"] == "cpa":
            d["cost_action"] = d["cost_total"] = float(balance)
        buffers.append(d)
    # @TODO upsert mode?
    if buffer_only:
        ret.append(buffers)
    else:
        ReportAdvertLog().collection.insert(buffers)
    # --------------------
    # App Report
    buffers = []
    for (app_id, report) in aggregate_report_app(logs):
        d = ReportAppLog()
        d["app"] = object_id(app_id)
        d["date_start"] = date_start
        d["date_end"] = date_end
        d["number_request"] = int(report["requests"])
        d["number_show"] = int(report["impressions"])
        d["number_click"] = int(report["clicks"])
        d["number_action"] = int(report["actions"])
        d["cost_total"] = meaningful_float(report["balance"])
        d["cost_show"] = meaningful_float(report["cpm_balance"])
        d["cost_click"] = meaningful_float(report["cpc_balance"])
        d["cost_action"] = meaningful_float(report["cpa_balance"])
        buffers.append(d)
    # @TODO upsert mode?
    if buffer_only:
        ret.append(buffers)
    else:
        ReportAppLog().collection.insert(buffers)
    return ret


def reaggregate_all():
    """ This function is use for rebuild all ReportAdvertLog,
        ReportAppLog, and ReportPlatformLog by daily, using all TrackLog
        in database.

        When record amount can not fit in memory, this function will be
        crash.
    """
    set_default_timezone("Asia/Shanghai")
    ReportPlatformLog.remove()
    ReportAppLog.remove()
    ReportAdvertLog.remove()
    logs = TrackLog.query().sort("date_creation", 1)
    logs = transform_track_log(list(logs))
    k_fn = lambda x: x["date_creation"].strftime("%Y-%m-%d")
    stats = []
    for date_str, lst in groupby(logs, k_fn):
        lst = list(lst)
        d = parse_date_str(date_str, "Asia/Shanghai") + timedelta(hours=8)
        aggregate_all(lst, d, d + timedelta(days=1))
        stats.append((date_str, len(lst)))
    return stats


def transform_report_to_protobuf(wrapper, date_str, lst):
    message = wrapper()
    message.date = date_str
    for i in lst:
        message.number_request += i["number_request"]
        message.number_show += i["number_show"]
        message.number_click += i["number_click"]
        message.number_action += i["number_action"]
        message.cost_click += i["cost_click"]
        message.cost_show += i["cost_show"]
        message.cost_action += i["cost_action"]
    message.percentage_click = 0
    message.percentage_action = 0
    if message.number_show > 0:
        message.percentage_click = round(message.number_click * 1.0 / message.number_show * 100, 2)
    if message.number_action > 0:
        message.percentage_action = round(message.number_action * 1.0 / message.number_click * 100, 2)
    message.cost_total = message.cost_click + message.cost_show + message.cost_action
    return message


def transform_date_range(fn):
    """ This function ONLY use as decorator for report access functions.
    """
    def _wrap_in_transform_date_range(*args, **kwargs):
        # `date_start` and `date_end` are both optional. By default,
        # Last 7 days' report will return.
        date_end = kwargs.pop("date_end", None)
        date_start = kwargs.pop("date_start", None)
        if date_end is not None:
            date_end = parse_date_str(date_end)
        if date_end is None:
            date_end = today(zero_time=True)
        if date_start is not None:
            date_start = parse_date_str(date_start)
        if date_start is None:
            date_start = date_end - timedelta(days=7)
        kwargs["date_start"] = date_start
        kwargs["date_end"] = date_end
        # real time mode: pre-process real-time mode data.
        day = today(zero_time=True)
        real_time = kwargs.pop("real_time", False)
        if real_time and date_end == day:
            for_now = today()
            kwargs["buffers"] = _aggregate_track_log(day, for_now)
        return fn(*args, **kwargs)
    return _wrap_in_transform_date_range


def _aggregate_track_log(day, for_now):
    platform_logs = list(PeriodicalPlatformLog.query({'date_start': {"$gte": day, "$lte": for_now}}).sort("date_end", -1))
    advert_logs = list(PeriodicalAdvertLog.query({'date_start': {"$gte": day, "$lte": for_now}}))
    app_logs = list(PeriodicalAppLog.query({'date_start': {"$gte": day, "$lte": for_now}}))

#    last_time = day
#    if len(platform_logs) > 0:
#        last_time = to_timezone(as_timezone(platform_logs[0]['date_end'], "UTC"))

#    logs = TrackLog.query({"date_creation": {"$gte": last_time}})
#    logs = transform_track_log(list(logs))
#    buffers = aggregate_all(logs, day, day + timedelta(days=1),
#            buffer_only=True)

#    buffers[0].extend(platform_logs)
#    buffers[1].extend(advert_logs)
#    buffers[2].extend(app_logs)

    buffers = [platform_logs, advert_logs, app_logs]

    return buffers


def transform_platform_finance_report(d, default_group_name):
    nd = {"group_name": default_group_name, "revenue": 0.0}
    if d["group_name"]:
        nd["group_name"] = d["group_name"]
    if d["revenue"] is not None:
        nd["revenue"] = d.get("revenue")
    return nd


@transform_date_range
def get_platform_finance_report(date_start, date_end, **kwargs):
    keys = ("cpm", "cpc", "cpa", "banner_word+icon",
            "banner_image_static", "banner_image_dynamic",
            "full_screen", "popup", "total")
    reports = ReportPlatformLog.query({"date_start": {
        "$gte": date_start, "$lt": date_end}})
    reports.sort("date_start", 1)
    fn = lambda x: to_timezone(as_timezone(x, "UTC"), "Asia/Shanghai").strftime("%Y-%m-%d")
    lst = [(fn(i["date_start"]), i) for i in reports]
    exists = map(lambda x: x[0], lst)
    buffers = kwargs.pop("buffers", None)
    if buffers:
        buffers, __, __ = buffers
        lst.extend([(fn(b["date_start"]), b)
                    for b in buffers])
        exists.append(fn(buffers[0]["date_start"]))
    exists = tuple(exists)
    __ = date_start
    while __ <= date_end:
        date_str = __.strftime("%Y-%m-%d")
        if date_str not in exists:
            for k in keys:
                d = transform_platform_finance_report(
                    ReportPlatformLog(), k)
                lst.append((date_str, d))
        __ = __ + timedelta(days=1)
    lst.sort()
    # group by date
    data = []
    defaults = dict(((k, 0) for k in keys))
    for date_str, g in groupby(lst, lambda x: x[0]):
        d = defaults.copy()
        for (__, x) in g:
            k = x["group_name"]
            d[k] = d.get(k, 0.0) + x["revenue"]
            d["date"] = d["dates"] = __
        data.append(d)
    return {"date_start": date_start, "date_end": date_end, "data": data}


@transform_date_range
def get_campaign_report(ids, date_start, date_end, **kwargs):
    date_end += timedelta(days=1) -timedelta(seconds=1)
    is_admin = kwargs.pop("admin", False)
    query = {"date_start": {"$gte": date_start, "$lt": date_end}}
    reports = []
    if ids:
        query["advert"] = {"$in": bulk_object_id(ids)}

    if is_admin or ids:
        reports = ReportAdvertLog.query(query)
        reports.sort("date_start", 1)
        buffers = kwargs.pop("buffers", None)
        if buffers:
            buffers = buffers[1]
            if ids:
                buffers = filter(lambda x: object_id(x["advert"]) in ids, buffers)
            reports = chain(reports, buffers)

    lst, exists = [], []
    f = lambda x: to_timezone(as_timezone(x["date_start"], "UTC"), "Asia/Shanghai").strftime("%Y-%m-%d")
    for key, l in groupby(reports, f):
        l = list(l)
        lst.append((key, transform_report_to_protobuf(
            data_pb2.AdvertReport, key, l)))
        exists.append(key)
    exists = tuple(exists)
    __ = date_start
    while __ <= date_end:
        date_str = __.strftime("%Y-%m-%d")
        if date_str not in exists:
            x = data_pb2.AdvertReport()
            x.date = date_str
            lst.append((date_str, x))
        __ = __ + timedelta(days=1)
    lst.sort()
    return {"date_start": date_start, "date_end": date_end,
            "data": [i[1] for i in lst]}


@transform_date_range
def get_publisher_report(ids, date_start, date_end, **kwargs):
    date_end += timedelta(days=1) -timedelta(seconds=1)
    is_admin = kwargs.pop("admin", False)
    query = {"date_start": {"$gte": date_start, "$lt": date_end}}
    reports = []
    if ids:
        query["app"] = {"$in": bulk_object_id(ids)}

    if is_admin or ids:
        reports = ReportAppLog.query(query)
        reports.sort("date_start", 1)
        buffers = kwargs.pop("buffers", None)
        if buffers:
            buffers = buffers[2]
            if ids:
                buffers = filter(lambda x: object_id(x["app"]) in ids, buffers)
            reports = chain(reports, buffers)

    lst, exists = [], []
    f = lambda x: to_timezone(as_timezone(x["date_start"], "UTC"), "Asia/Shanghai").strftime("%Y-%m-%d")
    for key, l in groupby(reports, f):
        lst.append((key, transform_report_to_protobuf(
            data_pb2.AppReport, key, l)))
        exists.append(key)
    exists = tuple(exists)
    __ = date_start
    while __ <= date_end:
        date_str = __.strftime("%Y-%m-%d")
        if date_str not in exists:
            x = data_pb2.AppReport()
            x.date = date_str
            lst.append((date_str, x))
        __ = __ + timedelta(days=1)
    lst.sort()
    return {"date_start": date_start, "date_end": date_end,
            "data": [i[1] for i in lst]}


def get_publisher_report_for_excel(ids, date_start, date_end, **kwargs):
    #生成每一个的数据并统计平均值
    date_end += timedelta(days=1) -timedelta(seconds=1)
    querybase = {"date_start": {"$gte": date_start, "$lt": date_end}}
    datas = {}
    for id in ids:
        querybase["app"] =object_id(id)
        reports = [dict(i) for i in ReportAppLog.query(querybase).sort("date_start", 1)]
        daycounts =len(reports)
        all_req,all_show,all_click,all_click_income,all_show_income,all_cpa_income,all_income = 0,0,0,0,0,0,0
        advert_details = {
            'open_screen': {'show_req': 0, 'show': 0, 'req': 0, 'click_show': 0, 'click_cost': 0, 'click': 0},
            'popup': {'show_req': 0, 'show': 0, 'req': 0, 'click_show': 0, 'click_cost': 0, 'click': 0},
            'Banner': {'show_req': 0, 'show': 0, 'req': 0, 'click_show': 0, 'click_cost': 0, 'click': 0},
            'full_screen': {'show_req': 0, 'show': 0, 'req': 0, 'click_show': 0, 'click_cost': 0, 'click': 0}
        }

        lst = []
        f = lambda x: to_timezone(as_timezone(x["date_start"], "UTC"), "Asia/Shanghai").strftime("%Y-%m-%d")
        for key, l in groupby(reports, f):
            l = list(l)
            report = l[0]
            for r in l[1:]:
                report['number_request'] += r['number_request']
                report['number_show'] += r['number_show']
                report['number_click'] += r['number_click']
                report['cost_click'] += r['cost_click']
                report['cost_show'] += r['cost_show']
                report['cost_action'] += r['cost_action']
                report['cost_total'] += r['cost_total']
            lst.append(report)
        reports = lst

        for report in reports:
            all_req +=report['number_request']
            all_show +=report['number_show']
            all_click +=report['number_click']
            all_click_income +=report['cost_click']
            all_show_income +=report['cost_show']
            all_cpa_income +=report['cost_action']
            all_income +=report['cost_total']
            #按广告类型
            query = {"date_start": {"$gte": report['date_start'], "$lt": report['date_end']},'app':object_id(id)}
            details = ReportAppLogDetail.query(query,fields={'number_request':True,'number_show':True,'number_click':True,'cost_click':True,'show_type':True}).sort("date_start", 1)
            f = lambda x: x['show_type']
            infos = {'Banner':{'req':0,'show':0,'click':0,'click_cost':0},'popup':{'req':0,'show':0,'click':0,'click_cost':0},'full_screen':{'req':0,'show':0,'click':0,'click_cost':0},'open_screen':{'req':0,'show':0,'click':0,'click_cost':0}}
            for showtype, l in sorted_groupby(list(details), f):
                info = {'req':0,'show':0,'click':0,'click_cost':0}
                if 'banner' in showtype:
                    showtype = 'Banner'
                    if 'Banner' in infos:
                        info = infos['Banner']
                for i in l:
                    info['req'] += i["number_request"]
                    info['show'] += i["number_show"]
                    info['click'] += i["number_click"]
                    info['click_cost'] += i["cost_click"]
                infos[showtype] =info
            for showtype in infos:
                advert_details[showtype]['req']+=infos[showtype]['req']
                advert_details[showtype]['show']+=infos[showtype]['show']
                advert_details[showtype]['click']+=infos[showtype]['click']
                advert_details[showtype]['click_cost']+=infos[showtype]['click_cost']
                infos[showtype]['show_req'] = infos[showtype]['req'] and infos[showtype]['show']/infos[showtype]['req'] or 0
                infos[showtype]['click_show'] = infos[showtype]['show'] and infos[showtype]['click']/infos[showtype]['show'] or 0
                report[showtype] = infos[showtype]
            report['show_req'] = report['number_request'] and report['number_show']/report['number_request'] or 0
            report['click_show'] = report['number_show'] and report['number_click']/report['number_show'] or 0
        tmpdict = {}
        tmpdict['Banner'] = {}
        tmpdict['popup'] = {}
        tmpdict['full_screen'] = {}
        tmpdict['open_screen'] = {}
        for showtype in advert_details:
            advert_details[showtype]['show_req'] = advert_details[showtype]['req'] and advert_details[showtype]['show']/advert_details[showtype]['req'] or 0
            advert_details[showtype]['click_show'] = advert_details[showtype]['show'] and advert_details[showtype]['click']/advert_details[showtype]['show'] or 0
            tmpdict[showtype] = advert_details[showtype]
        tmpdict['dayscount'] =daycounts *1.0
        tmpdict['logs'] =reports
        tmpdict['all_req'] =all_req
        tmpdict['all_show'] =all_show
        tmpdict['all_click'] =all_click
        tmpdict['all_click_income'] =all_click_income
        tmpdict['all_show_income'] =all_show_income
        tmpdict['all_cpa_income'] =all_cpa_income
        tmpdict['all_income'] =all_income
        tmpdict['avg_req'] =daycounts and all_req/daycounts or 0
        tmpdict['avg_show'] =daycounts and all_show/daycounts or 0
        tmpdict['show_req'] = tmpdict['avg_req'] and tmpdict['avg_show']/tmpdict['avg_req'] or 0
        tmpdict['avg_click'] =daycounts and all_click/daycounts or 0
        tmpdict['click_show'] =tmpdict['avg_show'] and tmpdict['avg_click']/tmpdict['avg_show'] or 0
        tmpdict['avg_income'] =daycounts and all_income/daycounts or 0
        datas[id] = tmpdict
    return datas



def upsert_report_by_day(date_start):
    timer = [("start", time())]
    one_day = timedelta(days=1)
    date_end = date_start + one_day
    scope = {"date_creation": {"$gte": date_start, "$lt": date_end}}
    cursor = TrackLog.query(scope)
    count = cursor.count()
    logs = transform_track_log(list(cursor))
    timer.append(("retrieved", time()))
    buffers = aggregate_all(logs, date_start, date_end, True)
    timer.append(("aggreated", time()))
    counts = map(len, buffers)
    inserted, __ = [], []
    for rec in buffers[0]:
        if rec.insertIfNotExists(["group_name", "date_start", "date_end"]):
            __.append(rec["_id"])
    inserted.append(__)
    __ = []
    for rec in buffers[1]:
        if rec.insertIfNotExists(["advert", "date_start", "date_end"]):
            __.append(rec["_id"])
    inserted.append(__)
    __ = []
    for rec in buffers[2]:
        if rec.insertIfNotExists(["app", "date_start", "date_end"]):
            __.append(rec["_id"])
    inserted.append(__)
    timer.append(("saved", time()))
    return {"timer": timer, "platforms": counts[0], "adverts": counts[1],
            "apps": counts[2], "raw": count, "date": date_start, "inserted": inserted}


def has_generated_report(date_start):
    conds = {
        "date_start": date_start,
        "date_end": date_start + timedelta(days=1),
    }
    c1 = ReportPlatformLog.query(conds).count()
    c2 = ReportAdvertLog.query(conds).count()
    c3 = ReportAppLog.query(conds).count()
    if c1 > 1 and c2 > 0 and c3 > 0:
        return True
    return False


def has_generated_period_report(start_time, end_time):
    conds = {
        "date_start": start_time,
        "date_end": end_time,
    }
    c1 = PeriodicalPlatformLog.query(conds).count()
    c2 = PeriodicalAdvertLog.query(conds).count()
    c3 = PeriodicalAppLog.query(conds).count()
    if c1 > 0 and c2 > 0 and c3 > 0:
        return True
    return False

def upsert_report_by_period(start_time, end_time):
    timer = [("start", time())]
    scope = {"date_creation": {"$gte": start_time, "$lt": end_time}}
    cursor = TrackLog.query(scope)
    logs = transform_track_log(list(cursor))
    timer.append(("retrieved", time()))
    buffers = aggregate_all(logs, start_time, end_time, True)
    timer.append(("aggreated", time()))
    counts = map(len, buffers)
    inserted, __ = [], []
    for rec in buffers[0]:
        rec = PeriodicalPlatformLog(rec)
        if rec.insertIfNotExists(["group_name", "date_start", "date_end"]):
            __.append(rec["_id"])
    inserted.append(__)
    __ = []
    for rec in buffers[1]:
        rec = PeriodicalAdvertLog(rec)
        if rec.insertIfNotExists(["advert", "date_start", "date_end"]):
            __.append(rec["_id"])
    inserted.append(__)
    __ = []
    for rec in buffers[2]:
        rec = PeriodicalAppLog(rec)
        if rec.insertIfNotExists(["app", "date_start", "date_end"]):
            __.append(rec["_id"])
    inserted.append(__)
    timer.append(("saved", time()))
    return {"timer": timer}


#-----------------------------------------------
#  DSP广告报表统计
#-----------------------------------------------
from model.data.definition import ReportLomark, PeriodicalAppLogDetail


def set_fill_and_click(result):
    if result['show'] != 0:
        result['click_rate'] = float(result['click']) / result['show']
    if result['request'] != 0:
        result['fill_rate'] = float(result['show']) / result['request']


# 使用字典参数构造一个最终输出的dict，kw每个key表示不同的统计，dsp_list表示合并的统计
#-------------------------
def dsp_data_merge(with_detail=True, **kw):
    result = {'dsp_list': [], 'detail_list': {}}
    dsp_list = []
    calc_list = []

    # 将字典项设置到details_list作为明细(需要去除第一个字段)，然后其他开始计算
    # 每个对象都是tuple, 先放到一个list里面
    for k in kw:
        result['detail_list'][k] = kw[k]
        calc_list += kw[k]

    # 将tuple元素进行按照x[0](date)进行分类，然后分别统计最终的数据
    for k, v in groupby(calc_list, lambda x: x['date']):
        items = v
        calc = {
            'request': 0, 'show': 0, 'click': 0, 'fill_rate': 0, 'click_rate': 0, 'date': k,
            'details': {
                'Banner': {'request': 0, 'show': 0, 'click': 0, 'fill_rate': 0, 'click_rate': 0},
                u'插屏': {'request': 0, 'show': 0, 'click': 0, 'fill_rate': 0, 'click_rate': 0},
                u'全屏': {'request': 0, 'show': 0, 'click': 0, 'fill_rate': 0, 'click_rate': 0}
            }
        }
        main_fields = ('request', 'show', 'click')
        for it in items:
            for mf in main_fields:
                calc[mf] += it[mf]

            # 如果是百灵的则不统计详细
            if not with_detail:
                continue
            for dk in calc['details']:
                for mf in main_fields:
                    calc['details'][dk][mf] += it['details'][dk][mf]

        set_fill_and_click(calc)

        if with_detail:
            for dk in calc['details']:
                set_fill_and_click(calc['details'][dk])

        dsp_list.append((k, calc))

    # 排序dsp_list 并且输出dict列表（不是tuple）
    dsp_list.sort(key=lambda x: x[0])
    result['dsp_list'] = [x[1] for x in dsp_list]

    return result

# 因为report_app_log和report_app_log_detail 一天整理一次，如果end_date包含今天，则需要查找当天数据
#--------------------------------------------------------------------------------------
def period_data_merge(current, collection, end_date, app_ids=None, show_type=None):
    last_end = datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
    last_end = to_timezone(last_end, 'Asia/Shanghai')
    # 如果end_date不包含当天数据，直接返回
    if end_date < last_end:
        return list(current)

    # 修正end_date
    query_end_date = end_date + timedelta(days=1, seconds=-1)

    data_list = list(current)

    # if len(data_list) == 0:
    #     return data_list

    # last_date = data_list[-1]['date_start']

    query_rules = {'date_start': {'$gte': last_end, '$lte': query_end_date}, 'dsp_platform': {'$ne': 'o2omobi'}}
    if app_ids:
        query_rules['app'] = {'$in': app_ids}
    if show_type:
        query_rules['show_type'] = show_type

    result = collection.query(query_rules).sort('date_start', -1)
    return data_list + list(result)


def calc_dsp_lomark(key, data_list=None):
    result = {'date': key, 'click': 0, 'request': 0,
              'show': 0, 'fill_rate': 0.0, 'click_rate': 0.0, 'details': {}}

    # 补充详细信息
    detail_fields = ('Banner', u'全屏', u'插屏')
    for k in detail_fields:
        result['details'][k] = {'click': 0, 'show': 0, 'request': 0, 'fill_rate': 0, 'click_rate': 0}

    if not data_list:
        return result

    calc_fields = (('click', 'click'), ('request', 'request'), ('show', 'impression'))
    for data in data_list:
        if data['adspacetype'] not in result['details']:
            result['details'][data['adspacetype']] = {'click': 0, 'request': 0,
                                                      'show': 0, 'fill_rate': 0, 'click_rate': 0}
        for field in calc_fields:
            # 总数计算
            result[field[0]] += data[field[1]]
            # 详细计算
            result['details'][data['adspacetype']][field[0]] += data[field[1]]

    # 总汇的填充率和点击率
    set_fill_and_click(result)
    # 详细的填充率和点击率
    for k in detail_fields:
        item = result['details'][k]
        set_fill_and_click(item)

    return result


def calc_dsp_balin_lomark(key, data_list=None):
    result = {'date': key, 'click': 0, 'request': 0,
              'show': 0, 'fill_rate': 0.0, 'click_rate': 0.0}

    if not data_list:
        return result

    calc_fields = (('click', 'number_click'), ('request', 'number_request'), ('show', 'number_show'))
    for data in data_list:
        for field in calc_fields:
            # 总数计算
            result[field[0]] += data[field[1]]

    # 总汇的填充率和点击率
    set_fill_and_click(result)

    return result

# 统计点媒的数据
#-----------------------------------------
def get_dsp_lomark_report(client, adtype, start_at, end_at):
    query_rules = {'date': {'$gte': start_at, '$lte': end_at}}
    adtype_refer = {'banner': 'Banner', 'popup': u'插屏', 'fullscreen': u'全屏'}

    # 临时加上我们的APPID查找
    # query_rules['appid'] = '27e8cfda00d711e4afec000c2943dacd'

    # 设置查询内容
    if client and client.strip() != '':
        query_rules['client'] = client.lower()
    if adtype and adtype.strip() != '' and adtype in adtype_refer:
        query_rules['adspacetype'] = adtype_refer[adtype]

    result = ReportLomark.query(query_rules).sort('date', -1)

    if not result:
        return []

    data_list, exists_list = [], []
    group_func = lambda x: x['date']
    for k, item in groupby(result, group_func):
        data = list(item)
        data_list.append((k, calc_dsp_lomark(k, data)))
        exists_list.append(k)

    # 列出从start_at 到 end_at的日期，判断是否存在数据，不存在则返回默认
    cur = datetime.strptime(start_at, '%Y-%m-%d')
    last = datetime.strptime(end_at, '%Y-%m-%d')

    while cur <= last:
        k = cur.strftime('%Y-%m-%d')
        if k not in exists_list:
            data_list.append((k, calc_dsp_lomark(k, None)))
        cur += timedelta(days=1)

    # 重新排序data_list 并且输出，将tuple原本用来排序的第一个元素（date）去除
    data_list.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))
    return [x[1] for x in data_list]

# 查询百灵平台统计的DSP数据
#---------------------------------
def get_dsp_balin_report(client, adtype, start_at, end_at):
    # 获取缓存
    from apps.outlet_layer.services.campaign import Property
    client_cache = Property.platforms_by_code_to__id()
    # 表示涉及的应用的id集合，当且仅当指定了平台的时候才有
    apps = None

    # 需要变为UTC时间
    start_at = to_timezone(datetime.strptime(start_at, '%Y-%m-%d'), 'Asia/Shanghai')
    end_at = to_timezone(datetime.strptime(end_at, '%Y-%m-%d'), 'Asia/Shanghai')

    # 如果end_at 是今天，则只查询到昨天，其他的使用period合并
    has_today, real_end_date = False, end_at
    today_date = to_timezone(datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d'), 'Asia/Shanghai')
    if end_at == today_date:
        has_today = True
        end_at = today_date + timedelta(days=-1)

    query_rules = {'date_start': {'$gte': start_at, '$lte': end_at}, 'dsp_platform': {'$ne': 'o2omobi'}}
    # todo: banner可能为banner image static或者banner
    adtype_refer = {'banner': ['banner_image_static', 'banner'], 'popup': 'popup', 'fullscreen': 'full_screen', 'open': 'open_screen'}

    # 设置查询内容
    if client and client.strip() != '':
        # 查询相关类型应用的APP，然后把APP ID作为条件去查询广告
        apps = App.query({'platform': object_id(client_cache[client])}).distinct('_id')
        query_rules['app'] = {'$in': list(apps)}

    # 如果指定了某类型的广告的查询，则查找的是detail，如果没有指定则查找普通的app_log
    if adtype and adtype.strip() != '' and adtype in adtype_refer:
        if adtype == 'banner':
            query_rules['$or'] = []
            for atype in adtype_refer['banner']:
                query_rules['$or'].append({'banner': atype})
        else:
            query_rules['show_type'] = adtype_refer[adtype]
        result = ReportAppLogDetail.query(query_rules).sort('date_start', -1)
        result = period_data_merge(result, PeriodicalAppLogDetail, real_end_date, apps, adtype_refer[adtype])
    else:
        result = ReportAppLog.query(query_rules).sort('date_start', -1)
        result = period_data_merge(result, PeriodicalAppLog, real_end_date, apps)

    if not result:
        return []

    data_list, exists_list = [], []
    group_func = lambda x: to_timezone(as_timezone(x['date_start'], 'UTC'), 'Asia/Shanghai').strftime('%Y-%m-%d')
    for k, item in groupby(result, group_func):
        data = list(item)
        key = k
        data_list.append((key, calc_dsp_balin_lomark(key, data)))
        exists_list.append(key)

    # 列出从start_at 到 end_at的日期，判断是否存在数据，不存在则返回默认
    cur = start_at
    last = end_at

    # 如果实际日期包含今日，last需要加一天
    if has_today:
        last += timedelta(days=1)

    while cur <= last:
        k = cur.strftime('%Y-%m-%d')
        if k not in exists_list:
            data_list.append((k, calc_dsp_balin_lomark(k, None)))
        cur += timedelta(days=1)

    # 重新排序data_list 并且输出，将tuple原本用来排序的第一个元素（date）去除
    data_list.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'))
    return [x[1] for x in data_list]


#  获取DSP平台（点媒）的某天的详细数据，如果是当天的数据需要由period统计，
#  其他的直接从相关数据表获取. platform参数暂时不用
#----------------------------------------------------------------
def get_dsp_detail(date, client, platform=None):
    query_rules = {'date': date}

    if client:
        query_rules['client'] = client
    data_list = ReportLomark.query(query_rules)

    result = {
        'Banner': {'click': 0, 'show': 0, 'request': 0, 'click_rate': 0, 'fill_rate': 0},
        u'插屏': {'click': 0, 'show': 0, 'request': 0, 'click_rate': 0, 'fill_rate': 0},
        u'全屏': {'click': 0, 'show': 0, 'request': 0, 'click_rate': 0, 'fill_rate': 0}
    }

    for data in data_list:
        result[data['adspacetype']]['click'] += data['click']
        result[data['adspacetype']]['show'] += data['impression']
        result[data['adspacetype']]['request'] += data['request']

    for key in result:
        set_fill_and_click(result[key])

    return result


# 获取某天的详细数据，返回json.当天的数据需要由period统计，
# 当天之前的直接从reportapplogdetail获取。
#----------------------------------
def get_dsp_balin_detail(date, client, platform):
    now = to_timezone(datetime.strptime(datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d'), 'Asia/Shanghai')
    start_at, end_at = date, date + timedelta(days=1, seconds=-1)
    start_at = to_timezone(start_at, 'Asia/Shanghai')
    end_at = to_timezone(end_at, 'Asia/Shanghai')

    query_rules = {'dsp_platform': {'$ne': 'o2omobi'}, 'date_start': {'$gte': start_at, '$lte': end_at}}
    if platform is list or platform is tuple:
        query_rules['dsp_platform'] = {'$in': platform}
    if client:
        client_cache = Property.platforms_by_code_to__id()
        apps = App.query({'platform': object_id(client_cache[client])}, {'_id': 1})
        query_rules['app'] = {'$in': [a['_id'] for a in list(apps)]}

    if date < now:
        data_list = ReportAppLogDetail.query(query_rules)
    else:
        data_list = PeriodicalAppLogDetail.query(query_rules)

    result = {
        'Banner': {'click': 0, 'show': 0, 'request': 0, 'click_rate': 0, 'fill_rate': 0},
        u'插屏': {'click': 0, 'show': 0, 'request': 0, 'click_rate': 0, 'fill_rate': 0},
        u'全屏': {'click': 0, 'show': 0, 'request': 0, 'click_rate': 0, 'fill_rate': 0}
    }
    calc_fields = {'banner_image_static': 'Banner', 'popup': u'插屏', 'full_screen': u'全屏', 'banner': 'Banner'}
    if not data_list:
        data_list = []

    data_list = list(data_list)

    for item in data_list:
        show_field = calc_fields[item['show_type']]
        result[show_field]['click'] += item['number_click']
        result[show_field]['show'] += item['number_show']
        result[show_field]['request'] += item['number_request']

    for key in result:
        set_fill_and_click(result[key])
    return result

#-----------------------------------------------
#  积分广告相关
#-----------------------------------------------

# 计算积分广告统计数据的总和
#--------------------------------------------
def calc_offerwall(key, data_list, is_current=False, id_name=None, id_list=None):
    result = {'date': key, 'click': 0,
              'show': 0, 'activation': 0,
              'exchange': 0, 'effective click': 0,
              'money': 0, 'convert': 0.0}

    if data_list is not None:
        for item in data_list:
            # 如果is_current=true,并且id_list有输入，但是当前的id不存在，则跳过
            if is_current and id_list and item[id_name] not in id_list:
                continue

            result['click'] += item.get('click', 0)
            result['show'] += item.get('show',0)
            result['activation'] += item.get('activation', 0)
            result['exchange'] += item.get('exchange', 0)
            result['effective click'] += item.get('effective click', 0)
            result['money'] += item.get('money', 0)

        if result['click'] != 0:
            result['convert'] = result['activation']*100 / result['click']
        else:
            result['convert'] = 0

    return result

from apps.outlet_layer.module.api.statistics import group_track_log_action
from base.utils import pre_days, pre_hours
from model.data.definition import PeriodicalOfferWallAdvertLogDay, PeriodicalOfferWallAppLogDay,\
    PeriodicalRecommendWallAppLogHour, PeriodicalRecommendWallAppLogDay


# 计算积分墙相关的报表数据
#-----------------------------------------
def prepare_offerwall_report(target_name, id_list, start_at, end_at, **kwargs):
    is_admin = kwargs.pop("admin", False)
    is_today = kwargs.pop('is_today', False)
    is_same_day = start_at.date() == end_at.date()

    if target_name == 'ad':
        target = ((is_today or is_same_day) and PeriodicalOfferWallAdvertLogHour) or PeriodicalOfferWallAdvertLogDay
    elif target_name == 'app':
        target = ((is_today or is_same_day) and PeriodicalOfferWallAppLogHour) or PeriodicalOfferWallAppLogDay
    else:
        target = ((is_today or is_same_day) and PeriodicalRecommendWallAppLogHour) or PeriodicalRecommendWallAppLogDay
    # 如果是当天的数据，则从0点统计到当前小时的前一小时（当前小时另外有API返回）
    # 如果是月报表，如果end是今天之前的，则统计start->end, 否则统计start->(end-1)，再加上end实时
    cur_hour = 0
    end_of_today = False

    if not is_today:
        if end_at.date() >= datetime.today().date():
            end_of_today = True
            end_at -= timedelta(seconds=1)
        else:
            end_at += timedelta(days=1) - timedelta(seconds=1)
    else:
        cur_hour = datetime.today().hour
        if cur_hour > 0:
            end_at += timedelta(hours=cur_hour-1)

    # 日期统一为UTC
    _start_date = to_timezone(start_at, 'Asia/Shanghai')
    _end_date = to_timezone(end_at, 'Asia/Shanghai')


    query_rules = {"date_start": {"$gte": _start_date, "$lte": _end_date}}
    reports = []
    if id_list:
        if target_name == 'ad':
            query_rules["advert"] = {"$in": bulk_object_id(id_list)}
        else:
            query_rules["app"] = {"$in": bulk_object_id(id_list)}

    if is_admin or id_list:
        reports = target.query(query_rules)
        reports.sort("date_start", 1)
    else:
        return {'start_at': start_at, 'end_at': end_at, 'data': []}

    lst, exists = [], []

    # 默认按照“日期”分组，如果is_today=true，则按照小时分组
    time_format = ((is_today or is_same_day) and '%H:00') or '%Y-%m-%d'
    f = lambda x: to_timezone(as_timezone(x["date_start"], "UTC"), "Asia/Shanghai").strftime(time_format)

    for key, l in groupby(reports, f):
        l = list(l)
        lst.append((key, calc_offerwall(key, l)))
        exists.append(key)

    if is_today or end_of_today:
        if is_today:
            cur_app_list, cur_recommend_app_list, cur_offer_list = group_track_log_action(pre_hours(0))
            cur_key = '%02d:00' % cur_hour
        else:
            cur_app_list, cur_recommend_app_list, cur_offer_list = group_track_log_action(pre_days(0), 24)
            cur_key = datetime.today().strftime('%Y-%m-%d')

        if target_name == 'ad':
            lst.append((cur_key, calc_offerwall(cur_key, cur_offer_list, True, 'advert', id_list)))
        elif target_name == 'app':
            lst.append((cur_key, calc_offerwall(cur_key, cur_app_list, True, 'app', id_list)))
        else:
            lst.append((cur_key, calc_offerwall(cur_key, cur_recommend_app_list, True, 'app', id_list)))

        exists.append(cur_key)

    exists = tuple(exists)
    __ = start_at

    # 如果结束日期为当天的话，则重新补上一天（因为之前减了1秒，为了先获取前一天，再计算实时）
    if not is_today and end_of_today:
        end_at += timedelta(days=1)

    # 如果没有这个日期的则当作0处理
    while __ <= end_at:
        date_str = __.strftime(time_format)
        if date_str not in exists:
            lst.append((date_str, calc_offerwall(date_str, None)))

        # 如果是当天的，则使用小时作为delta来计算
        if not is_today and not is_same_day:
            __ = __ + timedelta(days=1)
        else:
            __ = __ + timedelta(hours=1)

    lst.sort()

    return {"start_at": start_at, "end_at": end_at,
            "data": [i[1] for i in lst]}

# 统计积分广告相关的报表
#---------------------------------
def get_offerwall_ad_report(id_list, start_at=None, end_at=None, **kwargs):
    return prepare_offerwall_report('ad', id_list, start_at, end_at, **kwargs)


# 统计积分广告所对应的应用相关的报表
#---------------------------------
def get_offerwall_app_report(id_list, start_at=None, end_at=None, **kwargs):
    return prepare_offerwall_report('app', id_list, start_at, end_at, **kwargs)

