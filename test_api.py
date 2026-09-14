import os
# Read API key from environment variable
if 'GEMINI_API_KEY' not in os.environ:
    os.environ['GEMINI_API_KEY'] = ''
from google import genai
from google.genai.errors import ClientError

client = genai.Client()
try:
    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents='hello'
    )
    print(response.text)
except Exception as e:
    print(f"Exception Type: {type(e)}")
    print(f"Exception args: {e.args}")
    if hasattr(e, 'code'):
        print(f"Code: {e.code}")
    print(f"Str: {str(e)}")
