@echo off
echo ================================================================
echo           PDF OCR PROCESSOR - CONFIGURACION INICIAL
echo ================================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instala Python 3.8+ desde python.org
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Crear entorno virtual
echo [1/4] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)
echo [OK] Entorno virtual creado

REM Activar entorno virtual
echo [2/4] Activando entorno virtual...
call venv\Scripts\activate.bat
echo [OK] Entorno virtual activado

REM Actualizar pip
echo [3/4] Actualizando pip...
python -m pip install --upgrade pip

REM Instalar dependencias
echo [4/4] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Fallo instalando dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas

REM Crear estructura de directorios
echo Creando estructura de directorios...
mkdir input 2>nul
mkdir output 2>nul
mkdir tests 2>nul
echo [OK] Directorios creados

echo.
echo ================================================================
echo                     INSTALACION COMPLETADA
echo ================================================================
echo.
echo SIGUIENTE PASO: Instalar Tesseract OCR
echo 1. Descargar desde: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Instalar en: C:\Program Files\Tesseract-OCR\
echo 3. Agregar al PATH del sistema
echo 4. Reiniciar terminal
echo.
echo PARA USAR EL PROGRAMA:
echo 1. Activar entorno: venv\Scripts\activate
echo 2. Ejecutar: python src/main.py input/archivo.pdf output/archivo_ocr.pdf
echo.
pause