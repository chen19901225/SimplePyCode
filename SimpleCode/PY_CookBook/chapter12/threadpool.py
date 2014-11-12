import urllib

def fetch_url(url):
    u=urllib.urlopen(url)
    data=u.read()
    return data


pool=ThreadPoolExecutor(10)