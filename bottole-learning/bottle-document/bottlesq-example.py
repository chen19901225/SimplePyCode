__author__ = 'Administrator'

import bottle

app=bottle.Bottle()
plugin=bottle.ext.sqlite.Plugin(dbfile='/tmp/test.db')
app.install(plugin)

@bottle.app.route('/show/:item')
def show(item,db):
    row=db.execute('select * from items where name=?').fetchone()
    if row:
        return bottle.template('showitem',page=row)
    return bottle.HTTPError(404,'page not found')