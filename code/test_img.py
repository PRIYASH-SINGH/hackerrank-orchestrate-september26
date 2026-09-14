import urllib.request
import base64
import os
import json
key = os.environ.get('GEMINI_API_KEY', '')
url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:generateContent?key={key}'

p = "dataset/media/images/E-012.png"
with open(p, 'rb') as f:
    img_data = base64.b64encode(f.read()).decode('utf-8')

data = json.dumps({
    "contents": [{"parts": [{"text": "Extract"}, {"inline_data": {"mime_type": "image/png", "data": img_data}}]}]
}).encode()

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    print(urllib.request.urlopen(req).read().decode()[:200])
except Exception as e:
    print(e)
    if hasattr(e, 'read'):
        print(e.read().decode())
