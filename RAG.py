import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq

from query_transformation import transform_query

# --- Configurações ---
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HUGGINGFACE_HUB_DISABLE_SYMLINKS"] = "1"

# Configurações serão obtidas dinamicamente baseadas na base atual
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 
GEN_MODEL_ID = os.getenv("GEN_MODEL_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 
TOP_K = int(os.getenv("TOP_K", 3))

PROMPT = PromptTemplate.from_template(
    "Você é um assistente acadêmico especializado da UFAPE (Universidade Federal do Agreste de Pernambuco). Sua única missão é responder perguntas baseando-se estrita e exclusivamente no CONTEXTO fornecido, que contém trechos de documentos oficiais do Departamento de Registro e Controle Acadêmico (DRCA). \nContexto fornecido.\n---------------------\n{context}\n---------------------\nHistórico da conversa.\n---------------------\n{conversation}\n---------------------\nInstruções para a resposta: 1. O CONTEXTO é sua única fonte de informação. NÃO utilize nenhum conhecimento prévio ou externo à UFAPE ou ao mundo.\n2. Se a informação para responder a pergunta não estiver contida no CONTEXTO, sua única e obrigatória resposta deve ser: 'Com base nos documentos oficiais fornecidos, não encontrei informações sobre este tópico.' Não tente adivinhar ou inferir.\n3. Não sugira outros documentos, sites, links ou departamentos, a menos que o CONTEXTO fornecido os mencione explicitamente como um próximo passo.\n4. Nunca use frases como 'conforme descrito no contexto', 'segundo o contexto fornecido' ou similares em sua resposta final. Sua função é agir como se você fosse a fonte da informação, sintetizando os fatos do contexto de forma direta.\npergunta: {input}\nResposta (Forneça uma resposta clara, concisa e profissional, extraída diretamente do CONTEXTO. Se possível, inicie citando a fonte, como 'De acordo com o Art. XX do Regimento...'):\n",
)

# --- Variáveis globais para estado atual ---
current_vectorstore = None
current_retriever = None
conversation_history = []

# --- Gerenciador de bases (será injetado) ---
# Vamos assumir que temos um base_manager global disponível
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

# --- Inicialização da Aplicação ---

def load_vector_store(faiss_index_path=None):
    """Carrega o índice FAISS do disco. Retorna None em caso de erro."""
    try:
        if faiss_index_path is None:
            faiss_index_path = base_manager.get_current_base_config()["faiss_index_path"]
        
        if not Path(faiss_index_path).exists():
            raise FileNotFoundError(
                f"Diretório do índice FAISS não encontrado em '{faiss_index_path}'. "
                "Por favor, execute o script 'ingest.py' primeiro para criar o índice."
            )
        print(f"✅ Carregando índice FAISS existente de '{faiss_index_path}'...")
        embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL_ID)
        vectorstore = FAISS.load_local(faiss_index_path, embedding, allow_dangerous_deserialization=True)
        print("✅ Índice carregado com sucesso.")
        return vectorstore
    except Exception as e:
        print(f"⚠️ Erro ao carregar o índice FAISS: {e}")
        return None

def initialize_rag_system():
    """Inicializa o sistema RAG com a base atual"""
    global current_vectorstore, current_retriever
    
    try:
        base_config = base_manager.get_current_base_config()

        faiss_index_path = base_config["faiss_index_path"]
        
        current_vectorstore = load_vector_store(faiss_index_path)
        
        if current_vectorstore is not None:
            current_retriever = current_vectorstore.as_retriever(search_kwargs={"k": TOP_K})
            print(f"✅ Sistema RAG inicializado para base: {base_manager.current_base}")
        else:
            current_retriever = None
            print(f"⚠️ Continuando sem vectorstore para base: {base_manager.current_base}")
            
    except Exception as e:
        print(f"❌ Erro ao inicializar sistema RAG: {e}")
        current_vectorstore = None
        current_retriever = None

def switch_base_rag(base_name):
    """Muda para uma base específica"""
    global current_vectorstore, current_retriever

    if base_name in base_manager.bases_config:
        base_manager.current_base = base_name
        initialize_rag_system()
        reset_conversation_history()
        return True
    return False

def get_current_base():
    """Retorna o nome da base atual"""
    return base_manager.current_base

# 2. Criar o cliente do LLM
client = ChatGroq(
    api_key=GROQ_API_KEY, 
    model_name=GEN_MODEL_ID
)

# 3. Lógica de Conversação
def reset_conversation_history():
    """Reseta o histórico da conversa."""
    global conversation_history
    conversation_history = []
    print("Histórico da conversa resetado.")

def update_conversation_history(question, answer):
    """Adiciona a pergunta e resposta ao histórico."""
    conversation_history.append({"question": question, "answer": answer})

def rag_chain(input_text: str):
    """Executa a cadeia de RAG. Funciona mesmo sem o vectorstore carregado."""
    global current_retriever
    
    try:
        # Se não tivermos um retriever, usamos um contexto vazio
        if current_retriever is None:
            context = ""
            context_docs = []
            transformed_query = input_text
        else:
            original_docs = current_retriever.get_relevant_documents(input_text)
            transformed_query = transform_query(input_text, conversation_history)
            transformed_docs = current_retriever.get_relevant_documents(transformed_query)

            all_docs = original_docs + transformed_docs
            unique_docs = []
            seen_content = set()

            for doc in all_docs:
                if doc.page_content not in seen_content:
                    seen_content.add(doc.page_content)
                    unique_docs.append(doc)
            
            context_docs = unique_docs[:TOP_K*2]
            context = "\n".join([doc.page_content for doc in context_docs])
        
        # Formata o histórico para o prompt
        formatted_history = "\n".join([f"User: {turn['question']}\nAI: {turn['answer']}" for turn in conversation_history])

        final_prompt = PROMPT.format(context=context, input=input_text, conversation=formatted_history)
        
        response = client.invoke(final_prompt)
        answer = response.content
        
        update_conversation_history(input_text, answer)

        # LOGs para depuração
        print('='*50)
        print(f"Base: {base_manager.current_base} | LLM: {GEN_MODEL_ID} | Embedding: {EMBED_MODEL_ID}")
        print('='*50)
        print(f"QUERY ORIGINAL: {input_text}")
        if current_retriever is not None:
            print(f"QUERY TRANSFORMADA: {transformed_query}")
        else:
            print("QUERY TRANSFORMADA: (não aplicável - sem vectorstore)")
        print('='*50)
        print(f"PROMPT ENVIADO:\n{final_prompt}")
        print('='*50)
        print(f"RESPOSTA RECEBIDA:\n{answer}")
        print('='*50)

        return {
            "input": input_text,
            "transformed_query": transformed_query,
            "resposta": answer,
            "contexto": context_docs if current_retriever is not None else [],
            "base_used": base_manager.current_base
        }
    except Exception as e:
        print(f"⚠️ Erro durante o processamento RAG: {e}")
        # Retorna uma resposta padrão em caso de erro
        return {
            "input": input_text,
            "transformed_query": input_text,
            "resposta": "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
            "contexto": [],
            "base_used": base_manager.current_base
        }

# Inicializar o sistema ao importar
initialize_rag_system()