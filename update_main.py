import re

with open("code/main.py", "r", encoding="utf-8") as f:
    code = f.read()

import_stmt = "from llm_utils import extract_amount_from_image, interpret_message_intent, generate_final_decision\n"
code = code.replace("from datetime import datetime, timedelta\n", "from datetime import datetime, timedelta\n" + import_stmt)

preprocess_code = """
def preprocess_data(data):
    \"\"\"
    Apply multi-modal OCR for missing amounts and interpret messages for event updates.
    \"\"\"
    # 1. OCR
    images_by_event = {row['related_event_id']: row['image_id'] for row in data['images'] if row.get('related_event_id')}
    for event in data['events']:
        if not event['amount'].strip():
            event_id = event['event_id']
            image_id = images_by_event.get(event_id)
            if image_id:
                img_path = os.path.join(DATA_DIR, "media", "images", f"{image_id}.png")
                extracted_amount = extract_amount_from_image(img_path)
                event['amount'] = str(extracted_amount)
    
    # 2. Interpret Messages
    messages_by_event = defaultdict(list)
    for msg in data['messages']:
        if msg.get('related_event_id'):
            messages_by_event[msg['related_event_id']].append(msg)
            
    for event in data['events']:
        event_id = event['event_id']
        if event_id in messages_by_event:
            for msg in sorted(messages_by_event[event_id], key=lambda x: x['sent_at']):
                update = interpret_message_intent(msg['message_text'])
                if update.is_cancelled:
                    event['status'] = 'cancelled'
                if update.new_amount is not None:
                    event['amount'] = str(update.new_amount)
                if update.new_date:
                    event['event_date'] = update.new_date
"""

code = code.replace("def load_data():", preprocess_code + "\n\ndef load_data():")

main_replacement = """def main():
    \"\"\"
    Entry point for the evaluation process.
    Explicit intent: Orchestrate data loading, iterative evaluation, and output writing.
    \"\"\"
    data = load_data()
    preprocess_data(data)
    forecaster = FinancialForecaster(data)"""

code = code.replace("""def main():
    \"\"\"
    Entry point for the evaluation process.
    Explicit intent: Orchestrate data loading, iterative evaluation, and output writing.
    \"\"\"
    data = load_data()
    forecaster = FinancialForecaster(data)""", main_replacement)


# We also want to replace the manual evaluation logic in evaluate_request with the LLM final decision
eval_req = """def evaluate_request(request_row, data, forecaster):
    \"\"\"
    Core logic to evaluate a single request.
    V3: Uses deterministic 90-day cashflow as context for the LLM to make the final decision.
    \"\"\"
    req_id = request_row['request_id']
    user_id = request_row['user_id']
    request_date = request_row['request_date']
    requested_amount = float(request_row['requested_amount'])
    
    profile = next((p for p in data['profiles'] if p['user_id'] == user_id), None)
    home_currency = profile['home_currency'] if profile else 'USD'
    current_balance = float(profile['current_available_balance']) if profile else 0.0
    min_balance = float(profile['minimum_balance_to_keep']) if profile else 0.0
    
    forecast_balances = forecaster.run_90_day_forecast(user_id, request_date, current_balance, home_currency)
    min_projected_balance = min(forecast_balances)
    base_safe_amount = max(0.0, min_projected_balance - min_balance)
    
    # Gather Context for LLM
    import json
    
    context = f"Request: {json.dumps(request_row)}\\n"
    context += f"Profile: {json.dumps(profile)}\\n"
    context += f"90-Day Deterministic Minimum Projected Balance: {min_projected_balance}\\n"
    context += f"Deterministic Base Safe Amount (without spending changes): {base_safe_amount}\\n"
    
    # Pass user messages for personalized constraints (e.g. willingness to stop subscriptions)
    user_messages = [m for m in data['messages'] if m['user_id'] == user_id]
    context += f"User Messages: {json.dumps(user_messages)}\\n"
    
    user_options = [o for o in data['options'] if o['request_id'] == req_id]
    context += f"Payment Options: {json.dumps(user_options)}\\n"
    
    # Generate final decision
    decision = generate_final_decision(context)
    
    return {
        'request_id': req_id,
        'amount_safe_to_pay': decision.amount_safe_to_pay,
        'affordability_status': decision.affordability_status,
        'recommended_payment_method': decision.recommended_payment_method,
        'payment_plan': decision.payment_plan,
        'earliest_date_for_full_payment': decision.earliest_date_for_full_payment,
        'spending_changes_needed': decision.spending_changes_needed,
        'decision_explanation': decision.decision_explanation
    }"""

# Find and replace the function evaluate_request
import ast
 # Not available probably. I'll just use regex.
import re

pattern = re.compile(r"def evaluate_request\(.*?return \{.*?\}", re.DOTALL)
code = pattern.sub(eval_req, code)

with open("code/main.py", "w", encoding="utf-8") as f:
    f.write(code)
