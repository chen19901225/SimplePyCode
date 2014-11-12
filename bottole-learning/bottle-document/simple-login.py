import os
import re

__author__ = 'Administrator'

import bottle


#bottle.FormsDict
app=bottle.Bottle()
@bottle.get('/login')
def login():
    return """
    <form action='/login' method='post'>
    Username:<input name="username" type="text" />
    Password:<input  name="password" type="password"/>
    <button type='submit' text="submit"  name="submit"/>
    </form>
    """
@bottle.post('/login')
def do_login():
    username=bottle.request.forms.get('username')
    password=bottle.request.forms.get('password')
    if username=='ch' and password=='123456':
        return "<p>You login information was correct.</p>"
    else:
        return "<p>Login failed.</p>"
@bottle.route('/hello')
def hello_again():
    if bottle.request.get_cookie('visited'):
        return "Welcome back!Nice to see you again"
    else:
        bottle.response.set_cookie('visited','yes')
        return "Hello there!Nice to meet you "
@bottle.route('/is_ajax')
def is_ajax():
    if bottle.request.headers.get('X-Requested-With')=='XMLHttpRequest':
        return 'This is an Ajax request'
    else:
        return 'This is a normal request'

@bottle.route('/forum')
def display_forum():
    forum_id=bottle.request.query.id
    page=bottle.request.query.page or '1'
    return bottle.template('Form ID:{{id}} (page{{page}})',id=forum_id,page=page)

@bottle.get('/upload')
def upload():
    return """
    <form action="/upload" method="post" enctype="multipart/form-data">
    Category: <input type="text" name="category" />
    Select a file:<input type="file" name='upload' />
    </form>
    """
# @bottle.post('/upload')
# def do_upload():
#     category=bottle.request.forms.get('category')
#     upload=bottle.request.files.get('upload')
#     name,ext=os.path.splitext(upload.filename)
#     if ext not in ('.png','.jpg','.jpeg'):
#         return 'File extenstion not allowed'
#     save_path=get_save_path_for_category(category)
#     upload.save(save_path)
#     return 'OK'

def  list_filter(config):
    delimiter=config or ','
    regexp=r'\d+(%s\d)*'%re.escape(delimiter)

    def to_python(match):
        return map(int,match.split(delimiter))

    def to_url(numbers):
        return delimiter.join(map(str,numbers))

    return regexp,to_python,to_url

app.router.add_filter('list',list_filter)
@app.route('/follow/<ids:list>')
def follow_users(ids):
    return "Follow ids:{}".format(str(ids))
bottle.run(app=app,host='localhost',port='8081')