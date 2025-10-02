"""
Limpiador de texto extraído de PDFs
Autor: PDF Processor Team
"""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class TextCleaner:
    """Limpia y procesa texto extraído de PDFs"""
    
    def __init__(self):
        """Inicializa el limpiador de texto"""
        # Patrones regex para limpieza
        self.patterns = {
            'multiple_spaces': re.compile(r'\s+'),
            'multiple_newlines': re.compile(r'\n\s*\n\s*\n'),
            'page_numbers': re.compile(r'^\s*\d+\s*$', re.MULTILINE),
            'headers_footers': re.compile(r'^[-=_]{3,}.*$', re.MULTILINE),
            'bullet_points': re.compile(r'^[\s]*[•\-\*]\s*', re.MULTILINE),
            'special_chars': re.compile(r'[^\w\s\.\,\;\:\!\?\(\)\[\]\-\"\'\n]'),
        }
    
    def clean_text(self, text: str) -> str:
        """
        Limpia texto extraído de PDF
        
        Args:
            text (str): Texto crudo del PDF
            
        Returns:
            str: Texto limpio
        """
        if not text or not text.strip():
            return ""
        
        try:
            # Remover caracteres de control y especiales
            cleaned = text.replace('\x00', '').replace('\ufeff', '')
            
            # Normalizar saltos de línea
            cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
            
            # Remover múltiples saltos de línea
            cleaned = self.patterns['multiple_newlines'].sub('\n\n', cleaned)
            
            # Normalizar espacios
            cleaned = self.patterns['multiple_spaces'].sub(' ', cleaned)
            
            # Remover números de página solitarios
            cleaned = self.patterns['page_numbers'].sub('', cleaned)
            
            # Remover líneas de headers/footers
            cleaned = self.patterns['headers_footers'].sub('', cleaned)
            
            # Limpiar caracteres especiales problemáticos
            cleaned = self.patterns['special_chars'].sub('', cleaned)
            
            # Limpiar espacios al inicio y final
            cleaned = cleaned.strip()
            
            # Verificar que quedó contenido útil
            if len(cleaned) < 10:
                logger.warning("Texto muy corto después de limpieza")
                return text.strip()  # Devolver original si quedó muy poco
            
            logger.debug(f"Texto limpiado: {len(text)} → {len(cleaned)} caracteres")
            return cleaned
            
        except Exception as e:
            logger.error(f"Error limpiando texto: {e}")
            return text.strip()  # Devolver original en caso de error
    
    def split_into_chunks(self, text: str, chunk_size: int = 2500, overlap: int = 200) -> List[str]:
        """
        Divide texto en chunks respetando párrafos
        
        Args:
            text (str): Texto a dividir
            chunk_size (int): Tamaño máximo del chunk
            overlap (int): Solapamiento entre chunks
            
        Returns:
            List[str]: Lista de chunks de texto
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        try:
            # Dividir por párrafos primero
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                # Si el párrafo solo es muy grande, dividirlo
                if len(paragraph) > chunk_size:
                    # Guardar chunk actual si existe
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                    
                    # Dividir párrafo grande por oraciones
                    sentences = re.split(r'[.!?]+\s+', paragraph)
                    for sentence in sentences:
                        if len(current_chunk + sentence) > chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                # Mantener overlap
                                if overlap > 0 and len(sentence) > overlap:
                                    current_chunk = sentence[-overlap:]
                                else:
                                    current_chunk = sentence
                            else:
                                current_chunk = sentence
                        else:
                            current_chunk += " " + sentence if current_chunk else sentence
                
                # Párrafo normal
                elif len(current_chunk + paragraph) <= chunk_size:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph
                
                else:
                    # Guardar chunk actual y empezar nuevo
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph
            
            # Agregar último chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # Filtrar chunks muy pequeños
            chunks = [chunk for chunk in chunks if len(chunk) > 100]
            
            logger.info(f"Texto dividido en {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error dividiendo texto: {e}")
            # Fallback: división simple
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)]
    
    def extract_metadata(self, text: str) -> dict:
        """
        Extrae metadata básica del texto
        
        Args:
            text (str): Texto a analizar
            
        Returns:
            dict: Metadata extraída
        """
        try:
            words = len(text.split())
            chars = len(text)
            paragraphs = len([p for p in text.split('\n\n') if p.strip()])
            
            # Estimación de páginas (aproximadamente 500 palabras por página)
            estimated_pages = max(1, round(words / 500))
            
            # Detectar fechas
            date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b')
            dates = date_pattern.findall(text)
            
            return {
                'characters': chars,
                'words': words,
                'paragraphs': paragraphs,
                'estimated_pages': estimated_pages,
                'dates_found': len(dates),
                'language': 'spanish',  # Asumimos español
                'reading_time_minutes': max(1, round(words / 200))  # 200 palabras por minuto
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo metadata: {e}")
            return {'error': str(e)}