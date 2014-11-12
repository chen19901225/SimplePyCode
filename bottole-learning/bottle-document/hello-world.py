from bottle import route, template, run

@route('/')
@route('/hello/<name>')
def index(name='Stranger'):
    return template('<b>Hello{{name}}</b>!',name=name)


run(host='localhost',port=8080)
