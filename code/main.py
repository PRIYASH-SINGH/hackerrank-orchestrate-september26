import csv
import os
import json
from collections import defaultdict
from datetime import datetime, timedelta
from llm_utils import extract_amounts_from_images, interpret_messages_intent_batch, generate_final_decisions_batch, tracker

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output.csv")

def read_csv_to_dicts(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def preprocess_data(data):
    # 1. OCR
    images_by_event = {row['related_event_id']: row['image_id'] for row in data['images'] if row.get('related_event_id')}
    
    ocr_tasks = []
    for event in data['events']:
        if not event['amount'].strip():
            event_id = event['event_id']
            image_id = images_by_event.get(event_id)
            if image_id:
                img_path = os.path.join(DATA_DIR, "media", "images", f"{image_id}.png")
                ocr_tasks.append((event, img_path))
                
    if ocr_tasks:
        image_paths = [task[1] for task in ocr_tasks]
        amounts = extract_amounts_from_images(image_paths)
        for task, amount in zip(ocr_tasks, amounts):
            task[0]['amount'] = str(amount)
            
    # 2. Interpret Messages
    messages_by_event = defaultdict(list)
    unlinked_messages = []
    for msg in data['messages']:
        if msg.get('related_event_id'):
            messages_by_event[msg['related_event_id']].append(msg)
        else:
            unlinked_messages.append(msg)
            
    messages_to_interpret = []
    
    for event in data['events']:
        event_id = event['event_id']
        if event_id in messages_by_event:
            for msg in sorted(messages_by_event[event_id], key=lambda x: x.get('sent_at', '')):
                messages_to_interpret.append((event, msg, True))
                
    for msg in sorted(unlinked_messages, key=lambda x: x.get('sent_at', '')):
        messages_to_interpret.append((None, msg, False))

    if messages_to_interpret:
        texts = [m[1]['message_text'] for m in messages_to_interpret]
        updates = interpret_messages_intent_batch(texts)
        for (event, msg, is_linked), update in zip(messages_to_interpret, updates):
            if is_linked:
                if update.is_cancelled:
                    event['status'] = 'cancelled'
                if update.new_amount is not None:
                    event['amount'] = str(update.new_amount)
                if update.new_date:
                    event['event_date'] = update.new_date
            else:
                if update.target_event_keyword:
                    keyword = update.target_event_keyword.lower()
                    for ev in data['events']:
                        if ev.get('user_id') == msg.get('user_id') and keyword in ev.get('description', '').lower():
                            if update.is_cancelled:
                                ev['status'] = 'cancelled'
                            if update.new_amount is not None:
                                ev['amount'] = str(update.new_amount)
                            if update.new_date:
                                ev['event_date'] = update.new_date

def load_data():
    print("Loading data...")
    return {
        "requests": read_csv_to_dicts(os.path.join(DATA_DIR, "requests.csv")),
        "profiles": read_csv_to_dicts(os.path.join(DATA_DIR, "financial_profiles.csv")),
        "events": read_csv_to_dicts(os.path.join(DATA_DIR, "financial_events.csv")),
        "options": read_csv_to_dicts(os.path.join(DATA_DIR, "request_payment_options.csv")),
        "rates": read_csv_to_dicts(os.path.join(DATA_DIR, "exchange_rates.csv")),
        "messages": read_csv_to_dicts(os.path.join(DATA_DIR, "messages.csv")),
        "images": read_csv_to_dicts(os.path.join(DATA_DIR, "images.csv"))
    }

class FinancialForecaster:
    def __init__(self, data):
        self.data = data
        self.rates = data.get('rates', [])
        self.events = data.get('events', [])
        
        self.rate_graph = defaultdict(lambda: defaultdict(dict))
        for r in self.rates:
            ym = r['rate_date'][:7]
            f_curr = r['from_currency']
            t_curr = r['to_currency']
            rate = float(r['rate'])
            
            self.rate_graph[ym][f_curr][t_curr] = rate
            self.rate_graph[ym][t_curr][f_curr] = 1.0 / rate

        self.latest_graph = defaultdict(dict)
        for r in self.rates:
            f_curr = r['from_currency']
            t_curr = r['to_currency']
            rate = float(r['rate'])
            self.latest_graph[f_curr][t_curr] = rate
            self.latest_graph[t_curr][f_curr] = 1.0 / rate
        
    def get_exchange_rate(self, from_currency, to_currency, date_str):
        if from_currency == to_currency:
            return 1.0
        
        target_ym = date_str[:7]
        graph = self.rate_graph.get(target_ym, self.latest_graph)
        
        queue = [(from_currency, 1.0)]
        visited = set([from_currency])
        
        while queue:
            curr, current_rate = queue.pop(0)
            if curr == to_currency:
                return current_rate
                
            for neighbor, rate in graph.get(curr, {}).items():
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, current_rate * rate))
                    
        return 1.0

    def get_recurring_events(self, user_id, request_date_str):
        user_events = [e for e in self.events if e['user_id'] == user_id]
        
        grouped = defaultdict(list)
        for e in user_events:
            if e['status'] != 'settled' or e['event_date'] >= request_date_str:
                continue
            if not e['amount'].strip():
                continue
            grouped[e['description']].append(e)
            
        recurring = []
        for desc, evs in grouped.items():
            if len(evs) > 1:
                evs.sort(key=lambda x: x['event_date'])
                dates = [datetime.strptime(e['event_date'], '%Y-%m-%d') for e in evs]
                diffs = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                avg_interval = sum(diffs) / len(diffs)
                
                if avg_interval <= 0:
                    continue
                    
                is_recurring = False
                if len(evs) >= 3 and (max(diffs) - min(diffs)) <= 10:
                    is_recurring = True
                elif evs[0]['event_type'] in ['subscription', 'debt_payment']:
                    is_recurring = True
                    
                if is_recurring:
                    recurring.append({
                        'description': desc,
                        'category': evs[-1]['category'],
                        'direction': evs[-1]['direction'],
                        'amount': float(evs[-1]['amount']),
                        'currency': evs[-1]['currency'],
                        'last_date': evs[-1]['event_date'],
                        'avg_interval': avg_interval,
                        'flexibility': evs[-1]['flexibility']
                    })
        return recurring

    def get_future_confirmed_events(self, user_id, request_date_str):
        user_events = [e for e in self.events if e['user_id'] == user_id]
        future_events = []
        for e in user_events:
            if e['event_date'] >= request_date_str:
                if e['status'] == 'scheduled' or e['status'] == 'pending':
                    if e['amount'].strip():
                        future_events.append({
                            'description': e['description'],
                            'direction': e['direction'],
                            'amount': float(e['amount']),
                            'currency': e['currency'],
                            'date': e['event_date']
                        })
        return future_events

    def run_90_day_forecast(self, user_id, request_date_str, current_balance, home_currency):
        req_date = datetime.strptime(request_date_str, '%Y-%m-%d')
        recurring = self.get_recurring_events(user_id, request_date_str)
        future_confirmed = self.get_future_confirmed_events(user_id, request_date_str)
        
        balances = [current_balance]
        balance = current_balance
        
        for day_offset in range(1, 91):
            curr_date = req_date + timedelta(days=day_offset)
            curr_date_str = curr_date.strftime('%Y-%m-%d')
            
            for r in recurring:
                last_date = datetime.strptime(r['last_date'], '%Y-%m-%d')
                days_since = (curr_date - last_date).days
                interval = max(1, round(r['avg_interval']))
                
                if days_since > 0 and days_since % interval == 0:
                    has_scheduled = any(f['description'] == r['description'] and f['date'] == curr_date_str for f in future_confirmed)
                    if not has_scheduled:
                        rate = self.get_exchange_rate(r['currency'], home_currency, curr_date_str)
                        amount_home = r['amount'] * rate
                        if r['direction'] == 'debit':
                            balance -= amount_home
                        else:
                            balance += amount_home
                            
            for f in future_confirmed:
                if f['date'] == curr_date_str:
                    rate = self.get_exchange_rate(f['currency'], home_currency, curr_date_str)
                    amount_home = f['amount'] * rate
                    if f['direction'] == 'debit':
                        balance -= amount_home
                    else:
                        balance += amount_home
                        
            balances.append(balance)
            
        return balances

def main():
    data = load_data()
    preprocess_data(data)
    forecaster = FinancialForecaster(data)
    
    print(f"Evaluating {len(data['requests'])} requests...")
    contexts = []
    
    for row in data['requests']:
        req_id = row['request_id']
        user_id = row['user_id']
        request_date = row['request_date']
        
        profile = next((p for p in data['profiles'] if p['user_id'] == user_id), None)
        home_currency = profile['home_currency'] if profile else 'USD'
        current_balance = float(profile['current_available_balance']) if profile else 0.0
        min_balance = float(profile['minimum_balance_to_keep']) if profile else 0.0
        
        forecast_balances = forecaster.run_90_day_forecast(user_id, request_date, current_balance, home_currency)
        min_projected_balance = min(forecast_balances)
        base_safe_amount = max(0.0, min_projected_balance - min_balance)
        
        context = f"Request: {json.dumps(row)}\n"
        context += f"Profile: {json.dumps(profile)}\n"
        context += f"90-Day Deterministic Minimum Projected Balance: {min_projected_balance}\n"
        context += f"Deterministic Base Safe Amount (without spending changes): {base_safe_amount}\n"
        
        user_messages = [m for m in data['messages'] if m['user_id'] == user_id]
        context += f"User Messages: {json.dumps(user_messages)}\n"
        
        user_options = [o for o in data['options'] if o['request_id'] == req_id]
        context += f"Payment Options: {json.dumps(user_options)}\n"
        
        contexts.append(context)
        
    decisions = generate_final_decisions_batch(contexts)
    
    results = []
    for row, dec in zip(data['requests'], decisions):
        if dec is None:
            # Fallback if something fails
            results.append({
                'request_id': row['request_id'],
                'amount_safe_to_pay': 0.0,
                'affordability_status': 'error',
                'recommended_payment_method': 'none',
                'payment_plan': 'none',
                'earliest_date_for_full_payment': '',
                'spending_changes_needed': '',
                'decision_explanation': 'Failed to process'
            })
            continue
            
        results.append({
            'request_id': row['request_id'],
            'amount_safe_to_pay': dec.amount_safe_to_pay,
            'affordability_status': dec.affordability_status,
            'recommended_payment_method': dec.recommended_payment_method,
            'payment_plan': dec.payment_plan,
            'earliest_date_for_full_payment': dec.earliest_date_for_full_payment,
            'spending_changes_needed': dec.spending_changes_needed,
            'decision_explanation': dec.decision_explanation
        })
        
    columns = [
        'request_id', 'amount_safe_to_pay', 'affordability_status', 
        'recommended_payment_method', 'payment_plan', 
        'earliest_date_for_full_payment', 'spending_changes_needed', 
        'decision_explanation'
    ]
    
    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Evaluation complete. Output written to {OUTPUT_FILE}")
    
    eval_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'evaluation')
    os.makedirs(eval_dir, exist_ok=True)
    report_path = os.path.join(eval_dir, 'usage_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Token Usage Report\n\n")
        f.write(f"- Prompt Tokens: {tracker.prompt_tokens}\n")
        f.write(f"- Completion Tokens: {tracker.candidates_tokens}\n")
        f.write(f"- Total Tokens: {tracker.total_tokens}\n")
    print(f"Usage report generated at {report_path}")

if __name__ == "__main__":
    main()
