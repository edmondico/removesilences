import streamlit as st
import os
import tempfile
import subprocess
from pathlib import Path
import speech_recognition as sr
from faster_whisper import WhisperModel
import ffmpeg
import shutil
from datetime import timedelta

# Configuración de la página
st.set_page_config(
    page_title="Cortador de Silencios",
    page_icon="🎥",
    layout="wide"
)

# Verificar si FFmpeg está instalado
try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    st.success("FFmpeg está instalado correctamente")
except subprocess.CalledProcessError:
    st.error("Error: FFmpeg no está instalado. Por favor, instala FFmpeg en tu sistema.")
    st.stop()

# Título y descripción
st.title("🎥 Cortador de Silencios")
st.markdown("""
Esta aplicación te permite:
- Eliminar automáticamente los silencios de tus videos
- Transcribir el audio usando Whisper o Google Speech Recognition
- Generar subtítulos en formato SRT
""")

# Sidebar para configuración
with st.sidebar:
    st.header("Configuración")
    
    # Opciones de procesamiento
    threshold = st.slider("Sensibilidad al silencio", 0.01, 0.1, 0.04, 0.01)
    min_duration = st.slider("Duración mínima del silencio (seg)", 0.1, 1.0, 0.3, 0.1)
    words_per_line = st.number_input("Palabras por línea (transcripción)", 1, 20, 10)
    generate_srt = st.checkbox("Generar subtítulos en formato SRT", value=True)
    
    # Selección de motor de transcripción
    transcription_engine = st.radio(
        "Motor de transcripción",
        ["Whisper", "Google Speech Recognition"]
    )

# Función para procesar el video
def process_video(video_file, output_path, threshold, min_duration):
    # Crear archivo temporal para el video
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(video_file.name).suffix) as tmp_file:
        tmp_file.write(video_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Usar ffmpeg para procesar el video
        cmd = [
            "ffmpeg",
            "-i", tmp_path,
            "-af", f"silenceremove=1:0:{threshold}:1:0:{threshold}:0:1",
            "-c:v", "copy",
            "-y",  # Sobrescribir archivo si existe
            output_path
        ]
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        if process.returncode != 0:
            st.error(f"Error en FFmpeg: {process.stderr}")
            return False
            
        return True
    except Exception as e:
        st.error(f"Error al procesar el video: {str(e)}")
        return False
    finally:
        os.unlink(tmp_path)

# Función para transcribir audio
def transcribe_audio(audio_path, engine="whisper"):
    if engine == "whisper":
        try:
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_path)
            return [(segment.start, segment.end, segment.text) for segment in segments]
        except Exception as e:
            st.error(f"Error con Whisper: {str(e)}")
            return []
    else:
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio)
                return [(0, 0, text)]
        except Exception as e:
            st.error(f"Error en la transcripción: {str(e)}")
            return []

# Función para crear archivo SRT
def create_srt(segments, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(segments, 1):
            start_time = str(timedelta(seconds=start)).replace(".", ",")[:11]
            end_time = str(timedelta(seconds=end)).replace(".", ",")[:11]
            f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

# Interfaz principal
uploaded_file = st.file_uploader("Sube tu video", type=["mp4", "avi", "mov", "mkv"])

if uploaded_file is not None:
    # Mostrar información del archivo
    st.write("Archivo cargado:", uploaded_file.name)
    
    # Crear directorio temporal para los archivos de salida
    with tempfile.TemporaryDirectory() as temp_dir:
        output_video = os.path.join(temp_dir, f"editado_{uploaded_file.name}")
        output_audio = os.path.join(temp_dir, "audio.wav")
        output_srt = os.path.join(temp_dir, f"{Path(uploaded_file.name).stem}.srt")
        
        # Procesar video
        if st.button("Procesar Video"):
            with st.spinner("Procesando video..."):
                if process_video(uploaded_file, output_video, threshold, min_duration):
                    st.success("¡Video procesado exitosamente!")
                    
                    # Extraer audio para transcripción
                    try:
                        ffmpeg.input(output_video).output(output_audio, acodec='pcm_s16le', ac=1, ar='16k').run(quiet=True)
                    except Exception as e:
                        st.error(f"Error al extraer audio: {str(e)}")
                        return
                    
                    # Transcribir audio
                    with st.spinner("Transcribiendo audio..."):
                        segments = transcribe_audio(output_audio, transcription_engine.lower())
                        
                        if generate_srt and segments:
                            create_srt(segments, output_srt)
                            st.success("¡Subtítulos generados!")
                    
                    # Mostrar resultados
                    st.video(output_video)
                    
                    # Botones de descarga
                    with open(output_video, "rb") as f:
                        st.download_button(
                            label="Descargar Video",
                            data=f,
                            file_name=f"editado_{uploaded_file.name}",
                            mime="video/mp4"
                        )
                    
                    if generate_srt and segments:
                        with open(output_srt, "rb") as f:
                            st.download_button(
                                label="Descargar Subtítulos",
                                data=f,
                                file_name=f"{Path(uploaded_file.name).stem}.srt",
                                mime="text/plain"
                            ) 