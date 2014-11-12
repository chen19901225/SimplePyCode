
import requests

url='http://httpbin.org/get?name=Dave&n=37'
r=requests.get(url,
               headers={'User-agent':'goaway/1.0'})
resp=r.json
print resp["header"]
print resp['args']