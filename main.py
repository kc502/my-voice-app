import os
import uvicorn
import edge_tts
import shutil
from fastapi import FastAPI, Request, Form, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from gradio_client import Client, handle_file

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Hugging Face Space သို့ ချိတ်ဆက်ခြင်း
HF_CLIENT = Client("r3gm/AICoverGen")

# ယာယီဖိုင်များ သိမ်းရန်
TEMP_DIR = "/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

# ==========================================
# Startup: Black Panther Model ကို ကြိုတင်ဒေါင်းထားခြင်း
# ==========================================
print("Downloading Voice Model... (Please wait)")
try:
    # 1. Model ဒေါင်းလုဒ်ဆွဲခြင်း (Snippet အတိုင်း)
    HF_CLIENT.predict(
        url="https://huggingface.co/TJKAI/BlackPannther/resolve/main/BlackPanther.zip",
        dir_name="Black Panther",
        api_name="/download_online_model_1"
    )
    # 2. Model List ကို Update လုပ်ခြင်း
    HF_CLIENT.predict(api_name="/update_models_list")
    print("Voice Model Ready: Black Panther")
except Exception as e:
    print(f"Model Download Warning: {e}")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_voice(
    text: str = Form(...),
    pitch: int = Form(0) # အသံအနိမ့်အမြင့် (ယောက်ျားလေးမို့ 0 or -12 ထားပါ)
):
    try:
        # Step 1: Edge TTS ဖြင့် မြန်မာစာဖတ်ခြင်း (Nilar)
        tts_filename = os.path.join(TEMP_DIR, "tts_input.mp3")
        communicate = edge_tts.Communicate(text, "my-MM-NilarNeural")
        await communicate.save(tts_filename)

        # Step 2: AICoverGen သို့ ပို့ပြီး အသံပြောင်းခြင်း
        # Nano Banana ပေးထားတဲ့ Parameter တွေအတိုင်း အတိအကျ ထည့်ထားပါတယ်
        result = HF_CLIENT.predict(
            song_input=handle_file(tts_filename), # Edge TTS ဖိုင်
            voice_model="Black Panther",          # Model Name
            pitch_change=pitch,                   # Pitch
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
            steps=1, # 1 Step ဆိုတာ မြန်ပေမယ့် Quality နည်းနည်းလျော့မယ်
            api_name="/song_cover_pipeline"
        )

        # Step 3: ရလာတဲ့ Result (Zip or Audio path) ကို ဖတ်ပြီး ပြန်ပို့ခြင်း
        # Gradio က တခါတလေ Folder path ပြန်ပေးတတ်လို့ စစ်ရပါတယ်
        if isinstance(result, tuple):
             output_path = result[1] # Audio path
        else:
             output_path = result

        with open(output_path, "rb") as f:
            audio_data = f.read()

        return Response(content=audio_data, media_type="audio/mpeg")

    except Exception as e:
        return Response(content=f"Error: {str(e)}", status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
