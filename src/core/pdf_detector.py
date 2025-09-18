"""
Detector de tipo de PDF - Determina si contiene texto o es escaneado
Autor: PDF Processor Team
"""

import logging
from pathlib import Path
from typing import Tuple, Dict, Any
import PyPDF2
import fitz  # pymupdf - más robusto que PyPDF2

logger = logging.getLogger(__name__)

class PDFDetector:
    """Detecta si un PDF contiene texto embebido o es una imagen escaneada"""
    
    def __init__(self):
        self.min_text_threshold = 50  # Mínimo de caracteres para considerar que tiene texto
        self.min_text_ratio = 0.1     # Ratio mínimo de texto por página
    
    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analiza un PDF y determina su tipo y características
        
        Args:
            pdf_path (str): Ruta del archivo PDF
            
        Returns:
            Dict: Información detallada del PDF
        """
        try:
            result = {
                'file_path': pdf_path,
                'has_text': False,
                'is_searchable': False,
                'needs_ocr': True,
                'total_pages': 0,
                'pages_with_text': 0,
                'total_characters': 0,
                'average_chars_per_page': 0,
                'analysis_method': '',
                'error': None
            }
            
            # Intentar con PyMuPDF primero (más confiable)
            success_pymupdf = self._analyze_with_pymupdf(pdf_path, result)
            
            if not success_pymupdf:
                # Fallback a PyPDF2
                logger.info("Intentando análisis con PyPDF2...")
                success_pypdf2 = self._analyze_with_pypdf2(pdf_path, result)
                
                if not success_pypdf2:
                    result['error'] = "No se pudo analizar el PDF con ningún método"
                    return result
            
            # Determinar si necesita OCR
            self._determine_ocr_need(result)
            
            logger.info(f"PDF analizado: {result['total_pages']} páginas, "
                       f"{result['pages_with_text']} con texto, "
                       f"OCR necesario: {result['needs_ocr']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando PDF {pdf_path}: {e}")
            return {
                'file_path': pdf_path,
                'has_text': False,
                'is_searchable': False,
                'needs_ocr': True,
                'error': str(e)
            }
    
    def _analyze_with_pymupdf(self, pdf_path: str, result: Dict) -> bool:
        """
        Analiza PDF usando PyMuPDF (más robusto)
        
        Args:
            pdf_path (str): Ruta del PDF
            result (Dict): Diccionario para almacenar resultados
            
        Returns:
            bool: True si el análisis fue exitoso
        """
        try:
            doc = fitz.open(pdf_path)
            result['analysis_method'] = 'PyMuPDF'
            result['total_pages'] = len(doc)
            
            total_chars = 0
            pages_with_text = 0
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                # Limpiar texto (eliminar espacios extra, saltos de línea)
                clean_text = ' '.join(text.split())
                char_count = len(clean_text)
                
                if char_count > self.min_text_threshold:
                    pages_with_text += 1
                
                total_chars += char_count
                
                # Log de progreso cada 10 páginas
                if (page_num + 1) % 10 == 0:
                    logger.debug(f"Analizadas {page_num + 1} páginas...")
            
            doc.close()
            
            result['total_characters'] = total_chars
            result['pages_with_text'] = pages_with_text
            result['average_chars_per_page'] = total_chars / result['total_pages'] if result['total_pages'] > 0 else 0
            
            return True
            
        except Exception as e:
            logger.warning(f"Error con PyMuPDF: {e}")
            return False
    
    def _analyze_with_pypdf2(self, pdf_path: str, result: Dict) -> bool:
        """
        Analiza PDF usando PyPDF2 (fallback)
        
        Args:
            pdf_path (str): Ruta del PDF
            result (Dict): Diccionario para almacenar resultados
            
        Returns:
            bool: True si el análisis fue exitoso
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                result['analysis_method'] = 'PyPDF2'
                result['total_pages'] = len(reader.pages)
                
                total_chars = 0
                pages_with_text = 0
                
                for page_num, page in enumerate(reader.pages):
                    try:
                        text = page.extract_text()
                        clean_text = ' '.join(text.split())
                        char_count = len(clean_text)
                        
                        if char_count > self.min_text_threshold:
                            pages_with_text += 1
                        
                        total_chars += char_count
                        
                    except Exception as e:
                        logger.warning(f"Error extrayendo texto de página {page_num}: {e}")
                        continue
                
                result['total_characters'] = total_chars
                result['pages_with_text'] = pages_with_text
                result['average_chars_per_page'] = total_chars / result['total_pages'] if result['total_pages'] > 0 else 0
                
                return True
                
        except Exception as e:
            logger.warning(f"Error con PyPDF2: {e}")
            return False
    
    def _determine_ocr_need(self, result: Dict) -> None:
        """
        Determina si el PDF necesita OCR basado en el análisis
        
        Args:
            result (Dict): Diccionario con resultados del análisis
        """
        # Criterios para determinar si tiene texto útil
        has_sufficient_text = (
            result['total_characters'] > self.min_text_threshold and
            result['average_chars_per_page'] > self.min_text_threshold and
            result['pages_with_text'] / result['total_pages'] >= self.min_text_ratio
        )
        
        result['has_text'] = has_sufficient_text
        result['is_searchable'] = has_sufficient_text
        result['needs_ocr'] = not has_sufficient_text
        
        # Log del análisis
        if result['needs_ocr']:
            logger.info(f"PDF requiere OCR - Texto insuficiente: "
                       f"{result['total_characters']} caracteres total, "
                       f"{result['average_chars_per_page']:.1f} por página")
        else:
            logger.info(f"PDF ya tiene texto buscable - "
                       f"{result['pages_with_text']}/{result['total_pages']} páginas con texto")
    
    def is_pdf_searchable(self, pdf_path: str) -> bool:
        """
        Método rápido para determinar si un PDF es buscable
        
        Args:
            pdf_path (str): Ruta del archivo PDF
            
        Returns:
            bool: True si el PDF ya es buscable
        """
        result = self.analyze_pdf(pdf_path)
        return result.get('is_searchable', False)