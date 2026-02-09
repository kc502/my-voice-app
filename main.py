import os
import io
import uvicorn
import edge_tts
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from elevenlabs.client import ElevenLabs

# App ကို တည်ဆောက်ခြင်း
app = FastAPI()

# HTML ဖိုင်များထားရှိရာ နေရာ (templates folder ရှိရပါမယ်)
templates = Jinja2Templates(directory="templates")

# Render Environment Variable မှ API Key ယူမည်
API_KEY = os.environ.get("ELEVEN_API_KEY")

# ElevenLabs Client ကို စတင်ခြင်း
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
        return Response(content="Error: ElevenLabs API Key မရှိပါ။ Render Environment တွင် ထည့်ပေးပါ။", status_code=500)

    try:
        # Step 1: Edge TTS ဖြင့် မြန်မာစာ ဖတ်ခြင်း (Nilar)
        # Nilar အသံက မြန်မာစာ ပီသလို့ Base Audio အနေနဲ့ သုံးပါတယ်
        communicate = edge_tts.Communicate(text, "my-MM-NilarNeural")
        
        # Memory Buffer ထဲသို့ အသံသွင်းခြင်း (ဖိုင်မဆောက်တော့ပါ)
        mp3_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_buffer.write(chunk["data"])
        
        mp3_buffer.seek(0) # Pointer ကို အစပြန်ရွှေ့

        # Step 2: ElevenLabs Speech-to-Speech (Voice Clone)
        # အသံဖိုင် (Audio) ကို Input အဖြစ်ထည့်ပြီး အသံပြောင်းခြင်း
        audio_generator = client.speech_to_speech.convert(
            audio=mp3_buffer, 
            voice_id=voice_id,
            model_id="eleven_multilingual_sts_v2", # STS Model (အရေးကြီးပါတယ်)
            output_format="mp3_44100_128"
        )

        # Generator မှ data များကို စုစည်းခြင်း
        final_audio = b"".join(audio_generator)

        # အသံဖိုင် ပြန်ထုတ်ပေးခြင်း
        return Response(content=final_audio, media_type="audio/mpeg")

    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)

# ==========================================
# Render အတွက် အရေးကြီးဆုံး အပိုင်း (Port Fix)
# ==========================================
if __name__ == "__main__":
    # Render က ပေးတဲ့ PORT ကို ယူမယ်၊ မရှိရင် 10000 ကို သုံးမယ်
    port = int(os.environ.get("PORT", 10000))
    
    # 0.0.0.0 ဆိုတာက Public ကို ဖွင့်ပေးတာပါ (Render လိုချင်တဲ့ ပုံစံ)
    uvicorn.run(app, host="0.0.0.0", port=port)
