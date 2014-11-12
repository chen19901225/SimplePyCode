#coding=utf-8
import os,re,datetime
_curDir=os.path.dirname(__file__)
_logfile_name='request_diary.txt'
full_request_logfile_name=os.path.join(_curDir,_logfile_name)
import logging
logger=logging.getLogger()
fileHandler=logging.FileHandler(full_request_logfile_name)
logger.addHandler(fileHandler)
logger.setLevel(logging.NOTSET)
re_getaction=re.compile('(?<=a\=)([^&]+)')
action_description_dict={
        u"getvcard":u"第二版获取名片详情",
        u"login":u"用户登录",
        u"getloginfobykey":u"通过会话ID获取登录信息"
    }


def loginfo(url_request):
    action=re_getaction.search(url_request).groups()[0]
    if not action:
        return
    action_des_str=get_description_from_action(action)
    loginfo=u"""
    {1}{0}{1}
    操作描述：{2}
    操作链接:{3}
    {1}{0}{1}

    """.format(datetime.datetime.now(),
               '-'*20,
               action_des_str,
               url_request)
    global  logger
    logger.info(loginfo)
    logger.info(os.linesep)

def get_description_from_action(action_name):
    global  action_description_dict
    description_value=action_description_dict.get(action_name.lower(),u"该操作未知道"+action_name)
    return description_value


