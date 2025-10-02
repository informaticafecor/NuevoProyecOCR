"""
Servicio de IA - Integración con Ollama para resúmenes
Autor: PDF Processor Team
"""

import logging
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class AIService:
    """Servicio para generar resúmenes usando IA local"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434", model: str = "mistral:7b"):
        """
        Inicializa el servicio de IA
        
        Args:
            ollama_host (str): URL del servidor Ollama
            model (str): Modelo a usar
        """
        self.ollama_client = OllamaClient(ollama_host, model)
        
        # Templates de prompts
        self.block_summary_prompt = """Eres un asistente que resume documentos en español.
Tarea: Resume el siguiente texto tomando en cuenta su extensión.
- Si el texto es breve (1-2 páginas), genera un resumen de máximo 2 párrafos.
- Si el texto es mediano (3-10 páginas), genera un resumen de 3 a 5 párrafos o en viñetas claras.
- Si el texto es extenso (+10 páginas), genera un resumen más amplio en viñetas o secciones, pero siempre breve comparado al documento original.
En todos los casos:
- Mantén solo las ideas principales.
- Sé claro, conciso y en español.
- No inventes información.

Texto:
{TEXTO_DEL_BLOQUE}

Resumen:"""

        self.consolidation_prompt = """Eres un asistente que genera resúmenes consolidados en español.
Tarea: Une los siguientes resúmenes parciales en un meta-resumen único.
- No repitas información.
- Mantén un estilo claro y conciso.
- Extensión adaptada al tamaño total del documento original:
    - Documentos breves → 2 párrafos.
    - Documentos medianos → 3 a 5 párrafos o viñetas.
    - Documentos largos → resumen estructurado en secciones o viñetas.
- Destaca hechos, ideas principales y fechas relevantes.
- No inventes contenido adicional.

Resúmenes parciales:
{RESUMENES_BLOQUES}

Meta-resumen consolidado:"""
    
    def check_availability(self) -> Dict[str, Any]:
        """
        Verifica disponibilidad del servicio de IA
        
        Returns:
            Dict: Estado del servicio
        """
        return self.ollama_client.health_check()
    
    def generate_block_summaries(self, text_blocks: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Genera resúmenes para cada bloque de texto
        
        Args:
            text_blocks (List[str]): Lista de bloques de texto
            
        Returns:
            Tuple[bool, List[str], List[str]]: (éxito, resúmenes, errores)
        """
        try:
            if not text_blocks:
                return False, [], ["No hay bloques de texto para procesar"]
            
            summaries = []
            errors = []
            
            logger.info(f"Generando resúmenes para {len(text_blocks)} bloques")
            
            for i, block in enumerate(text_blocks, 1):
                logger.info(f"Procesando bloque {i}/{len(text_blocks)}")
                
                # Generar resumen del bloque
                summary = self.ollama_client.generate_summary(block, self.block_summary_prompt)
                
                if summary:
                    summaries.append(summary)
                    logger.debug(f"Bloque {i} resumido exitosamente")
                else:
                    error_msg = f"Error generando resumen del bloque {i}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    # Continuar con el siguiente bloque
            
            success = len(summaries) > 0
            return success, summaries, errors
            
        except Exception as e:
            logger.error(f"Error en generación de resúmenes por bloques: {e}")
            return False, [], [str(e)]
    
    def generate_consolidated_summary(self, partial_summaries: List[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Genera resumen consolidado final
        
        Args:
            partial_summaries (List[str]): Lista de resúmenes parciales
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (éxito, resumen_final, error)
        """
        try:
            if not partial_summaries:
                return False, None, "No hay resúmenes parciales para consolidar"
            
            if len(partial_summaries) == 1:
                # Si solo hay un resumen, devolverlo directamente
                return True, partial_summaries[0], None
            
            # Unir resúmenes parciales
            combined_summaries = "\n\n".join([f"Resumen {i+1}:\n{summary}" 
                                            for i, summary in enumerate(partial_summaries)])
            
            logger.info("Generando resumen consolidado final")
            
            # Generar meta-resumen
            final_summary = self.ollama_client.generate_summary(
                combined_summaries, 
                self.consolidation_prompt
            )
            
            if final_summary:
                logger.info("Resumen consolidado generado exitosamente")
                return True, final_summary, None
            else:
                error_msg = "Error generando resumen consolidado"
                logger.error(error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error en consolidación: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def generate_complete_summary(self, text_blocks: List[str]) -> Dict[str, Any]:
        """
        Genera resumen completo del documento
        
        Args:
            text_blocks (List[str]): Bloques de texto del documento
            
        Returns:
            Dict: Resultado completo del proceso
        """
        result = {
            'success': False,
            'final_summary': None,
            'partial_summaries': [],
            'blocks_processed': 0,
            'errors': [],
            'processing_time': 0
        }
        
        try:
            import time
            start_time = time.time()
            
            # Verificar disponibilidad
            health = self.check_availability()
            if not health['available']:
                result['errors'].append("Ollama no está disponible")
                return result
            
            # Generar resúmenes por bloques
            success, summaries, errors = self.generate_block_summaries(text_blocks)
            
            result['partial_summaries'] = summaries
            result['blocks_processed'] = len(summaries)
            result['errors'].extend(errors)
            
            if not success or not summaries:
                result['errors'].append("No se pudieron generar resúmenes parciales")
                return result
            
            # Generar resumen consolidado
            consolidation_success, final_summary, consolidation_error = self.generate_consolidated_summary(summaries)
            
            if consolidation_success and final_summary:
                result['success'] = True
                result['final_summary'] = final_summary
            else:
                result['errors'].append(consolidation_error or "Error en consolidación")
            
            result['processing_time'] = round(time.time() - start_time, 2)
            
            return result
            
        except Exception as e:
            result['errors'].append(f"Error general en proceso de resumen: {e}")
            return result