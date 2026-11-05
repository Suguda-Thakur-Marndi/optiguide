"""OptiGuide Voice Assistant — Live Microphone Interactive CLI.

Records your voice from your actual microphone, sends it to the OptiGuide
backend server at http://127.0.0.1:8000/api/v1/voice/chat, displays the recognized
speech and clinical guidance response, and plays OptiGuide's voice reply.

Usage:
    cd backend
    .\\.venv\\Scripts\\python record_and_chat.py
"""

from __future__ import annotations

import base64
import io
import sys
import time
import wave
import winsound

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install via: pip install httpx")
    sys.exit(1)

try:
    import numpy as np
    import sounddevice as sd
except ImportError:
    print("Error: sounddevice and numpy are required. Install via: pip install sounddevice numpy")
    sys.exit(1)

BACKEND_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{BACKEND_URL}/api/v1/voice/chat"
SAMPLE_RATE = 16000  # 16 kHz standard for speech recognition


def check_backend_health() -> bool:
    """Verifies that the OptiGuide FastAPI backend is online."""
    try:
        res = httpx.get(f"{BACKEND_URL}/health", timeout=3.0)
        return res.status_code == 200
    except Exception:
        return False


def record_microphone(duration_seconds: float = 4.0) -> bytes:
    """Records audio from default microphone for specified duration and returns PCM WAV bytes."""
    print(f"\n🎙️  RECORDING NOW ({duration_seconds}s)... Speak clearly into your microphone!")
    print("------------------------------------------------------------")

    # Record mono 16-bit PCM at 16,000 Hz
    num_samples = int(duration_seconds * SAMPLE_RATE)
    recording = sd.rec(num_samples, samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    
    # Progress countdown
    for i in range(int(duration_seconds), 0, -1):
        print(f"   ⏱️  {i} second{'s' if i > 1 else ''} remaining...", end="\r", flush=True)
        time.sleep(1.0)
    
    sd.wait()
    print("   ✅ Recording complete! Processing audio...                  ")

    # Package as standard PCM WAV in memory
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit = 2 bytes
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(recording.tobytes())

    return buf.getvalue()


def send_voice_to_backend(wav_bytes: bytes) -> dict | None:
    """Sends WAV audio bytes to OptiGuide voice chat endpoint."""
    try:
        files = {"file": ("microphone_input.wav", wav_bytes, "audio/wav")}
        with httpx.Client(timeout=25.0) as client:
            res = client.post(CHAT_ENDPOINT, files=files)
            if res.status_code == 200:
                return res.json()
            else:
                print(f"❌ Backend returned error {res.status_code}: {res.text}")
                return None
    except httpx.ConnectError:
        print(f"❌ Could not connect to backend at {BACKEND_URL}.")
        print("   Make sure the backend is running via:")
        print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return None
    except Exception as e:
        print(f"❌ Error dispatching voice request: {e}")
        return None


def play_audio_response(audio_b64: str) -> None:
    """Decodes base64 WAV audio and plays it through the user's speakers."""
    try:
        wav_bytes = base64.b64decode(audio_b64)
        print("\n🔊 Playing OptiGuide spoken response...")
        winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
    except Exception as e:
        print(f"⚠️  Could not play audio through speakers: {e}")


def main() -> None:
    print("=" * 64)
    print("       OPTIGUIDE VOICE ASSISTANT — LIVE MICROPHONE TEST")
    print("=" * 64)

    if not check_backend_health():
        print(f"❌ Backend server is NOT reachable at {BACKEND_URL}.")
        print("   Please start the backend first:")
        print("   cd backend; .\\.venv\\Scripts\\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return

    print(f"✅ Backend server is ONLINE at {BACKEND_URL}")
    print(f"✅ Active Voice Endpoint: {CHAT_ENDPOINT}")
    
    # List active microphone
    try:
        default_input = sd.query_devices(kind="input")
        print(f"🎤 Active Microphone: {default_input['name']}")
    except Exception:
        pass

    print("\nHow it works:")
    print("1. Press ENTER to start recording your microphone.")
    print("2. Speak a phrase (e.g. 'Hello OptiGuide, I want to start my vision screening').")
    print("3. The backend will recognize what you said, display it, and speak back!")
    print("Type 'q' or 'exit' and press ENTER to quit.\n")

    while True:
        try:
            user_cmd = input("\n👉 Press [ENTER] to record (or 'q' to quit): ").strip().lower()
            if user_cmd in ["q", "exit", "quit"]:
                print("Exiting OptiGuide Voice Test. Goodbye!")
                break

            # Record 4 seconds of microphone audio
            audio_bytes = record_microphone(duration_seconds=4.0)

            # Send to backend
            print("🚀 Transmitting microphone audio to OptiGuide backend...")
            data = send_voice_to_backend(audio_bytes)

            if data:
                print("\n" + "=" * 64)
                print(f"🎙️  WHAT YOU SAID (STT):")
                print(f"   \"{data.get('transcription')}\"")
                print(f"   (Confidence: {data.get('confidence', 'N/A')})")
                print(f"🎯 DETECTED INTENT: {data.get('intent')}")
                print("-" * 64)
                print(f"🤖 OPTIGUIDE'S RESPONSE:")
                print(f"   \"{data.get('response_text')}\"")
                print("-" * 64)
                print(f"⚕️  {data.get('clinical_disclaimer')}")
                print("=" * 64)

                # Play response audio through speakers
                audio_b64 = data.get("audio_base64")
                if audio_b64:
                    play_audio_response(audio_b64)

        except KeyboardInterrupt:
            print("\nExiting OptiGuide Voice Test.")
            break


if __name__ == "__main__":
    main()
