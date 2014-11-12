
import urllib

url='http://www.baidu.com'

params=dict(name1='value1',name2='value2')

querystring=urllib.urlencode(params)

u=urllib.urlopen(url+'?'+querystring)
resp=u.read()
print resp
