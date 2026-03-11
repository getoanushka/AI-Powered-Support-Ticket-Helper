import requests, json
BASE='http://localhost:8000'
payload={'ticket_text':'My password reset link returns 404 and I cannot login.'}
res = requests.post(BASE+'/api/recommend', json=payload)
print('STATUS', res.status_code)
try:
    print(json.dumps(res.json(), indent=2))
except Exception:
    print(res.text)
