import urllib.request
import time
import os
key = os.environ.get('GEMINI_API_KEY', '')
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={key}'
data = b'{"contents":[{"parts":[{"text":"hi"}]}]}'
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

for i in range(3):
    try:
        print("Try", i)
        print(urllib.request.urlopen(req).read())
        break
    except Exception as e:
        print("Error 3.6:", e)
        if hasattr(e, 'read'):
            err = e.read().decode()
            print(err)
            if 'retryDelay' in err:
                time.sleep(16)
