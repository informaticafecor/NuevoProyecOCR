"""
Cliente para conectar con Ollama API local
Autor: PDF Processor Team
"""

import requests
import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

class OllamaClient:
    """Cliente para interactuar con Ollama API"""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "mistral:7b"):
        """
        Inicializa el cliente Ollama
        
        Args:
            host (str): URL del servidor Ollama
            model (str): Nombre del modelo a usar
        """
        self.host = host.rstrip('/')
        self.model = model
        self.timeout = 120  # 2 minutos timeout
    
    def is_available(self) -> bool:
        """
        Verifica si Ollama está disponible
        
        Returns:
            bool: True si está disponible
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama no disponible: {e}")
            return False
    
    def get_models(self) -> list:
        """
        Obtiene lista de modelos disponibles
        
        Returns:
            list: Lista de modelos instalados
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.error(f"Error obteniendo modelos: {e}")
            return []
    
    def generate_summary(self, text: str, prompt_template: str) -> Optional[str]:
        """
        Genera resumen usando Ollama
        
        Args:
            text (str): Texto a resumir
            prompt_template (str): Template del prompt con {TEXTO_DEL_BLOQUE}
            
        Returns:
            str: Resumen generado o None si hay error
        """
        try:
            # Preparar prompt
            full_prompt = prompt_template.format(TEXTO_DEL_BLOQUE=text)
            
            # Preparar request
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Más conservador para resúmenes
                    "top_p": 0.9,
                    "num_predict": 1000  # Máximo tokens para respuesta
                }
            }
            
            logger.info(f"Enviando texto a Ollama ({len(text)} caracteres)")
            start_time = time.time()
            
            # Hacer request
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('response', '').strip()
                
                elapsed_time = time.time() - start_time
                logger.info(f"Resumen generado en {elapsed_time:.2f}s")
                
                return summary
            else:
                logger.error(f"Error Ollama: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Timeout conectando con Ollama")
            return None
        except Exception as e:
            logger.error(f"Error generando resumen: {e}")
            return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica estado de salud de Ollama
        
        Returns:
            Dict: Estado del servicio
        """
        health_status = {
            'available': False,
            'model_loaded': False,
            'models': [],
            'error': None
        }
        
        try:
            # Verificar disponibilidad
            health_status['available'] = self.is_available()
            
            if health_status['available']:
                # Obtener modelos
                models = self.get_models()
                health_status['models'] = models
                health_status['model_loaded'] = self.model in models
                
                if not health_status['model_loaded']:
                    health_status['error'] = f"Modelo {self.model} no encontrado"
            else:
                health_status['error'] = "Ollama no está ejecutándose"
                
        except Exception as e:
            health_status['error'] = str(e)
        
        return health_status