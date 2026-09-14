import os
import json
import time
import hashlib
import urllib.request
import urllib.error
import base64

class TokenTracker:
    def __init__(self):
        self.prompt_tokens = 0
        self.candidates_tokens = 0
        self.total_tokens = 0

    def add(self, prompt: int, candidates: int):
        self.prompt_tokens += prompt
        self.candidates_tokens += candidates
        self.total_tokens += (prompt + candidates)

tracker = TokenTracker()

def _get_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return api_key

CACHE_FILE = 'llm_cache.json'
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(c):
    with open(CACHE_FILE, 'w') as f:
        json.dump(c, f)

global_cache = load_cache()

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def call_gemini_api(payload: dict) -> dict:
    import sys
    print("Calling Gemini API...", flush=True)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={_get_api_key()}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    retries = 20
    delay = 2
    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
            if e.code == 429 or e.code >= 500:
                if i < retries - 1:
                    sleep_time = delay
                    if e.code == 429:
                        try:
                            err_json = json.loads(err_body)
                            for detail in err_json.get('error', {}).get('details', []):
                                if 'retryDelay' in detail:
                                    delay_str = detail['retryDelay'].replace('s', '')
                                    sleep_time = float(delay_str) + 1
                        except Exception:
                            pass
                    print(f"Rate limit or server error hit. Retrying in {sleep_time} seconds... Error: {e}")
                    time.sleep(sleep_time)
                    delay = min(delay * 2, 8)
                    continue
            raise RuntimeError(f"HTTP {e.code}: {err_body}")
        except Exception as e:
            if i < retries - 1:
                print(f"Request failed. Retrying in {delay} seconds... Error: {e}")
                time.sleep(delay)
                delay = min(delay * 2, 8)
                continue
            raise
    raise Exception("Max retries exceeded")

class Dummy:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def extract_amounts_from_images(image_paths: list[str]) -> list[float]:
    if not image_paths:
        return []
    
    final_amounts = []
    
    for batch_paths in chunk_list(image_paths, 2):
        cache_key = f"batch_img_{hashlib.md5(str(batch_paths).encode()).hexdigest()}"
        if cache_key in global_cache:
            cached = global_cache[cache_key]
            tracker.add(cached['prompt_tokens'], cached['candidates_tokens'])
            final_amounts.extend(cached['result'])
            continue
            
        valid_indices = []
        parts = [{"text": "Extract the final total amount from each receipt or image. Output the result in JSON as a list in the same order. Return {\"amounts\": [1.23, 0.0]}."}]
        for i, p in enumerate(batch_paths):
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img_data
                    }
                })
                valid_indices.append(i)
                
        if len(parts) == 1:
            final_amounts.extend([0.0] * len(batch_paths))
            continue
            
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        
        response = call_gemini_api(payload)
        
        usage = response.get("usageMetadata", {})
        p_tokens = usage.get("promptTokenCount", 0)
        c_tokens = usage.get("candidatesTokenCount", 0)
        tracker.add(p_tokens, c_tokens)
        
        text = response['candidates'][0]['content']['parts'][0]['text']
        try:
            result = json.loads(text)
        except:
            print("Failed to parse JSON for images:", text)
            result = {}
        amounts = result.get("amounts", [])
        
        while len(amounts) < len(valid_indices):
            amounts.append(0.0)
            
        batch_results = [0.0] * len(batch_paths)
        for i, idx in enumerate(valid_indices):
            try:
                batch_results[idx] = float(amounts[i])
            except:
                batch_results[idx] = 0.0
            
        global_cache[cache_key] = {
            'result': batch_results,
            'prompt_tokens': p_tokens,
            'candidates_tokens': c_tokens
        }
        save_cache(global_cache)
        final_amounts.extend(batch_results)
        time.sleep(2)
        
    return final_amounts


def interpret_messages_intent_batch(messages: list[str]) -> list[Dummy]:
    if not messages:
        return []
    
    final_updates = []
    
    for batch_msgs in chunk_list(messages, 10):
        cache_key = f"batch_msg_{hashlib.md5(str(batch_msgs).encode('utf-8')).hexdigest()}"
        if cache_key in global_cache:
            cached = global_cache[cache_key]
            tracker.add(cached['prompt_tokens'], cached['candidates_tokens'])
            final_updates.extend([Dummy(**u) for u in cached['result']])
            continue
            
        prompt = "Analyze the following messages and extract any updates to the financial event. Return a list of updates corresponding to the order of the messages. Output a JSON object with {\"updates\": [{\"is_cancelled\": false, \"new_amount\": 1.23, \"new_date\": \"2023-01-01\", \"target_event_keyword\": \"keyword\"}]}\nIf a field is missing, omit it or set it to null.\n\n"
        for i, m in enumerate(batch_msgs):
            prompt += f"Message {i}: {m}\n"
            
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        
        response = call_gemini_api(payload)
        
        usage = response.get("usageMetadata", {})
        p_tokens = usage.get("promptTokenCount", 0)
        c_tokens = usage.get("candidatesTokenCount", 0)
        tracker.add(p_tokens, c_tokens)
        
        text = response['candidates'][0]['content']['parts'][0]['text']
        try:
            result = json.loads(text)
        except:
            print("Failed to parse JSON for messages:", text)
            result = {}
        updates = result.get("updates", [])
        
        while len(updates) < len(batch_msgs):
            updates.append({"is_cancelled": False, "new_amount": None, "new_date": None, "target_event_keyword": None})
            
        for u in updates:
            for k in ["is_cancelled", "new_amount", "new_date", "target_event_keyword"]:
                if k not in u:
                    u[k] = False if k == "is_cancelled" else None
            
        global_cache[cache_key] = {
            'result': updates,
            'prompt_tokens': p_tokens,
            'candidates_tokens': c_tokens
        }
        save_cache(global_cache)
        final_updates.extend([Dummy(**u) for u in updates])
        time.sleep(2)
        
    return final_updates

def generate_final_decisions_batch(contexts: list[str]) -> list[Dummy]:
    if not contexts:
        return []
        
    final_decisions = []
    
    for batch_ctx in chunk_list(contexts, 5):
        cache_key = f"batch_dec_{hashlib.md5(str(batch_ctx).encode('utf-8')).hexdigest()}"
        if cache_key in global_cache:
            cached = global_cache[cache_key]
            tracker.add(cached['prompt_tokens'], cached['candidates_tokens'])
            final_decisions.extend([Dummy(**d) for d in cached['result']])
            continue
            
        prompt = "Based on the following financial contexts, generate the final payment recommendations. Return a list of decisions corresponding to the order of the contexts. Output a JSON object with {\"decisions\": [{\"request_id\": \"req1\", \"amount_safe_to_pay\": 1.23, \"affordability_status\": \"status\", \"recommended_payment_method\": \"method\", \"payment_plan\": \"plan\", \"earliest_date_for_full_payment\": \"date\", \"spending_changes_needed\": \"changes\", \"decision_explanation\": \"expl\"}]}\n\n"
        for i, c in enumerate(batch_ctx):
            prompt += f"--- Context {i} ---\n{c}\n"
            
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0
            }
        }
        
        response = call_gemini_api(payload)
        
        usage = response.get("usageMetadata", {})
        p_tokens = usage.get("promptTokenCount", 0)
        c_tokens = usage.get("candidatesTokenCount", 0)
        tracker.add(p_tokens, c_tokens)
        
        text = response['candidates'][0]['content']['parts'][0]['text']
        try:
            result = json.loads(text)
        except:
            print("Failed to parse JSON for decisions:", text)
            result = {}
        decisions = result.get("decisions", [])
        
        global_cache[cache_key] = {
            'result': decisions,
            'prompt_tokens': p_tokens,
            'candidates_tokens': c_tokens
        }
        save_cache(global_cache)
        final_decisions.extend([Dummy(**d) for d in decisions])
        time.sleep(2)
        
    return final_decisions
