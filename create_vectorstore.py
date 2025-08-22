import os
import pickle
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


load_dotenv()
# --- Laboratório de Experimentos ---
# MODIFIQUE ESTAS VARIÁVEIS PARA TESTAR DIFERENTES CONFIGURAÇÕES
# --------------------------------------------------------------------------
# Modelos de Embedding para testar:
# - "sentence-transformers/all-MiniLM-L6-v2" (inglês/multilíngue, rápido)
# - "neuralmind/bert-base-portuguese-cased-sts" (bom para português)
# - "sentence-transformers/paraphrase-multilingual-mpnet-base-v2" (mais robusto)
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 

# Estratégia de Chunking para testar:
CHUNK_SIZE = 1000 
CHUNK_OVERLAP = 200

# Nome do índice de saída (pode ser útil mudar se quiser manter várias versões)
FAISS_INDEX_PATH = "faiss_index"
# --------------------------------------------------------------------------


# --- Configurações Gerais ---
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HUGGINGFACE_HUB_DISABLE_SYMLINKS"] = "1"
INPUT_DOCS_FILE = "processed_docs.pkl"

def create_vectorstore():
    """
    Carrega documentos pré-processados e cria um Vector Store com
    as configurações de chunking e embedding especificadas.
    """
    print("🚀 Etapa 2: Iniciando a criação do Vector Store...")
    
    # 1. Carregar os documentos pré-processados do arquivo pickle
    print(f"🔄 Carregando documentos de '{INPUT_DOCS_FILE}'...")
    try:
        with open(INPUT_DOCS_FILE, "rb") as f:
            processed_docs = pickle.load(f)
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{INPUT_DOCS_FILE}' não encontrado.")
        print("➡️ Por favor, execute 'python load_docs.py' primeiro.")
        return
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

    print(f"💾 Criando e salvando o índice FAISS em '{FAISS_INDEX_PATH}'...")
    if not splits:
        print("❌ Nenhum chunk foi criado. Abortando a criação do índice.")
        return
        
    vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"🎉 Etapa 2 concluída! Vector Store criado com sucesso.")

if __name__ == "__main__":
    create_vectorstore()