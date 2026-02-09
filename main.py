import os
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Nano Banana ရဲ့ Space Link အမှန်
HF_SPACE_NAME = "kochit/myanmar-rvc-tts"

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
def generate_voice(
    text: str = Form(...),
    tts_voice: str = Form(...),
    rvc_model: str = Form(...),
    pitch: int = Form(0)
):
    try:
        print(f"Connecting to Space: {HF_SPACE_NAME}...")
        client = Client(HF_SPACE_NAME)
        
        # Screenshot ထဲကအတိုင်း Parameter တွေကို အတိအကျ ပို့ပါမယ်
        result = client.predict(
            text,           # Text Input
            tts_voice,      # 'Nilar (Female)' or 'Thiha (Male)'
            rvc_model,      # 'Black Panther', 'Tom Holland', etc.
            pitch,          # Number (e.g. 0)
            api_name="/convert_voice"  # Screenshot ထဲက နာမည်အမှန်
        )
        
        # Result က (filepath, status) ပုံစံပြန်လာလို့ [0] ကို ယူရပါမယ်
        audio_path = result[0]
        
        # ရလာတဲ့ အသံဖိုင်ကို ဖတ်ပြီး Web App သို့ ပြန်ပို့ခြင်း
        with open(audio_path, "rb") as f:
            audio_data = f.read()
            
        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return Response(content=f"Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
