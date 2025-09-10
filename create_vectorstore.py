import os
import pickle
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

# Configurações padrão (podem ser sobrescritas por parâmetros)
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 
CHUNK_SIZE = 1000 
CHUNK_OVERLAP = 200

# Gerenciador de bases
try:
    from base_manager import base_manager
except ImportError:
    # Fallback para compatibilidade
    class FallbackBaseManager:
        def __init__(self):
            self.current_base = "default"
            self.bases_config = {
                "default": {
                    "faiss_index_path": "faiss_index",
                    "documents_dir": "documents",
                    "output_docs_file": "processed_docs.pkl"
                }
            }
        
        def get_current_base_config(self):
            return self.bases_config.get(self.current_base, self.bases_config["default"])
    
    base_manager = FallbackBaseManager()

def create_vectorstore(documents_dir=None, faiss_index_path=None, output_docs_file=None, base_name=None):
    """
    Carrega documentos pré-processados e cria um Vector Store.
    Se base_name for fornecido, usa a configuração dessa base.
    """
    print("🚀 Iniciando a criação do Vector Store...")
    
    # Determinar qual configuração usar
    if base_name:
        # Usar configuração de base específica
        if base_name not in base_manager.bases_config:
            return {
                "status": "error",
                "message": f"Base '{base_name}' não encontrada"
            }
        
        base_config = base_manager.bases_config[base_name]
        documents_dir = base_config["documents_dir"]
        faiss_index_path = base_config["faiss_index_path"]
        output_docs_file = base_config["output_docs_file"]
        print(f"📁 Criando vectorstore para base: {base_name}")
    else:
        # Usar configuração fornecida ou padrão da base atual
        if documents_dir is None:
            documents_dir = base_manager.get_current_base_config()["documents_dir"]
        if faiss_index_path is None:
            faiss_index_path = base_manager.get_current_base_config()["faiss_index_path"]
        if output_docs_file is None:
            output_docs_file = base_manager.get_current_base_config()["output_docs_file"]
        print(f"📁 Criando vectorstore para diretório: {documents_dir}")

    # 1. Carregar os documentos pré-processados do arquivo pickle
    print(f"🔄 Carregando documentos de '{output_docs_file}'...")
    try:
        with open(output_docs_file, "rb") as f:
            processed_docs = pickle.load(f)
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{output_docs_file}' não encontrado.")
        print("➡️ Por favor, processe os documentos primeiro.")
        return {
            "status": "error",
            "message": f"Arquivo '{output_docs_file}' não encontrado"
        }
    print(f"✅ {len(processed_docs)} documentos carregados.")

    # 2. Aplicar a estratégia de Chunking
    print(f"📄 Aplicando chunking: size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
    )
    splits = text_splitter.split_documents(processed_docs)
    print(f"✅ Documentos divididos em {len(splits)} chunks.")
    
    # 3. Criar os Embeddings e o Vector Store
    print(f"🧠 Criando embeddings com o modelo: {EMBED_MODEL_ID}")
    embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL_ID)

    print(f"💾 Criando e salvando o índice FAISS em '{faiss_index_path}'...")
    if not splits:
        print("❌ Nenhum chunk foi criado. Abortando a criação do índice.")
        return {
            "status": "error",
            "message": "Nenhum chunk foi criado a partir dos documentos"
        }
        
    vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
    vectorstore.save_local(faiss_index_path)
    
    result = {
        "status": "success",
        "message": "Vector Store criado com sucesso",
        "base": base_name if base_name else base_manager.current_base,
        "documents_dir": documents_dir,
        "faiss_index_path": faiss_index_path,
        "output_docs_file": output_docs_file,
        "chunks_created": len(splits),
        "embedding_model": EMBED_MODEL_ID
    }
    
    print(f"🎉 Vector Store criado com sucesso para base: {result['base']}")
    return result

def create_vectorstore_for_all_bases():
    """Cria vectorstores para todas as bases configuradas"""
    results = {}
    
    for base_name in base_manager.bases_config:
        print(f"\n{'='*50}")
        print(f"PROCESSANDO BASE: {base_name}")
        print(f"{'='*50}")
        
        result = create_vectorstore(base_name=base_name)
        results[base_name] = result
    
    return results

if __name__ == "__main__":
    # Comportamento padrão: criar para a base atual
    result = create_vectorstore()
    
    if result and result.get("status") == "success":
        print(f"\n🎉 Vector Store criado com sucesso!")
        print(f"Base: {result['base']}")
        print(f"Documentos: {result['documents_dir']}")
        print(f"Índice: {result['faiss_index_path']}")
        print(f"Chunks: {result['chunks_created']}")
    else:
        print(f"\n❌ Falha ao criar Vector Store: {result.get('message', 'Erro desconhecido')}")