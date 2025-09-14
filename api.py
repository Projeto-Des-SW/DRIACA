import os
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import re
from pydantic import BaseModel

from fastapi import (
    FastAPI,
    Depends,
    File,
    HTTPException,
    Request,
    status,
    UploadFile,
)
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import shutil

# Local application imports
from RAG import rag_chain, reset_conversation_history, get_current_base, switch_base_rag
from store_manager import FileStorageManager
from load_docs import (
    load_all_files_from_directory,
    preprocess_text,
    rebuild_pdf_from_text,
    DoclingLoader,
    ExportType,
    Document
)

from create_vectorstore import create_vectorstore

# --- Modelo para atualização do .env ---
class EnvUpdateRequest(BaseModel):
    GROQ_API_KEY: Optional[str] = None
    TOP_K: Optional[str] = None
    EMBED_MODEL_ID: Optional[str] = None
    GEN_MODEL_ID: Optional[str] = None

# --- Modelo para gerenciamento de bases ---
class BaseConfig(BaseModel):
    base_name: str
    documents_dir: str
    faiss_index_path: str
    output_docs_file: str
    description: Optional[str] = None

class SwitchBaseRequest(BaseModel):
    base_name: str

# --- Configuração da API ---
app = FastAPI(
    title="API de Consulta Acadêmica UFAPE",
    description="API para consulta de documentos oficiais da UFAPE usando RAG com múltiplas bases",
    version="1.0.0"
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuração de Segurança ---
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Configurações padrão (serão substituídas pela base ativa)
DEFAULT_DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "documents")
DEFAULT_FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")
DEFAULT_OUTPUT_DOCS_FILE = os.getenv("OUTPUT_DOCS_FILE", "processed_docs.pkl")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 
INPUT_DOCS_FILE = os.getenv("INPUT_DOCS_FILE", "processed_docs.pkl")

VALID_API_KEYS = {
    os.getenv("API_KEY", "default-secret-key"): "client-1"
}

async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida ou não fornecida"
        )
    return api_key

# --- Configuração de Logs ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("UFAPE-RAG-API")

# --- Gerenciador de Bases ---
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
                import json
                with open(config_file, 'r') as f:
                    self.bases_config = json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar configuração de bases: {e}")
                self.bases_config = {}
        
        # Garantir que a base padrão existe
        if "default" not in self.bases_config:
            self.bases_config["default"] = {
                "documents_dir": DEFAULT_DOCUMENTS_DIR,
                "faiss_index_path": DEFAULT_FAISS_INDEX_PATH,
                "output_docs_file": DEFAULT_OUTPUT_DOCS_FILE,
                "description": "Base de dados padrão"
            }
            self.save_bases_config()
    
    def save_bases_config(self):
        """Salva configuração das bases em arquivo JSON"""
        try:
            import json
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
    
    def create_base(self, base_config: BaseConfig) -> bool:
        """Cria uma nova base"""
        if base_config.base_name in self.bases_config:
            return False
        
        # Criar diretórios se não existirem
        os.makedirs(base_config.documents_dir, exist_ok=True)
        os.makedirs(os.path.dirname(base_config.faiss_index_path) if os.path.dirname(base_config.faiss_index_path) else ".", exist_ok=True)
        
        self.bases_config[base_config.base_name] = {
            "documents_dir": base_config.documents_dir,
            "faiss_index_path": base_config.faiss_index_path,
            "output_docs_file": base_config.output_docs_file,
            "description": base_config.description
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
            return True
        return False

# Inicializar gerenciador de bases
base_manager = BaseManager()

# --- Funções auxiliares para obter configurações atuais ---
def get_current_documents_dir():
    return base_manager.get_current_base_config()["documents_dir"]

def get_current_faiss_index_path():
    return base_manager.get_current_base_config()["faiss_index_path"]

def get_current_output_docs_file():
    return base_manager.get_current_base_config()["output_docs_file"]

# --- Modelos Pydantic ---
class DocumentMetadata(BaseModel):
    source: str

class DocumentResponse(BaseModel):
    id: str
    page_content: str
    metadata: DocumentMetadata

class QueryInput(BaseModel):
    text: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class QueryOutput(BaseModel):
    input: str
    transformed_query: str
    resposta: str
    contexto: List[DocumentResponse]
    timestamp: str
    model_used: str
    base_used: str

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    current_base: str

# --- Middleware de Log ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    
    logger.info(
        f"Method={request.method} Path={request.url.path} "
        f"Status={response.status_code} "
        f"ProcessTime={process_time:.2f}ms"
    )
    
    return response

# --- Função Auxiliar ---
def convert_documents_to_response(docs):
    return [
        {
            "id": getattr(doc, 'id', ''),
            "page_content": getattr(doc, 'page_content', ''),
            "metadata": {
                "source": getattr(doc, 'metadata', {}).get('source', '')
            }
        }
        for doc in docs
    ]

# --- Endpoints ---
@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "current_base": base_manager.current_base
    }

@app.post("/query", response_model=QueryOutput)
async def process_query(query: QueryInput, api_key: str = Depends(get_api_key)):
    try:
        logger.info(f"Nova consulta - User: {query.user_id} - Session: {query.session_id} - Base: {base_manager.current_base}")
        
        result = rag_chain(query.text)
        
        response = QueryOutput(
            input=result["input"],
            transformed_query=result["transformed_query"],
            resposta=result["resposta"],
            contexto=convert_documents_to_response(result["contexto"]),
            timestamp=datetime.now().isoformat(),
            model_used=os.getenv("GEN_MODEL_ID", "unknown"),
            base_used=base_manager.current_base
        )
        
        logger.info(f"Consulta processada - Input: {query.text[:50]}... - Base: {base_manager.current_base}")
        return jsonable_encoder(response)
        
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar a consulta: {str(e)}"
        )

@app.post("/reset-conversation")
async def reset_conversation(api_key: str = Depends(get_api_key)):
    try:
        reset_conversation_history()
        logger.info("Histórico da conversação resetado")
        return {"status": "success", "message": "Histórico resetado"}
    except Exception as e:
        logger.error(f"Erro ao resetar histórico: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao resetar histórico: {str(e)}"
        )

# ---- file manager -----
@app.post("/api/documents/")
async def upload_document(file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    try:
        documents_dir = get_current_documents_dir()
        storage_manager = FileStorageManager(storage_root=documents_dir)
        
        file_content = await file.read()
        result = storage_manager.save_file(file.filename, file_content)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/")
async def list_documents(api_key: str = Depends(get_api_key)):
    documents_dir = get_current_documents_dir()
    storage_manager = FileStorageManager(storage_root=documents_dir)
    return storage_manager.list_files()

@app.delete("/api/documents/{filename}")
async def delete_document(filename: str, api_key: str = Depends(get_api_key)):
    """
    Deleta um documento específico do sistema de arquivos da base atual.
    """
    try:
        documents_dir = get_current_documents_dir()
        storage_manager = FileStorageManager(storage_root=documents_dir)
        
        # Verificar se o arquivo existe
        file_path = storage_manager.get_file_path(filename)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo não encontrado"
            )
        
        # Deletar o arquivo
        os.remove(file_path)
        
        logger.info(f"Documento deletado: {filename} da base {base_manager.current_base}")
        
        return {
            "status": "success",
            "message": f"Documento '{filename}' deletado com sucesso",
            "deleted_file": filename,
            "base": base_manager.current_base
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar documento {filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar documento: {str(e)}"
        )

@app.get("/api/documents/{filename}")
async def get_document(filename: str, api_key: str = Depends(get_api_key)):
    documents_dir = get_current_documents_dir()
    storage_manager = FileStorageManager(storage_root=documents_dir)
    file_path = storage_manager.get_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path)

@app.post("/process/", status_code=status.HTTP_202_ACCEPTED)
async def process_documents(reprocess: bool = False, api_key: str = Depends(get_api_key)):
    """
    Endpoint para processar todos os documentos no diretório da base atual.
    """
    try:
        start_time = datetime.now()
        documents_dir = get_current_documents_dir()
        output_docs_file = get_current_output_docs_file()
        
        file_paths = load_all_files_from_directory(documents_dir)
        if not file_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum arquivo encontrado no diretório {documents_dir}"
            )
        
        all_docs = []
        failed_files = []

        for file_path in file_paths:
            file_name = Path(file_path).name
            
            # Pular arquivos já reconstruídos, a menos que reprocess=True
            if "_REBUILT_FROM_" in file_name and not reprocess:
                continue
                
            try:
                loader = DoclingLoader(file_path=file_path, export_type=ExportType.MARKDOWN)
                docs_from_file = loader.load()
                all_docs.extend(docs_from_file)
                
            except Exception as e:
                # Tentar reconstruir o PDF
                base_name, ext = os.path.splitext(file_path)
                rebuilt_file_path = f"{base_name}_REBUILT_FROM_TEXT{ext}"
                
                if rebuild_pdf_from_text(file_path, rebuilt_file_path):
                    try:
                        loader = DoclingLoader(file_path=rebuilt_file_path, export_type=ExportType.MARKDOWN)
                        docs_from_file = loader.load()
                        all_docs.extend(docs_from_file)
                    except Exception as e2:
                        failed_files.append(file_name)
                else:
                    failed_files.append(file_name)
        
        # Pré-processamento
        processed_docs = []
        for doc in all_docs:
            cleaned_content = preprocess_text(doc.page_content)
            if cleaned_content:
                processed_docs.append(Document(
                    page_content=cleaned_content,
                    metadata=doc.metadata
                ))
        
        # Salvar documentos processados
        with open(output_docs_file, "wb") as f:
            pickle.dump(processed_docs, f)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "completed",
            "processed_documents": len(processed_docs),
            "failed_documents": len(failed_files),
            "failed_files": failed_files,
            "processing_time_seconds": processing_time,
            "output_file": output_docs_file,
            "base": base_manager.current_base
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante o processamento: {str(e)}"
        )

@app.get("/processed-documents/", response_model=List[dict])
async def get_processed_documents(api_key: str = Depends(get_api_key)):
    """
    Retorna a lista de documentos processados da base atual.
    """
    try:
        output_docs_file = get_current_output_docs_file()
        
        if not os.path.exists(output_docs_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum documento processado encontrado"
            )
            
        with open(output_docs_file, "rb") as f:
            processed_docs = pickle.load(f)
            
        return [
            {
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "length": len(doc.page_content)
            }
            for doc in processed_docs
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao recuperar documentos processados: {str(e)}"
        )

@app.get("/status/")
async def get_processing_status(api_key: str = Depends(get_api_key)):
    """
    Retorna o status atual do processamento de documentos da base atual.
    """
    try:
        documents_dir = get_current_documents_dir()
        output_docs_file = get_current_output_docs_file()
        
        total_files = len(load_all_files_from_directory(documents_dir))
        processed_exists = os.path.exists(output_docs_file)
        
        return {
            "documents_directory": documents_dir,
            "total_files": total_files,
            "processing_completed": processed_exists,
            "last_processed": datetime.fromtimestamp(os.path.getmtime(output_docs_file)).isoformat() if processed_exists else None,
            "current_base": base_manager.current_base
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status: {str(e)}"
        )

#  ------ vector store
@app.post("/create-vector-store")
async def create_vector_store_endpoint(api_key: str = Depends(get_api_key)):
    """
    Cria um novo vector store para a base atual
    """
    try:
        documents_dir = get_current_documents_dir()
        faiss_index_path = get_current_faiss_index_path()
        output_docs_file = get_current_output_docs_file()
        
        result = create_vectorstore(
            documents_dir=documents_dir,
            faiss_index_path=faiss_index_path,
            output_docs_file=output_docs_file
        )
        
        result["base"] = base_manager.current_base
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------- gerenciamento de bases -----------
@app.get("/bases/")
async def list_bases(api_key: str = Depends(get_api_key)):
    """
    Lista todas as bases disponíveis
    """
    return {
        "current_base": base_manager.current_base,
        "available_bases": list(base_manager.bases_config.keys()),
        "bases_config": base_manager.bases_config
    }

@app.post("/bases/")
async def create_base(base_config: BaseConfig, api_key: str = Depends(get_api_key)):
    """
    Cria uma nova base
    """
    try:
        success = base_manager.create_base(base_config)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Base '{base_config.base_name}' já existe"
            )
        
        return {
            "status": "success",
            "message": f"Base '{base_config.base_name}' criada com sucesso",
            "base_config": base_config.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar base: {str(e)}"
        )

@app.post("/bases/switch")
async def switch_base(switch_request: SwitchBaseRequest, api_key: str = Depends(get_api_key)):
    """
    Muda para uma base específica
    """
    try:
        success = base_manager.switch_base(switch_request.base_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Base '{switch_request.base_name}' não encontrada"
            )
        
        # Atualizar o RAG chain para usar a nova base
        switch_base_rag(switch_request.base_name)
        
        return {
            "status": "success",
            "message": f"Base alterada para '{switch_request.base_name}'",
            "new_base": switch_request.base_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao mudar de base: {str(e)}"
        )

@app.delete("/bases/{base_name}")
async def delete_base(base_name: str, api_key: str = Depends(get_api_key)):
    """
    Remove uma base (apenas configuração, não deleta arquivos)
    """
    try:
        success = base_manager.delete_base(base_name)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não foi possível deletar a base '{base_name}'"
            )
        
        return {
            "status": "success",
            "message": f"Base '{base_name}' removida com sucesso"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover base: {str(e)}"
        )

# ----------- atualizar env
@app.post("/update-env")
async def update_environment_variables(update_request: EnvUpdateRequest, api_key: str = Depends(get_api_key)):
    """
    Atualiza variáveis de ambiente no arquivo .env
    
    Parâmetros:
    - GROQ_API_KEY: Chave API da Groq
    - TOP_K: Número de documentos relevantes a recuperar
    - EMBED_MODEL_ID: ID do modelo de embedding
    - GEN_MODEL_ID: ID do modelo generativo
    """
    try:
        env_file_path = ".env"
        
        # Verificar se o arquivo .env existe
        if not os.path.exists(env_file_path):
            # Criar um arquivo .env vazio se não existir
            with open(env_file_path, "w") as f:
                f.write("# Environment variables\n")
        
        # Ler o conteúdo atual do arquivo
        with open(env_file_path, "r") as f:
            lines = f.readlines()
        
        # Preparar as atualizações
        updates = {
            "GROQ_API_KEY": update_request.GROQ_API_KEY,
            "TOP_K": update_request.TOP_K,
            "EMBED_MODEL_ID": update_request.EMBED_MODEL_ID,
            "GEN_MODEL_ID": update_request.GEN_MODEL_ID
        }
        
        # Processar cada linha do arquivo
        new_lines = []
        updated_vars = set()
        
        for line in lines:
            line_stripped = line.strip()
            
            # Verificar se a linha contém alguma das variáveis que queremos atualizar
            matched = False
            for var_name, var_value in updates.items():
                if line_stripped.startswith(f"{var_name}="):
                    if var_value is not None:
                        # Atualizar a linha com o novo valor
                        new_lines.append(f"{var_name}={var_value}\n")
                        updated_vars.add(var_name)
                    else:
                        # Manter a linha original se o valor for None
                        new_lines.append(line)
                    matched = True
                    break
            
            if not matched:
                # Manter linhas que não são variáveis que queremos atualizar
                new_lines.append(line)
        
        # Adicionar variáveis que não existiam no arquivo (apenas se o valor não for None)
        for var_name, var_value in updates.items():
            if var_value is not None and var_name not in updated_vars:
                new_lines.append(f"{var_name}={var_value}\n")
                updated_vars.add(var_name)
        
        # Escrever o novo conteúdo no arquivo
        with open(env_file_path, "w") as f:
            f.writelines(new_lines)
        
        # Atualizar as variáveis de ambiente em tempo de execução
        if update_request.GROQ_API_KEY is not None:
            os.environ["GROQ_API_KEY"] = update_request.GROQ_API_KEY
        if update_request.TOP_K is not None:
            os.environ["TOP_K"] = update_request.TOP_K
        if update_request.EMBED_MODEL_ID is not None:
            os.environ["EMBED_MODEL_ID"] = update_request.EMBED_MODEL_ID
        if update_request.GEN_MODEL_ID is not None:
            os.environ["GEN_MODEL_ID"] = update_request.GEN_MODEL_ID
        
        logger.info(f"Variáveis de ambiente atualizadas: {list(updated_vars)}")
        
        return {
            "status": "success",
            "message": "Variáveis de ambiente atualizadas com sucesso",
            "updated_variables": list(updated_vars),
            "note": "Algumas mudanças podem requerer reinício da aplicação para ter efeito completo"
        }
        
    except Exception as e:
        logger.error(f"Erro ao atualizar variáveis de ambiente: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar variáveis de ambiente: {str(e)}"
        )


@app.get("/env-status")
async def get_environment_status(api_key: str = Depends(get_api_key)):
    """
    Retorna o status atual das variáveis de ambiente
    """
    try:
        return {
            "GROQ_API_KEY": "***" if os.getenv("GROQ_API_KEY") else "Não definida",
            "TOP_K": os.getenv("TOP_K", "3"),
            "EMBED_MODEL_ID": os.getenv("EMBED_MODEL_ID", "Qwen/Qwen3-Embedding-0.6B"),
            "GEN_MODEL_ID": os.getenv("GEN_MODEL_ID", "llama-3.1-8b-instant"),
            "env_file_exists": os.path.exists(".env")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status do ambiente: {str(e)}"
        )

# Documentação adicional
app.openapi_tags = [{
    "name": "consultas",
    "description": "Endpoints para processamento de consultas acadêmicas"
}, {
    "name": "bases",
    "description": "Endpoints para gerenciamento de múltiplas bases de dados"
}]