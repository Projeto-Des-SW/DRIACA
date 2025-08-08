import os
from dotenv import load_dotenv
from typing import List, Dict

from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

# --- Configurações Iniciais ---
# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações da API e Modelos
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEN_MODEL_ID = os.getenv("GEN_MODEL_ID", "llama3-8b-8192")

# Validação da chave da API
if not GROQ_API_KEY:
    raise ValueError("A chave da API da GROQ não foi encontrada. Por favor, configure-a no arquivo .env")

# --- Lógica Central de Transformação ---

# O mesmo prompt usado no seu RAG para garantir consistência
QUERY_TRANSFORM_PROMPT = PromptTemplate.from_template(
"""Analise a pergunta do usuário e o histórico de conversa abaixo. Reescreva a pergunta para:
1. Remover ambiguidades e referências implícitas.
2. Incluir termos relevantes do contexto quando necessário.
3. Manter a intenção original, mas otimizada para recuperação de documentos precisos em um vectorstore.
4. Evitar pronomes e linguagem coloquial.
5. Sua resposta deve conter apenas a pergunta reescrita.

Histórico:
{conversation}

Pergunta Original:
{question}

Pergunta Transformada:
"""
)

# Inicializa o cliente do LLM que fará a transformação
try:
    client = ChatGroq(
        api_key=GROQ_API_KEY,
        model_name=GEN_MODEL_ID
    )
except Exception as e:
    print(f"Erro ao inicializar o cliente Groq: {e}")
    exit()

def format_history_for_prompt(history: List[Dict[str, str]]) -> str:
    """Formata o histórico para ser inserido de forma legível no prompt."""
    if not history:
        return "Nenhum histórico ainda."
    return "\n".join([f"Usuário: {turn['question']}\nAssistente: {turn['answer']}" for turn in history])

def transform_query(question: str, history: List[Dict[str, str]]) -> str:
    """
    Usa o LLM para transformar a query do usuário em uma query otimizada para busca.
    Esta é a função principal a ser testada.
    """
    prompt_formatado = QUERY_TRANSFORM_PROMPT.format(
        conversation=format_history_for_prompt(history),
        question=question
    )
    
    try:
        response = client.invoke(prompt_formatado)
        transformed_query = response.content.strip()
        return transformed_query
    except Exception as e:
        return f"Ocorreu um erro durante a chamada à API: {e}"

# --- Loop Interativo para Testes ---

def run_tester():
    """Inicia um loop interativo no terminal para testar a transformação de queries."""
    conversation_history: List[Dict[str, str]] = []
    print("--- Testador Interativo de Transformação de Query ---")
    print("Digite sua pergunta a qualquer momento.")
    print("Use 'reset' para limpar o histórico da conversa.")
    print("Use 'sair' para terminar o programa.")
    print("-" * 50)

    while True:
        user_input = input("Você: ")

        if user_input.lower() == 'sair':
            print("Encerrando o testador. Até mais!")
            break
        
        if user_input.lower() == 'reset':
            conversation_history = []
            print("\n>> HISTÓRICO DA CONVERSA RESETADO <<\n")
            continue

        # Executa a transformação
        print("... Processando transformação ...")
        transformed = transform_query(user_input, conversation_history)

        # Exibe os resultados
        print("\n" + "="*20 + " RESULTADO " + "="*20)
        print(f"  PERGUNTA ORIGINAL: '{user_input}'")
        print(f"QUERY TRANSFORMADA: '{transformed}'")
        print("="*53 + "\n")

        # Simula a continuação da conversa para testes de acompanhamento
        # No RAG real, esta seria a resposta do LLM. Aqui, é apenas um placeholder.
        simulated_answer = "[Resposta simulada do assistente para manter o contexto]"
        conversation_history.append({"question": user_input, "answer": simulated_answer})
        
        print("Histórico atualizado para a próxima pergunta. Para ver o histórico, digite 'histórico'.")
        if user_input.lower() == 'histórico':
            print(format_history_for_prompt(conversation_history))


if __name__ == "__main__":
    run_tester()