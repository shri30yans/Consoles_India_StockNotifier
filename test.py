import requests
from itertools import cycle
import traceback
#If you are copy pasting proxy ips, put in the list below
proxies = ['209.40.237.43']
proxy_pool = cycle(proxies)
url = 'https://httpbin.org/ip'
while True:
    proxy = next(proxy_pool)
    print("Request" )
    try:
        response = requests.get(url,proxies={"http": proxy, "https": proxy})
        print(response.json())
    except:
    #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work. 
    #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url 
        print("Skipping. Connnection error")