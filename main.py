import os
import io
import uvicorn
import edge_tts
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from elevenlabs.client import ElevenLabs

app = FastAPI()

# HTML ဖိုင်များထားရှိရာ နေရာ
templates = Jinja2Templates(directory="templates")

# Render Environment Variable မှ API Key ယူမည်
API_KEY = os.environ.get("ELEVEN_API_KEY")
client = ElevenLabs(api_key=API_KEY)

# ၁။ Website စာမျက်နှာ (Frontend) ပြသခြင်း
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ၂။ အသံထုတ်လုပ်ခြင်း (Backend Logic)
@app.post("/generate")
async def generate_voice(
    text: str = Form(...), 
    voice_id: str = Form(...)
):
    if not API_KEY:
        return Response(content="Error: ElevenLabs API Key မရှိပါ။ Render တွင် ထည့်ပေးပါ။", status_code=500)

    try:
        # Step 1: Edge TTS ဖြင့် မြန်မာစာ ဖတ်ခြင်း (Nilar)
        communicate = edge_tts.Communicate(text, "my-MM-NilarNeural")
        
        # Memory Buffer ထဲသို့ အသံသွင်းခြင်း
        mp3_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.write(chunk["data"])
        
        mp3_buffer.seek(0) # အစသို့ ပြန်ရွှေ့

        # Step 2: ElevenLabs Speech-to-Speech (Voice Clone)
        # အသံဖိုင် (Audio) ကို Input အဖြစ်ထည့်ပြီး အသံပြောင်းခြင်း
        audio_generator = client.speech_to_speech.convert(
            audio=mp3_buffer, 
            voice_id=voice_id,
            model_id="eleven_multilingual_sts_v2",
            output_format="mp3_44100_128"
        )

        final_audio = b"".join(audio_generator)

        # အသံဖိုင် ပြန်ထုတ်ပေးခြင်း
        return Response(content=final_audio, media_type="audio/mpeg")

    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
