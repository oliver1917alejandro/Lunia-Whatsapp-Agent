import os
import requests
import json
from dotenv import load_dotenv
import openai # For Whisper

load_dotenv()

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None
if OPENAI_API_KEY:
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        print("whatsapp_client: OpenAI client initialized.")
    except Exception as e:
        print(f"whatsapp_client_error: Failed to initialize OpenAI client: {e}")
else:
    print("whatsapp_client_warning: OPENAI_API_KEY not found. Audio transcription will be skipped.")

def send_message(phone_number: str, message: str):
    if not all([EVOLUTION_API_URL, EVOLUTION_API_KEY, EVOLUTION_INSTANCE_NAME]):
        print("evolution_api_error: API URL, Key, or Instance Name not configured.")
        return None
    # Basic check for default URL to prevent accidental live calls with placeholder
    if EVOLUTION_API_URL == "https://your-evolution-api-domain.com":
        print("evolution_api_warning: EVOLUTION_API_URL is default. Sending may fail or is unintended.")

    api_url_base = EVOLUTION_API_URL
    if not api_url_base.startswith(('http://', 'https://')):
        api_url_base = 'https://' + api_url_base

    api_url = f"{api_url_base.rstrip('/')}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": phone_number, "options": {"delay": 1200, "presence": "composing"}, "textMessage": {"text": message}}

    print(f"whatsapp_client: Sending to {phone_number} (URL: {api_url})")
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        print(f"whatsapp_client: API Success {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"whatsapp_client: API Error during send_message - {type(e).__name__}: {e}")
        return None

def transcribe_audio_file(audio_file_path: str):
    if not client:
        print("transcribe_audio_file: OpenAI client not initialized.")
        return "[OpenAI client not available for transcription]"
    if not os.path.exists(audio_file_path):
        print(f"transcribe_audio_file: Audio file not found: {audio_file_path}")
        return "[Audio file not found for transcription]"
    if os.path.getsize(audio_file_path) < 100: # Check if it's likely a placeholder
        print(f"transcribe_audio_file: {audio_file_path} is very small, likely a placeholder. Skipping actual transcription.")
        return "[Audio file was a placeholder, not transcribed]"


    print(f"transcribe_audio_file: Transcribing {audio_file_path}...")
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcribed_text = transcript.text
        print(f"transcribe_audio_file: Success - Text: '{transcribed_text[:50]}...'")
        return transcribed_text if transcribed_text else "[Transcription resulted in empty text]"
    except Exception as e:
        print(f"transcribe_audio_file: Error during transcription - {type(e).__name__}: {e}")
        return "[Audio transcription failed]"

def receive_message_webhook_handler(webhook_payload: dict):
    print(f"webhook_handler: Raw - {json.dumps(webhook_payload)[:150]}...")
    sender, text = None, None
    audio_to_process_path = None

    event = webhook_payload.get("event")
    data = webhook_payload.get("data", {})

    if event == "messages.upsert" and data:
        sender = data.get("key", {}).get("remoteJid")
        msg_obj = data.get("message", {})
        if msg_obj:
            text = msg_obj.get("conversation") or msg_obj.get("extendedTextMessage", {}).get("text")

            # Audio message detection (example, verify with Evolution API docs)
            audio_msg_details = msg_obj.get("audioMessage")
            if audio_msg_details:
                print(f"webhook_handler: Audio message detected. Details: {audio_msg_details}")
                # SIMULATION: Use local sample if "url" field is "use_sample_audio.mp3"
                if audio_msg_details.get("url") == "use_sample_audio.mp3":
                    audio_to_process_path = "data/sample_audio.mp3" # Relative to app dir
                    print(f"webhook_handler: Using local sample: {audio_to_process_path}")
                else:
                    # Placeholder for actual audio download logic from a real URL
                    actual_url = audio_msg_details.get("url")
                    print(f"webhook_handler: Real audio URL '{actual_url}' detected. Download logic not implemented in this sim.")
                    text = "[Audio message URL received, but live download/processing is not part of this simulation step]"
                    audio_to_process_path = None # Ensure we don't try to transcribe

    if audio_to_process_path:
        transcribed_text = transcribe_audio_file(audio_to_process_path)
        text = transcribed_text # Overwrite original text if transcription happened

    if sender and (text is not None): # text can be empty string
        print(f"webhook_handler: Parsed/Transcribed - From: {sender}, Text: '{text[:60]}...'")
        return {"sender": sender, "text": text}

    print(f"webhook_handler: Failed to parse. Sender: {sender}, Text: {text}")
    return None

if __name__ == '__main__':
    print("--- Test whatsapp_client.py (Audio) ---")
    if OPENAI_API_KEY and client:
        print("\nTesting transcribe_audio_file (data/sample_audio.mp3)...")
        # NOTE: Replace data/sample_audio.mp3 with a REAL audio file for meaningful test.
        if os.path.exists("data/sample_audio.mp3"):
            transcribed = transcribe_audio_file("data/sample_audio.mp3")
            print(f"Test transcription output: '{transcribed}'")
        else:
            print("Skipping: data/sample_audio.mp3 not found.")
    else:
        print("Skipping transcription test: OPENAI_API_KEY missing or client init failed.")

    print("\nTesting receive_message_webhook_handler (simulated audio)...")
    audio_payload = {
        "event": "messages.upsert", "data": {
            "key": {"remoteJid": "audio_user@s.whatsapp.net"},
            "message": {"audioMessage": {"url": "use_sample_audio.mp3"}}
        }
    }
    parsed = receive_message_webhook_handler(audio_payload)
    print(f"Audio webhook parse result: {parsed}")
    print("--- End Test whatsapp_client.py ---")
