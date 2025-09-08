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
from RAG import rag_chain, reset_conversation_history
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


# --- Configuração da API ---
app = FastAPI(
    title="API de Consulta Acadêmica UFAPE",
    description="API para consulta de documentos oficiais da UFAPE usando RAG",
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

DOCUMENTS_DIR =  os.getenv("DOCUMENTS_DIR")
OUTPUT_DOCS_FILE = os.getenv("OUTPUT_DOCS_FILE")
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH")
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

class HealthCheck(BaseModel):
    status: str
    timestamp: str

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
        "timestamp": datetime.now().isoformat()
    }

@app.post("/query", response_model=QueryOutput)
async def process_query(query: QueryInput, api_key: str = Depends(get_api_key)):
    try:
        logger.info(f"Nova consulta - User: {query.user_id} - Session: {query.session_id}")
        
        result = rag_chain(query.text)
        
        response = QueryOutput(
            input=result["input"],
            transformed_query=result["transformed_query"],
            resposta=result["resposta"],
            contexto=convert_documents_to_response(result["contexto"]),
            timestamp=datetime.now().isoformat(),
            model_used=os.getenv("GEN_MODEL_ID", "unknown")
        )
        
        logger.info(f"Consulta processada - Input: {query.text[:50]}...")
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

storage_manager = FileStorageManager(storage_root=DOCUMENTS_DIR)

@app.post("/api/documents/")
async def upload_document(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        result = storage_manager.save_file(file.filename, file_content)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/")
async def list_documents():
    return storage_manager.list_files()



@app.delete("/api/documents/{filename}")
async def delete_document(filename: str, api_key: str = Depends(get_api_key)):
    """
    Deleta um documento específico do sistema de arquivos.
    
    Parâmetros:
    - filename: Nome do arquivo a ser deletado
    """
    try:
        # Verificar se o arquivo existe
        file_path = storage_manager.get_file_path(filename)
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo não encontrado"
            )
        
        # Deletar o arquivo
        os.remove(file_path)
        
        logger.info(f"Documento deletado: {filename}")
        
        return {
            "status": "success",
            "message": f"Documento '{filename}' deletado com sucesso",
            "deleted_file": filename
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
async def get_document(filename: str):
    file_path = storage_manager.get_file_path(filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(file_path)



@app.post("/process/", status_code=status.HTTP_202_ACCEPTED)
async def process_documents(reprocess: bool = False):
    """
    Endpoint para processar todos os documentos no diretório.
    
    Parâmetros:
    - reprocess: Se True, reprocessa todos os documentos, incluindo os já processados
    """
    try:
        start_time = datetime.now()
        
        file_paths = load_all_files_from_directory(DOCUMENTS_DIR)
        if not file_paths:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum arquivo encontrado no diretório {DOCUMENTS_DIR}"
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
        with open(OUTPUT_DOCS_FILE, "wb") as f:
            pickle.dump(processed_docs, f)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "completed",
            "processed_documents": len(processed_docs),
            "failed_documents": len(failed_files),
            "failed_files": failed_files,
            "processing_time_seconds": processing_time,
            "output_file": OUTPUT_DOCS_FILE
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante o processamento: {str(e)}"
        )

@app.get("/processed-documents/", response_model=List[dict])
async def get_processed_documents():
    """
    Retorna a lista de documentos processados.
    """
    try:
        if not os.path.exists(OUTPUT_DOCS_FILE):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum documento processado encontrado"
            )
            
        with open(OUTPUT_DOCS_FILE, "rb") as f:
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
async def get_processing_status():
    """
    Retorna o status atual do processamento de documentos.
    """
    try:
        total_files = len(load_all_files_from_directory(DOCUMENTS_DIR))
        processed_exists = os.path.exists(OUTPUT_DOCS_FILE)
        
        return {
            "documents_directory": DOCUMENTS_DIR,
            "total_files": total_files,
            "processing_completed": processed_exists,
            "last_processed": datetime.fromtimestamp(os.path.getmtime(OUTPUT_DOCS_FILE)).isoformat() if processed_exists else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar status: {str(e)}"
        )

#  ------ vector store

@app.post("/create-vector-store")
async def create_vector_store_endpoint():
    """
    Cria um novo vector store
    """
    try:
        return create_vectorstore()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


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
}]