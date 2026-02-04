import os
import asyncio
import edge_tts
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file

app = Flask(__name__)
CORS(app)  # Frontend မှ လှမ်းခေါ်ခွင့်ပြုရန်

# ယာယီဖိုင်များ သိမ်းရန်နေရာ (Render မှာ /tmp ကို သုံးတာ စိတ်ချရပါတယ်)
TEMP_DIR = "/tmp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

async def create_tts(text, voice, output_file):
    """Edge-TTS ဖြင့် စာကို အသံပြောင်းပေးမည့် Function"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@app.route('/generate', methods=['POST'])
def generate_voice():
    try:
        # Frontend မှ ပို့လိုက်သော Data ကို ယူမယ်
        data = request.json
        text = data.get("text", "")
        
        if not text:
            return jsonify({"error": "စာသားထည့်ပါ"}), 400

        print(f"Processing text: {text}")

        # ၁. Edge-TTS ဖြင့် အသံဖိုင်အရင်ထုတ်မယ်
        tts_filename = "temp_tts.mp3"
        tts_path = os.path.join(TEMP_DIR, tts_filename)
        
        # Thiha (ကျား) သို့မဟုတ် Nilar (မ) ရွေးနိုင်သည်
        voice = "my-MM-ThihaNeural" 
        
        # Async function ကို run မယ်
        asyncio.run(create_tts(text, voice, tts_path))
        print("Edge-TTS generated.")

        # ၂. Hugging Face RVC သို့ ပို့ပြီး အသံပြောင်းမယ်
        # သင်ပြထားသော AICoverGen Space ကို သုံးထားပါသည်
        client = Client("r3gm/AICoverGen")
        
        # Model List ကို update လုပ်ခြင်း (မလုပ်ရင် error တက်တတ်လို့ပါ)
        client.predict(api_name="/update_models_list")

        print("Converting voice with RVC...")
        
        result_path = client.predict(
            song_input=handle_file(tts_path),
            voice_model="Ben 10",  # Space ထဲက ကြိုက်တဲ့ Model နာမည် ပြောင်းထည့်နိုင်ပါတယ်
            pitch_change=0,           # 0 = ပုံမှန်၊ 12 = မိန်းမသံဘက်သွားမယ်
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
        
        print(f"RVC finished. File at: {result_path}")

        # ၃. ရလာတဲ့ အသံဖိုင်ကို Frontend သို့ ပြန်ပို့မယ်
        return send_file(result_path, mimetype="audio/mpeg")

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render အတွက် Port Configuration
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
