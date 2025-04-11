import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import sys
import os
from threading import Thread
import pkg_resources
import queue
import re
from datetime import datetime, timedelta
import shutil
import speech_recognition as sr

# Ruta al ejecutable AEGPU
AEGPU_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AEGPU.exe")

# Definir la ruta de FFmpeg instalado con soporte para libx265
FFMPEG_PATH = os.path.join("C:", "ffmpeg", "bin", "ffmpeg.exe")

# Ruta al ejecutable de Faster-Whisper si está instalado
FASTER_WHISPER_PATH = None
for whisper_path in ["faster-whisper-xxl.exe", os.path.join("Faster-Whisper-XXL", "faster-whisper-xxl.exe")]:
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), whisper_path)
    if os.path.exists(full_path):
        FASTER_WHISPER_PATH = full_path
        break

# Función para mostrar errores de importación
def show_error_and_exit(message):
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal
    messagebox.showerror("Error de Inicio", 
                        f"Error al iniciar la aplicación:\n\n{message}\n\n" +
                        "Verifique que AEGPU.exe esté disponible en el directorio de la aplicación.")
    sys.exit(1)

class CortadorSilencios:
    def __init__(self, root):
        self.root = root
        self.root.title("Cortador de Silencios")
        self.root.geometry("900x700")
        
        # Verificar que AEGPU.exe existe
        if not os.path.exists(AEGPU_PATH):
            show_error_and_exit(f"No se encontró AEGPU.exe en {AEGPU_PATH}")
        
        # Configurar colores y estilos
        self.style = ttk.Style()
        self.style.configure('Custom.TButton', padding=10)
        self.style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        self.style.configure('Subtitle.TLabel', font=('Helvetica', 10))
        self.style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        
        # Frame principal con padding
        main_frame = ttk.Frame(root, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        
        # Título y subtítulo
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="Cortador de Silencios", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        subtitle_label = ttk.Label(title_frame, 
                                 text="Elimina automáticamente los silencios de tus videos", 
                                 style='Subtitle.TLabel')
        subtitle_label.grid(row=1, column=0)
        
        # Frame superior para botones principales
        top_buttons_frame = ttk.Frame(main_frame)
        top_buttons_frame.grid(row=1, column=0, columnspan=2, pady=(0, 20), sticky='ew')
        
        # Botones principales en la parte superior
        self.select_button = ttk.Button(top_buttons_frame, text="Seleccionar Videos", 
                                      command=self.select_file, style='Custom.TButton')
        self.select_button.grid(row=0, column=0, padx=5, sticky='ew')
        
        self.select_output_button = ttk.Button(top_buttons_frame, text="Seleccionar Carpeta de Salida", 
                                             command=self.select_output_folder, style='Custom.TButton')
        self.select_output_button.grid(row=0, column=1, padx=5, sticky='ew')
        
        self.cut_silence_button = ttk.Button(top_buttons_frame, text="Cortar Silencios", 
                                           command=self.cut_silences, style='Custom.TButton')
        self.cut_silence_button.grid(row=0, column=2, padx=5, sticky='ew')
        self.cut_silence_button['state'] = 'disabled'
        
        self.transcribe_button = ttk.Button(top_buttons_frame, text="Transcribir (Whisper)", 
                                          command=self.transcribe_only, style='Custom.TButton')
        self.transcribe_button.grid(row=0, column=3, padx=5, sticky='ew')
        self.transcribe_button['state'] = 'disabled'
        
        self.transcribe_google_button = ttk.Button(top_buttons_frame, text="Transcribir (Google)", 
                                                 command=self.transcribe_with_google, style='Custom.TButton')
        self.transcribe_google_button.grid(row=0, column=4, padx=5, sticky='ew')
        self.transcribe_google_button['state'] = 'disabled'
        
        # Configurar pesos de columnas para que los botones se distribuyan equitativamente
        for i in range(5):
            top_buttons_frame.columnconfigure(i, weight=1)
        
        # Frame para el contenido principal (opciones y logs)
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.rowconfigure(2, weight=1)
        
        # Frame izquierdo para opciones
        left_frame = ttk.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 20))
        content_frame.columnconfigure(0, weight=1)
        
        # Frame para opciones
        options_frame = ttk.LabelFrame(left_frame, text="Opciones", padding="15")
        options_frame.grid(row=0, column=0, pady=(0, 20), sticky='ew')
        
        # Sensibilidad al silencio
        ttk.Label(options_frame, text="Sensibilidad al silencio:", 
                 style='Header.TLabel').grid(row=0, column=0, pady=5)
        self.threshold_var = tk.StringVar(value="0.04")
        threshold_entry = ttk.Entry(options_frame, textvariable=self.threshold_var, 
                                  width=10, justify='center')
        threshold_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # Duración mínima del silencio
        ttk.Label(options_frame, text="Duración mínima del silencio (seg):", 
                 style='Header.TLabel').grid(row=1, column=0, pady=5)
        self.min_duration_var = tk.StringVar(value="0.3")
        duration_entry = ttk.Entry(options_frame, textvariable=self.min_duration_var, 
                                 width=10, justify='center')
        duration_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Palabras por línea
        ttk.Label(options_frame, text="Palabras por línea (transcripción):", 
                 style='Header.TLabel').grid(row=2, column=0, pady=5)
        self.words_per_line_var = tk.StringVar(value="10")
        words_entry = ttk.Entry(options_frame, textvariable=self.words_per_line_var, 
                              width=10, justify='center')
        words_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # Opción de formato SRT
        self.srt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Generar subtítulos en formato SRT", 
                       variable=self.srt_var).grid(row=3, column=0, 
                       columnspan=2, pady=10)
        
        # Frame para procesamiento
        process_frame = ttk.LabelFrame(left_frame, text="Procesamiento", padding="15")
        process_frame.grid(row=1, column=0, sticky='ew')
        
        # Barra de progreso
        self.progress = ttk.Progressbar(process_frame, length=350, mode='indeterminate')
        self.progress.grid(row=0, column=0, pady=(0, 10), sticky='ew')
        
        # Estado
        self.status_label = ttk.Label(process_frame, text="")
        self.status_label.grid(row=1, column=0, pady=(0, 10))
        
        # Frame derecho para logs y archivos seleccionados
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(1, weight=2)
        
        # Frame para archivos seleccionados
        files_frame = ttk.LabelFrame(right_frame, text="Archivos Seleccionados", padding="15")
        files_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        right_frame.rowconfigure(0, weight=1)
        
        # Etiqueta para mostrar los archivos seleccionados
        self.file_label = ttk.Label(files_frame, text="Ningún archivo seleccionado", 
                                  wraplength=350)
        self.file_label.grid(row=0, column=0, pady=(0, 10))
        
        # Etiqueta para mostrar la carpeta de salida
        self.output_label = ttk.Label(files_frame, text="Carpeta de salida no seleccionada", 
                                    wraplength=350)
        self.output_label.grid(row=1, column=0, pady=(0, 10))
        
        # Frame para logs
        logs_frame = ttk.LabelFrame(right_frame, text="Registro de Actividad", padding="15")
        logs_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(1, weight=2)
        
        # Área de logs
        self.log_area = scrolledtext.ScrolledText(logs_frame, width=50, height=25)
        self.log_area.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        # Cola para los logs
        self.log_queue = queue.Queue()
        
        # Verificar instalación
        self.check_installation()
        
        # Iniciar el procesamiento de logs
        self.process_logs()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}\n"
        self.log_queue.put(log_message)

    def process_logs(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_area.insert(tk.END, message)
                self.log_area.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_logs)

    def check_installation(self):
        if os.path.exists(AEGPU_PATH):
            self.log(f"AEGPU encontrado en: {AEGPU_PATH}")
        else:
            self.log(f"ADVERTENCIA: No se encontró AEGPU.exe en: {AEGPU_PATH}", "WARN")
            self.log("La aplicación puede no funcionar correctamente", "WARN")
            
        if FASTER_WHISPER_PATH:
            self.log(f"Faster-Whisper encontrado en: {FASTER_WHISPER_PATH}")
        else:
            self.log("ADVERTENCIA: No se encontró Faster-Whisper. Las funciones de transcripción con Whisper no estarán disponibles.", "WARN")

    def select_file(self):
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Videos", "*.mp4 *.avi *.mov *.mkv"), ("Todos los archivos", "*.*")])
        if file_paths:
            self.file_paths = file_paths
            file_names = [os.path.basename(path) for path in file_paths]
            self.file_label['text'] = f"Archivos seleccionados:\n" + "\n".join(file_names)
            self.cut_silence_button['state'] = 'normal' if hasattr(self, 'output_folder') else 'disabled'
            self.transcribe_button['state'] = 'normal'
            self.transcribe_google_button['state'] = 'normal'
            self.log(f"Videos seleccionados: {', '.join(file_names)}")

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if folder_path:
            self.output_folder = folder_path
            self.output_label['text'] = f"Carpeta de salida: {folder_path}"
            self.cut_silence_button['state'] = 'normal' if hasattr(self, 'file_paths') else 'disabled'
            self.log(f"Carpeta de salida seleccionada: {folder_path}")

    def update_progress(self, percentage):
        self.progress['mode'] = 'determinate'
        self.progress['value'] = percentage

    def cut_silences(self):
        """Función para cortar silencios usando AEGPU con CPU"""
        if not hasattr(self, 'file_paths'):
            return
            
        if not hasattr(self, 'output_folder'):
            messagebox.showerror("Error", "Por favor, seleccione una carpeta de salida primero.")
            return
            
        self.select_button['state'] = 'disabled'
        self.select_output_button['state'] = 'disabled'
        self.cut_silence_button['state'] = 'disabled'
        self.transcribe_button['state'] = 'disabled'
        self.transcribe_google_button['state'] = 'disabled'
        self.progress.start()
        self.status_label['text'] = "Procesando videos..."
        self.log("Iniciando corte de silencios...")
        
        def process():
            try:
                # Obtener valores configurados por el usuario
                threshold = self.threshold_var.get()
                min_duration = self.min_duration_var.get()
                
                total_files = len(self.file_paths)
                processed_files = 0
                
                for file_path in self.file_paths:
                    # Crear nombre de archivo de salida
                    output_filename = f"editado_{os.path.basename(file_path)}"
                    output_path = os.path.join(self.output_folder, output_filename)
                    
                    # Construir el comando con configuración fija para alta calidad
                    cmd = [
                        AEGPU_PATH,
                        file_path,
                        "--video-codec", "h264",
                        "--video-bitrate", "500M",
                        "--audio-bitrate", "320k",
                        "--no-open",  # Evitar que se reproduzca automáticamente
                        "-o", output_path
                    ]
                    
                    # Si se han cambiado los valores por defecto, añadir los parámetros
                    if threshold != "0.04":
                        cmd.extend(["--edit", f"audio:threshold={threshold}"])
                    
                    if min_duration != "0.3":
                        cmd.extend(["--margin", f"{min_duration}sec"])
                    
                    self.log(f"Procesando: {os.path.basename(file_path)}")
                    self.log(f"Ejecutando comando: {' '.join(cmd)}")
                    
                    process = subprocess.Popen(cmd,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            universal_newlines=True,
                                            bufsize=1)
                    
                    # Procesar la salida en tiempo real
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            self.log(output.strip())
                    
                    # Verificar si el proceso se completó correctamente
                    if process.returncode == 0:
                        processed_files += 1
                        self.log(f"Video procesado exitosamente: {output_filename}")
                        self.root.after(0, lambda: self.update_progress((processed_files / total_files) * 100))
                    else:
                        self.log(f"Error al procesar el video: {os.path.basename(file_path)}")
                
                self.root.after(0, self.processing_complete)
                
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Error en el procesamiento: {str(e)}"))
        
        Thread(target=process).start()
        
    def processing_complete(self):
        self.progress.stop()
        self.select_button['state'] = 'normal'
        self.select_output_button['state'] = 'normal'
        self.cut_silence_button['state'] = 'normal'
        self.transcribe_button['state'] = 'normal'
        self.transcribe_google_button['state'] = 'normal'
        self.status_label['text'] = "¡Procesamiento completado!"
        messagebox.showinfo("Completado", 
                          "Los videos han sido procesados exitosamente.\n" +
                          f"Los archivos resultantes están en la carpeta:\n{self.output_folder}")

    def format_time(self, seconds):
        """Convierte segundos a formato de tiempo SRT (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        hours = td.seconds//3600
        minutes = (td.seconds//60)%60
        seconds = td.seconds%60
        milliseconds = round(td.microseconds/1000)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

    def create_srt_file(self, transcript_path, segments):
        """Crea un archivo SRT a partir de los segmentos de transcripción"""
        srt_path = os.path.splitext(transcript_path)[0] + ".srt"
        words_per_line = int(self.words_per_line_var.get())
        
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start_time = self.format_time(segment['start'])
                end_time = self.format_time(segment['end'])
                text = segment['text'].strip()
                
                # Dividir el texto en líneas según palabras_por_línea
                if words_per_line > 0:
                    words = text.split()
                    lines = []
                    for j in range(0, len(words), words_per_line):
                        line = ' '.join(words[j:j+words_per_line])
                        lines.append(line)
                    formatted_text = '\n'.join(lines)
                else:
                    formatted_text = text
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{formatted_text}\n\n")
        
        return srt_path
        
    def transcribe_only(self):
        """Función para transcribir sin procesar el video"""
        if not hasattr(self, 'file_paths'):
            return
            
        if not hasattr(self, 'output_folder'):
            messagebox.showerror("Error", "Por favor, seleccione una carpeta de salida primero.")
            return
            
        if not FASTER_WHISPER_PATH:
            self.show_error("No se encontró el ejecutable de Faster-Whisper. Por favor, descárguelo e instálelo.")
            return
            
        self.select_button['state'] = 'disabled'
        self.select_output_button['state'] = 'disabled'
        self.cut_silence_button['state'] = 'disabled'
        self.transcribe_button['state'] = 'disabled'
        self.transcribe_google_button['state'] = 'disabled'
        self.progress.start()
        self.status_label['text'] = "Transcribiendo videos..."
        self.log("Iniciando transcripción de videos con Faster-Whisper...")
        
        def process():
            try:
                total_files = len(self.file_paths)
                processed_files = 0
                
                for file_path in self.file_paths:
                    # Crear nombre de archivo de salida
                    output_filename = f"transcripcion_{os.path.splitext(os.path.basename(file_path))[0]}{'.srt' if self.srt_var.get() else '.txt'}"
                    output_path = os.path.join(self.output_folder, output_filename)
                    
                    # Crear el directorio si no existe
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    cmd = [
                        FASTER_WHISPER_PATH,
                        file_path,
                        "--language", "English",
                        "--model", "medium",
                        "--output_dir", os.path.dirname(output_path),
                        "--output_format", "srt" if self.srt_var.get() else "txt"
                    ]
                    
                    self.log(f"Transcribiendo: {os.path.basename(file_path)}")
                    self.log(f"Ejecutando comando: {' '.join(cmd)}")
                    
                    process = subprocess.Popen(cmd,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            universal_newlines=True)
                    
                    # Procesar la salida en tiempo real
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            self.log(output.strip())
                    
                    # Verificar si el proceso se completó correctamente
                    if process.returncode == 0:
                        # Mover el archivo de transcripción generado
                        generated_file = os.path.join(os.path.dirname(output_path), 
                                                   os.path.splitext(os.path.basename(file_path))[0] + 
                                                   (".srt" if self.srt_var.get() else ".txt"))
                                                   
                        if os.path.exists(generated_file):
                            # Si es un archivo SRT, reemplazar por uno con el formato de palabras por línea
                            if self.srt_var.get():
                                # Leer el archivo SRT generado
                                with open(generated_file, "r", encoding="utf-8") as f:
                                    content = f.read()
                                
                                # Extraer los segmentos
                                segments = []
                                pattern = r'(\d+)\s+(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s+(.*?)(?=\s*\d+\s+\d{2}:\d{2}:\d{2},\d{3}|$)'
                                matches = re.findall(pattern, content, re.DOTALL)
                                
                                for match in matches:
                                    segment_num = match[0]
                                    start_time = match[1]
                                    end_time = match[2]
                                    text = match[3].strip()
                                    
                                    # Convertir tiempo a segundos para compatibilidad con create_srt_file
                                    h, m, s = map(float, re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', start_time + ',000').groups())
                                    start_seconds = h * 3600 + m * 60 + s
                                    
                                    h, m, s = map(float, re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', end_time + ',000').groups())
                                    end_seconds = h * 3600 + m * 60 + s
                                    
                                    segments.append({
                                        'start': start_seconds,
                                        'end': end_seconds,
                                        'text': text
                                    })
                                
                                # Crear nuevo archivo SRT con formato personalizado
                                self.create_srt_file(output_path, segments)
                            else:
                                # Para archivo TXT, simplemente mover
                                shutil.move(generated_file, output_path)
                        
                        processed_files += 1
                        self.log(f"Video transcrito exitosamente: {output_filename}")
                        self.root.after(0, lambda: self.update_progress((processed_files / total_files) * 100))
                    else:
                        self.log(f"Error al transcribir el video: {os.path.basename(file_path)}")
                
                self.root.after(0, self.transcription_complete)
                
            except Exception as e:
                self.log(f"Error en la transcripción: {str(e)}", "ERROR")
                self.root.after(0, lambda: self.show_error(f"Error en la transcripción: {str(e)}"))
        
        Thread(target=process).start()
        
    def transcribe_with_google(self):
        """Función para transcribir usando SpeechRecognition y Google"""
        if not hasattr(self, 'file_paths'):
            return
            
        if not hasattr(self, 'output_folder'):
            messagebox.showerror("Error", "Por favor, seleccione una carpeta de salida primero.")
            return
            
        self.select_button['state'] = 'disabled'
        self.select_output_button['state'] = 'disabled'
        self.cut_silence_button['state'] = 'disabled'
        self.transcribe_button['state'] = 'disabled'
        self.transcribe_google_button['state'] = 'disabled'
        self.progress.start()
        self.status_label['text'] = "Extrayendo audio..."
        self.log("Iniciando extracción de audio para transcripción con Google...")
        
        def process():
            try:
                total_files = len(self.file_paths)
                processed_files = 0
                
                for file_path in self.file_paths:
                    # Crear nombre de archivo de salida
                    output_filename = f"transcripcion_google_{os.path.splitext(os.path.basename(file_path))[0]}{'.srt' if self.srt_var.get() else '.txt'}"
                    output_path = os.path.join(self.output_folder, output_filename)
                    
                    # Crear directorio temporal si no existe
                    temp_dir = os.path.join(self.output_folder, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Archivo de audio temporal
                    audio_temp = os.path.join(temp_dir, f"temp_audio_{processed_files}.wav")
                    
                    try:
                        # Extraer audio del video usando FFmpeg
                        self.log(f"Extrayendo audio de: {os.path.basename(file_path)}")
                        
                        # Si pydub está instalado, usarlo
                        try:
                            from pydub import AudioSegment
                            video_audio = AudioSegment.from_file(file_path)
                            video_audio.export(audio_temp, format="wav")
                            self.log("Audio extraído con pydub.")
                        except ImportError:
                            # Si no, usar FFmpeg directamente
                            ffmpeg_cmd = ["ffmpeg", "-i", file_path, "-y", "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1", audio_temp]
                            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                            self.log("Audio extraído con FFmpeg.")
                        
                        # Dividir en chunks de 30 segundos
                        self.log("Procesando audio en segmentos...")
                        
                        # Usamos directamente ffmpeg para dividir el audio en chunks
                        chunk_length = 30  # segundos
                        
                        # Obtener duración del audio
                        ffprobe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_temp]
                        duration_output = subprocess.check_output(ffprobe_cmd, text=True).strip()
                        total_duration = float(duration_output)
                        
                        # Calcular número de chunks
                        num_chunks = int(total_duration / chunk_length) + 1
                        
                        # Crear un reconocedor para Google Speech
                        recognizer = sr.Recognizer()
                        segments = []
                        
                        for i in range(num_chunks):
                            # Establecer el tiempo de inicio para este chunk
                            start_time = i * chunk_length
                            if start_time >= total_duration:
                                break
                                
                            # Generar el archivo de chunk
                            chunk_path = os.path.join(temp_dir, f"chunk_{processed_files}_{i}.wav")
                            
                            # Extraer el chunk
                            chunk_cmd = ["ffmpeg", "-y", "-i", audio_temp, "-ss", str(start_time), "-t", str(chunk_length), chunk_path]
                            subprocess.run(chunk_cmd, check=True, capture_output=True, text=True)
                            
                            # Actualizar progreso
                            progress = (processed_files * num_chunks + i + 1) / (total_files * num_chunks) * 100
                            self.root.after(0, lambda p=progress: self.update_progress(p))
                            self.root.after(0, lambda f=processed_files+1, t=total_files, c=i+1, n=num_chunks: 
                                          self.status_label.configure(text=f"Transcribiendo video {f}/{t}, segmento {c}/{n}..."))
                            
                            # Transcribir el chunk
                            with sr.AudioFile(chunk_path) as source:
                                audio_data = recognizer.record(source)
                                try:
                                    texto = recognizer.recognize_google(audio_data, language="en-US")
                                    # Guardar segmento con tiempos
                                    segment = {
                                        'start': start_time,
                                        'end': min(start_time + chunk_length, total_duration),
                                        'text': texto
                                    }
                                    segments.append(segment)
                                    self.log(f"Segmento {i+1}/{num_chunks} transcrito")
                                except Exception as e:
                                    self.log(f"Error en segmento {i+1}: {str(e)}", "ERROR")
                                    segments.append({
                                        'start': start_time,
                                        'end': min(start_time + chunk_length, total_duration),
                                        'text': "[Transcription error]"
                                    })
                            
                            # Limpiar el archivo de chunk
                            try:
                                os.remove(chunk_path)
                            except:
                                pass
                        
                        # Guardar transcripción en el formato seleccionado
                        if self.srt_var.get():
                            final_path = self.create_srt_file(output_path, segments)
                        else:
                            # Guardar como texto plano con límite de palabras por línea
                            words_per_line = int(self.words_per_line_var.get())
                            with open(output_path, "w", encoding="utf-8") as f:
                                for segment in segments:
                                    text = segment['text']
                                    if words_per_line > 0:
                                        words = text.split()
                                        for j in range(0, len(words), words_per_line):
                                            line = ' '.join(words[j:j+words_per_line])
                                            f.write(f"{line}\n")
                                    else:
                                        f.write(f"{text}\n")
                            final_path = output_path
                        
                        processed_files += 1
                        self.log(f"Video transcrito exitosamente: {output_filename}")
                        self.root.after(0, lambda: self.update_progress((processed_files / total_files) * 100))
                        
                    finally:
                        # Limpiar archivos temporales
                        if os.path.exists(audio_temp):
                            try:
                                os.remove(audio_temp)
                            except:
                                pass
                
                # Limpiar directorio temporal
                if os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                
                self.root.after(0, self.transcription_complete)
                
            except Exception as e:
                self.log(f"Error en la transcripción: {str(e)}", "ERROR")
                self.root.after(0, lambda: self.show_error(f"Error en la transcripción: {str(e)}"))
        
        Thread(target=process).start()
        
    def transcription_complete(self):
        """Muestra mensaje de completado para la transcripción"""
        self.progress.stop()
        self.select_button['state'] = 'normal'
        self.select_output_button['state'] = 'normal'
        self.cut_silence_button['state'] = 'normal'
        self.transcribe_button['state'] = 'normal'
        self.transcribe_google_button['state'] = 'normal'
        self.status_label['text'] = "¡Transcripción completada!"
        messagebox.showinfo("Completado", 
                          "Los videos han sido transcritos exitosamente.\n" +
                          f"Los archivos resultantes están en la carpeta:\n{self.output_folder}")

    def show_error(self, message):
        self.progress.stop()
        self.select_button['state'] = 'normal'
        self.cut_silence_button['state'] = 'normal'
        self.transcribe_button['state'] = 'normal' if hasattr(self, 'file_paths') and FASTER_WHISPER_PATH else 'disabled'
        self.transcribe_google_button['state'] = 'normal' if hasattr(self, 'file_paths') else 'disabled'
        self.status_label['text'] = "Error"
        messagebox.showerror("Error", message)

def main():
    try:
        # Verificar AEGPU.exe existe
        aegpu_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AEGPU.exe")
        if not os.path.exists(aegpu_path):
            raise FileNotFoundError(
                "No se encontró AEGPU.exe. Por favor:\n"
                "1. Asegúrese de que AEGPU.exe está en la misma carpeta que este programa.\n"
                "2. Si no lo tiene, descárguelo desde:\n"
                "   https://github.com/petermg/auto-editor/releases/latest\n"
            )

        root = tk.Tk()
        app = CortadorSilencios(root)
        root.mainloop()

    except Exception as e:
        # Crear una ventana de error si no existe
        try:
            error_window = tk.Tk()
            error_window.withdraw()  # Ocultar la ventana principal
            messagebox.showerror(
                "Error de Inicio",
                f"Error al iniciar la aplicación:\n\n{str(e)}\n\n"
                "Si el error persiste, por favor:\n"
                "1. Asegúrese de que AEGPU.exe está disponible\n"
                "2. Reinicie la aplicación"
            )
            error_window.destroy()
        except:
            # Si falla la ventana de error, usar print
            print(f"Error crítico: {str(e)}")
            input("Presione Enter para cerrar...")

if __name__ == '__main__':
    main() 