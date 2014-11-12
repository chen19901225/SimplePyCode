#coding:utf-8
import datetime
import pymongo
import setting
import os
__author__ = 'cqh'
import bottle


app=application=bottle.Bottle()

bottle.debug(True)


@app.route('/static/<file_name:path>')
def get_static(file_name):
    form_pattern,extension=os.path.splitext(file_name)
    if not extension:
        return None
    extension=extension[1:]
    mime_type='text/plain'
    if extension in ('png','jpg'):
        mime_type='text/'+extension

    return bottle.static_file(file_name,setting.staic_path)


@app.route('/hello')
def hello_world():
    return "Hello"



@app.route('/')
def index():
    #return "Hello wrld"
    return bottle.static_file('templates/base.html',setting.root_path,mimetype='text/html')
    #return None
    return "This is the main page ! now time is "+str(datetime.datetime.now())







if __name__=="__main__":
    bottle.run(host='127.0.0.1',port='8082',reload=True,app=app)

