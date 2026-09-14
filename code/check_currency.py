import csv

events = list(csv.DictReader(open('dataset/financial_events.csv', encoding='utf-8')))
profiles = {p['user_id']: p['home_currency'] for p in csv.DictReader(open('dataset/financial_profiles.csv', encoding='utf-8'))}
requests = list(csv.DictReader(open('dataset/requests.csv', encoding='utf-8')))

diff_currency_events = [e for e in events if e['currency'] != profiles[e['user_id']]]
print(f"Events with different currency: {len(diff_currency_events)}")
if diff_currency_events:
    print(f"Example: {diff_currency_events[0]}")
    
currencies = set(e['currency'] for e in events)
currencies.update(p['home_currency'] for p in profiles.values())
print(f"Currencies involved: {currencies}")
