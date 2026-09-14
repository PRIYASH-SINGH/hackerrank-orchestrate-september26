import csv

def load_csv(path):
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

events = load_csv('dataset/financial_events.csv')
statuses = set(e['status'] for e in events)
print("Statuses:", statuses)

pending_credits = sum(1 for e in events if e['status'] == 'pending' and e['direction'] == 'credit')
pending_debits = sum(1 for e in events if e['status'] == 'pending' and e['direction'] == 'debit')
scheduled = sum(1 for e in events if e['status'] == 'scheduled')
print(f"Pending credits: {pending_credits}, Pending debits: {pending_debits}, Scheduled: {scheduled}")
