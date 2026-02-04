# app.py အပေါ်ဆုံးနားမှာ ဒါတွေပါမပါ စစ်ပါ (မပါရင် ထပ်ထည့်ပါ)
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from gradio_client import Client, handle_file
import edge_tts
import asyncio
import os

app = Flask(__name__)
CORS(app)

# Client ကို Global အနေနဲ့ တစ်ခါတည်း ကြေညာထားတာ ပိုမြန်ပါတယ်
# (ဒါပေမဲ့ Error တက်ရင် ပြန်ချိတ်ဖို့ try-except ခံထားသင့်ပါတယ်)
try:
    hf_client = Client("r3gm/AICoverGen")
except:
    print("Cannot connect to Hugging Face initially.")
    hf_client = None

# --- အသစ်ထပ်ထည့်ရမည့်အပိုင်း (Model List ယူရန်) ---
@app.route('/models', methods=['GET'])
def get_models():
    global hf_client
    try:
        if hf_client is None:
             hf_client = Client("r3gm/AICoverGen")
        
        # Space ထဲက Model စာရင်း update လုပ်ပေးတဲ့ API ကို ခေါ်လိုက်တာပါ
        # ဒီကောင်က list ပြန်ပေးလေ့ရှိပါတယ်
        models_result = hf_client.predict(api_name="/update_models_list")
        
        # Gradio API က return ပြန်တာ ပုံစံအမျိုးမျိုးရှိနိုင်လို့ list ကို သေချာဆွဲထုတ်ပါမယ်
        # များသောအားဖြင့် Tuple (dropdown_update, list, ...) ပုံစံနဲ့ လာတတ်ပါတယ်
        # ဒါကြောင့် models_result တွေကို စစ်ပြီး List ဖြစ်တဲ့ကောင်ကို ယူပါမယ်
        
        valid_models = []
        
        # ရလာတဲ့ Result ကို Print ထုတ်ကြည့်မယ် (Logs မှာ စစ်ဖို့)
        print(f"Raw Models Result: {models_result}")

        if isinstance(models_result, (list, tuple)):
            for item in models_result:
                # Gradio Dropdown update object တွေက Dictionary ပုံစံနဲ့ choices ပါတတ်တယ်
                if isinstance(item, dict) and 'choices' in item:
                    valid_models = item['choices']
                    break
                # တခါတလေ List အစစ်အတိုင်း ပါလာတတ်တယ်
                elif isinstance(item, list) and len(item) > 0 and isinstance(item[0], str):
                    valid_models = item
                    break
        
        # ဘာမှရှာမတွေ့ရင် Default စာရင်းတစ်ခု ပေးလိုက်မယ် (Error မတက်အောင်)
        if not valid_models:
             valid_models = ['Ben 10', 'Spongebob', 'Doraemon'] # Fallback

        return jsonify({"models": valid_models})

    except Exception as e:
        print(f"Model fetch error: {e}")
        return jsonify({"error": str(e), "models": ["Error Fetching Models"]}), 500

# --- အသံထုတ်သည့်အပိုင်း (Generate) ---
@app.route('/generate', methods=['POST'])
def generate_voice():
    global hf_client
    try:
        data = request.json
        text = data.get("text", "")
        # Frontend က ရွေးလိုက်တဲ့ Model နာမည်ကို လက်ခံယူမယ်
        selected_model = data.get("model", "Ben 10") # မပါရင် Default ယူမယ်
        
        if not text:
            return jsonify({"error": "No text provided"}), 400

        # ၁. Edge-TTS (မြန်မာအသံ)
        voice = "my-MM-ThihaNeural"
        tts_path = "/tmp/temp_tts.mp3"
        asyncio.run(edge_tts.Communicate(text, voice).save(tts_path))

        # ၂. RVC (Voice Conversion)
        if hf_client is None: hf_client = Client("r3gm/AICoverGen")
        
        print(f"Using Model: {selected_model}")
        
        result_path = hf_client.predict(
            song_input=handle_file(tts_path),
            voice_model=selected_model, # ဒီနေရာမှာ User ရွေးတာ ထည့်မယ်
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
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
