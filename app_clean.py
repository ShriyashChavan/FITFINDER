"""FitFinder - Clean AI-capable backend (single canonical file)

This backend is self-contained and avoids duplicate route definitions.
Endpoints:
- GET  /api/health
- POST /api/generate-outfit
- POST /api/tryon
- POST /api/contact
- GET  /api/admin/stats
- static file serving

Demo mode: when no HF token is set, the generator returns a Pillow placeholder image.
"""

import os
import io
import json
import time
import base64
from datetime import datetime

import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image, ImageDraw


app = Flask(__name__, static_folder='static')
CORS(app)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated_outfits'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

CONTACTS_FILE = 'contacts.json'

HF_MODEL = os.environ.get('HF_MODEL', 'stabilityai/stable-diffusion-2-1')
HF_TOKEN = os.environ.get('HF_API_TOKEN') or os.environ.get('HUGGINGFACE_API_TOKEN')

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


def build_prompt(scene, style, gender, custom=''):
    parts = [GENDER_PROMPTS.get(gender, 'fashion model'), 'wearing', SCENE_PROMPTS.get(scene, ''), STYLE_PROMPTS.get(style, '')]
    if custom:
        parts.append(custom)
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
    return jsonify({'status': 'healthy', 'hf': bool(HF_TOKEN), 'time': datetime.now().isoformat()})


@app.post('/api/generate-outfit')
def generate_outfit():
    data = request.get_json(silent=True) or {}
    scene = data.get('scene')
    style = data.get('style')
    gender = data.get('gender')
    custom = (data.get('custom_prompt') or '').strip()
    if scene not in SCENES or style not in STYLES or gender not in GENDERS:
        return jsonify({'success': False, 'error': 'invalid scene/style/gender'}), 400
    prompt = build_prompt(scene, style, gender, custom)
    try:
        if HF_TOKEN:
            url = f'https://api-inference.huggingface.co/models/{HF_MODEL}'
            headers = {'Authorization': f'Bearer {HF_TOKEN}', 'Accept': 'image/png'}
            resp = requests.post(url, headers=headers, json={'inputs': prompt}, timeout=120)
            if resp.status_code == 200:
                img_uri = 'data:image/png;base64,' + base64.b64encode(resp.content).decode('utf-8')
            else:
                img_uri = demo_image(scene, style, gender, note='hf-failed')
        else:
            img_uri = demo_image(scene, style, gender, note='no-hf')
        saved = save_data_uri(img_uri, app.config['GENERATED_FOLDER'], f'outfit_{scene}_{style}')
        return jsonify({'success': True, 'file': os.path.basename(saved), 'image': img_uri})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.post('/api/tryon')
def tryon():
    if 'person_image' not in request.files or 'cloth_image' not in request.files:
        return jsonify({'success': False, 'error': 'upload both files'}), 400
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
    saved = save_data_uri(img_uri, app.config['GENERATED_FOLDER'], 'tryon')
    return jsonify({'success': True, 'file': os.path.basename(saved), 'image': img_uri})


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
    gen = len([f for f in os.listdir(app.config['GENERATED_FOLDER']) if f.endswith('.png')])
    up = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.png')])
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
    print('FitFinder starting. HF configured:', bool(HF_TOKEN))
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
