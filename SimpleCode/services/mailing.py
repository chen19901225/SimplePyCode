#!/usr/bin/env python
# encoding: utf-8

from datetime import datetime
from model.data.definition import ModelBase
from base.backend import mailer
from base.utils import to_unicode, today
from base import config

from . import accounting

"""
There four notify method:

    - `DEBUG`: 所有通知邮件将会以同步执行的方式，发送至
               `DEFAULT_DEBUG_NOTIFY_RECEIVER` 所指定的收件人。
    - `SYNC`: 通过同步执行的方式发送邮件。
    - `MOCK`: 不会发送任何邮件，但会产生一条邮件发送记录。
    - ``
"""
__ = config.get("mailing.default_notify_method", "MOCK").upper()
if __ not in ("DEBUG", "SYNC", "MOCK"):
    __ = "MOCK"
DEFAULT_NOTIFY_METHOD = __
DEFAULT_DEBUG_NOTIFY_RECEIVER = config.get("mailing.debug_notify_receiver", "balin_dev@163.com")


def check_health():
    statuses = []
    # 发信方式检查
    if mailer.DEFAULT_MAILER == "simple_smtp":
        statuses.append({
            "heading": "不可控的发信方式",
            "body": "当前所用的邮件发送方式并不能保证用户能够正常收取邮件！",
            "code": "unstable_mailer",
            "html_class": "alert alert-block",
        })
    # 通知模式检查
    if DEFAULT_NOTIFY_METHOD == "DEBUG":
        statuses.append({
            "heading": "开发模式",
            "body": "系统正以开发模式运行，自动发信的邮件将会统一发送至 <code>%s</code>。" % DEFAULT_DEBUG_NOTIFY_RECEIVER,
            "code": "debug_deliver_method",
            "html_class": "alert alert-block",
        })
    elif DEFAULT_NOTIFY_METHOD == "SYNC":
        statuses.append({
            "heading": "同步模式",
            "body": "系统正以同步执行模式运行，所有邮件将会同步发出。",
            "code": "debug_deliver_sync",
            "html_class": "alert alert-block alert-success",
        })
    elif DEFAULT_NOTIFY_METHOD == "ASYNC":
        statuses.append({
            "heading": "异步模式",
            "body": "系统正以异步执行模式运行，所有邮件将会通过独立进程发送，请确保独立进程正常进行。",
            "code": "debug_deliver_async",
            "html_class": "alert alert-block alert-info",
        })
        # TODO check standalone mailer status and report.
    elif DEFAULT_NOTIFY_METHOD == "MOCK":
        statuses.append({
            "heading": "模拟模式",
            "body": "系统正以模拟模式执行，所有邮件将不会被真正发送（但你/妳可以在发信记录中找到相应的记录）。",
            "code": "debug_deliver_mock",
            "html_class": "alert alert-block",
        })
    for s in statuses:
        s["heading"] = to_unicode(s["heading"])
        s["body"] = to_unicode(s["body"])
    return statuses


class MailTemplate(ModelBase):
    __collection__ = "mail_template"
    structure = {
        "code": basestring,
        "title": basestring,
        "body": basestring,
        "version": int,
        "enabled": bool,
    }
    required_fields = ["code", "title", "body", "version", "enabled"]
    indexes = [
        {
            "fields": ["code", "version"],
            "unique": True,
        },
    ]

    PAIR_TEMPLATE_READABLE_NAMES = (
        ("notify_advertiser_certificated", "广告主身份审核成功"),
        ("notify_advertiser_uncertificated", "广告主身份审核失败"),
        ("notify_developer_certificated", "开发者身份审核成功"),
        ("notify_developer_uncertificated", "开发者身份审核失败"),
        ("notify_app_certificated", "应用审核成功"),
        ("notify_app_uncertificated", "应用审核失败"),
        ("notify_advert_certificated", "广告审核成功"),
        ("notify_advert_uncertificated", "广告审核失败"),
        ("notify_charge_confirmed", "充值审核成功"),
        ("notify_charge_unconfirmed", "充值审核失败"),
        ("notify_draw_permitted", "提现审核成功"),
        ("notify_draw_unpermitted", "提现审核失败"),
        ("notify_campaign_finished", "广告结案"),
        ("notify_password_reset", "重置密码"),
        ("notify_daily_income", "开发者日收入通知"),
        ("notify_daily_outgo", "广告主日支出通知"),
        ("notify_developer_balancing", "开发者总收入通知"),
        ("notify_advertiser_balancing", "广告主余额通知"),
        ("notify_campaign_paused_by_outaged", "余额不足，暂停投放"),
    )

    @classmethod
    def fill_default_template(cls):
        """ 填充默认邮件提醒模板到数据库中。

            这一方法应仅在系统时使用。
        """
        templates = []
        # 广告主资料审核：通过/不通过
        templates.append({
            "code": "notify_advertiser_certificated",
            "title": "[百灵移动广告平台] 您的广告主资格已通过审核",
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴地告诉您，您的广告主资格已经通过审核。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        templates.append({
            "code": "notify_advertiser_uncertificated",
            "title": "[百灵移动广告平台] 您的广告主资格未能通过审核",
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地告诉您，您的广告主资格未能通过审核，原因如下：</div>
<blockquote>${verification["message"]}</blockquote>
<div>您可以发信至 abc@example.com 需求更多帮助。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        # 开发者资料审核：通过/不通过
        templates.append({
            "code": "notify_developer_certificated",
            "title": "[百灵移动广告平台] 您的开发者资格已通过审核",
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴地告诉您，您的开发者资格已经通过审核。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        templates.append({
            "code": "notify_developer_uncertificated",
            "title": "[百灵移动广告平台] 您的开发者资格未能通过审核",
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地告诉您，您的开发者资格未能通过审核，原因如下：</div>
<blockquote>${verification["message"]}</blockquote>
<div>您可以发信至 abc@example.com 需求更多帮助。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        # 应用审核：通过/不通过
        templates.append({
            "code": "notify_app_certificated",
            "title": '[百灵移动广告平台] 您的应用 ${app["name"]} 已通过审核',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴地告诉您，您的应用 ${app["name"]} 已经通过审核。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        templates.append({
            "code": "notify_app_uncertificated",
            "title": '[百灵移动广告平台] 您的应用 ${app["name"]} 未能通过审核',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地告诉您，您的应用 ${app["name"]} 未能通过审核，原因如下：</div>
<blockquote>${verification["message"]}</blockquote>
<div>您可以发信至 abc@example.com 需求更多帮助。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        # 广告审核：通过/不通过
        templates.append({
            "code": "notify_advert_certificated",
            "title": '[百灵移动广告平台] 您的广告 ${advert["name"]} 已通过审核',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴地告诉您，您的广告 ${advert["name"]} 已经通过审核。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        templates.append({
            "code": "notify_advert_uncertificated",
            "title": '[百灵移动广告平台] 您的广告 ${advert["name"]} 未能通过审核',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地告诉您，您的广告 ${advert["name"]} 未能通过审核，原因如下：</div>
<blockquote>${verification["message"]}</blockquote>
<div>您可以发信至 abc@example.com 需求更多帮助。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        # 充值审核：通过/不通过
        templates.append({
            "code": "notify_charge_confirmed",
            "title": '[百灵移动广告平台] 您的充值已确认到帐',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴地告诉您，您的充值已经确认到帐。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        templates.append({
            "code": "notify_charge_unconfirmed",
            "title": '[百灵移动广告平台] 您的充值未能到帐',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地告诉您，您的充值未能确认到帐。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        # 提现审核：通过/不通过
        templates.append({
            "code": "notify_draw_permitted",
            "title": '[百灵移动广告平台] 您的提现已经汇出',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴地告诉您，您的提现已经汇出。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        templates.append({
            "code": "notify_draw_unpermitted",
            "title": '[百灵移动广告平台] 您的提现请求未能通过',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地地告诉您，您的提现请求未被通过。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
<div style="color: #666">这是系统自动发送的邮件，请勿直接回复。</div>
            """,
        })
        # 广告结案
        templates.append({
            "code": "notify_campaign_finished",
            "title": '[百灵移动广告平台] 广告 ${advert["name"]} 已经结束投放',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>您的广告 ${advert["name"]} 已经结束投放。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })
        # 重置密码
        templates.append({
            "code": "notify_password_reset",
            "title": '[百灵移动广告平台] 您的密码重设请求',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>我们于 ${request_date} 收到您重置密码请求，请您通过以下链接重设密码：<a href="${reset_password_url}" target="blank">${reset_password_url}</a></div>
<div>上述链接将在72小时内有效。如果您并没有发出过重设密码请求，请忽略本邮件。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })
        # 开发者日收入通知
        templates.append({
            "code": "notify_daily_income",
            "title": '[百灵移动广告平台] 您今天收入超过了 ￥${receiver["notify_daily_balance"]}',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很高兴告诉您，您今天的收入超过了 ￥${receiver["notify_daily_balance"]}。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })
        # 广告主日支出通知
        templates.append({
            "code": "notify_daily_outgo",
            "title": '[百灵移动广告平台] 您今天支出超过了 ￥${receiver["notify_daily_balance"]}',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>在此，我们提醒您今天的支出超过了 ￥${receiver["notify_daily_balance"]}。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })
        # 开发者总收入达到预期通知
        templates.append({
            "code": "notify_developer_balancing",
            "title": '[百灵移动广告平台] 您总收入超过了 ￥${receiver["notify_total_balance"]}',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>在此，我们提醒您当前账户余额超过了 ￥${receiver["notify_total_balance"]}。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })
        # 开发者总收入达到预期通知
        templates.append({
            "code": "notify_advertiser_balancing",
            "title": '[百灵移动广告平台] 您余额低于 ￥${receiver["notify_total_balance"]}',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>在此，我们提醒您当前账户余额低于 ￥${receiver["notify_total_balance"]}。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })
        # 余额不足，暂停投放
        templates.append({
            "code": "notify_campaign_paused_by_outaged",
            "title": '[百灵移动广告平台] 您的广告 ${advert["name"]} 已暂停投放',
            "body": """\
<div>尊敬的 ${receiver["full_name"]}，您好：</div>
<div>很遗憾地告诉您，由于余额不足，您的广告 ${advert["name"]} 已经暂停投放。</div>
<div><br />百灵移动广告平台<br />${send_date}</div>
            """,
        })

        for t in templates:
            mt = cls()
            for k, v in t.items():
                mt[k] = v
            mt["body"] = mt["body"].strip()
            mt["version"] = 1
            mt["enabled"] = True
            mt.upsert(fields=("code", "version"))

    @classmethod
    def get_template_list(cls):
        mt = cls().collection
        pipeline = [
            {"$match": {"enabled": True}},
            {"$group": {
                "_id": "$code",
                "version": {"$max": "$version"},
                "id": {"$addToSet": "$_id"}}
            },
            {"$sort": {"version": 1}},
        ]
        qr = mt.aggregate(pipeline)
        if not qr["ok"]:
            pass
        ids = map(lambda x: x["id"][0], qr["result"])
        rs = mt.find({"_id": {"$in": ids}})
        if rs.count() < len(cls.PAIR_TEMPLATE_READABLE_NAMES):
            raise RuntimeError("Empty mail template database.")
        rs = dict(map(lambda x: (x["code"], x), rs))
        tmpl = []
        for code, name in cls.PAIR_TEMPLATE_READABLE_NAMES:
            if code in ("mock", "debug"):
                continue
            d = dict(rs[code])
            d["name"] = to_unicode(name)
            tmpl.append(d)
        return tmpl

    @classmethod
    def get_current_by_code(cls, code):
        cursor = cls().find({"code": code, "enabled": True})
        cursor.sort("version", 1)
        if cursor.count() > 0:
            return cursor.next()
        return None

    def getName(self):
        i = filter(lambda x: x[0] == self["code"], self.PAIR_TEMPLATE_READABLE_NAMES)
        return i[0][1]

    def send(self, mail_addr, **kwargs):
        to = None
        if "to" in kwargs:
            to = kwargs["to"]
            del kwargs["to"]
        tags = [self.getName()]
        is_test = kwargs.get("is_test")
        if is_test:
            tags.append("测试邮件")
        elif DEFAULT_NOTIFY_METHOD == "DEBUG":
            mail_addr = DEFAULT_DEBUG_NOTIFY_RECEIVER
            tags.append("开发模式")
        mail = mailer.Mail(mail_addr, self["title"], self["body"], to)
        kwargs["send_date"] = today(fmt="%Y-%m-%d %H:%M:%S")
        mail.fill_subject(**kwargs)
        mail.fill_body(**kwargs)
        if DEFAULT_NOTIFY_METHOD == "MOCK" and not is_test:
            tags.append("模拟发送")
        else:
            mail.send()
        log = MailLog()
        log["tags"] = tags
        log["receiver"] = mail_addr
        log["to"] = mail.to
        log["subject"] = mail.subject
        log["body"] = mail.body
        log.collection.insert(log)


def get_mail(code):
    return MailTemplate.get_current_by_code(code)


class MailLog(ModelBase):
    __collection__ = "mail_log"
    structure = {
        "tags": [basestring],
        "receiver": basestring,
        "to": basestring,
        "subject": basestring,
        "body": basestring,
    }

    def resend(self):
        mail = mailer.Mail(self["receiver"], self["subject"],
                           self["body"], self["to"])
        mail.send()
        d = dict(self)
        if "_id" in d:
            del d["_id"]
        self.collection.insert(d)


def mock_mail_data(code):
    return {
        "receiver": accounting.mock_user(1, save=False)[0],
        "advert": {"name": u"测试广告"},
        "app": {"name": u"测试应用"},
        "verification": {"message": u"您未能通过是因为这是测试邮件。"},
        "is_test": True,
    }
