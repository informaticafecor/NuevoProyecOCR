1. Primero verifica que tu entorno virtual esté activado:

venv\Scripts\activate

4. Instala las dependencias:

pip install -r requirements.txt


Si sigue fallando, prueba esto:

Opción A - Instalar uno por uno (más seguro):

pip install ocrmypdf
pip install PyPDF2
pip install pytesseract
pip install pymupdf
pip install Pillow
pip install pdf2image
pip install tqdm
pip install colorama
pip install python-dotenv


comando para ejecutar el ocr por consola, subir el archivo a input 
# Coloca un PDF en la carpeta input/ y ejecuta:

# 1. Activar entorno virtual
venv\Scripts\activate

# 2. Ejecutar el procesador
python src/main.py input/Oficio.pdf output/Oficio_ocr.pdf


Si persiste el error, instalar todas las dependencias una por una:


pip install colorama
pip install tqdm
pip install ocrmypdf
pip install PyPDF2
pip install pytesseract
pip install pymupdf
pip install Pillow
pip install pdf2image
pip install python-dotenv





















