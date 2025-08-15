import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from RAG import rag_chain, reset_conversation_history
from fastapi.encoders import jsonable_encoder

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

# Documentação adicional
app.openapi_tags = [{
    "name": "consultas",
    "description": "Endpoints para processamento de consultas acadêmicas"
}]