#!bin/usr/bin python
#coding:utf-8
from email.mime.text import MIMEText
import json
import os
import smtplib
import urllib
import urllib2
import time

url="http://api.wooyun.org/auth/b0047a58245fcb36f42975dfecb2b15d/bugs/limit/10"
mail_tolist="2813274210@qq.com"#这里填接受人的邮箱
mail_host="smtp.qq.com"
mail_user="1832866299"#这里填你的QQ号码
mail_pass="Chen19901225"#这里填你的QQ密码
mail_postfix="qq.com"


def send_email(title,content):
    me=mail_user+"<"+mail_user+"@"+mail_postfix+">"
    msg=MIMEText(content,_charset='utf-8')
    msg['Subject']=title
    msg['From']=me
    msg['To']=mail_tolist
    try:
        s=smtplib.SMTP()
        s.connect(mail_host)
        s.login(mail_user,mail_pass)
        s.sendmail(me,mail_tolist,msg.as_string())
        s.close()
        print 'Over'
        return True
    except Exception,e:
        print 'Error'
        print str(e)
        return False

def produce_format_str(out_no,title,status,date,link):
    re_str=u"错误{out_no}: {line_sep}{indent_sep}标题{title}:{line_sep}{indent_sep}状态：{status}{line_sep}{indent_sep}时间：{date}{line_sep}\
    {indent_sep}URL:{link}{line_sep}".format(out_no=out_no,title=title,status=status,date=date,link=link,line_sep=os.linesep,indent_sep=' '*4)

    return re_str

def get_content_title():
    global data, params, url_reqest, response, page_str, page_data, title, content_str, per_dict, status, date, link, new_dict
    data = dict()
    params = urllib.urlencode(data)
    url_reqest = urllib2.Request(url, params)
    response = urllib2.urlopen(url, timeout=15)
    page_str = response.read()
    page_data = json.loads(page_str)
    title, content_str = None, ""
    count_index=1
    for per_dict in page_data:
        per_dict['status'] = int(per_dict.get('status', '0'))
        title, status, date, link = per_dict['title'], per_dict['status'], per_dict['date'], per_dict['link']
        if status == 0:
            new_dict = dict(title=title, status=status, data=data, link=link)
            content_str += produce_format_str(count_index,title,status,date,link)
            count_index+=1
            if not title:
                title = date
    return title,content_str

def main():
    title,content_str=get_content_title()
    if not content_str:
        return
    else:
        send_email(title,content=content_str)

if __name__=="__main__":
    try_index=1
    while True:
        main()
        print 'No.{} try ok'.format(try_index)
        try_index+=1
        break
        time.sleep(30)


    print "over"











