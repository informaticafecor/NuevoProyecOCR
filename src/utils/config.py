"""
Configuración general del proyecto PDF OCR Processor
Autor: PDF Processor Team
Versión: 1.0.0
"""

import os
from pathlib import Path

class Config:
    """Configuración principal del proyecto"""
    
    # Rutas del proyecto
    ROOT_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = ROOT_DIR / "src"
    INPUT_DIR = ROOT_DIR / "input"
    OUTPUT_DIR = ROOT_DIR / "output"
    TESTS_DIR = ROOT_DIR / "tests"
    
    # Configuración OCR
    TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    DEFAULT_LANGUAGE = 'spa'  # Español
    OCR_DPI = 300  # Calidad de imagen para OCR
    
    # Configuración de archivos
    ALLOWED_EXTENSIONS = ['.pdf']
    MAX_FILE_SIZE_MB = 100
    
    # Configuración de logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # OCRmyPDF configuración
    OCRMYPDF_CONFIG = {
        'language': DEFAULT_LANGUAGE,
        'deskew': True,  # Corregir inclinación
        'clean': True,   # Limpiar imagen
        'optimize': 1,   # Optimizar PDF
        'pdf_renderer': 'hocr',  # Mejor para texto
        'progress_bar': True
    }
    
    # Futura configuración IA (Ollama)
    AI_CONFIG = {
        'enabled': False,  # Por ahora deshabilitado
        'ollama_host': 'http://localhost:11434',
        'model': 'llama2-spanish',
        'max_tokens': 2000
    }
    
    @classmethod
    def create_directories(cls):
        """Crear directorios necesarios si no existen"""
        directories = [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.TESTS_DIR]
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    @classmethod
    def validate_tesseract(cls):
        """Validar que Tesseract esté instalado correctamente"""
        return os.path.exists(cls.TESSERACT_CMD)