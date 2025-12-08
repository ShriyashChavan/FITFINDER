import requests

url = 'http://127.0.0.1:5000/api/virtual-try-on'
files = {
    'person_image': ('test_person.jpg', open('tests/test_person.jpg', 'rb'), 'image/jpeg'),
    'cloth_image': ('test_cloth.png', open('tests/test_cloth.png', 'rb'), 'image/png')
}
try:
    r = requests.post(url, files=files, timeout=15)
    print('STATUS', r.status_code)
    try:
        print('JSON:', r.json())
    except Exception:
        print('TEXT:', r.text[:400])
except Exception as e:
    print('ERR', e)
