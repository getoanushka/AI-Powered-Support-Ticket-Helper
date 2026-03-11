import requests
import json

def pretty(r):
    print('STATUS:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)

BASE='http://localhost:8000'
print('GET /')
r = requests.get(BASE+'/')
pretty(r)

print('\nGET /api/tickets')
r = requests.get(BASE+'/api/tickets')
pretty(r)

print('\nPOST /api/analyze-ticket')
payload={'ticket_text':'I cannot login to my account after the password reset link. The email link shows 404.'}
r = requests.post(BASE+'/api/analyze-ticket', json=payload)
pretty(r)
