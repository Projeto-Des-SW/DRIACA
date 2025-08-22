import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime
import unicodedata
import re
from dotenv import load_dotenv

load_dotenv()

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCUMENTS_DIR =  os.getenv("DOCUMENTS_DIR")


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres especiais, acentos e espaços do nome do arquivo.
    Substitui espaços por underscores e remove caracteres não-ASCII.
    """
    # Normaliza os caracteres (remove acentos)
    filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove caracteres especiais, mantendo apenas letras, números, pontos e underscores
    filename = re.sub(r'[^\w\.-]', '_', filename)
    
    # Remove múltiplos underscores consecutivos
    filename = re.sub(r'_{2,}', '_', filename)
    
    # Remove underscores no início e no final
    filename = filename.strip('_')
    
    return filename

class FileStorageManager:
    def __init__(self, storage_root: str = DOCUMENTS_DIR):
        """
        Inicializa o gerenciador de armazenamento de arquivos.
        
        Args:
            storage_root (str): Diretório raiz para armazenamento dos documentos
        """
        self.storage_root = Path(storage_root)
        self._setup_storage_directory()
        
    def _setup_storage_directory(self):
        """Cria o diretório de armazenamento se não existir"""
        try:
            self.storage_root.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de armazenamento configurado em: {self.storage_root}")
        except Exception as e:
            logger.error(f"Erro ao configurar diretório de armazenamento: {e}")
            raise

    def _generate_storage_filename(self, original_filename: str) -> str:
        """
        Gera um nome de arquivo para armazenamento com timestamp e nome sanitizado.
        
        Args:
            original_filename (str): Nome original do arquivo
            
        Returns:
            str: Nome gerado no formato: YYYYMMDD_HHMMSS_nomesanitizado.ext
        """
        # Sanitiza o nome do arquivo
        sanitized_name = sanitize_filename(original_filename)
        
        # Separa a extensão do nome do arquivo
        stem = Path(sanitized_name).stem
        ext = Path(sanitized_name).suffix
        
        # Adiciona timestamp para evitar conflitos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{timestamp}_{stem}{ext}"

    def save_file(self, file_path: str, file_content: Optional[bytes] = None) -> dict:
        """
        Salva um arquivo no diretório de armazenamento.
        
        Args:
            file_path (str): Caminho do arquivo a ser salvo (ou nome se file_content for fornecido)
            file_content (Optional[bytes]): Conteúdo binário do arquivo (opcional)
            
        Returns:
            dict: Informações sobre o arquivo salvo ou erro
        """
        try:
            original_filename = Path(file_path).name
            storage_filename = self._generate_storage_filename(original_filename)
            destination_path = self.storage_root / storage_filename
            
            # Se o conteúdo for fornecido (como em uploads HTTP), escreve o conteúdo
            if file_content is not None:
                with open(destination_path, 'wb') as f:
                    f.write(file_content)
            else:
                # Se for um caminho de arquivo local, copia o arquivo
                shutil.copy2(file_path, destination_path)
            
            file_info = {
                "original_filename": original_filename,
                "stored_filename": storage_filename,
                "sanitized_filename": sanitize_filename(original_filename),
                "file_path": str(destination_path),
                "file_size": os.path.getsize(destination_path),
                "status": "success",
                "message": "Arquivo armazenado com sucesso"
            }
            
            logger.info(f"Arquivo salvo: {file_info}")
            return file_info
            
        except Exception as e:
            error_msg = f"Erro ao salvar arquivo {file_path}: {str(e)}"
            logger.error(error_msg)
            return {
                "original_filename": original_filename,
                "status": "error",
                "message": error_msg
            }

    def list_files(self) -> list:
        """Lista todos os arquivos armazenados"""
        files = []
        for item in self.storage_root.iterdir():
            if item.is_file():
                files.append({
                    "filename": item.name,
                    "path": str(item),
                    "size": item.stat().st_size,
                    "last_modified": datetime.fromtimestamp(item.stat().st_mtime)
                })
        return files

    def get_file_path(self, stored_filename: str) -> Optional[str]:
        """Retorna o caminho completo de um arquivo armazenado"""
        file_path = self.storage_root / stored_filename
        return str(file_path) if file_path.exists() else None


# Exemplo de uso
if __name__ == "__main__":
    # Inicializa o gerenciador de arquivos
    storage_manager = FileStorageManager()
    
    # Exemplo 1: Salvar um arquivo local
    try:
        # Substitua pelo caminho do seu arquivo de teste
        test_file = "exemplo.pdf"
        result = storage_manager.save_file(test_file)
        print("Arquivo salvo:", result)
    except Exception as e:
        print(f"Erro no exemplo 1: {e}")
    
    # Exemplo 2: Listar arquivos armazenados
    print("\nArquivos armazenados:")
    for file_info in storage_manager.list_files():
        print(f"- {file_info['filename']} ({file_info['size']} bytes)")