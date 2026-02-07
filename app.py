import gradio as gr
import edge_tts
import asyncio
import os
from gradio_client import Client, handle_file

# --- Configuration ---
# အစ်ကို့ရဲ့ AICoverGen Link (၇၂ နာရီပြည့်ရင် လဲပေးရမယ်)
RVC_API_URL = "https://d60218d453d601423b.gradio.live/" 

# RVC Model နာမည်များ (API ဘက်မှာ Download လုပ်ပြီးသား ဖြစ်ရမယ်)
AVAILABLE_MODELS = ["Ado", "Tom Holland", "LiSA", "Kurt Cobain"] 

async def process_tts_rvc(text, model_name, pitch_change, tts_voice):
    output_file = "temp_tts.mp3"
    
    # 1. Edge TTS ဖြင့် စာမှ အသံပြောင်းခြင်း
    try:
        print(f"Generating TTS for: {text}")
        communicate = edge_tts.Communicate(text, tts_voice)
        await communicate.save(output_file)
    except Exception as e:
        return None, f"TTS Error: {str(e)}"

    # 2. RVC API သို့ ပို့ခြင်း
    try:
        print(f"Converting with RVC Model: {model_name}")
        client = Client(RVC_API_URL)
        
        # Model List Update လုပ် (မလုပ်ရင် တခါတလေ error တက်လို့)
        client.predict(api_name="/update_models_list")
        
        result = client.predict(
            song_input=handle_file(output_file),
            voice_model=model_name,
            pitch_change=pitch_change,
            keep_files=True,
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
        return result, "Success"
        
    except Exception as e:
        return None, f"RVC Error: {str(e)}"

# --- Gradio UI ---
with gr.Blocks(title="EdgeTTS + RVC WebUI") as demo:
    gr.Markdown("# 🎤 EdgeTTS to RVC Converter")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="ပြောစေချင်သော စာသား (Text)", placeholder="မင်္ဂလာပါ...")
            model_drop = gr.Dropdown(choices=AVAILABLE_MODELS, label="RVC Model ရွေးရန်", value="Ado")
            voice_drop = gr.Dropdown(
                choices=["my-MM-KhineVoiceNeural", "en-US-AnaNeural"], 
                label="TTS မူရင်းအသံ (Language)", 
                value="my-MM-KhineVoiceNeural"
            )
            pitch_slider = gr.Slider(minimum=-12, maximum=12, step=1, label="Pitch Change", value=0)
            btn = gr.Button("Generate Voice", variant="primary")
        
        with gr.Column():
            audio_output = gr.Audio(label="ရလာသော အသံ (Result)")
            status_output = gr.Label(label="Status")

    # Button Click Event
    btn.click(
        fn=process_tts_rvc, 
        inputs=[text_input, model_drop, pitch_slider, voice_drop], 
        outputs=[audio_output, status_output]
    )

# Run App
if __name__ == "__main__":
    demo.queue().launch()
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
