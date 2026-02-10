import os
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

HF_SPACE_NAME = "kochit/myanmar-rvc-tts"

# ==========================================
# Render Environment မှ Token ကို လှမ်းယူခြင်း
# (Code ထဲမှာ Token မရေးတော့ပါ)
# ==========================================
HF_TOKEN = os.environ.get("HF_TOKEN")

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
        
        # Token မရှိရင် Error တက်မှာစိုးလို့ စစ်ပေးမယ်
        if not HF_TOKEN:
            print("Warning: HF_TOKEN မရှိပါ။ Quota Error တက်နိုင်ပါသည်။")
            client = Client(HF_SPACE_NAME) # Token မပါဘဲ ချိတ်မယ်
        else:
            print("Using Secure Token from Render Environment.")
            client = Client(HF_SPACE_NAME, hf_token=HF_TOKEN) # Token နဲ့ ချိတ်မယ်
        
        # Hugging Face သို့ အလုပ်ခိုင်းခြင်း
        result = client.predict(
            text,           
            tts_voice,      
            rvc_model,      
            pitch,          
            api_name="/convert_voice"
        )
        
        audio_path = result[0]
        status_msg = result[1]
        
        if audio_path is None:
            print(f"HF Returned Error: {status_msg}")
            if "quota" in str(status_msg).lower():
                 return Response(content="Error: Hugging Face Quota ကုန်သွားပါပြီ။", status_code=500)
            return Response(content=f"Hugging Face Error: {status_msg}", status_code=500)
        
        with open(audio_path, "rb") as f:
            audio_data = f.read()
            
        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return Response(content=f"System Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
