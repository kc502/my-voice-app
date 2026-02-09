import os
import uvicorn
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
        
        # Hugging Face သို့ အလုပ်ခိုင်းခြင်း
        result = client.predict(
            text,           
            tts_voice,      
            rvc_model,      
            pitch,          
            api_name="/convert_voice"
        )
        
        # result[0] = အသံဖိုင်လမ်းကြောင်း
        # result[1] = Status Message (Success သို့မဟုတ် Error စာသား)
        audio_path = result[0]
        status_msg = result[1]
        
        # =======================================================
        # ပြင်ဆင်ချက်: အသံဖိုင် မပါလာရင် Error စာသားကို ပြန်ပို့မည်
        # =======================================================
        if audio_path is None:
            print(f"HF Returned Error: {status_msg}")
            return Response(content=f"Hugging Face Error: {status_msg}", status_code=500)
        
        # အသံဖိုင် ပါလာမှ ဖွင့်မည်
        with open(audio_path, "rb") as f:
            audio_data = f.read()
            
        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return Response(content=f"System Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
