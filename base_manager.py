import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger("UFAPE-RAG-API")

class BaseManager:
    def __init__(self):
        self.bases_config = {}
        self.current_base = "default"
        self.load_bases_config()
    
    def load_bases_config(self):
        """Carrega configuração das bases de um arquivo JSON"""
        config_file = "bases_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.bases_config = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar configuração de bases: {e}")
                self.bases_config = {}
        
        # Garantir que a base padrão existe
        if "default" not in self.bases_config:
            self.bases_config["default"] = {
                "documents_dir": os.getenv("DOCUMENTS_DIR", "documents"),
                "faiss_index_path": os.getenv("FAISS_INDEX_PATH", "faiss_index"),
                "output_docs_file": os.getenv("OUTPUT_DOCS_FILE", "processed_docs.pkl"),
                "description": "Base de dados padrão"
            }
            self.save_bases_config()
    
    def save_bases_config(self):
        """Salva configuração das bases em arquivo JSON"""
        try:
            with open("bases_config.json", 'w') as f:
                json.dump(self.bases_config, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de bases: {e}")
    
    def get_base_config(self, base_name: str) -> Optional[Dict]:
        """Retorna configuração de uma base específica"""
        return self.bases_config.get(base_name)
    
    def get_current_base_config(self) -> Dict:
        """Retorna configuração da base atual"""
        return self.bases_config.get(self.current_base, self.bases_config["default"])
    
    def create_base(self, base_config: Dict) -> bool:
        """Cria uma nova base"""
        base_name = base_config["base_name"]
        
        if base_name in self.bases_config:
            return False
        
        # Criar diretórios se não existirem
        os.makedirs(base_config["documents_dir"], exist_ok=True)
        os.makedirs(os.path.dirname(base_config["faiss_index_path"]) if os.path.dirname(base_config["faiss_index_path"]) else ".", exist_ok=True)
        
        self.bases_config[base_name] = {
            "documents_dir": base_config["documents_dir"],
            "faiss_index_path": base_config["faiss_index_path"],
            "output_docs_file": base_config["output_docs_file"],
            "description": base_config.get("description", "")
        }
        
        self.save_bases_config()
        return True
    
    def switch_base(self, base_name: str) -> bool:
        """Muda para uma base específica"""
        if base_name not in self.bases_config:
            return False
        
        self.current_base = base_name
        return True
    
    def delete_base(self, base_name: str) -> bool:
        """Remove uma base (apenas configuração, não deleta arquivos)"""
        if base_name == "default":
            return False
        
        if base_name in self.bases_config:
            del self.bases_config[base_name]
            self.save_bases_config()
            
            # Se estava usando a base deletada, voltar para default
            if self.current_base == base_name:
                self.current_base = "default"
                
            return True
        return False

# Instância global do gerenciador de bases
base_manager = BaseManager()