import requests, json, time
payload={'scene':'casual','style':'minimalist','gender':'female'}
for i in range(12):
    try:
        r = requests.post('http://127.0.0.1:5000/api/generate-outfit', json=payload, timeout=120)
        out = {'status': r.status_code, 'text': r.text}
        with open('last_generate.json', 'w', encoding='utf-8') as f:
            json.dump(out, f)
        print('SAVED')
        break
    except Exception as e:
        print('wait', i, str(e))
        time.sleep(1)
else:
    with open('last_generate.json', 'w', encoding='utf-8') as f:
        json.dump({'error': 'timeout'}, f)
print('done')
