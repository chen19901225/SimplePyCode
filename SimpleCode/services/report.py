
from itertools import groupby
from .campaign import get_advert, get_app, Property
from .aggregate import transform_app, transform_advert

from apps.outlet_layer.settings import redis_conn

from model.data.definition import (
    ReportAdvertLog, ReportAppLog, ReportPlatformLog, PeriodicalAppLog, PeriodicalAdvertLog, PeriodicalPlatformLog, TrackLog, ReportAppLogDetail, PeriodicalAppLogDetail,
)

from base.utils import (
    today, timedelta, object_id,
)

import datetime


try:
    from cdecimal import Decimal
except:
    from decimal import Decimal

k_advert = lambda x : x.split("-")[0]
k_app = lambda x : x.split("-")[1]

def aggregate_report_app(hkey, logs):
    fn = lambda advert, app: app[advert["payment_type"]]["sharing"]
    __ = lambda x: x[0]
    lst = []
    details = []
    for (report, advert, app) in aggregate_report_by_campaign(hkey, logs, fn):
        report["cpm_balance"] = report["cpc_balance"] = report["cpa_balance"] = 0
        if advert["payment_type"] == "cpm":
            report["cpm_balance"] = report["balance"]
        elif advert["payment_type"] == "cpc":
            report["cpc_balance"] = report["balance"]
        elif advert["payment_type"] == "cpa":
            report["cpa_balance"] = report["balance"]

        details.append((report, advert, app))
        lst.append((app["_id"], advert["payment_type"], report))
    ret = []
    for app_id, group in groupby(sorted(lst, key=__), __):
        group = list(group)
        report = {}
        report["requests"] = sum(i[-1]["requests"] for i in group)
        report["impressions"] = sum(i[-1]["impressions"] for i in group)
        report["clicks"] = sum(i[-1]["clicks"] for i in group)
        report["actions"] = sum(i[-1]["actions"] for i in group)
        report["cpm_balance"] = sum(i[-1]["cpm_balance"] for i in group)
        report["cpc_balance"] = sum(i[-1]["cpc_balance"] for i in group)
        report["cpa_balance"] = sum(i[-1]["cpa_balance"] for i in group)
        report["balance"] = report["cpm_balance"] + report["cpc_balance"] + report["cpa_balance"]
        ret.append((app_id, report))

    return (ret, details)

def aggregate_report_by_campaign(hkey, logs, fn_base):
    for app_id, lst1 in groupby(sorted(logs, key=k_app), k_app):
        lst1 = list(lst1)
        app = get_app_and_transform(app_id)
        for advert_id, lst2 in groupby(sorted(lst1, key=k_advert), k_advert):
            lst2 = list(lst2)
            advert = get_advert_and_transform(advert_id)
            if advert["payment_type"] in ("cpm", "cpc", "cpa"):
                base = fn_base(advert, app)
            else:
                raise ValueError("Unexpected payment type %s."
                                 % payment_type)
            yield (summarize_advert(advert, hkey, lst2, base), advert, app)

	

def aggregate_report_advert(hkey, logs):
    ret = []
    for __, lst in groupby(sorted(logs, key=k_advert), k_advert):
        lst = list(lst)
        advert = get_advert_and_transform(__)
        report = summarize_advert(advert, hkey, lst)
        report["type"] = advert["payment_type"]
        ret.append((__, report))

    return ret

	
def summarize_advert(advert, hkey, logs, base=None):
    d = {}
    d["requests"] = d["impressions"] = d["clicks"] = d["actions"] = 0
    for log in logs:
        action_code = log.split("-")[-1]
	if action_code == "request":
	    d["requests"] += int(redis_conn.hget(hkey, log))
	elif action_code == "show":
	    d["impressions"] += int(redis_conn.hget(hkey, log))
	elif action_code == "click":
	    d["clicks"] += int(redis_conn.hget(hkey, log))
	elif action_code == "action":
	    d["actions"] += int(redis_conn.hget(hkey, log))

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

def aggregate_report_platform(hkey, logs):
    fn = lambda ad, app: ad["price"] - app[ad["payment_type"]]["sharing"]
    __ = lambda x: x[0]
    lst = []
    for (report, advert, app) in aggregate_report_by_campaign(hkey, logs, fn):
        lst.append((advert["payment_type"], report))
        lst.append((advert["show_type"], report))

    ret = []
    for key, group in groupby(sorted(lst, key=__), __):
        group, report = list(group), {}
        for k in ("requests", "impressions", "clicks", "actions", "balance"):
            report[k] = sum(map(lambda x: x[1][k], group))
        ret.append((key, report))
    return ret

def aggregate_all(hkey, logs, date_start, date_end):
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
    for (group_name, report) in aggregate_report_platform(hkey, logs):
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
    ret.append(buffers)
	
    # --------------------
    # Advert Report
    buffers = []
    for (advert_id, report) in aggregate_report_advert(hkey, logs):
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

    ret.append(buffers)
	
    reports, details = aggregate_report_app(hkey, logs)
    buffers = []
    for (app_id, report) in reports:
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
    
    ret.append(buffers)

    buffers = []
    for (report, advert, app) in details:
        d = ReportAppLogDetail()
        d["app"] = object_id(app["_id"])
        d["advert"] = object_id(advert["_id"])
        d["show_type"] = advert["show_type"]
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

    ret.append(buffers)

    return ret

def meaningful_float(i):
    if type(i) is not Decimal:
        try:
            i = Decimal(str(i))
        except Exception, err:
            print i
            raise err
    return float(i.quantize(Decimal(".01")))

def upsert_report_by_period(start_time, end_time):
    hkey = "periodical_log_%s" % start_time.strftime("%Y%m%d%H")
    logs = redis_conn.hkeys(hkey)

    buffers = aggregate_all(hkey, logs, start_time, end_time)
    req = 0
    for rec in buffers[2]:
        rec = PeriodicalAppLog(rec)
        req += rec['number_show']

    print req


def upsert_report_by_period2(start_time, end_time):
    hkey = "periodical_log_%s" % start_time.strftime("%Y%m%d%H")
    logs = redis_conn.hkeys(hkey)

    buffers = aggregate_all(hkey, logs, start_time, end_time)
    for rec in buffers[0]:
        rec = PeriodicalPlatformLog(rec)
        rec.insertIfNotExists(["group_name", "date_start", "date_end"])

    for rec in buffers[1]:
        rec = PeriodicalAdvertLog(rec)
        rec.insertIfNotExists(["advert", "date_start", "date_end"])

    for rec in buffers[2]:
        rec = PeriodicalAppLog(rec)
        rec.insertIfNotExists(["app", "date_start", "date_end"])


    for rec in buffers[3]:
        rec = PeriodicalAppLogDetail(rec)
        rec.insertIfNotExists(["app", "advert", "date_start", "date_end"])


def upsert_report_by_period3(start_time, end_time):
    hkey = "periodical_log_%s" % start_time.strftime("%Y%m%d%H")
    logs = redis_conn.hkeys(hkey)

    buffers = aggregate_all(hkey, logs, start_time, end_time)
    now = datetime.datetime.utcnow()
    for rec in buffers[0]:
        rec = PeriodicalPlatformLog(rec)
        rec["date_creation"] = now
        PeriodicalPlatformLog.update({"group_name": rec["group_name"], "date_start": rec["date_start"], "date_end": rec["date_end"]}, rec, upsert=True)
        #rec.insertIfNotExists(["group_name", "date_start", "date_end"])

    for rec in buffers[1]:
        rec = PeriodicalAdvertLog(rec)
        rec["date_creation"] = now
        PeriodicalAdvertLog.update({"advert": rec["advert"], "date_start": rec["date_start"], "date_end": rec["date_end"]}, rec, upsert=True)
        #rec.insertIfNotExists(["advert", "date_start", "date_end"])

    for rec in buffers[2]:
        rec = PeriodicalAppLog(rec)
        rec["date_creation"] = now
        PeriodicalAppLog.update({"app": rec["app"], "dsp_platform": rec["dsp_platform"],
                                 "date_start": rec["date_start"], "date_end": rec["date_end"]},
                                rec, upsert=True)
        #rec.insertIfNotExists(["app", "date_start", "date_end"])


    for rec in buffers[3]:
        rec = PeriodicalAppLogDetail(rec)
        rec["date_creation"] = now
        PeriodicalAppLogDetail.update({"app": rec["app"], "advert": rec["advert"],
                                       "dsp_platform": rec["dsp_platform"], "show_type": rec["show_type"],
                                       "date_start": rec["date_start"], "date_end": rec["date_end"]},
                                      rec, upsert=True)
        #rec.insertIfNotExists(["app", "advert", "date_start", "date_end"])

k_dsp_app_show_type = lambda x : "{0}-{1}-{3}".format(*x.split("-"))

def upsert_dsp_report_by_period(start_time, end_time):
    hkey = "dsp_periodical_log_%s" % start_time.strftime("%Y%m%d%H")
    logs = redis_conn.hkeys(hkey)

    buffers = dsp_aggregate_all(hkey, logs, start_time, end_time)
    now = datetime.datetime.utcnow()

    for rec in buffers[0]:
        rec = PeriodicalAppLog(rec)
        rec["date_creation"] = now
        PeriodicalAppLog.update({"app": rec["app"], "dsp_platform": rec["dsp_platform"],
                                 "date_start": rec["date_start"], "date_end": rec["date_end"]},
                                rec, upsert=True)
        #rec.insertIfNotExists(["app", "date_start", "date_end"])


    for rec in buffers[1]:
        rec = PeriodicalAppLogDetail(rec)
        rec["date_creation"] = now
        PeriodicalAppLogDetail.update({"app": rec["app"], "advert": rec["advert"],
                                       "dsp_platform": rec["dsp_platform"], "show_type": rec["show_type"],
                                       "date_start": rec["date_start"], "date_end": rec["date_end"]},
                                      rec, upsert=True)
        #rec.insertIfNotExists(["app", "advert", "date_start", "date_end"])


def dsp_aggregate_all(hkey, logs, date_start, date_end):
    ret = []

    buffers = []
    reports, details = dsp_aggregate_report_app(hkey, logs)
    for (dsp, app_id, report) in reports:
        d = ReportAppLog()
        d["dsp_platform"] = dsp
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

    ret.append(buffers)

    buffers = []
    for (dsp, app_id, show_type, report) in details:
        d = ReportAppLogDetail()
        d["dsp_platform"] = dsp
        d["app"] = object_id(app_id)
        d["show_type"] = show_type
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

    ret.append(buffers)

    return ret


def dsp_aggregate_report_app(hkey, logs):
    fn = lambda app: app["cpc"]["sharing"]  # TODO only cpc?
    __ = lambda x: "{0}-{1}".format(*x)
    details = []
    for (report, show_type, dsp, app) in dsp_aggregate_report_by_campaign(hkey, logs, fn):
        report["cpm_balance"] = report["cpc_balance"] = report["cpa_balance"] = 0
        report["cpc_balance"] = report["balance"]      # TODO only cpc?

        details.append((dsp, app["_id"], show_type, report))
    ret = []
    for dsp_app_id, group in groupby(sorted(details, key=__), __):
        dsp, app_id = dsp_app_id.split("-")
        group = list(group)
        report = {}
        report["requests"] = sum(i[-1]["requests"] for i in group)
        report["impressions"] = sum(i[-1]["impressions"] for i in group)
        report["clicks"] = sum(i[-1]["clicks"] for i in group)
        report["actions"] = sum(i[-1]["actions"] for i in group)
        report["cpm_balance"] = sum(i[-1]["cpm_balance"] for i in group)
        report["cpc_balance"] = sum(i[-1]["cpc_balance"] for i in group)
        report["cpa_balance"] = sum(i[-1]["cpa_balance"] for i in group)
        report["balance"] = report["cpm_balance"] + report["cpc_balance"] + report["cpa_balance"]
        ret.append((dsp, app_id, report))

    return (ret, details)

def dsp_aggregate_report_by_campaign(hkey, logs, fn_base):
    for dsp_app_id, lst1 in groupby(sorted(logs, key=k_dsp_app_show_type), k_dsp_app_show_type):
        lst1 = list(lst1)
        dsp, app_id, show_type = dsp_app_id.split("-")
        app = get_app_and_transform(app_id)
        base = fn_base(app)
        yield (dsp_summarize_advert(hkey, lst1, base), show_type, dsp, app)

def dsp_summarize_advert(hkey, logs, base):
    d = {}
    d["requests"] = d["impressions"] = d["clicks"] = d["actions"] = 0
    for log in logs:
        action_code = log.split("-")[-2]
        if action_code == "request":
            d["requests"] += int(redis_conn.hget(hkey, log))
        elif action_code == "show":
            d["impressions"] += int(redis_conn.hget(hkey, log))
        elif action_code == "click":
            d["clicks"] += int(redis_conn.hget(hkey, log))
        elif action_code == "action":
            d["actions"] += int(redis_conn.hget(hkey, log))

    base = Decimal(str(base))
    d["balance"] = d["clicks"] * base   # TODO only cpc?
    return d

def get_advert_and_transform(advert_id):
    advert = get_advert(advert_id)
    return transform_advert(advert)

def get_app_and_transform(app_id):
    app = get_app(app_id)
    return transform_app(app)

