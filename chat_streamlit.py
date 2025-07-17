
import streamlit as st

# Configuração da interface do Streamlit (DEVE SER A PRIMEIRA CHAMADA)
st.set_page_config(page_title="Chat com DRiaCA", layout="wide")

# Agora importe outros módulos e defina funções
from RAG import *
import json

# Função para resetar o histórico de conversa
def reset_conversation():
    reset_conversation_history()
    st.session_state.conversation_history = []

# Adicionar o GIF ao lado do título usando HTML/CSS
st.markdown(
    """
    <div style="display: flex; align-items: center;">
        <img src="https://s3.gifyu.com/images/bSr5s.gif" width="250" style="margin-right: 10px;">
        <h1>Chat com DRiaCA</h1>
        <img src="https://ufape.edu.br/sites/default/files/BRAS%C3%83O_SITE.fw_.png" width="50" style="margin-right: 10px;">
    </div>
    """,
    unsafe_allow_html=True
)

# Inicializar o histórico de conversa na sessão
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Exibir o histórico de conversa como um chat
chat_container = st.container()
with chat_container:
    for index, message in enumerate(st.session_state.conversation_history, start=1):
        with st.chat_message("user"):
            st.markdown(f"**Você:** {message['question']}")
        with st.chat_message("assistant"):
            st.markdown(f"**RAG:** {message['answer']}")

            # Exibir as fontes em um dropdown
            with st.expander("📚 Fontes da resposta"):
                for i, doc in enumerate(message["sources"]):
                    st.write(f"**Fonte {i+1}:**")
                    source = doc.metadata["source"]
                    st.write(f"Caminho: {source} ")
                    st.text_area("", value=doc.page_content, height=150, disabled=True, key=f"text_area_{index}_{i}")

# Entrada do usuário
user_input = st.chat_input("Digite sua pergunta...")

# Botão para resetar o histórico de conversa
if st.button("Resetar Conversa", key="reset_button", help="Clique para resetar o histórico de conversa"):
    reset_conversation()
    st.rerun()

# Estilo CSS para o botão vermelho
st.markdown("""
    <style>
        div.stButton > button:first-child {
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 10px 24px;
            border-radius: 5px;
            cursor: pointer;
        }
        div.stButton > button:first-child:hover {
            background-color: #ff1c1c;
        }
    </style>
""", unsafe_allow_html=True)

if user_input:
    with st.spinner("Pensando..."):
        # Processar a pergunta do usuário
        resp_dict = rag_chain(user_input)

    # Atualizar o histórico de conversa
    st.session_state.conversation_history.append({
        "question": resp_dict['input'],
        "answer": resp_dict["resposta"],
        "sources": resp_dict["contexto"]
    })

    # Recarregar a página para atualizar o chat
    st.rerun()