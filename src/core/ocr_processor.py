"""
Procesador OCR - Aplica OCR a PDFs escaneados usando OCRmyPDF
Autor: PDF Processor Team
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import ocrmypdf
from tqdm import tqdm
import shutil

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Procesador OCR para PDFs escaneados"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el procesador OCR
        
        Args:
            config (Dict): Configuración del OCR
        """
        self.config = config
        self.tesseract_cmd = config.get('tesseract_cmd')
        self.language = config.get('language', 'spa')
        self.dpi = config.get('dpi', 300)
    
    def process_pdf(self, input_path: str, output_path: str, 
                   force_ocr: bool = False) -> Dict[str, Any]:
        """
        Procesa un PDF aplicando OCR si es necesario
        
        Args:
            input_path (str): Ruta del PDF de entrada
            output_path (str): Ruta del PDF de salida
            force_ocr (bool): Forzar OCR incluso si tiene texto
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            result = {
                'success': False,
                'input_file': input_path,
                'output_file': output_path,
                'processing_method': '',
                'pages_processed': 0,
                'processing_time': 0,
                'file_size_before': 0,
                'file_size_after': 0,
                'error': None
            }
            
            # Obtener información inicial
            input_path_obj = Path(input_path)
            result['file_size_before'] = input_path_obj.stat().st_size
            
            logger.info(f"Iniciando procesamiento OCR de: {input_path}")
            
            # Determinar método de procesamiento
            if force_ocr:
                result['processing_method'] = 'OCR_FORCED'
                success = self._apply_ocr(input_path, output_path, result)
            else:
                # Verificar si ya tiene texto
                from .pdf_detector import PDFDetector
                detector = PDFDetector()
                analysis = detector.analyze_pdf(input_path)
                
                if analysis.get('needs_ocr', True):
                    result['processing_method'] = 'OCR_APPLIED'
                    success = self._apply_ocr(input_path, output_path, result)
                else:
                    result['processing_method'] = 'COPY_EXISTING'
                    success = self._copy_existing(input_path, output_path, result)
            
            # Verificar resultado final
            if success and Path(output_path).exists():
                result['success'] = True
                result['file_size_after'] = Path(output_path).stat().st_size
                logger.info(f"Procesamiento exitoso: {output_path}")
            else:
                result['error'] = "El archivo de salida no se generó correctamente"
            
            return result
            
        except Exception as e:
            logger.error(f"Error procesando PDF: {e}")
            return {
                'success': False,
                'input_file': input_path,
                'output_file': output_path,
                'error': str(e)
            }
    
    def _apply_ocr(self, input_path: str, output_path: str, 
                   result: Dict) -> bool:
        """
        Aplica OCR usando OCRmyPDF
        
        Args:
            input_path (str): Archivo de entrada
            output_path (str): Archivo de salida
            result (Dict): Diccionario para almacenar resultados
            
        Returns:
            bool: True si el proceso fue exitoso
        """
        try:
            logger.info("Aplicando OCR con OCRmyPDF...")
            
            # Configuración para OCRmyPDF
            ocr_config = {
                'language': self.language,
                'deskew': False,          # Deshabilitar corrección de inclinación
                'clean': False,           # Deshabilitar limpieza (requiere unpaper)
                'optimize': 1,            # Nivel de optimización
                'pdf_renderer': 'hocr',   # Mejor calidad de texto
                'progress_bar': False,    # Deshabilitamos para manejar nuestro propio progreso
                'force_ocr': True,        # Forzar OCR en todas las páginas
                'redo_ocr': False,        # No rehacer OCR en texto existente
                'skip_text': False        # No saltar páginas con texto
            }
            # Crear barra de progreso
            with tqdm(desc="Procesando OCR", unit="página") as pbar:
                # Función callback para progreso
                def progress_callback(progress_info):
                    if 'page' in progress_info:
                        pbar.update(1)
                        result['pages_processed'] = progress_info['page']
                
                # Ejecutar OCRmyPDF
                ocrmypdf.ocr(
                    input_file=input_path,
                    output_file=output_path,
                    **ocr_config
                )
            
            logger.info("OCR aplicado exitosamente")
            return True
            
        except ocrmypdf.exceptions.ExitCodeNotOk as e:
            logger.error(f"Error OCRmyPDF: {e}")
            return False
        except Exception as e:
            logger.error(f"Error aplicando OCR: {e}")
            return False
    
    def _copy_existing(self, input_path: str, output_path: str, 
                      result: Dict) -> bool:
        """
        Copia el PDF existente sin cambios (ya tiene texto)
        
        Args:
            input_path (str): Archivo de entrada
            output_path (str): Archivo de salida
            result (Dict): Diccionario para almacenar resultados
            
        Returns:
            bool: True si la copia fue exitosa
        """
        try:
            logger.info("PDF ya contiene texto, copiando sin cambios...")
            
            # Copiar archivo
            shutil.copy2(input_path, output_path)
            
            # Actualizar resultado
            result['pages_processed'] = 'N/A (copia directa)'
            
            logger.info("Archivo copiado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error copiando archivo: {e}")
            return False
    
    def validate_ocr_installation(self) -> Dict[str, Any]:
        """
        Valida que OCRmyPDF y Tesseract estén instalados correctamente
        
        Returns:
            Dict: Estado de la validación
        """
        validation = {
            'ocrmypdf_available': False,
            'tesseract_available': False,
            'language_available': False,
            'all_valid': False,
            'errors': []
        }
        
        try:
            # Verificar OCRmyPDF
            import ocrmypdf
            validation['ocrmypdf_available'] = True
            logger.info("OCRmyPDF disponible")
        except ImportError:
            validation['errors'].append("OCRmyPDF no está instalado")
        
        try:
            # Verificar Tesseract
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                validation['tesseract_available'] = True
                logger.info(f"Tesseract disponible: {result.stdout.split()[1]}")
            else:
                validation['errors'].append("Tesseract no responde correctamente")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            validation['errors'].append("Tesseract no encontrado en PATH")
        
        try:
            # Verificar idioma español
            result = subprocess.run(['tesseract', '--list-langs'], 
                                  capture_output=True, text=True, timeout=10)
            if self.language in result.stdout:
                validation['language_available'] = True
                logger.info(f"Idioma {self.language} disponible")
            else:
                validation['errors'].append(f"Idioma {self.language} no disponible")
        except Exception:
            validation['errors'].append("No se pudo verificar idiomas disponibles")
        
        # Verificar estado general
        validation['all_valid'] = (
            validation['ocrmypdf_available'] and 
            validation['tesseract_available'] and 
            validation['language_available']
        )
        
        return validation
    
    def get_supported_languages(self) -> list:
        """
        Obtiene lista de idiomas soportados por Tesseract
        
        Returns:
            list: Lista de códigos de idioma
        """
        try:
            result = subprocess.run(['tesseract', '--list-langs'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                languages = result.stdout.strip().split('\n')[1:]  # Skip header
                return languages
        except Exception as e:
            logger.error(f"Error obteniendo idiomas: {e}")
        
        return []