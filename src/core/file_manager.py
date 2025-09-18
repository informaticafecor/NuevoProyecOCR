"""
Gestor de archivos PDF - Maneja operaciones de archivos y directorios
Autor: PDF Processor Team
"""

import os
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FileManager:
    """Gestor de archivos para el procesador PDF"""
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        Inicializa el gestor de archivos
        
        Args:
            input_dir (str): Directorio de archivos de entrada
            output_dir (str): Directorio de archivos de salida
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.setup_directories()
    
    def setup_directories(self) -> None:
        """Crea los directorios necesarios si no existen"""
        try:
            self.input_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directorios configurados: {self.input_dir}, {self.output_dir}")
        except Exception as e:
            logger.error(f"Error creando directorios: {e}")
            raise
    
    def get_pdf_files(self, directory: Optional[str] = None) -> List[Path]:
        """
        Obtiene lista de archivos PDF en un directorio
        
        Args:
            directory (str, optional): Directorio a escanear. Por defecto input_dir
            
        Returns:
            List[Path]: Lista de archivos PDF encontrados
        """
        try:
            scan_dir = Path(directory) if directory else self.input_dir
            
            if not scan_dir.exists():
                logger.warning(f"Directorio no existe: {scan_dir}")
                return []
            
            pdf_files = list(scan_dir.glob("*.pdf"))
            pdf_files.extend(scan_dir.glob("*.PDF"))  # Incluir mayúsculas
            
            logger.info(f"Encontrados {len(pdf_files)} archivos PDF en {scan_dir}")
            return sorted(pdf_files)
            
        except Exception as e:
            logger.error(f"Error escaneando directorio {scan_dir}: {e}")
            return []
    
    def generate_output_filename(self, input_path: str, suffix: str = "_ocr") -> str:
        """
        Genera nombre de archivo de salida basado en el archivo de entrada
        
        Args:
            input_path (str): Ruta del archivo de entrada
            suffix (str): Sufijo a añadir al nombre
            
        Returns:
            str: Ruta completa del archivo de salida
        """
        try:
            input_file = Path(input_path)
            base_name = input_file.stem
            
            # Evitar duplicar el sufijo
            if not base_name.endswith(suffix):
                base_name += suffix
            
            output_filename = f"{base_name}.pdf"
            output_path = self.output_dir / output_filename
            
            # Si existe, añadir timestamp
            if output_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name_with_timestamp = f"{base_name}_{timestamp}"
                output_filename = f"{base_name_with_timestamp}.pdf"
                output_path = self.output_dir / output_filename
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error generando nombre de salida: {e}")
            # Fallback
            return str(self.output_dir / f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    def backup_file(self, file_path: str, backup_suffix: str = "_backup") -> Optional[str]:
        """
        Crea una copia de respaldo de un archivo
        
        Args:
            file_path (str): Ruta del archivo a respaldar
            backup_suffix (str): Sufijo para el archivo de respaldo
            
        Returns:
            str: Ruta del archivo de respaldo creado
        """
        try:
            original_file = Path(file_path)
            if not original_file.exists():
                logger.warning(f"Archivo no existe para respaldo: {file_path}")
                return None
            
            backup_name = f"{original_file.stem}{backup_suffix}{original_file.suffix}"
            backup_path = original_file.parent / backup_name
            
            # Si ya existe un backup, añadir timestamp
            if backup_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{original_file.stem}{backup_suffix}_{timestamp}{original_file.suffix}"
                backup_path = original_file.parent / backup_name
            
            shutil.copy2(str(original_file), str(backup_path))
            logger.info(f"Respaldo creado: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creando respaldo: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un archivo
        
        Args:
            file_path (str): Ruta del archivo
            
        Returns:
            Dict: Información del archivo
        """
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return {'exists': False, 'error': 'File not found'}
            
            stat = file_obj.stat()
            
            info = {
                'exists': True,
                'name': file_obj.name,
                'path': str(file_obj),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'is_readable': os.access(str(file_obj), os.R_OK),
                'is_writable': os.access(str(file_obj), os.W_OK),
                'extension': file_obj.suffix.lower()
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error obteniendo info del archivo: {e}")
            return {'exists': False, 'error': str(e)}
    
    def clean_output_directory(self, older_than_days: int = 30) -> Dict[str, Any]:
        """
        Limpia archivos antiguos del directorio de salida
        
        Args:
            older_than_days (int): Días de antigüedad para considerar archivos viejos
            
        Returns:
            Dict: Resultado de la limpieza
        """
        try:
            if not self.output_dir.exists():
                return {'cleaned_files': 0, 'freed_space_mb': 0}
            
            cutoff_timestamp = datetime.now().timestamp() - (older_than_days * 24 * 3600)
            cleaned_files = 0
            freed_space = 0
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == '.pdf':
                    if file_path.stat().st_mtime < cutoff_timestamp:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        cleaned_files += 1
                        freed_space += file_size
                        logger.debug(f"Eliminado archivo antiguo: {file_path.name}")
            
            freed_space_mb = round(freed_space / (1024 * 1024), 2)
            logger.info(f"Limpieza completada: {cleaned_files} archivos, {freed_space_mb} MB liberados")
            
            return {
                'cleaned_files': cleaned_files,
                'freed_space_mb': freed_space_mb,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error en limpieza: {e}")
            return {
                'cleaned_files': 0,
                'freed_space_mb': 0,
                'success': False,
                'error': str(e)
            }
    
    def validate_paths(self, input_path: str, output_path: str) -> Tuple[bool, List[str]]:
        """
        Valida rutas de entrada y salida
        
        Args:
            input_path (str): Ruta de archivo de entrada
            output_path (str): Ruta de archivo de salida
            
        Returns:
            Tuple[bool, List[str]]: (válido, lista_de_errores)
        """
        errors = []
        
        try:
            # Validar archivo de entrada
            input_file = Path(input_path)
            if not input_file.exists():
                errors.append(f"Archivo de entrada no existe: {input_path}")
            elif not input_file.is_file():
                errors.append(f"Ruta de entrada no es un archivo: {input_path}")
            elif input_file.suffix.lower() != '.pdf':
                errors.append(f"Archivo de entrada no es PDF: {input_path}")
            elif not os.access(str(input_file), os.R_OK):
                errors.append(f"Sin permisos de lectura: {input_path}")
            
            # Validar ruta de salida
            output_file = Path(output_path)
            output_dir = output_file.parent
            
            # Crear directorio de salida si no existe
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"No se puede crear directorio de salida: {e}")
            
            # Verificar permisos de escritura
            if output_file.exists() and not os.access(str(output_file), os.W_OK):
                errors.append(f"Sin permisos de escritura en archivo existente: {output_path}")
            elif not os.access(str(output_dir), os.W_OK):
                errors.append(f"Sin permisos de escritura en directorio: {output_dir}")
            
            # Verificar que no sea el mismo archivo
            if input_file.resolve() == output_file.resolve():
                errors.append("Archivo de entrada y salida no pueden ser el mismo")
            
        except Exception as e:
            errors.append(f"Error validando rutas: {e}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_directory_stats(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un directorio
        
        Args:
            directory (str, optional): Directorio a analizar
            
        Returns:
            Dict: Estadísticas del directorio
        """
        try:
            target_dir = Path(directory) if directory else self.input_dir
            
            if not target_dir.exists():
                return {'exists': False, 'error': 'Directory not found'}
            
            pdf_files = self.get_pdf_files(str(target_dir))
            total_size = sum(f.stat().st_size for f in pdf_files)
            
            stats = {
                'exists': True,
                'path': str(target_dir),
                'total_files': len(pdf_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'largest_file': None,
                'smallest_file': None,
                'average_size_mb': 0
            }
            
            if pdf_files:
                file_sizes = [(f, f.stat().st_size) for f in pdf_files]
                largest = max(file_sizes, key=lambda x: x[1])
                smallest = min(file_sizes, key=lambda x: x[1])
                
                stats['largest_file'] = {
                    'name': largest[0].name,
                    'size_mb': round(largest[1] / (1024 * 1024), 2)
                }
                stats['smallest_file'] = {
                    'name': smallest[0].name,
                    'size_mb': round(smallest[1] / (1024 * 1024), 2)
                }
                stats['average_size_mb'] = round(stats['total_size_mb'] / len(pdf_files), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {'exists': False, 'error': str(e)}