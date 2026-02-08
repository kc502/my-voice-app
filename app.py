import gradio as gr
import edge_tts
import asyncio
import os
from gradio_client import Client, handle_file

# --- Configuration ---
RVC_API_URL = "https://d60218d453d601423b.gradio.live/" 
AVAILABLE_MODELS = ["Ado", "Tom Holland", "LiSA", "Kurt Cobain"] 

async def process_tts_rvc(text, model_name, pitch_change, tts_voice):
    output_file = "temp_tts.mp3"
    
    # 1. Edge TTS Generation
    try:
        print(f"Generating TTS for: {text}")
        communicate = edge_tts.Communicate(text, tts_voice)
        await communicate.save(output_file)
    except Exception as e:
        return None, f"TTS Error: {str(e)}"

    # 2. RVC Conversion
    try:
        print(f"Converting with RVC Model: {model_name}")
        client = Client(RVC_API_URL)
        
        # Refresh models
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

# --- UI Layout ---
with gr.Blocks(title="EdgeTTS + RVC WebUI") as demo:
    gr.Markdown("# 🎤 EdgeTTS to RVC Converter")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Text Input", placeholder="စာရိုက်ပါ...")
            model_drop = gr.Dropdown(choices=AVAILABLE_MODELS, label="RVC Model", value="Ado")
            voice_drop = gr.Dropdown(choices=["my-MM-KhineVoiceNeural", "en-US-AnaNeural"], label="TTS Voice", value="my-MM-KhineVoiceNeural")
            pitch_slider = gr.Slider(minimum=-12, maximum=12, step=1, label="Pitch", value=0)
            btn = gr.Button("Generate", variant="primary")
        
        with gr.Column():
            audio_output = gr.Audio(label="Result")
            status_output = gr.Label(label="Status")

    btn.click(fn=process_tts_rvc, inputs=[text_input, model_drop, pitch_slider, voice_drop], outputs=[audio_output, status_output])

# Render Port Configuration
if __name__ == "__main__":
    demo.queue().launch(server_name="0.0.0.0", server_port=7860)
