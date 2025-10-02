"""
Servicio de resúmenes - Orquestador principal para generar resúmenes de PDFs
Autor: PDF Processor Team
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
sys.path.append(str(Path(__file__).parent.parent))
from services.text_processor import TextProcessor
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class SummaryService:
    """Servicio principal para generar resúmenes de documentos PDF"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "mistral:7b"):
        """
        Inicializa el servicio de resúmenes
        
        Args:
            ollama_host (str): URL del servidor Ollama
            model (str): Modelo de IA a usar
        """
        self.text_processor = TextProcessor()
        self.ai_service = AIService(ollama_host, model)
        self.chunk_size = 2500  # Tamaño óptimo para Mistral
    
    def create_summary_from_pdf(self, pdf_path: str, output_dir: str = "output") -> Dict[str, Any]:
        """
        Genera resumen completo de un PDF
        
        Args:
            pdf_path (str): Ruta del archivo PDF
            output_dir (str): Directorio para guardar resultados
            
        Returns:
            Dict: Resultado completo del proceso
        """
        result = {
            'success': False,
            'pdf_file': pdf_path,
            'summary_file': None,
            'metadata_file': None,
            'final_summary': None,
            'document_metadata': {},
            'processing_stats': {},
            'errors': [],
            'processing_time': 0
        }
        
        try:
            import time
            start_time = time.time()
            
            logger.info(f"Iniciando generación de resumen para: {pdf_path}")
            
            # 1. Validar PDF
            valid, validation_message = self.text_processor.validate_pdf_for_text_extraction(pdf_path)
            if not valid:
                result['errors'].append(f"PDF no válido: {validation_message}")
                return result
            
            # 2. Extraer texto del PDF
            extraction_success, full_text, pdf_metadata = self.text_processor.extract_text_from_pdf(pdf_path)
            if not extraction_success:
                result['errors'].append(f"Error extrayendo texto: {pdf_metadata.get('error', 'Error desconocido')}")
                return result
            
            result['document_metadata'] = pdf_metadata
            
            # 3. Preparar texto para resumen
            text_blocks, chunking_info = self.text_processor.prepare_text_for_summary(full_text, self.chunk_size)
            if not text_blocks:
                result['errors'].append("No se pudieron crear bloques de texto")
                return result
            
            # 4. Verificar disponibilidad de IA
            ai_health = self.ai_service.check_availability()
            if not ai_health['available']:
                result['errors'].append(f"IA no disponible: {ai_health.get('error', 'Error desconocido')}")
                return result
            
            # 5. Generar resumen usando IA
            summary_result = self.ai_service.generate_complete_summary(text_blocks)
            if not summary_result['success']:
                result['errors'].extend(summary_result['errors'])
                return result
            
            result['final_summary'] = summary_result['final_summary']
            result['processing_stats'] = {
                'total_chunks': len(text_blocks),
                'chunks_processed': summary_result['blocks_processed'],
                'ai_processing_time': summary_result['processing_time'],
                'chunking_info': chunking_info
            }
            
            # 6. Guardar resultados
            save_success, file_paths = self._save_results(pdf_path, result, output_dir)
            if save_success:
                result['summary_file'] = file_paths['summary']
                result['metadata_file'] = file_paths['metadata']
            else:
                result['errors'].append("Error guardando archivos de salida")
            
            result['processing_time'] = round(time.time() - start_time, 2)
            result['success'] = True
            
            logger.info(f"Resumen generado exitosamente en {result['processing_time']}s")
            return result
            
        except Exception as e:
            error_msg = f"Error general generando resumen: {e}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def _save_results(self, pdf_path: str, result: Dict[str, Any], output_dir: str) -> Tuple[bool, Dict[str, str]]:
        """
        Guarda archivos de resumen y metadata
        
        Args:
            pdf_path (str): Ruta del PDF original
            result (Dict): Resultado del procesamiento
            output_dir (str): Directorio de salida
            
        Returns:
            Tuple[bool, Dict[str, str]]: (éxito, rutas_archivos)
        """
        try:
            # Crear directorio de salida
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Generar nombres de archivos
            pdf_name = Path(pdf_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            summary_file = output_path / f"{pdf_name}_resumen_{timestamp}.txt"
            metadata_file = output_path / f"{pdf_name}_metadata_{timestamp}.json"
            
            # Guardar resumen en texto
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"RESUMEN AUTOMÁTICO - {pdf_name}\n")
                f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(result['final_summary'])
                f.write(f"\n\n" + "=" * 60)
                f.write(f"\nTiempo de procesamiento: {result.get('processing_time', 0)}s")
                f.write(f"\nChunks procesados: {result.get('processing_stats', {}).get('chunks_processed', 0)}")
            
            # Guardar metadata en JSON
            metadata = {
                'pdf_file': pdf_path,
                'generated_at': datetime.now().isoformat(),
                'document_metadata': result['document_metadata'],
                'processing_stats': result['processing_stats'],
                'summary_preview': result['final_summary'][:200] + "..." if len(result['final_summary']) > 200 else result['final_summary']
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Archivos guardados: {summary_file.name}, {metadata_file.name}")
            
            return True, {
                'summary': str(summary_file),
                'metadata': str(metadata_file)
            }
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
            return False, {}
    
    def get_summary_preview(self, pdf_path: str, max_chars: int = 500) -> Dict[str, Any]:
        """
        Genera vista previa rápida del documento sin resumen completo
        
        Args:
            pdf_path (str): Ruta del PDF
            max_chars (int): Máximo caracteres para preview
            
        Returns:
            Dict: Vista previa del documento
        """
        try:
            # Extraer texto
            success, text, metadata = self.text_processor.extract_text_from_pdf(pdf_path)
            
            if not success:
                return {'success': False, 'error': 'No se pudo extraer texto'}
            
            # Crear preview
            preview = text[:max_chars] + "..." if len(text) > max_chars else text
            
            return {
                'success': True,
                'preview': preview,
                'metadata': metadata,
                'ready_for_summary': len(text) > 100
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def estimate_processing_time(self, pdf_path: str) -> Dict[str, Any]:
        """
        Estima tiempo de procesamiento para un PDF
        
        Args:
            pdf_path (str): Ruta del PDF
            
        Returns:
            Dict: Estimación de tiempo
        """
        try:
            # Obtener metadata rápida
            success, text, metadata = self.text_processor.extract_text_from_pdf(pdf_path)
            
            if not success:
                return {'success': False, 'error': 'No se pudo analizar el PDF'}
            
            # Estimar basado en longitud
            words = len(text.split())
            estimated_chunks = max(1, len(text) // self.chunk_size)
            
            # Tiempo estimado: ~30 segundos por chunk en Mistral
            estimated_seconds = estimated_chunks * 30
            estimated_minutes = round(estimated_seconds / 60, 1)
            
            return {
                'success': True,
                'estimated_chunks': estimated_chunks,
                'estimated_time_seconds': estimated_seconds,
                'estimated_time_minutes': estimated_minutes,
                'document_words': words,
                'document_pages': metadata.get('estimated_pages', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}