"""
PDF OCR Processor - Programa principal
Detecta y procesa PDFs aplicando OCR cuando es necesario

Uso:
    python src/main.py input/archivo.pdf output/archivo_ocr.pdf
    python src/main.py input/archivo.pdf output/archivo_ocr.pdf --idioma spa --calidad alta

Autor: PDF Processor Team
Versión: 1.0.0
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style

# Agregar el directorio src al path para imports
sys.path.append(str(Path(__file__).parent))

from utils.config import Config
from utils.validators import FileValidator, SystemValidator
from core.pdf_detector import PDFDetector
from core.ocr_processor import OCRProcessor
from core.file_manager import FileManager

# Inicializar colorama para colores en Windows
init(autoreset=True)

def setup_logging(log_level: str = 'INFO') -> None:
    """
    Configura el sistema de logging
    
    Args:
        log_level (str): Nivel de logging
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pdf_processor.log', encoding='utf-8')
        ]
    )

def print_banner():
    """Muestra el banner del programa"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════╗
║                          PDF OCR PROCESSOR v1.0                      ║
║                    Procesamiento automático de PDFs                  ║
╚═══════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)

def print_status(message: str, status: str = 'INFO') -> None:
    """
    Imprime mensajes de estado con colores
    
    Args:
        message (str): Mensaje a mostrar
        status (str): Tipo de mensaje (INFO, SUCCESS, ERROR, WARNING)
    """
    colors = {
        'INFO': Fore.BLUE,
        'SUCCESS': Fore.GREEN,
        'ERROR': Fore.RED,
        'WARNING': Fore.YELLOW
    }
    
    color = colors.get(status.upper(), Fore.WHITE)
    icon = {
        'INFO': 'ℹ',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠'
    }.get(status.upper(), '•')
    
    print(f"{color}{icon} {message}{Style.RESET_ALL}")

def validate_system() -> bool:
    """
    Valida que el sistema esté configurado correctamente
    
    Returns:
        bool: True si el sistema está listo
    """
    print_status("Validando configuración del sistema...", 'INFO')
    
    # Validar Tesseract
    validator = SystemValidator()
    tesseract_valid, tesseract_error = validator.validate_tesseract_installation(Config.TESSERACT_CMD)
    
    if not tesseract_valid:
        print_status(f"Error Tesseract: {tesseract_error}", 'ERROR')
        print_status("Instala Tesseract desde: https://github.com/UB-Mannheim/tesseract/wiki", 'INFO')
        return False
    
    print_status("Tesseract OCR encontrado ✓", 'SUCCESS')
    
    # Validar idioma español
    lang_valid, lang_error = validator.validate_language_support('spa')
    if not lang_valid:
        print_status(f"Error idioma: {lang_error}", 'ERROR')
        return False
    
    print_status("Idioma español disponible ✓", 'SUCCESS')
    
    # Crear directorios necesarios
    try:
        Config.create_directories()
        print_status("Directorios configurados ✓", 'SUCCESS')
    except Exception as e:
        print_status(f"Error creando directorios: {e}", 'ERROR')
        return False
    
    return True

def process_single_pdf(input_path: str, output_path: str, force_ocr: bool = False) -> bool:
    """
    Procesa un único archivo PDF
    
    Args:
        input_path (str): Ruta del PDF de entrada
        output_path (str): Ruta del PDF de salida
        force_ocr (bool): Forzar OCR aunque tenga texto
        
    Returns:
        bool: True si el procesamiento fue exitoso
    """
    try:
        print_status(f"Procesando: {Path(input_path).name}", 'INFO')
        
        # Validar archivos
        file_validator = FileValidator()
        valid_input, input_error = file_validator.validate_pdf_file(input_path)
        
        if not valid_input:
            print_status(f"Error en archivo de entrada: {input_error}", 'ERROR')
            return False
        
        valid_output, output_error = file_validator.validate_output_path(output_path)
        if not valid_output:
            print_status(f"Error en ruta de salida: {output_error}", 'ERROR')
            return False
        
        # Analizar PDF
        print_status("Analizando contenido del PDF...", 'INFO')
        detector = PDFDetector()
        analysis = detector.analyze_pdf(input_path)
        
        if analysis.get('error'):
            print_status(f"Error analizando PDF: {analysis['error']}", 'ERROR')
            return False
        
        # Mostrar información del análisis
        print_status(f"Páginas: {analysis['total_pages']}", 'INFO')
        print_status(f"Páginas con texto: {analysis['pages_with_text']}", 'INFO')
        print_status(f"Caracteres totales: {analysis['total_characters']}", 'INFO')
        
        if analysis['needs_ocr']:
            print_status("PDF requiere OCR - Iniciando procesamiento...", 'WARNING')
        else:
            print_status("PDF ya contiene texto buscable", 'SUCCESS')
            if not force_ocr:
                print_status("Copiando archivo sin cambios...", 'INFO')
        
        # Procesar con OCR
        ocr_processor = OCRProcessor(Config.OCRMYPDF_CONFIG)
        result = ocr_processor.process_pdf(input_path, output_path, force_ocr)
        
        if result['success']:
            print_status(f"✅ Procesamiento completado: {Path(output_path).name}", 'SUCCESS')
            
            # Mostrar estadísticas
            size_before = result['file_size_before'] / (1024 * 1024)
            size_after = result['file_size_after'] / (1024 * 1024)
            print_status(f"Tamaño antes: {size_before:.1f} MB", 'INFO')
            print_status(f"Tamaño después: {size_after:.1f} MB", 'INFO')
            print_status(f"Método: {result['processing_method']}", 'INFO')
            
            return True
        else:
            print_status(f"Error en procesamiento: {result.get('error', 'Error desconocido')}", 'ERROR')
            return False
            
    except Exception as e:
        print_status(f"Error procesando PDF: {e}", 'ERROR')
        return False

def main():
    """Función principal del programa"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Procesador PDF con OCR automático',
        epilog='Ejemplo: python src/main.py input/documento.pdf output/documento_ocr.pdf'
    )
    
    parser.add_argument('input_file', 
                       help='Archivo PDF de entrada')
    parser.add_argument('output_file', 
                       help='Archivo PDF de salida')
    parser.add_argument('--idioma', '-l', 
                       default='spa', 
                       help='Idioma para OCR (por defecto: spa)')
    parser.add_argument('--forzar-ocr', '-f', 
                       action='store_true',
                       help='Forzar OCR incluso si el PDF ya tiene texto')
    parser.add_argument('--log-level', 
                       default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Nivel de logging')
    parser.add_argument('--version', '-v',
                       action='version',
                       version='PDF OCR Processor 1.0.0')
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Mostrar banner
    print_banner()
    
    print_status(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'INFO')
    
    try:
        # Validar sistema
        if not validate_system():
            print_status("Sistema no configurado correctamente. Abortando.", 'ERROR')
            sys.exit(1)
        
        # Actualizar configuración con argumentos
        Config.OCRMYPDF_CONFIG['language'] = args.idioma
        
        # Procesar archivo
        success = process_single_pdf(
            args.input_file, 
            args.output_file, 
            args.forzar_ocr
        )
        
        if success:
            print_status("🎉 ¡Procesamiento completado exitosamente!", 'SUCCESS')
            print_status(f"Archivo generado: {args.output_file}", 'INFO')
        else:
            print_status("💥 Error en el procesamiento", 'ERROR')
            sys.exit(1)
            
    except KeyboardInterrupt:
        print_status("Procesamiento interrumpido por el usuario", 'WARNING')
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        print_status(f"Error inesperado: {e}", 'ERROR')
        sys.exit(1)

if __name__ == "__main__":
    main()