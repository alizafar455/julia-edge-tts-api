from flask import Flask, request, jsonify
import edge_tts
import asyncio
import base64
import os
from functools import wraps

app = Flask(__name__)

# Simple API key protection (optional)
API_KEY = os.environ.get('API_KEY', 'julia-math-tutor-2024')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip API key check if not required
        if not os.environ.get('REQUIRE_API_KEY', 'false').lower() == 'true':
            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'ok': False, 'error': 'Missing API key'}), 401
        
        provided_key = auth_header.replace('Bearer ', '')
        if provided_key != API_KEY:
            return jsonify({'ok': False, 'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

async def generate_speech(text, voice='en-US-AnaNeural', rate='+0%', pitch='+0Hz'):
    """Generate speech using Edge TTS"""
    try:
        # Create temporary file path
        temp_file = f"/tmp/tts_{os.getpid()}.mp3"
        
        # Generate speech
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(temp_file)
        
        # Read and encode to base64
        with open(temp_file, 'rb') as f:
            audio_data = f.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        return audio_base64
    except Exception as e:
        raise Exception(f"TTS generation failed: {str(e)}")

@app.route('/')
def home():
    return jsonify({
        'service': 'Julia Math Tutor - Edge TTS API',
        'status': 'online',
        'version': '1.0',
        'endpoint': '/api/tts'
    })

@app.route('/api/tts', methods=['POST'])
@require_api_key
def text_to_speech():
    """
    Convert text to speech using Edge TTS
    
    Request body:
    {
        "text": "Hello world",
        "voice": "en-US-AnaNeural",  // optional
        "rate": "+0%",                // optional: -50% to +100%
        "pitch": "+0Hz"               // optional: -50Hz to +50Hz
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'ok': False, 'error': 'No JSON body provided'}), 400
        
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'ok': False, 'error': 'Text is required'}), 400
        
        # Limit text length
        if len(text) > 1000:
            text = text[:1000]
        
        voice = data.get('voice', 'en-US-AnaNeural')
        rate = data.get('rate', '+0%')
        pitch = data.get('pitch', '+0Hz')
        
        # Generate speech
        audio_base64 = asyncio.run(generate_speech(text, voice, rate, pitch))
        
        return jsonify({
            'ok': True,
            'audio': f'data:audio/mpeg;base64,{audio_base64}',
            'voice': voice,
            'format': 'mp3'
        })
    
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500

@app.route('/api/voices', methods=['GET'])
def list_voices():
    """List available voices"""
    voices = [
        {'name': 'en-US-AnaNeural', 'language': 'English (US)', 'gender': 'Female', 'description': 'Young, friendly - Perfect for kids!'},
        {'name': 'en-US-JennyNeural', 'language': 'English (US)', 'gender': 'Female', 'description': 'Warm, professional'},
        {'name': 'en-US-AriaNeural', 'language': 'English (US)', 'gender': 'Female', 'description': 'Natural, clear'},
        {'name': 'en-US-GuyNeural', 'language': 'English (US)', 'gender': 'Male', 'description': 'Friendly, casual'},
        {'name': 'en-GB-SoniaNeural', 'language': 'English (UK)', 'gender': 'Female', 'description': 'British accent'},
    ]
    return jsonify({'ok': True, 'voices': voices})

if __name__ == '__main__':
    app.run(debug=True)
