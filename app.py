"""FitFinder - Canonical backend (fresh copy)

This file will replace the corrupted `app.py`.
"""

import os
import io
import time
import json
import base64
from datetime import datetime
import os
import io
import time
import json
import base64
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from PIL import Image
import sqlite3

DB_NAME = os.path.join(os.path.dirname(__file__), 'users.db')


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
GENERATED_FOLDER = os.path.join(APP_ROOT, 'generated_outfits')
TMP_FOLDER = os.path.join(APP_ROOT, 'tmp')
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(TMP_FOLDER, exist_ok=True)


app = Flask(__name__, static_folder='static')
CORS(app)


# Miragic configuration
API_KEY = os.environ.get('MIRAGIC_API_KEY')
BASE_URL = 'https://backend.miragic.ai'


def _post_files(url, data, files):
    opened = []
    multipart = []
    try:
        for key, (filename, path, content_type) in files:
            f = open(path, 'rb')
            opened.append(f)
            multipart.append((key, (filename, f, content_type)))

        headers = {'X-API-Key': API_KEY}
        resp = requests.post(url, headers=headers, data=data, files=multipart)
        return resp
    finally:
        for f in opened:
            try:
                f.close()
            except Exception:
                pass


def create_vto_job_single(human_path, cloth_path, garment_type='full_body'):
    url = f"{BASE_URL}/api/v1/virtual-try-on"
    data = {'garmentType': garment_type}
    files = [
        ('humanImage', (os.path.basename(human_path), human_path, 'image/jpeg')),
        ('clothImage', (os.path.basename(cloth_path), cloth_path, 'image/jpeg')),
    ]
    return _post_files(url, data, files)


def create_vto_job_combo(human_path, top_path, bottom_path, garment_type='comb'):
    url = f"{BASE_URL}/api/v1/virtual-try-on"
    data = {'garmentType': garment_type}
    files = [
        ('humanImage', (os.path.basename(human_path), human_path, 'image/jpeg')),
        ('clothImage', (os.path.basename(top_path), top_path, 'image/jpeg')),
        ('bottomClothImage', (os.path.basename(bottom_path), bottom_path, 'image/jpeg')),
    ]
    return _post_files(url, data, files)


def poll_job(job_id, timeout_sec=60, interval_sec=2):
    start = time.time()
    url = f"{BASE_URL}/api/v1/virtual-try-on/{job_id}"
    headers = {'X-API-Key': API_KEY}

    while True:
        resp = requests.get(url, headers=headers)
        try:
            data = resp.json()
        except Exception:
            data = {'success': False, 'error': 'invalid json response', 'raw': resp.text}

        try:
            status = data['data']['status']
        except Exception:
            return {'success': False, 'error': 'unexpected response', 'raw': data}

        if status in ('COMPLETED', 'FAILED'):
            return data

        if time.time() - start > timeout_sec:
            return {'success': False, 'error': 'Polling timeout', 'raw': data}

        time.sleep(interval_sec)


def _image_to_datauri(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    b = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/png;base64,{b}'


def local_fallback_single(human_path, cloth_path):
    try:
        human = Image.open(human_path).convert('RGBA')
        cloth = Image.open(cloth_path).convert('RGBA')
        cloth = cloth.resize((int(human.width * 0.6), int(human.height * 0.6)))
        out = Image.new('RGBA', human.size)
        out.paste(human, (0, 0))
        x = (human.width - cloth.width) // 2
        y = int(human.height * 0.25)
        out.paste(cloth, (x, y), cloth)
        out = out.convert('RGB')

        filename = f"virtual_tryon_fallback_{int(time.time()*1000)}.png"
        path = os.path.join(GENERATED_FOLDER, filename)
        out.save(path, format='PNG')

        return {'success': True, 'note': 'local_fallback', 'file': filename, 'image': _image_to_datauri(out)}
    except Exception as e:
        return {'success': False, 'error': 'local fallback failed', 'details': str(e)}


@app.route('/api/tryon/single', methods=['POST'])
def tryon_single():
    garment_type = request.form.get('garmentType', 'full_body')

    human_file = request.files.get('humanImage')
    cloth_file = request.files.get('clothImage')
    if human_file is None or cloth_file is None:
        return jsonify({'success': False, 'error': 'humanImage and clothImage are required'}), 400

    human_path = os.path.join(TMP_FOLDER, f"human_{int(time.time()*1000)}.jpg")
    cloth_path = os.path.join(TMP_FOLDER, f"cloth_{int(time.time()*1000)}.jpg")
    human_file.save(human_path)
    cloth_file.save(cloth_path)

    if API_KEY:
        resp = create_vto_job_single(human_path, cloth_path, garment_type)
        try:
            os.remove(human_path)
            os.remove(cloth_path)
        except OSError:
            pass

        if not resp.ok:
            return jsonify({'success': False, 'error': 'Miragic request failed', 'details': resp.text}), 500

        data = resp.json()
        if not data.get('success'):
            return jsonify({'success': False, 'error': 'Miragic returned error', 'details': data}), 500

        job_id = data['data'].get('jobId')
        if not job_id:
            return jsonify({'success': False, 'error': 'no job id returned', 'details': data}), 500

        job_result = poll_job(job_id)
        return jsonify(job_result)
    else:
        result = local_fallback_single(human_path, cloth_path)
        try:
            os.remove(human_path)
            os.remove(cloth_path)
        except OSError:
            pass
        return jsonify(result)


@app.route('/api/tryon/combo', methods=['POST'])
def tryon_combo():
    garment_type = request.form.get('garmentType', 'comb')

    human_file = request.files.get('humanImage')
    top_file = request.files.get('clothImage')
    bottom_file = request.files.get('bottomClothImage')
    if human_file is None or top_file is None or bottom_file is None:
        return jsonify({'success': False, 'error': 'humanImage, clothImage, bottomClothImage are required'}), 400

    human_path = os.path.join(TMP_FOLDER, f"human_{int(time.time()*1000)}.jpg")
    top_path = os.path.join(TMP_FOLDER, f"top_{int(time.time()*1000)}.jpg")
    bottom_path = os.path.join(TMP_FOLDER, f"bottom_{int(time.time()*1000)}.jpg")
    human_file.save(human_path)
    top_file.save(top_path)
    bottom_file.save(bottom_path)

    if API_KEY:
        resp = create_vto_job_combo(human_path, top_path, bottom_path, garment_type)
        for p in [human_path, top_path, bottom_path]:
            try:
                os.remove(p)
            except OSError:
                pass

        if not resp.ok:
            return jsonify({'success': False, 'error': 'Miragic request failed', 'details': resp.text}), 500

        data = resp.json()
        if not data.get('success'):
            return jsonify({'success': False, 'error': 'Miragic returned error', 'details': data}), 500

        job_id = data['data'].get('jobId')
        if not job_id:
            return jsonify({'success': False, 'error': 'no job id returned', 'details': data}), 500

        job_result = poll_job(job_id)
        return jsonify(job_result)
    else:
        # Simple local combo fallback: overlay top and bottom onto human
        try:
            human = Image.open(human_path).convert('RGBA')
            top = Image.open(top_path).convert('RGBA')
            bottom = Image.open(bottom_path).convert('RGBA')
            top = top.resize((int(human.width * 0.6), int(human.height * 0.35)))
            bottom = bottom.resize((int(human.width * 0.6), int(human.height * 0.35)))
            out = Image.new('RGBA', human.size)
            out.paste(human, (0, 0))
            x = (human.width - top.width) // 2
            y_top = int(human.height * 0.2)
            y_bottom = int(human.height * 0.55)
            out.paste(top, (x, y_top), top)
            out.paste(bottom, (x, y_bottom), bottom)
            out = out.convert('RGB')

            filename = f"virtual_tryon_fallback_{int(time.time()*1000)}.png"
            path = os.path.join(GENERATED_FOLDER, filename)
            out.save(path, format='PNG')

            result = {'success': True, 'note': 'local_fallback', 'file': filename, 'image': _image_to_datauri(out)}
        except Exception as e:
            result = {'success': False, 'error': 'local fallback failed', 'details': str(e)}

        for p in [human_path, top_path, bottom_path]:
            try:
                os.remove(p)
            except OSError:
                pass

        return jsonify(result)


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'miragic': bool(API_KEY)})


# --- Simple login route using SQLite users.db ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/login', methods=['POST'])
def login():
    userid = request.form.get('userid')
    password = request.form.get('password')

    if not userid or not password:
        return jsonify({'success': False, 'message': 'User ID and password are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE userid = ? AND password = ?', (userid, password))
    user = cur.fetchone()
    conn.close()

    if user:
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)