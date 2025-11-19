from http.server import BaseHTTPRequestHandler
import json
import asyncio
import edge_tts
import base64
import os
import tempfile

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests - return service info"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "service": "Julia Math Tutor - Edge TTS API",
            "status": "online",
            "version": "1.0",
            "endpoint": "/api/tts"
        }
        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):
        """Handle POST requests - generate TTS"""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Extract parameters
            text = data.get('text', '').strip()
            voice = data.get('voice', 'en-US-AnaNeural')
            rate = data.get('rate', '+0%')
            pitch = data.get('pitch', '+0Hz')
            
            # Validate
            if not text:
                self.send_error_response(400, "No text provided")
                return
            
            # Limit text length
            text = text[:1000]
            
            # Generate speech using async
            audio_base64 = asyncio.run(self.generate_speech(text, voice, rate, pitch))
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response = {
                "ok": True,
                "audio": f"data:audio/mpeg;base64,{audio_base64}",
                "voice": voice,
                "format": "mp3"
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error_response(500, str(e))

    async def generate_speech(self, text, voice, rate, pitch):
        """Generate speech using edge-tts"""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.mp3', delete=False) as tmp_file:
                tmp_filename = tmp_file.name
            
            # Generate speech
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(tmp_filename)
            
            # Read the file and encode to base64
            with open(tmp_filename, 'rb') as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Clean up
            try:
                os.remove(tmp_filename)
            except:
                pass
            
            return audio_base64
            
        except Exception as e:
            raise Exception(f"TTS generation failed: {str(e)}")

    def send_error_response(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "ok": False,
            "error": message
        }
        self.wfile.write(json.dumps(response).encode())
