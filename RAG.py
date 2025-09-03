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

FAISS_INDEX_PATH = "faiss_index"
EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID") 
GEN_MODEL_ID = os.getenv("GEN_MODEL_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

TOP_K = 3
PROMPT = PromptTemplate.from_template(
    "Você é um assistente acadêmico especializado da UFAPE (Universidade Federal do Agreste de Pernambuco). Sua única missão é responder perguntas baseando-se estrita e exclusivamente no CONTEXTO fornecido, que contém trechos de documentos oficiais do Departamento de Registro e Controle Acadêmico (DRCA). \nContexto fornecido.\n---------------------\n{context}\n---------------------\nHistórico da conversa.\n---------------------\n{conversation}\n---------------------\nInstruções para a resposta: 1. O CONTEXTO é sua única fonte de informação. NÃO utilize nenhum conhecimento prévio ou externo à UFAPE ou ao mundo.\n2. Se a informação para responder a pergunta não estiver contida no CONTEXTO, sua única e obrigatória resposta deve ser: 'Com base nos documentos oficiais fornecidos, não encontrei informações sobre este tópico.' Não tente adivinhar ou inferir.\n3. Não sugira outros documentos, sites, links ou departamentos, a menos que o CONTEXTO fornecido os mencione explicitamente como um próximo passo.\n4. Nunca use frases como 'conforme descrito no contexto', 'segundo o contexto fornecido' ou similares em sua resposta final. Sua função é agir como se você fosse a fonte da informação, sintetizando os fatos do contexto de forma direta.\npergunta: {input}\nResposta (Forneça uma resposta clara, concisa e profissional, extraída diretamente do CONTEXTO. Se possível, inicie citando a fonte, como 'De acordo com o Art. XX do Regimento...'):\n",
)

# --- Inicialização da Aplicação ---

# 1. Carregar o Vector Store existente
def load_vector_store():
    """Carrega o índice FAISS do disco. Retorna None em caso de erro."""
    try:
        if not Path(FAISS_INDEX_PATH).exists():
            raise FileNotFoundError(
                f"Diretório do índice FAISS não encontrado em '{FAISS_INDEX_PATH}'. "
                "Por favor, execute o script 'ingest.py' primeiro para criar o índice."
            )
        print("✅ Carregando índice FAISS existente...")
        embedding = HuggingFaceEmbeddings(model_name=EMBED_MODEL_ID)
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding, allow_dangerous_deserialization=True)
        print("✅ Índice carregado com sucesso.")
        return vectorstore
    except Exception as e:
        print(f"⚠️ Erro ao carregar o índice FAISS: {e}")
        return None  # ou algum outro valor padrão que faça sentido no seu contexto

# vectorstore = load_vector_store()
# if vectorstore is not None:
#     retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
# else:
#     retriever = None 
#     print("⚠️ Continuando sem o vectorstore...")

# 2. Criar o cliente do LLM
client = ChatGroq(
    api_key=GROQ_API_KEY, 
    model_name=GEN_MODEL_ID
)

# 3. Lógica de Conversação
conversation_history = []

def reset_conversation_history():
    """Reseta o histórico da conversa."""
    global conversation_history
    conversation_history = []
    print("Histórico da conversa resetado.")

def update_conversation_history(question, answer):
    """Adiciona a pergunta e resposta ao histórico."""
    conversation_history.append({"question": question, "answer": answer})

def rag_chain(input_text: str):
    vectorstore = load_vector_store()
    if vectorstore is not None:
        retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    else:
        retriever = None 
        print("⚠️ Continuando sem o vectorstore...")
    """Executa a cadeia de RAG. Funciona mesmo sem o vectorstore carregado."""
    try:
        # Se não tivermos um retriever, usamos um contexto vazio
        if retriever is None:
            context = ""
            context_docs = []
        else:
            original_docs = retriever.get_relevant_documents(input_text)
            transformed_query = transform_query(input_text, conversation_history)
            transformed_docs = retriever.get_relevant_documents(transformed_query)

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
        print(f"LLM: {GEN_MODEL_ID} | Embedding: {EMBED_MODEL_ID}")
        print('='*50)
        print(f"QUERY ORIGINAL: {input_text}")
        if retriever is not None:
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
            "contexto": context_docs if retriever is not None else []
        }
    except Exception as e:
        print(f"⚠️ Erro durante o processamento RAG: {e}")
        # Retorna uma resposta padrão em caso de erro
        return {
            "input": input_text,
            "transformed_query": transformed_query,
            "resposta": "Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.",
            "contexto": []
        }