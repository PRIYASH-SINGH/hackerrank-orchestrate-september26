import urllib.request
import time
import os
key = os.environ.get('GEMINI_API_KEY', '')
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent?key={key}'
data = b'{"contents":[{"parts":[{"text":"hi"}]}]}'
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    print(urllib.request.urlopen(req).read().decode())
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
