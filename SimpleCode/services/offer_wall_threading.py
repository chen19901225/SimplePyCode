# coding=utf-8
import threading
import urllib2
import time

from model.data.definition import OfferWallTaskLogState, OfferWallCheck
from apps.outlet_layer.services.offer_wall_common import *
from base.pubsub.sub import command_listen


def activation_request(url, task_log, try_times=3, **kwargs):
    rst = _url_request(url, try_times)
    if rst is True:
        logger.info('---activation request success:%s---' % (url,))
        #assert task_log['state'] == OfferWallTaskLogState.failure
        #保存回调url的随机值到数据库TODO未测试
        offer_wall_check = OfferWallCheck()
        offer_wall_check['check_str'] = kwargs['check_str']
        offer_wall_check['extra_data'] = str(kwargs['extra_data'])
        offer_wall_check['task_log'] = task_log['_id']
        offer_wall_check.save()
        #有可能在这之前收到激活请求，任务完成
        OfferWallTaskLog.update({'_id': task_log['_id'], 'state': OfferWallTaskLogState.failure},
                                {'$set': {'state': OfferWallTaskLogState.not_activation}})

        user_task_num_increase_and_count(kwargs['user_id'], task_log['app_id'], task_log['advert_id'])
        remove_task_log_find_id_cache_with_state(task_log['user_id'], task_log['app_id'], OfferWallTaskLogState.not_activation)
        remove_task_log_find_id_cache_with_state(task_log['user_id'], task_log['app_id'], OfferWallTaskLogState.activation)

    else:
        logger.info('---activation request failure:%s---' % (url,))
    return rst


def app_request(url, try_times=3):
    rst = _url_request(url, try_times)
    if rst is True:
        logger.info('---app request success:%s---' % url)
    else:
        logger.info('---app request failure:%s---' % url)
    return rst


def _url_request(url, try_times=3):
    assert (try_times >= 1)
    try:
        logger.info('response:%s' % urllib2.urlopen(url).read())

    except urllib2.URLError, what:
        try_times -= 1
        logger.info('URL ERROR:' + str(what))
        if not try_times:
            return False
        else:
            return _url_request(url, try_times)
    else:
        return True
from base.utils import today

def timer_task(start_time, interval, times=-1):
    assert isinstance(interval, int)
    assert interval > 0

    def decorator(func):
        def _decorator(*args, **kwargs):
            _times = times
            _now = today()
            start_interval = int((start_time - _now).total_seconds())
            #start time is out
            if start_interval < 0:
                start_interval = start_interval % interval
            time.sleep(start_interval)
            if _times < 0:
                while 1:
                    func(*args, **kwargs)
                    time.sleep(interval)
            else:
                while _times:
                    func(*args, **kwargs)
                    time.sleep(interval)
                    _times -= 1
        return _decorator
    return decorator


def async_activation_request(*args, **kwargs):
    t = threading.Thread(target=activation_request, args=args, kwargs=kwargs)
    t.setDaemon(True)
    t.start()
    return t


def async_app_request(*args, **kwargs):
    t = threading.Thread(target=app_request, args=args)
    t.setDaemon(True)
    t.start()
    return t


