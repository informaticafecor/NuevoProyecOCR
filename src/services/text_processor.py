"""
Procesador de texto - Extrae texto de PDFs
Autor: PDF Processor Team
"""

import logging
import fitz  # PyMuPDF
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
sys.path.append(str(Path(__file__).parent.parent))
from utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

class TextProcessor:
    """Extrae y procesa texto de archivos PDF"""
    
    def __init__(self):
        """Inicializa el procesador de texto"""
        self.text_cleaner = TextCleaner()
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Extrae texto completo de un PDF
        
        Args:
            pdf_path (str): Ruta del archivo PDF
            
        Returns:
            Tuple[bool, str, Dict]: (éxito, texto_extraído, metadata)
        """
        try:
            if not Path(pdf_path).exists():
                return False, "", {"error": "Archivo no encontrado"}
            
            logger.info(f"Extrayendo texto de: {pdf_path}")
            
            # Abrir PDF con PyMuPDF
            doc = fitz.open(pdf_path)
            
            # Extraer texto de todas las páginas
            full_text = ""
            page_texts = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                
                if page_text.strip():
                    page_texts.append(page_text)
                    full_text += page_text + "\n\n"
                
                # Log progreso cada 10 páginas
                if (page_num + 1) % 10 == 0:
                    logger.debug(f"Procesadas {page_num + 1} páginas...")
            
            doc.close()
            
            # Limpiar texto extraído
            cleaned_text = self.text_cleaner.clean_text(full_text)
            
            # Obtener metadata
            metadata = self._get_pdf_metadata(pdf_path, len(doc), page_texts)
            metadata.update(self.text_cleaner.extract_metadata(cleaned_text))
            
            if not cleaned_text.strip():
                return False, "", {"error": "No se pudo extraer texto del PDF"}
            
            logger.info(f"Texto extraído exitosamente: {len(cleaned_text)} caracteres")
            return True, cleaned_text, metadata
            
        except Exception as e:
            logger.error(f"Error extrayendo texto: {e}")
            return False, "", {"error": str(e)}
    
    def _get_pdf_metadata(self, pdf_path: str, total_pages: int, page_texts: list) -> Dict[str, Any]:
        """
        Obtiene metadata del PDF
        
        Args:
            pdf_path (str): Ruta del PDF
            total_pages (int): Total de páginas
            page_texts (list): Textos por página
            
        Returns:
            Dict: Metadata del PDF
        """
        try:
            file_path = Path(pdf_path)
            file_stats = file_path.stat()
            
            # Calcular páginas con texto
            pages_with_text = len([text for text in page_texts if text.strip()])
            
            metadata = {
                'file_name': file_path.name,
                'file_size_mb': round(file_stats.st_size / (1024 * 1024), 2),
                'total_pages': total_pages,
                'pages_with_text': pages_with_text,
                'text_coverage': round((pages_with_text / total_pages) * 100, 1) if total_pages > 0 else 0,
                'extraction_method': 'PyMuPDF'
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error obteniendo metadata: {e}")
            return {'error': str(e)}
    
    def prepare_text_for_summary(self, text: str, chunk_size: int = 2500) -> Tuple[list, Dict[str, Any]]:
        """
        Prepara texto para resumen dividiendo en chunks
        
        Args:
            text (str): Texto completo
            chunk_size (int): Tamaño de chunks
            
        Returns:
            Tuple[list, Dict]: (chunks, info_procesamiento)
        """
        try:
            if not text.strip():
                return [], {"error": "Texto vacío"}
            
            # Dividir en chunks
            chunks = self.text_cleaner.split_into_chunks(text, chunk_size)
            
            # Información del procesamiento
            process_info = {
                'total_chunks': len(chunks),
                'chunk_size': chunk_size,
                'chunks_info': []
            }
            
            # Información detallada de cada chunk
            for i, chunk in enumerate(chunks):
                chunk_info = {
                    'chunk_number': i + 1,
                    'characters': len(chunk),
                    'words': len(chunk.split()),
                    'preview': chunk[:100] + "..." if len(chunk) > 100 else chunk
                }
                process_info['chunks_info'].append(chunk_info)
            
            logger.info(f"Texto preparado en {len(chunks)} chunks para resumen")
            return chunks, process_info
            
        except Exception as e:
            logger.error(f"Error preparando texto: {e}")
            return [], {"error": str(e)}
    
    def validate_pdf_for_text_extraction(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Valida si un PDF es apto para extracción de texto
        
        Args:
            pdf_path (str): Ruta del PDF
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje)
        """
        try:
            if not Path(pdf_path).exists():
                return False, "Archivo no encontrado"
            
            if not pdf_path.lower().endswith('.pdf'):
                return False, "El archivo no es un PDF"
            
            # Intentar abrir con PyMuPDF
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                doc.close()
                return False, "PDF vacío o corrupto"
            
            # Verificar si tiene texto en las primeras páginas
            has_text = False
            for page_num in range(min(3, len(doc))):  # Verificar máximo 3 páginas
                page = doc.load_page(page_num)
                if page.get_text().strip():
                    has_text = True
                    break
            
            doc.close()
            
            if not has_text:
                return False, "PDF no contiene texto extraíble (posiblemente escaneado)"
            
            return True, "PDF válido para extracción de texto"
            
        except Exception as e:
            logger.error(f"Error validando PDF: {e}")
            return False, f"Error validando PDF: {str(e)}"