import os
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ==========================================
# Hugging Face Space ကို လှမ်းချိတ်ခြင်း
# (Nano Banana ရဲ့ Space နာမည်အမှန် ဖြစ်ရပါမယ်)
# ==========================================
HF_SPACE_NAME = "kochit/myannar-rvc-tts"
client = Client(HF_SPACE_NAME)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
def generate_voice(
    text: str = Form(...),
    tts_voice: str = Form(...),  # Thiha or Nilar
    rvc_model: str = Form(...),  # Black Panther, etc.
    pitch: int = Form(0)
):
    try:
        print(f"Sending to Hugging Face: {text} | {tts_voice} | {rvc_model}")
        
        # Hugging Face ဆီ အမိန့်လှမ်းပေးခြင်း
        # အစဉ်လိုက်အတိုင်း တိကျရပါမယ် (Text, TTS Voice, Model, Pitch)
        result = client.predict(
            text,           
            tts_voice,      
            rvc_model,      
            pitch,          
            api_name="/predict" # Hugging Face ရဲ့ Default Endpoint
        )
        
        # result က (audio_path, message) ပုံစံနဲ့ ပြန်လာပါတယ်
        # Audio Path (result[0]) ကို ယူပါမယ်
        audio_path = result[0]
        
        # ရလာတဲ့ ဖိုင်ကို ဖတ်ပြီး Web App ဘက်ကို ပြန်ပို့ခြင်း
        with open(audio_path, "rb") as f:
            audio_data = f.read()
            
        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return Response(content=f"Error connecting to Hugging Face: {str(e)}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
