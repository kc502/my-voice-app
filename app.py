import gradio as gr
import edge_tts
import os
import asyncio
from gradio_client import Client, handle_file

# --- Configuration ---
# အစ်ကို့ရဲ့ RVC Link (Link သေရင် ဒီနေရာမှာ အသစ်လာထည့်ပေးရမယ်)
RVC_API_URL = "https://d60218d453d601423b.gradio.live/" 

AVAILABLE_MODELS = ["Ado", "Tom Holland", "LiSA", "Kurt Cobain"] 

async def process_automation(text, model_name, pitch_change, tts_voice):
    # ၁။ ဖိုင်သိမ်းမည့် နေရာသတ်မှတ် (Render ပေါ်တွင် error မတက်စေရန်)
    output_file = "tts_generated.mp3"
    
    # အဟောင်းရှိရင် အရင်ဖျက်မယ်
    if os.path.exists(output_file):
        os.remove(output_file)

    try:
        print(f"Step 1: Generating TTS for '{text}'...")
        
        # Edge TTS အသံထုတ်ခြင်း
        communicate = edge_tts.Communicate(text, tts_voice)
        await communicate.save(output_file)
        
        # ဖိုင်တကယ်ထွက်မထွက် စစ်ဆေးခြင်း (Crucial Step)
        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            return None, "❌ Error: Edge TTS က အသံဖိုင်မထုတ်ပေးနိုင်ပါ။ (Internet connection သို့မဟုတ် Text ကို စစ်ပါ)"
            
        print(f"Step 1 Complete: Audio file created ({os.path.getsize(output_file)} bytes).")

    except Exception as e:
        return None, f"TTS Generation Error: {str(e)}"

    # ၂။ RVC Server သို့ လှမ်းချိတ်ပြီး အသံပြောင်းခြင်း
    try:
        print(f"Step 2: Sending to RVC ({model_name})...")
        client = Client(RVC_API_URL)
        
        # Model List ကို refresh လုပ်ပါ
        try:
            client.predict(api_name="/update_models_list")
        except:
            pass # တချို့ version တွေမှာ error တက်တတ်လို့ ကျော်ပါမယ်

        # အသံပြောင်းပါ (Automation)
        result = client.predict(
            song_input=handle_file(output_file), # ထွက်လာတဲ့ TTS ဖိုင်ကို ပို့မယ်
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
        
        print("Step 2 Complete: Automation Success!")
        return result, "✅ Automation Success!"
        
    except Exception as e:
        return None, f"RVC Connection Error: {str(e)}"

# --- Gradio Interface ---
with gr.Blocks(title="AI Voice Automation") as demo:
    gr.Markdown("# 🤖 Auto TTS + RVC Converter")
    gr.Markdown("စာရိုက်ထည့်လိုက်တာနဲ့ အသံထွက်ပြီး AI Voice ပြောင်းပေးမည့် Automation စနစ်")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="စာရိုက်ရန် (Text Input)", placeholder="မင်္ဂလာပါ...", lines=3)
            with gr.Row():
                model_drop = gr.Dropdown(choices=AVAILABLE_MODELS, label="AI Model", value="Ado")
                voice_drop = gr.Dropdown(choices=["my-MM-KhineVoiceNeural", "en-US-AnaNeural"], label="TTS Language", value="my-MM-KhineVoiceNeural")
            
            pitch_slider = gr.Slider(minimum=-12, maximum=12, step=1, label="Pitch Change", value=0)
            btn = gr.Button("🚀 Start Automation", variant="primary")
        
        with gr.Column():
            audio_output = gr.Audio(label="ရလာသော အသံ (Final Output)")
            status_output = gr.Label(label="Status Log")

    # Button နှိပ်ရင် အလုပ်စမယ်
    btn.click(
        fn=process_automation, 
        inputs=[text_input, model_drop, pitch_slider, voice_drop], 
        outputs=[audio_output, status_output]
    )

# Render Configuration
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
