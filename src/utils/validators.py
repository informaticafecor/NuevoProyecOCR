"""
Validadores para archivos PDF y configuración del sistema
Autor: PDF Processor Team
"""

import os
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FileValidator:
    """Validador de archivos PDF"""
    
    @staticmethod
    def validate_pdf_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Valida si el archivo PDF es válido para procesamiento
        
        Args:
            file_path (str): Ruta del archivo PDF
            
        Returns:
            Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
        """
        try:
            path = Path(file_path)
            
            # Verificar si el archivo existe
            if not path.exists():
                return False, f"El archivo no existe: {file_path}"
            
            # Verificar extensión
            if path.suffix.lower() != '.pdf':
                return False, f"El archivo debe ser PDF, recibido: {path.suffix}"
            
            # Verificar tamaño (máximo 100MB por defecto)
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 100:
                return False, f"Archivo muy grande: {size_mb:.1f}MB (máximo 100MB)"
            
            # Verificar que el archivo no esté vacío
            if path.stat().st_size == 0:
                return False, "El archivo PDF está vacío"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validando archivo: {e}")
            return False, f"Error accediendo al archivo: {str(e)}"
    
    @staticmethod
    def validate_output_path(output_path: str) -> Tuple[bool, Optional[str]]:
        """
        Valida si la ruta de salida es válida
        
        Args:
            output_path (str): Ruta de salida para el archivo
            
        Returns:
            Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
        """
        try:
            path = Path(output_path)
            
            # Verificar que el directorio padre exista o se pueda crear
            parent_dir = path.parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    return False, f"No se puede crear directorio: {parent_dir}"
            
            # Verificar extensión PDF
            if path.suffix.lower() != '.pdf':
                return False, "El archivo de salida debe tener extensión .pdf"
            
            # Verificar permisos de escritura
            if path.exists() and not os.access(path, os.W_OK):
                return False, f"Sin permisos de escritura en: {output_path}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validando ruta de salida: {e}")
            return False, f"Error en ruta de salida: {str(e)}"

class SystemValidator:
    """Validador de configuración del sistema"""
    
    @staticmethod
    def validate_tesseract_installation(tesseract_path: str) -> Tuple[bool, Optional[str]]:
        """
        Valida si Tesseract OCR está instalado correctamente
        
        Args:
            tesseract_path (str): Ruta al ejecutable de Tesseract
            
        Returns:
            Tuple[bool, Optional[str]]: (está_instalado, mensaje_error)
        """
        try:
            # Verificar si el ejecutable existe
            if not os.path.exists(tesseract_path):
                return False, f"Tesseract no encontrado en: {tesseract_path}"
            
            # Verificar si es ejecutable
            if not os.access(tesseract_path, os.X_OK):
                return False, f"Tesseract no es ejecutable: {tesseract_path}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validando Tesseract: {e}")
            return False, f"Error verificando Tesseract: {str(e)}"
    
    @staticmethod
    def validate_language_support(language: str = 'spa') -> Tuple[bool, Optional[str]]:
        """
        Valida si el idioma está disponible en Tesseract
        
        Args:
            language (str): Código del idioma (por defecto 'spa' para español)
            
        Returns:
            Tuple[bool, Optional[str]]: (idioma_disponible, mensaje_error)
        """
        try:
            import subprocess
            result = subprocess.run(['tesseract', '--list-langs'], 
                                  capture_output=True, text=True, timeout=10)
            
            available_langs = result.stdout.strip().split('\n')[1:]  # Skip header
            
            if language not in available_langs:
                return False, f"Idioma '{language}' no disponible. Disponibles: {', '.join(available_langs)}"
            
            return True, None
            
        except subprocess.TimeoutExpired:
            return False, "Timeout verificando idiomas de Tesseract"
        except subprocess.CalledProcessError as e:
            return False, f"Error ejecutando tesseract --list-langs: {e}"
        except Exception as e:
            logger.error(f"Error validando idioma: {e}")
            return False, f"Error verificando idioma: {str(e)}"