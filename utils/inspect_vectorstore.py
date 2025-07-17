import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- Configurações ---
# Garanta que estas configurações sejam as mesmas usadas no ingest.py
load_dotenv()
FAISS_INDEX_PATH = "faiss_index"
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 
os.environ["HUGGINGFACE_HUB_DISABLE_SYMLINKS"] = "1"

def inspect_vector_store():
    """
    Carrega um índice FAISS existente e exibe informações sobre ele.
    """
    index_path = Path(FAISS_INDEX_PATH)
    if not index_path.exists():
        print(f"❌ Erro: Diretório do índice FAISS não encontrado em '{FAISS_INDEX_PATH}'.")
        print("➡️ Por favor, execute o script 'ingest.py' primeiro para criar o índice.")
        return

    # 1. Carregar o Vector Store do disco
    print(f"🔍 Carregando índice de '{FAISS_INDEX_PATH}'...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL_ID)
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    print("✅ Índice carregado com sucesso!")
    print("-" * 50)

    # --- Métodos de Inspeção ---

    # 📊 1. Informações Gerais
    # O FAISS armazena um mapeamento dos IDs do índice para os IDs do docstore.
    # O tamanho desse mapeamento nos diz quantos chunks/vetores temos.
    total_vectors = len(vectorstore.index_to_docstore_id)
    print(f"📊 Informações Gerais:")
    print(f"   - Total de chunks (vetores) no índice: {total_vectors}")
    print("-" * 50)

    if total_vectors > 0:
        # 📄 2. Visualizando Chunks Específicos pelo ID
        # Podemos acessar o docstore diretamente para buscar um chunk pelo seu ID.
        # Os IDs são strings, geralmente gerados aleatoriamente (UUIDs).
        print("📄 Visualizando o primeiro chunk (ID de índice 0):")
        
        # Pega o ID do documento correspondente ao primeiro vetor no índice FAISS
        first_doc_id = vectorstore.index_to_docstore_id[0]
        
        # Busca o documento no docstore usando esse ID
        doc = vectorstore.docstore.search(first_doc_id)
        
        if doc:
            print(f"   - Conteúdo do Chunk:\n     '{doc.page_content[:300]}...'") # Mostra os primeiros 300 caracteres
            print(f"   - Metadados: {doc.metadata}")
        else:
            print("   - Documento não encontrado no docstore.")
        print("-" * 50)

        # 🎯 3. Testando a Busca por Similaridade (a forma mais útil de inspeção)
        # Isso simula o que o retriever faz: encontrar os chunks mais relevantes para uma pergunta.
        print("🎯 Testando a busca por similaridade...")
        query = "Como faço para verificar pendências de documentos?"
        
        print(f"   - Buscando por: '{query}'")
        
        # O método similarity_search retorna os documentos mais relevantes.
        relevant_docs = vectorstore.similarity_search(query, k=3) # Pede os 3 chunks mais relevantes

        print(f"\n   - {len(relevant_docs)} documentos mais relevantes encontrados:")
        for i, doc in enumerate(relevant_docs):
            source = doc.metadata.get('source', 'N/A')
            print(f"\n     --- Documento Relevante #{i+1} ---")
            print(f"     Fonte: {source}")
            print(f"     Conteúdo: '{doc.page_content}'")
        print("-" * 50)


        print("🎯 Testando a busca por similaridade...")
        query = "O que é DRCA?"
        
        print(f"   - Buscando por: '{query}'")
        
        # O método similarity_search retorna os documentos mais relevantes.
        relevant_docs = vectorstore.similarity_search(query, k=3) 
        
        print(f"\n   - {len(relevant_docs)} documentos mais relevantes encontrados:")
        for i, doc in enumerate(relevant_docs):
            source = doc.metadata.get('source', 'N/A')
            print(f"\n     --- Documento Relevante #{i+1} ---")
            print(f"     Fonte: {source}")
            print(f"     Conteúdo: '{doc.page_content}'")
        print("-" * 50)

if __name__ == "__main__":
    inspect_vector_store()