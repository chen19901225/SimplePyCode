# coding=utf-8
import json
import logging
import logging.config
import os


from bson import objectid


from base import config
from model.data.definition import OfferWallTaskLog, OfferWallTrackLogType, OfferWallCenter, \
    OfferWallDeveloperSetting, SdkVersionServer, OfferWallAdvert, CarrierNetworkType, OfferWallConsumptionLog
from campaign import get_offerwall_setting, Property
from apps.outlet_layer.settings import redis_db, cache, cache_pool
from base.utils import today, bulk_up, smart_region_invalidate

logging.config.fileConfig('log4p.conf')
logger = logging.getLogger('OfferWallLog')
device_info_logger = logging.getLogger('OfferWallLogDevice')
activation_info_logger = logging.getLogger('OfferWallLogActivation')


def remove_task_log_find_id_cache_with_state(user_id, app_id, state):
    return OfferWallTaskLog.remove_cache_with_find({
        'user_id': objectid.ObjectId(user_id),
        'app_id': objectid.ObjectId(app_id),
        'removed': False,
        'state': state,
    }, {'_id': 1})
    pass


def remove_task_log_find_id_cache_with_user(user_id):
    return OfferWallTaskLog.remove_cache_with_find({
        'user_id': objectid.ObjectId(user_id),
        'removed': False,
    }, {'_id': 1})


def redis_track_log_action(app_id, advert_id, track_type, value=1):
    if track_type:
        assert isinstance(value, int)
        redis_map_name = 'offer_track_log_%s' % today().strftime('%Y%m%d%H')
        redis_key = '%s-%s-%s' % (app_id, advert_id, track_type)

        redis_db.hincrby(redis_map_name, redis_key, value)
        #TODO设置map name的过期时间


def user_task_num_increase_and_count(user_id, app_id, advert_id):
    advert = OfferWallAdvert.get_with_id(advert_id)
    if advert['channel'] != OfferWallAdvert.channel_recommend:
        user_task_num_increase(user_id)
    code = \
        Property.offer_wall_track_log_types_by_value_to_code(OfferWallTrackLogType.effective_click)
    redis_track_log_action(app_id, advert_id, code)


def user_task_num_increase(user_id):
    with cache_pool.reserve() as mc:
        limit_num = get_offerwall_setting('offerwall_daily_tasks')
        key_prefix = config.get('mc_key_prefix.offer_advert_task_limit')
        key = '%s-%s' % (key_prefix, str(user_id))
        if mc.get(key) is None:
            logger.info('key_prefix %s-%s' % (key_prefix, today()))
            mc.set(key, 0, int(config.get('env.offerwall_tasks_limit_time')))
        mc.incr(key)


def _sum_score(user_id):
    #从个人中心表查总积分
    reduce_str = """
function Reduce(doc, out) {
    out.score += doc.score;
}"""
    finalize_str = """
function Finalize(out) {
    return out.score;
}"""
    score_list = OfferWallCenter.group(
        key={"user_id": 1},
        condition={"user_id": objectid.ObjectId(user_id)},
        initial={"score": 0},
        reduce=reduce_str,
        finalize=finalize_str,
    )
    #查到的结果列表 只有一个
    if score_list:
        return score_list[0]
    return 0.0


def version_check(version, platform_value):  # TODO
    svs = SdkVersionServer.get_without_id({
        'version': version,
        'platform': platform_value
    })
    if not svs:
        SdkVersionServer.update({
            'version': version,
            'platform': platform_value
        }, {'status': SdkVersionServer.server})
        return SdkVersionServer.server
    return svs['status']


@bulk_up
def money_to_score(money_list, payment_rate):
    """积分转换公式:积分 = 人民币 * 转换率 * （ 1 - 预留利润 ） * 应用支付比例"""
    rate = get_offerwall_setting('offerwall_exchange_rate')
    profit = get_offerwall_setting('offerwall_exchange_profit')
    if isinstance(payment_rate, (list, tuple)):
        return map(lambda m, p: round(m * rate * (1 - profit) * p, 2), money_list, payment_rate)
    else:
        return map(lambda m: round(m * rate * (1 - profit) * payment_rate, 2), money_list)


@bulk_up
def score_to_app_unit_rate(unit_rate_list):
    score_rate = get_offerwall_setting('offerwall_exchange_rate')
    return [ur/score_rate for ur in unit_rate_list]


@bulk_up
def score_to_app_unit(score_list, app_mr):
    rate_expr = score_to_app_unit_rate
    if isinstance(app_mr, (list, tuple)):
        rate_list = rate_expr(app_mr)
        return map(lambda s, r: s * r, score_list, rate_list)
    else:
        rate = rate_expr(app_mr)
        return map(lambda s: s * rate, score_list)

__error_dict = {
    -400: 'check log str was not found',
    -401: 'task activation fail',

    -500: 'app status: paused',
    -502: 'app status: not verified',
    -503: 'app status: verifying',
    -504: 'app status: verified',
    -505: 'app status: rejected',
}


def response_error(error_num):
    """error result"""
    return json.dumps({
        'result': error_num,
        'error': __error_dict.get(error_num),
    })


def get_advert_list_rule(app_type_value, app_platform, is_test, channel):
    _today = today(zero_time=True)
    # _tomorrow = _today + timedelta(days=1)
    test_id = objectid.ObjectId(Property.advert_tags_by_code_to__id('test'))
    if is_test == test_id or is_test is True:
        tags = [test_id]
    else:
        tags = [objectid.ObjectId(Property.advert_tags_by_code_to__id(t)) for t in ('fill', 'sell')]

    rst = {
        'status': objectid.ObjectId(Property.campaign_statuses_by_code_to__id('running')),
        'removed': False,
        'start_date': {'$lte': _today},
        # platform用以区分android和ios
        'platform': app_platform,
        # 'end_data': {'$gte': _tomorrow},
        'app_main_type': app_type_value,
        'tag': {'$in': tags},
        'channel': channel,
    }

    print 'rule:', rst
    return rst


@cache.region('offer_wall_short')
def get_advert_id_list(rule):
    # 使用到游标，目前没有好的办法处理游标，offer wall 唯一一处手动调用cache.region
    advert_id_dict_list = list(OfferWallAdvert().find(rule, {'_id': 1}).sort('price', -1))
    logger.debug('advert_list:' + str(advert_id_dict_list))
    advert_id_list = [id_dict['_id'] for id_dict in advert_id_dict_list]
    return advert_id_list


def remove_cache_with_get_advert_id_list(rule):
    smart_region_invalidate(get_advert_id_list, 'offer_wall_short', rule)


def format_android_rule_key(attr, uid, aid):
    key_prefix = config.get("mc_key_prefix.offer_android_activation")
    return str("%s-%s-%s-%s" % (key_prefix, attr, uid, aid))


def get_current_android_rule(uid, advert):
    end_pos = None
    if uid and advert:
        if advert['app_apk_timeout'] == OfferWallAdvert.android_apk_not_timeout:
            end_pos = -1
        attributes = OfferWallTrackLogType.android['attributes'][:end_pos]
        with cache_pool.reserve() as mc:
            for index in reversed(xrange(len(attributes))):
                attr = attributes[index]
                key = format_android_rule_key(attr, uid, advert['_id'])
                value = mc.get(key)
                if value is not None:
                    return OfferWallTrackLogType.android['pos'] + index
    return -1


def carrier_code_with_imsi(imsi):
    if imsi in ("46000", "46002"):
        carrier_code = 'cmcc'
    elif imsi == "46001":
        carrier_code = 'unicom'
    elif imsi == "46003":
        carrier_code = 'cmnet'
    else:
        carrier_code = 'other'
    return carrier_code

def carrier_code_with_mnc(mcc, mnc):
    if mcc == '460':
        if mnc in ['00', '02', '07']:
            return 'cmcc'
        elif mnc in ['03', '05', ]:
            return 'cmnet'
        elif mnc in ['01', '06']:
            return 'unicom'
    return 'other'


def get_carrier_network_rule(carrier_code, network_mode):
    network_code = network_mode.lower()
    __list = Property._carrier_network_type()
    _all_id = Property.carrier_network_type_by_value_to__id(CarrierNetworkType.all_all)
    for i in __list:
        if i['carrier'] == carrier_code and i['network'] == network_code:
            dyna_rule = {'carrier_network': {'$in': {
                objectid.ObjectId(_all_id),
                i['_id']
            }}}
            return dyna_rule
    dyna_rule = {'carrier_network': objectid.ObjectId(_all_id)}
    return dyna_rule


def is_test_app(app_status_id):
    in_test = ('not verified', 'verifying', 'rejected')
    in_test_id = (objectid.ObjectId(Property.publisher_statuses_by_code_to__id(i)) for i in in_test)
    return any(i == app_status_id for i in in_test_id)


def is_test_advert(tag_id):
    return tag_id == objectid.ObjectId(Property.advert_tags_by_code_to__id('test'))

def remove_offer_user_info_with_app(app_id):
    print '<remove_offer_user_info_with_app>app id:', app_id
    task_list = OfferWallTaskLog().find({'app_id': app_id})
    center_list = OfferWallCenter().find({'app_id': app_id})
    consumption_list = OfferWallConsumptionLog().find({'app_id': app_id})

    task_id_set = set()
    task_state_set = set()
    task_user_set = set()
    center_id_set = set()
    center_user_set = set()
    center_user_app_set = set()
    consumption_id_set = set()

    for task in task_list:
        task_id_set.add(task['_id'])
        task_state_set.add((task['user_id'], task['advert_id'], task['state']))
        task_user_set.add(task['user_id'])

    for center in center_list:
        center_id_set.add(center['_id'])
        center_user_set.add(center['user_id'])
        center_user_app_set.add((center['user_id'], center['app_id']))

    for consumption in consumption_list:
        consumption_id_set.add(consumption['_id'])

    OfferWallTaskLog.remove({'app_id': app_id})
    OfferWallCenter.remove({'app_id': app_id})
    OfferWallConsumptionLog.remove({'app_id': app_id})
    for _id in task_id_set:
        OfferWallTaskLog.remove_cache_with_find_one({'_id': _id})
    for args in task_state_set:
        remove_task_log_find_id_cache_with_state(*args)
    for args in task_user_set:
        remove_task_log_find_id_cache_with_user(args)

    for _id in center_id_set:
        OfferWallCenter.remove_cache_with_find_one({'_id': _id})
    for user in center_user_set:
        OfferWallCenter.remove_cache_with_find({'user_id': user}, {'_id': 1})
    for user, app in center_user_app_set:
        OfferWallCenter.remove_cache_with_find_one({'app_id': app, 'user_id': user}, {'_id': 1})

    for _id in consumption_id_set:
        OfferWallConsumptionLog.remove_cache_with_find_one({'_id': _id})