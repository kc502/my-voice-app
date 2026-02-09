import os
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from elevenlabs.client import ElevenLabs

app = FastAPI()
templates = Jinja2Templates(directory="templates")

API_KEY = os.environ.get("ELEVEN_API_KEY")
client = ElevenLabs(api_key=API_KEY)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
def generate_voice(
    text: str = Form(...), 
    voice_id: str = Form(...) # Voice ID ထည့်ရန်
):
    if not API_KEY:
        return Response(content="Error: API Key မရှိပါ။", status_code=500)

    try:
        # Edge TTS ကို ဖြုတ်ပြီး ElevenLabs Direct TTS ကို သုံးထားပါတယ်
        # ဒါက ပိုမြန်ပြီး Error ကင်းပါတယ်
        audio_generator = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id, 
            model_id="eleven_multilingual_v2", # Text-to-Speech Model
            output_format="mp3_44100_128"
        )

        final_audio = b"".join(audio_generator)
        return Response(content=final_audio, media_type="audio/mpeg")

    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
