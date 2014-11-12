#coding:utf-8
import re

import sqlite3
import bottle

bottle.debug(True)

app=application=bottle.Bottle()
@bottle.route('/hello/<name>')
def try_test(name):

    return "Welcome! "+name
@bottle.route("/digit/<num:int>")
def show_num(num):
    return "You enter :"+num

if __name__=="__main__":
    bottle.run(host='localhost',port=8080,reloader=True)
