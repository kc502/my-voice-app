import os
import asyncio
import edge_tts
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file

app = Flask(__name__)
CORS(app)

# ယာယီဖိုင်များ သိမ်းရန်
TEMP_DIR = "/tmp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# --- သင်ပေးထားသော Model Links များ ---
MODEL_URLS = {
    "Tom Holland": "https://huggingface.co/TJKAI/TomHolland/resolve/main/TomHolland.zip",
    "Kurt Cobain": "https://huggingface.co/Florstie/Kurt_Cobain_byFlorst/resolve/main/Kurt_Florst.zip",
    "Bratishkinoff": "https://huggingface.co/JHmashups/Bratishkinoff/resolve/main/bratishkin.zip",
    "MaeASMR": "https://huggingface.co/ctian/VRC/resolve/main/MaeASMR.zip",
    "IvanZolo2004": "https://huggingface.co/fenikkusugosuto/IvanZolo2004/resolve/main/ivanZolo.zip",
    "Black Panther": "https://huggingface.co/TJKAI/BlackPannther/resolve/main/BlackPanther.zip"
}

@app.route('/generate', methods=['POST'])
def generate_voice():
    try:
        data = request.json
        text = data.get("text", "")
        # Frontend မှ ပို့လိုက်သော Model နာမည် (ဥပမာ "Tom Holland")
        model_name = data.get("model", "Tom Holland") 
        
        if not text:
            return jsonify({"error": "ကျေးဇူးပြု၍ စာရိုက်ထည့်ပါ"}), 400

        print(f"Processing: {text} | Voice: {model_name}")

        # ၁. Edge-TTS (မြန်မာအသံ ဖန်တီးခြင်း)
        tts_path = os.path.join(TEMP_DIR, "temp_tts.mp3")
        # Thiha (ကျား) အသံကို အဓိကထားသုံးပါမည်
        asyncio.run(edge_tts.Communicate(text, "my-MM-ThihaNeural").save(tts_path))
        print("Edge-TTS generated.")

        # ၂. RVC Client ချိတ်ဆက်ခြင်း
        # Public Space ကိုပဲ သုံးပါမည်
        client = Client("r3gm/AICoverGen")
        
        # ၃. Model Download လုပ်ခြင်း (အရေးကြီးဆုံးအဆင့်)
        # User ရွေးလိုက်တဲ့ Model က ကျွန်တော်တို့ စာရင်းထဲမှာ ရှိရင် Download အရင်လုပ်ခိုင်းမယ်
        if model_name in MODEL_URLS:
            print(f"Downloading Model: {model_name}...")
            try:
                # Hugging Face Space သို့ Model URL ပို့ပြီး Download ခိုင်းခြင်း
                client.predict(
                    MODEL_URLS[model_name], # ZIP URL
                    model_name,             # Name
                    api_name="/download_model"
                )
                print("Model download command sent.")
            except Exception as e:
                # တကယ်လို့ Model က ရှိပြီးသားဆိုရင် Error တက်နိုင်တယ်၊ ဒါကို ကျော်သွားမယ်
                print(f"Download warning (might already exist): {e}")

        # ၄. အသံပြောင်းခြင်း (Voice Conversion)
        print("Converting voice with RVC...")
        result_path = client.predict(
            song_input=handle_file(tts_path),
            voice_model=model_name, # Download လုပ်ထားတဲ့ နာမည်အတိုင်း သုံးမယ်
            pitch_change=0,
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
        
        # ၅. ရလာတဲ့ အသံဖိုင်ကို ပြန်ပို့ခြင်း
        return send_file(result_path, mimetype="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render Port Configuration
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
