# Cortador de Silencios Web

Aplicación web para eliminar silencios de videos y generar transcripciones automáticas.

## Archivos Necesarios

Debido a las limitaciones de tamaño de GitHub, algunos archivos necesarios deben descargarse por separado:

1. **AEGPU.exe**: Descargar desde [Auto-Editor GPU Releases](https://github.com/petermg/auto-editor/releases/latest)
2. **FFmpeg**: Descargar desde [FFmpeg Official Website](https://ffmpeg.org/download.html)
3. **Faster-Whisper**: Descargar desde [Hugging Face](https://huggingface.co/Systran/faster-whisper-large-v3)

Coloca estos archivos en el directorio raíz del proyecto antes de ejecutar la aplicación.

## Características

- Eliminación automática de silencios en videos
- Transcripción de audio usando Whisper o Google Speech Recognition
- Generación de subtítulos en formato SRT
- Interfaz web amigable y fácil de usar

## Despliegue en Streamlit Cloud (Gratuito)

1. Crea una cuenta en [Streamlit Cloud](https://streamlit.io/cloud)
2. Conecta tu repositorio de GitHub
3. Selecciona el archivo `app.py` como punto de entrada
4. Configura las variables de entorno si es necesario
5. ¡Listo! Tu aplicación estará disponible en una URL pública

## Despliegue en Hugging Face Spaces (Alternativa Gratuita)

1. Crea una cuenta en [Hugging Face](https://huggingface.co/)
2. Crea un nuevo Space
3. Selecciona "Streamlit" como framework
4. Sube los archivos de tu proyecto
5. Configura el archivo `requirements.txt`
6. ¡Listo! Tu aplicación estará disponible en una URL pública

## Requisitos del Sistema

- Python 3.8+
- FFmpeg instalado en el sistema
- Dependencias listadas en `requirements.txt`

## Instalación Local

1. Clona este repositorio
2. Descarga los archivos necesarios mencionados arriba
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Instala FFmpeg en tu sistema
5. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

## Notas Importantes

- Para el procesamiento de videos grandes, se recomienda usar un servicio con suficiente memoria y CPU
- La transcripción con Whisper requiere más recursos que la de Google
- Los archivos temporales se eliminan automáticamente después del procesamiento

## Licencia

Ver archivo `license.txt` para más detalles.

# Cortador de Silencios - Solución de Errores y Procesamiento Optimizado

Este paquete incluye scripts para resolver problemas comunes y optimizar el procesamiento de video con auto-editor.

## Problema de Codec OpenH264

Si encuentras el error `avcodec_open2("libopenh264", {})`, significa que falta el codec OpenH264 necesario para codificar videos con alta calidad.

### Solución Automática
Ejecuta `instalar_codec.bat` o `descargar_codec_manual.bat` para instalar automáticamente el codec.

### Solución Manual
Si los scripts automáticos no funcionan, sigue estos pasos:

1. Descarga el codec OpenH264 directamente:
   - Visita: https://artifacts.videolan.org/dependencies/contrib/openh264/v2.3.1/openh264-2.3.1-win64.dll

2. Copia el archivo a la ubicación correcta:
   ```
   %APPDATA%\Python\Python311\site-packages\basswood_av\ffmpeg\bin\libopenh264.dll
   ```
   
   Nota: Debes renombrar el archivo descargado de `openh264-2.3.1-win64.dll` a `libopenh264.dll`

3. Crea las carpetas necesarias si no existen.

## Scripts Disponibles

### 1. `instalar_codec.bat`
- Descarga e instala automáticamente el codec OpenH264 de Cisco
- Actualiza auto-editor y sus dependencias
- Configura el sistema para usar el codec correctamente

### 2. `instalar_ffmpeg.bat`
- Alternativa completa si el codec OpenH264 no funciona
- Descarga e instala FFmpeg completo con todos los codecs
- Configura las variables de entorno necesarias

### 3. `procesar_directo.bat`
- Procesa videos directamente sin necesidad de usar la interfaz gráfica
- Utiliza configuración optimizada para alta calidad
- Parámetros:
  - `--video-codec libx264`: Codec de alta calidad
  - `--video-bitrate 50M`: Bitrate adecuado para videos HD/4K
  - `-preset slow -crf 18`: Configuración para priorizar calidad sobre velocidad

### 4. `parametros_nvenc.bat`
- Para usuarios con tarjeta gráfica NVIDIA
- Utiliza codificación por hardware para procesamiento más rápido
- Mantiene alta calidad de video

### 5. `instalar_ffmpeg_codecs.bat` (NUEVO)
- Instala FFmpeg con soporte completo para codecs avanzados
- Crea los scripts procesador_h264.bat y procesador_h265.bat
- Configura todo el entorno para usar codecs de máxima calidad

### 6. `procesador_h264.bat` (NUEVO)
- Utiliza el codec H.264 (libx264) con configuración de máxima calidad
- Soporta bitrate de hasta 800 Mbps
- Perfil optimizado para vídeo con `-tune film`

### 7. `procesador_h265.bat` (NUEVO)
- Utiliza el codec H.265/HEVC (libx265) en modo sin pérdidas
- Soporta bitrate de hasta 1 Gbps
- Recomendado para videos 4K/8K
- Mejor compresión que H.264 manteniendo calidad

## Parámetros Usados

### Para libx264 (CPU)
```
--video-codec libx264
--video-bitrate 50M
--ffmpeg-args "-preset slow -crf 18 -pix_fmt yuv420p"
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| video-codec | libx264 | Codec H.264 de alta calidad |
| video-bitrate | 50M | 50 Mbps, suficiente para 4K |
| preset | slow | Balance entre calidad y velocidad |
| crf | 18 | Calidad casi sin pérdidas (0-51, menor=mejor) |
| pix_fmt | yuv420p | Formato de color compatible |

### Para NVENC (GPU NVIDIA)
```
--video-codec h264_nvenc
--ffmpeg-args "-preset p7 -rc vbr -cq 18 -b:v 50M -profile:v high"
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| video-codec | h264_nvenc | Codec H.264 con aceleración GPU |
| preset | p7 | Mayor calidad (p1-p7) |
| rc | vbr | Control de tasa variable para mejor calidad |
| cq | 18 | Factor de calidad constante |
| b:v | 50M | Bitrate máximo |
| profile | high | Perfil avanzado para mejor calidad |

### Para libx265 (HEVC, máxima calidad) (NUEVO)
```
--video-codec libx265
--ffmpeg-args "-x265-params lossless=1 -pix_fmt yuv420p"
```

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| video-codec | libx265 | Codec H.265/HEVC de alta eficiencia |
| lossless | 1 | Activa el modo sin pérdidas |
| pix_fmt | yuv420p | Formato de color compatible |

## Solución de Problemas

Si continúas teniendo problemas después de instalar el codec o FFmpeg:

1. Asegúrate de reiniciar tu terminal o consola después de la instalación
2. Verifica la versión de auto-editor: `python -m auto_editor --version`
3. Prueba con un bitrate menor (20M en lugar de 50M)
4. Si tienes tarjeta NVIDIA, prueba con la codificación por hardware
5. Para resolver errores específicos, consulta la documentación de auto-editor: https://auto-editor.com/ 