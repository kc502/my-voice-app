import os
import uvicorn
import edge_tts
import shutil
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ယာယီဖိုင်များ သိမ်းရန်
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

# -------------------------------------------------------
# အရင်က ဒီနေရာမှာ Client(...) ရေးထားလို့ Error တက်တာပါ
# အခု ဒီနေရာမှာ ဘာမှ မရေးဘဲ ကျော်သွားပါမယ်
# -------------------------------------------------------

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_voice(
    text: str = Form(...),
    pitch: int = Form(0)
):
    try:
        # Step 1: Edge TTS ဖြင့် မြန်မာစာဖတ်ခြင်း
        tts_filename = os.path.join(TEMP_DIR, "tts_input.mp3")
        communicate = edge_tts.Communicate(text, "my-MM-NilarNeural")
        await communicate.save(tts_filename)

        # Step 2: Hugging Face သို့ လှမ်းချိတ်ခြင်း (ဒီရောက်မှ စချိတ်ပါမယ်)
        print("Connecting to Hugging Face...")
        
        # ဒီနေရာမှာမှ Client ကို ခေါ်တဲ့အတွက် App စဖွင့်ချိန်မှာ Error မတက်တော့ပါဘူး
        hf_client = Client("r3gm/AICoverGen") 

        # Step 3: အသံပြောင်းခြင်း (API Call)
        result = hf_client.predict(
            song_input=handle_file(tts_filename),
            voice_model="Black Panther", 
            pitch_change=pitch,
            keep_files=False,
            is_webui=1,
            main_gain=0,
            backup_gain=0,
            inst_gain=0,
            index_rate=0.5,
            filter_radius=3,
            rms_mix_rate=0.25,
            f0_method="rmvpe+",
            crepe_hop_length=128,
            protect=0.33,
            pitch_change_all=0,
            reverb_rm_size=0.15,
            reverb_wet=0.2,
            reverb_dry=0.8,
            reverb_damping=0.7,
            output_format="mp3",
            extra_denoise=True,
            steps=1,
            api_name="/song_cover_pipeline"
        )

        # Step 4: ရလာတဲ့ Result ကို ပြန်ပို့ခြင်း
        if isinstance(result, tuple):
             output_path = result[1]
        else:
             output_path = result

        with open(output_path, "rb") as f:
            audio_data = f.read()

        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        # Error တက်ရင် ဘာကြောင့်လဲ သိရအောင် Log ထုတ်ကြည့်မယ်
        error_msg = str(e)
        print(f"Error Occurred: {error_msg}")
        
        if "Could not fetch api info" in error_msg:
            return Response(content="Error: Hugging Face Space (AICoverGen) သည် အိပ်ပျော်နေပါသဖြင့် နှိုးမရဖြစ်နေပါသည်။ ၅ မိနစ်ခန့်စောင့်ပြီး ပြန်စမ်းပါ (သို့) Space အသစ် ပြောင်းသုံးပါ။", status_code=500)
            
        return Response(content=f"Error: {error_msg}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
