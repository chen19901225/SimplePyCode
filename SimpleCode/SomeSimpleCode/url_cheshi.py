#!/usr/bin/python
#coding:utf-8
import httplib,urllib
import sys

def sendsms(mobile,content):
    conn = None
    try:
        params = 'uid=310004&pwd=bbdfe0e2d6f0772a418f13b14540ddce&mobile='+mobile+'&content='+content+'【广州嘉航】'
        headers = {"Content-Type":"application/x-www-form-urlencoded","Connection":"Keep-Alive","Referer":"http://202.85.221.42:9885/c123/sendsms?"}
        conn = httplib.HTTPConnection("202.85.221.42:9885")
        conn.request("POST","/c123/sendsms",params.decode('utf-8').encode('gb2312'),headers)
        response = conn.getresponse()
        print response.read()
        #if response.status == 200 and response.read() ==100:
        #               print "发布成功!^_^!"
        #       else:
        #               print "发布失败\^0^/"
    except Exception,e:
        print e
    finally:
        if conn:
            conn.close()

#sendsms(sys.argv[1],sys.argv[2])

if __name__=="__main__":
    sendsms('15914354390','中文')

