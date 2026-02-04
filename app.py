import os
import asyncio
import edge_tts
import time
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file

app = Flask(__name__)
CORS(app)

TEMP_DIR = "/tmp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

MODEL_URLS = {
    "Tom Holland": "https://huggingface.co/TJKAI/TomHolland/resolve/main/TomHolland.zip",
    "Kurt Cobain": "https://huggingface.co/Florstie/Kurt_Cobain_byFlorst/resolve/main/Kurt_Florst.zip",
    "Bratishkinoff": "https://huggingface.co/JHmashups/Bratishkinoff/resolve/main/bratishkin.zip",
    "MaeASMR": "https://huggingface.co/ctian/VRC/resolve/main/MaeASMR.zip",
    "IvanZolo2004": "https://huggingface.co/fenikkusugosuto/IvanZolo2004/resolve/main/ivanZolo.zip",
    "Black Panther": "https://huggingface.co/TJKAI/BlackPannther/resolve/main/BlackPanther.zip"
}

# *** ဒီနေရာမှာ Token ထည့်ပါ (အရေးကြီးဆုံး) ***
# "hf_xxxx..." နေရာမှာ သင် Copy ကူးလာတဲ့ Token ကို ထည့်ပါ
HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 

SPACE_ID = "r3gm/AICoverGen"

def get_valid_client():
    """Token အသုံးပြု၍ Client ချိတ်ဆက်ခြင်း"""
    max_retries = 5
    for i in range(max_retries):
        try:
            print(f"Connecting with Token... (Attempt {i+1}/{max_retries})")
            
            # *** hf_token ထည့်လိုက်မှ Quota တိုးမှာပါ ***
            client = Client(SPACE_ID, hf_token=HF_TOKEN)
            
            try:
                result = client.predict(api_name="/update_models_list")
                if "choices" in str(result) and "[]" not in str(result):
                    print("Connected and Models found!")
                    return client
                else:
                    print("Connected but List empty. Retrying...")
            except:
                print("Checking list failed. Retrying...")
                
        except Exception as e:
            print(f"Connection failed: {e}")
        
        time.sleep(5)
    
    return Client(SPACE_ID, hf_token=HF_TOKEN)

@app.route('/generate', methods=['POST'])
def generate_voice():
    try:
        data = request.json
        text = data.get("text", "")
        model_name = data.get("model", "Tom Holland") 
        
        if not text: return jsonify({"error": "စာရိုက်ပါ"}), 400

        print(f"=== Starting Process for {model_name} ===")

        # ၁. Edge-TTS
        tts_path = os.path.join(TEMP_DIR, "temp_tts.mp3")
        asyncio.run(edge_tts.Communicate(text, "my-MM-ThihaNeural").save(tts_path))
        print("1. Edge-TTS Done.")

        # ၂. Smart Client (Token ပါသည်)
        client = get_valid_client()

        # ၃. Download Logic
        if model_name in MODEL_URLS:
            print(f"2. Downloading Model: {model_name}...")
            try:
                client.predict(
                    MODEL_URLS[model_name],
                    model_name,
                    api_name="/download_model"
                )
                client.predict(api_name="/update_models_list")
                # Reload Client to see new models
                client = Client(SPACE_ID, hf_token=HF_TOKEN)
                
            except Exception as e:
                print(f"Download warning: {e}")

        # ၄. Voice Conversion
        print("3. Converting Voice...")
        result_path = client.predict(
            song_input=handle_file(tts_path),
            voice_model=model_name,
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
        
        return send_file(result_path, mimetype="audio/mpeg")

    except Exception as e:
        print(f"FINAL ERROR: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
