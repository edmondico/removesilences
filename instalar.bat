@echo off
echo Instalando dependencias necesarias...

:: Crear directorio para modelos si no existe
if not exist "_models" mkdir "_models"

echo.
echo ============================================================
echo IMPORTANTE: Descarga manual requerida
echo ============================================================
echo.
echo Por favor, siga estos pasos:
echo.
echo 1. Visite: https://github.com/Purfview/whisper-standalone-win/releases/latest
echo 2. Descargue el archivo "Faster-Whisper-XXL.zip"
echo 3. Extraiga el contenido del archivo ZIP en esta carpeta
echo 4. Presione cualquier tecla para continuar con la instalación
echo    de las dependencias de Python
echo.
echo ============================================================
pause

:: Instalar dependencias de Python
echo.
echo Instalando dependencias de Python...

:: Actualizar pip primero
echo Actualizando pip...
python -m pip install --upgrade pip

:: Instalar dependencias una por una con --no-cache-dir
echo.
echo Instalando auto-editor 27.0.0...
python -m pip install --no-cache-dir auto-editor==27.0.0

echo.
echo Instalando SpeechRecognition...
python -m pip install --no-cache-dir SpeechRecognition

echo.
echo Instalando pydub...
python -m pip install --no-cache-dir pydub

:: Verificar la instalación
echo.
echo Verificando instalación...
python -c "import speech_recognition; print('speech_recognition instalado correctamente')" || echo Error: speech_recognition no se instaló correctamente
python -c "import pydub; print('pydub instalado correctamente')" || echo Error: pydub no se instaló correctamente
python -m auto_editor --version || echo Error: auto-editor no se instaló correctamente

echo.
echo Instalacion de dependencias de Python completada!
echo.
echo RECUERDE: Debe descargar y extraer Faster-Whisper-XXL manualmente
echo si aun no lo ha hecho.
echo.
echo Una vez completados todos los pasos, puede ejecutar el programa
echo 'cortador_silencios.pyw'
echo.
pause 