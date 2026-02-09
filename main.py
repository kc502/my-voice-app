import os
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ==========================================
# Link အမှန် (Myanmar - M တစ်လုံးတည်းဖြင့်)
# ==========================================
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
        
        # Space ကို လှမ်းချိတ်ခြင်း
        client = Client(HF_SPACE_NAME)
        
        # Hugging Face သို့ အလုပ်ခိုင်းခြင်း
        # (Text, TTS Voice, RVC Model, Pitch)
        result = client.predict(
            text,           
            tts_voice,      
            rvc_model,      
            pitch,          
            api_name="/predict"
        )
        
        # အသံဖိုင်လမ်းကြောင်းကို ယူခြင်း
        audio_path = result[0]
        
        # ဖိုင်ကို ဖတ်ပြီး ပြန်ပို့ခြင်း
        with open(audio_path, "rb") as f:
            audio_data = f.read()
            
        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        error_msg = str(e)
        print(f"Connection Error: {error_msg}")
        return Response(content=f"Error: {error_msg}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
