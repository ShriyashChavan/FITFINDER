"""FitFinder - Canonical backend (fresh copy)

This file will replace the corrupted `app.py`.
"""

import os
import io
import time
import json
import base64
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import requests
from PIL import Image, ImageDraw


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
GENERATED_FOLDER = os.path.join(APP_ROOT, 'generated_outfits')
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
CONTACTS_FILE = os.path.join(APP_ROOT, 'contacts.json')

os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


app = Flask(__name__, static_folder='static')
CORS(app)


SCENES = {'casual', 'work', 'date-night', 'workout', 'formal', 'party'}
STYLES = {'minimalist', 'vintage', 'streetwear', 'comfort', 'bohemian', 'artistic'}
GENDERS = {'female', 'male', 'unisex'}

SCENE_PROMPTS = {
    'casual': 'casual everyday wear, comfortable and relaxed outfit',
    'work': 'professional business attire, office appropriate clothing',
    'date-night': 'elegant romantic outfit, stylish date night look',
    'workout': 'athletic sportswear, gym and fitness clothing',
    'formal': 'formal elegant attire, sophisticated evening wear',
    'party': 'trendy party outfit, festive celebration wear'
}

STYLE_PROMPTS = {
    'minimalist': 'minimalist clean lines, simple elegant design',
    'vintage': 'vintage retro fashion, classic timeless style',
    'streetwear': 'urban streetwear, contemporary hip fashion',
    'comfort': 'cozy comfortable clothing, relaxed fit',
    'bohemian': 'bohemian free-spirited, flowing artistic style',
    'artistic': 'artistic avant-garde, creative unique design'
}

GENDER_PROMPTS = {
    'female': 'female fashion model',
    'male': 'male fashion model',
    'unisex': 'androgynous fashion model'
}

QUALITY = 'high quality, professional fashion photography, realistic fabric texture, studio lighting'


def build_prompt(scene, style, gender):
    parts = [GENDER_PROMPTS.get(gender, 'fashion model'), 'wearing', SCENE_PROMPTS.get(scene, ''), STYLE_PROMPTS.get(style, '')]
    parts.append(QUALITY)
    return ', '.join([p for p in parts if p])


def save_data_uri(data_uri: str, out_dir: str, stem: str) -> str:
    if not data_uri.startswith('data:image'):
        raise ValueError('expected data uri')
    b64 = data_uri.split(',', 1)[1]
    raw = base64.b64decode(b64)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{stem}_{int(time.time())}.png")
    with open(path, 'wb') as f:
        f.write(raw)
    return path


def demo_image(scene, style, gender, note='demo'):
    img = Image.new('RGB', (768, 512), color=(240, 240, 250))
    d = ImageDraw.Draw(img)
    lines = [gender.upper(), f'{scene} | {style}', 'FitFinder Demo', note]
    y = 140
    for L in lines:
        d.text((40, y), L, fill=(30, 30, 60))
        y += 40
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')


@app.get('/api/health')
def health():
    return jsonify({'status': 'healthy', 'miragic': bool(os.environ.get('MIRAGIC_API_KEY')), 'time': datetime.now().isoformat()})


@app.post('/api/generate-outfit')
def generate_outfit():
    data = request.get_json(silent=True) or {}
    scene = data.get('scene')
    style = data.get('style')
    gender = data.get('gender')
    if scene not in SCENES or style not in STYLES or gender not in GENDERS:
        return jsonify({'success': False, 'error': 'invalid scene/style/gender'}), 400
    prompt = build_prompt(scene, style, gender)
    img_uri = demo_image(scene, style, gender, note='demo-only')
    saved = save_data_uri(img_uri, GENERATED_FOLDER, f'outfit_{scene}_{style}')
    return jsonify({'success': True, 'file': os.path.basename(saved), 'image': img_uri, 'prompt': prompt})


@app.post('/api/tryon')
def tryon():
    if 'person_image' not in request.files or 'cloth_image' not in request.files:
        return jsonify({'success': False, 'error': 'upload both files'}), 400
    try:
        person = Image.open(request.files['person_image'].stream).convert('RGBA')
        cloth = Image.open(request.files['cloth_image'].stream).convert('RGBA')
        pw, ph = person.size
        cw, ch = cloth.size
        target_w = int(pw * 0.55)
        scale = target_w / max(cw, 1)
        new_size = (max(int(cw*scale),1), max(int(ch*scale),1))
        cloth_r = cloth.resize(new_size, Image.LANCZOS)
        x = (pw - new_size[0]) // 2
        y = max(int(ph * 0.25) - new_size[1]//8, 0)
        comp = person.copy()
        comp.alpha_composite(cloth_r, (x,y))
        buf = io.BytesIO()
        comp.convert('RGB').save(buf, format='PNG')
        img_uri = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
        saved = save_data_uri(img_uri, GENERATED_FOLDER, 'tryon')
        return jsonify({'success': True, 'file': os.path.basename(saved), 'image': img_uri})
    except Exception as e:
        return jsonify({'success': False, 'error': 'tryon failed', 'detail': str(e)}), 500


@app.post('/api/virtual-try-on')
def virtual_try_on_proxy():
    api_key = os.environ.get('MIRAGIC_API_KEY')
    base_url = os.environ.get('MIRAGIC_BASE_URL', 'https://backend.miragic.ai')

    max_bytes = 8 * 1024 * 1024
    if request.content_length and request.content_length > max_bytes:
        return jsonify({'success': False, 'error': 'payload too large'}), 413

    person_file = request.files.get('person_image') or request.files.get('humanImage')
    cloth_file = request.files.get('cloth_image') or request.files.get('clothImage')
    if not person_file or not cloth_file:
        return jsonify({'success': False, 'error': 'please upload both person and cloth images'}), 400

    for f in (person_file, cloth_file):
        ctype = getattr(f, 'content_type', '')
        if not ctype or not ctype.startswith('image'):
            return jsonify({'success': False, 'error': 'invalid file type; images only'}), 400

    if not api_key:
        try:
            person = Image.open(person_file.stream).convert('RGBA')
            cloth = Image.open(cloth_file.stream).convert('RGBA')
            pw, ph = person.size
            cw, ch = cloth.size
            target_w = int(pw * 0.55)
            scale = target_w / max(cw, 1)
            new_size = (max(int(cw*scale),1), max(int(ch*scale),1))
            cloth_r = cloth.resize(new_size, Image.LANCZOS)
            x = (pw - new_size[0]) // 2
            y = max(int(ph * 0.25) - new_size[1]//8, 0)
            comp = person.copy()
            comp.alpha_composite(cloth_r, (x,y))
            buf = io.BytesIO()
            comp.convert('RGB').save(buf, format='PNG')
            img_uri = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('utf-8')
            saved = save_data_uri(img_uri, GENERATED_FOLDER, 'virtual_tryon_fallback')
            return jsonify({'success': True, 'image': img_uri, 'file': os.path.basename(saved), 'note': 'local_fallback'})
        except Exception as e:
            return jsonify({'success': False, 'error': 'local tryon failed', 'detail': str(e)}), 500

    url = base_url.rstrip('/') + '/api/v1/virtual-try-on'
    files = {
        'humanImage': (person_file.filename or 'person.jpg', person_file.stream, person_file.content_type or 'image/jpeg'),
        'clothImage': (cloth_file.filename or 'cloth.jpg', cloth_file.stream, cloth_file.content_type or 'image/jpeg')
    }
    headers = {'X-API-Key': api_key}
    try:
        resp = requests.post(url, headers=headers, files=files, timeout=60)
    except Exception as e:
        return jsonify({'success': False, 'error': f'request failed: {str(e)}'}), 502

    content_type = resp.headers.get('Content-Type', '')
    if resp.status_code == 200 and content_type.startswith('image'):
        b64 = base64.b64encode(resp.content).decode('utf-8')
        img_uri = f'data:{content_type};base64,{b64}'
        saved = save_data_uri(img_uri, GENERATED_FOLDER, 'virtual_tryon')
        return jsonify({'success': True, 'image': img_uri, 'file': os.path.basename(saved), 'note': 'miragic'})

    try:
        data = resp.json()
        if isinstance(data, dict) and 'image' in data:
            return jsonify({'success': True, **data})
        return jsonify({'success': False, 'error': 'external api error', 'detail': data}), resp.status_code
    except ValueError:
        return jsonify({'success': False, 'error': 'external api returned non-json', 'detail': resp.text}), resp.status_code


@app.post('/api/contact')
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    message = (data.get('message') or '').strip()
    if not (name and email and message):
        return jsonify({'success': False, 'error': 'all fields required'}), 400
    contacts = []
    if os.path.exists(CONTACTS_FILE):
        try:
            contacts = json.load(open(CONTACTS_FILE, 'r', encoding='utf-8'))
        except Exception:
            contacts = []
    contacts.append({'name': name, 'email': email, 'message': message, 'time': datetime.now().isoformat()})
    with open(CONTACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contacts, f, indent=2)
    return jsonify({'success': True})


@app.get('/api/admin/stats')
def admin_stats():
    gen = len([f for f in os.listdir(GENERATED_FOLDER) if f.endswith('.png')])
    up = len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.png')])
    contacts = 0
    if os.path.exists(CONTACTS_FILE):
        try:
            contacts = len(json.load(open(CONTACTS_FILE, 'r', encoding='utf-8')))
        except Exception:
            contacts = 0
    return jsonify({'success': True, 'generated': gen, 'uploads': up, 'contacts': contacts})


@app.get('/')
def index():
    return send_from_directory('static', 'index.html')


@app.get('/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


if __name__ == '__main__':
    print('FitFinder (clean) starting. MIRAGIC configured:', bool(os.environ.get('MIRAGIC_API_KEY')))
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)