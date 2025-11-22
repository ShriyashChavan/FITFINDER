"""
FitFinder - AI Fashion Assistant Backend
Complete Flask application for college project deployment

Features:
- AI Outfit Generator
- Virtual Try-On
- Contact Form
- Static file serving
- Email notifications

Author: College Project Team
Date: 2025
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import os
import base64
import time
from datetime import datetime
import json
import requests
import io

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['GENERATED_FOLDER'] = 'generated_outfits'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_FOLDER'], exist_ok=True)

# Store contact form submissions
CONTACTS_FILE = 'contacts.json'

# Fashion prompt templates
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

QUALITY_PROMPT = "high quality, professional fashion photography, detailed clothing, realistic fabric texture, studio lighting, clean background, 8k uhd, photorealistic"


# ==================== ROUTES ====================

@app.route('/')
def home():
    """Serve the home page"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'FitFinder API',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


# ==================== AI OUTFIT GENERATOR ====================

@app.route('/api/generate-outfit', methods=['POST'])
def generate_outfit():
    """
    Generate AI outfit based on user selections
    
    Request JSON:
    {
        "scene": "casual",
        "style": "minimalist",
        "gender": "female",
        "custom_prompt": "optional description"
    }
    """
    try:
        print("\n" + "="*60)
        print(f"📥 NEW OUTFIT GENERATION REQUEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        data = request.get_json()
        
        scene = data.get('scene', 'casual')
        style = data.get('style', 'minimalist')
        gender = data.get('gender', 'female')
        custom_prompt = data.get('custom_prompt', '')
        
        print(f"📋 Scene: {scene}")
        print(f"🎨 Style: {style}")
        print(f"👤 Gender: {gender}")
        if custom_prompt:
            print(f"💭 Custom Prompt: {custom_prompt}")
        
        # Build complete prompt
        prompt = build_prompt(scene, style, gender, custom_prompt)
        print(f"\n📝 Full Prompt: {prompt[:150]}...")
        
        # Try real AI generation if Hugging Face token provided
        hf_token = os.environ.get('HF_API_TOKEN') or os.environ.get('HUGGINGFACE_API_TOKEN')
        hf_model = os.environ.get('HF_MODEL', 'stabilityai/stable-diffusion-2-1')

        if hf_token:
            try:
                result_image = generate_with_huggingface(prompt, hf_token, hf_model)
            except Exception as e:
                print(f"⚠️ Hugging Face generation failed: {e}. Falling back to demo image.")
                result_image = generate_demo_image(scene, style, gender)
        else:
            # Demo placeholder image when no API key is configured
            result_image = generate_demo_image(scene, style, gender)
        
        # Save result
        timestamp = int(time.time())
        filename = f"outfit_{scene}_{style}_{timestamp}.png"
        filepath = os.path.join(app.config['GENERATED_FOLDER'], filename)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(result_image.split(',')[1]))
        
        print(f"💾 Saved: {filepath}")
        print("✅ SUCCESS")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'image': result_image,
            'filename': filename,
            'prompt': prompt[:200]
        })
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def build_prompt(scene, style, gender, custom_prompt=""):
    """Build complete fashion prompt"""
    components = [
        GENDER_PROMPTS.get(gender, 'fashion model'),
        'wearing',
        SCENE_PROMPTS.get(scene, 'fashionable outfit'),
        STYLE_PROMPTS.get(style, 'stylish design')
    ]
    
    if custom_prompt:
        components.append(custom_prompt)
    
    components.append(QUALITY_PROMPT)
    
    return ', '.join(components)


def generate_demo_image(scene, style, gender):
    """Generate demo placeholder image for college project"""
    # For demo purposes, return a colored placeholder
    # In production, this would call the AI model
    
    # Create a simple colored square as demo
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create image
    img = Image.new('RGB', (512, 768), color=(255, 181, 180))
    draw = ImageDraw.Draw(img)
    
    # Add text
    text = f"{gender.upper()}\n{scene.upper()}\n{style.upper()}\n\nAI Generated Outfit\n(Demo Mode)"
    
    # Draw text
    draw.text((50, 250), text, fill=(255, 140, 0))
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f'data:image/png;base64,{img_str}'


def generate_with_huggingface(prompt, token, model_id='stabilityai/stable-diffusion-2-1'):
    """Call Hugging Face Inference API to generate an image from the prompt.

    Returns a data URI (base64 PNG).
    """
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'image/png'
    }
    payload = {
        'inputs': prompt
    }

    print(f"🔗 Calling Hugging Face model: {model_id}")
    resp = requests.post(api_url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"HF API error {resp.status_code}: {resp.text}")

    # Response content is raw image bytes (PNG)
    img_bytes = resp.content
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    return f'data:image/png;base64,{img_b64}'


def process_tryon_with_api(person_path, cloth_path):
    """Optional: send uploaded images to an external try-on API if provided.

    Environment variable `TRYON_API_URL` should be set to the service endpoint.
    The function returns a path to the resulting image or raises on error.
    """
    tryon_url = os.environ.get('TRYON_API_URL')
    if not tryon_url:
        raise RuntimeError('TRYON_API_URL not set')

    files = {
        'person_image': open(person_path, 'rb'),
        'cloth_image': open(cloth_path, 'rb')
    }

    resp = requests.post(tryon_url, files=files, timeout=120)
    for f in files.values():
        f.close()

    if resp.status_code != 200:
        raise RuntimeError(f"Try-on API error {resp.status_code}: {resp.text}")

    # Assume the API returns raw image bytes
    out_path = os.path.join(app.config['GENERATED_FOLDER'], f'tryon_result_{int(time.time())}.png')
    with open(out_path, 'wb') as f:
        f.write(resp.content)
    return out_path


# ==================== VIRTUAL TRY-ON ====================

@app.route('/api/tryon', methods=['POST'])
def virtual_tryon():
    """
    Virtual try-on endpoint
    Expects: person_image and cloth_image files
    """
    try:
        print("\n📥 Virtual Try-On Request")
        
        if 'person_image' not in request.files or 'cloth_image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Please upload both images'
            }), 400
        
        person_file = request.files['person_image']
        cloth_file = request.files['cloth_image']
        
        # Save uploaded files
        timestamp = str(int(time.time()))
        person_path = os.path.join(app.config['UPLOAD_FOLDER'], f'person_{timestamp}.png')
        cloth_path = os.path.join(app.config['UPLOAD_FOLDER'], f'cloth_{timestamp}.png')
        
        person_file.save(person_path)
        cloth_file.save(cloth_path)
        
        print(f"💾 Saved uploads: {person_path}, {cloth_path}")
        
        # For college demo: Use Gradio Client API
        # result_path = process_tryon_with_api(person_path, cloth_path)
        
        # Demo mode: Return person image as result
        with open(person_path, 'rb') as f:
            result_image = f.read()
            result_base64 = base64.b64encode(result_image).decode('utf-8')
        
        print("✅ Try-on complete (demo mode)")
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{result_base64}',
            'message': 'Demo mode: Connect AI model for real try-on'
        })
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== CONTACT FORM ====================

@app.route('/api/contact', methods=['POST'])
def contact_form():
    """
    Handle contact form submissions
    
    Request JSON:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "message": "Hello..."
    }
    """
    try:
        data = request.get_json()
        
        Shriyash = data.get('name', '')
        shriyash22105@gmail.com = data.get('email', '')
        message = data.get('message', '')
        
        if not all([name, email, message]):
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Create contact entry
        contact = {
            'name': name,
            'email': email,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'status': 'new'
        }
        
        # Save to file
        contacts = []
        if os.path.exists(CONTACTS_FILE):
            with open(CONTACTS_FILE, 'r') as f:
                contacts = json.load(f)
        
        contacts.append(contact)
        
        with open(CONTACTS_FILE, 'w') as f:
            json.dump(contacts, f, indent=2)
        
        print(f"\n📧 New Contact Form Submission:")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   Message: {message[:50]}...")
        
        return jsonify({
            'success': True,
            'message': 'Thank you! We will contact you soon.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ADMIN ROUTES ====================

@app.route('/api/admin/contacts', methods=['GET'])
def get_contacts():
    """Get all contact form submissions (for admin)"""
    try:
        if os.path.exists(CONTACTS_FILE):
            with open(CONTACTS_FILE, 'r') as f:
                contacts = json.load(f)
            return jsonify({
                'success': True,
                'contacts': contacts,
                'total': len(contacts)
            })
        else:
            return jsonify({
                'success': True,
                'contacts': [],
                'total': 0
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    """Get usage statistics"""
    try:
        # Count generated outfits
        outfit_count = len([f for f in os.listdir(app.config['GENERATED_FOLDER']) 
                           if f.endswith('.png')])
        
        # Count uploads
        upload_count = len([f for f in os.listdir(app.config['UPLOAD_FOLDER']) 
                           if f.endswith('.png')])
        
        # Count contacts
        contact_count = 0
        if os.path.exists(CONTACTS_FILE):
            with open(CONTACTS_FILE, 'r') as f:
                contact_count = len(json.load(f))
        
        return jsonify({
            'success': True,
            'stats': {
                'generated_outfits': outfit_count,
                'uploads': upload_count,
                'contact_submissions': contact_count,
                'uptime': 'Active'
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎨 FITFINDER - AI FASHION ASSISTANT")
    print("="*70)
    print("📍 Server URL: http://localhost:5000")
    print("📍 API Health: http://localhost:5000/api/health")
    print("📍 Admin Stats: http://localhost:5000/api/admin/stats")
    print("\n📋 Available Endpoints:")
    print("   POST /api/generate-outfit  - Generate AI outfit")
    print("   POST /api/tryon            - Virtual try-on")
    print("   POST /api/contact          - Contact form")
    print("   GET  /api/admin/contacts   - View contacts")
    print("   GET  /api/admin/stats      - View statistics")
    print("\n💡 Press Ctrl+C to stop the server")
    print("="*70 + "\n")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
