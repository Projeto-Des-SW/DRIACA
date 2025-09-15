# 🤖 DRIACA Chatbot

![DRIACA Logo](https://s3.gifyu.com/images/bSr5s.gif)


## 📌 Visão Geral
O **DRIACA** é um chatbot inteligente desenvolvido para a **Universidade Federal do Agreste de Pernambuco (UFAPE)**, com o objetivo de modernizar o suporte acadêmico e otimizar a comunicação entre estudantes e os **Departamento de Registro e Controle Acadêmico (DRCA)** e **Coordenadoria de Estágio (CES)**.

O projeto utiliza a arquitetura **RAG (Retrieval-Augmented Generation)**, combinando modelos de linguagem (LLMs) com uma base de conhecimento estruturada para fornecer respostas precisas e contextualizadas a partir de documentos oficiais da universidade.


## 📖 Documentação
[![Plano de Projeto](https://img.shields.io/badge/Plano_de_Projeto-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1ciA1uj269cwhCDvi_zOg9lX838tDiqQD/view?usp=sharing)

[![TAP](https://img.shields.io/badge/TAP-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1ZDP1WI-V37c3pfj1kLncD6_ch6hX5mgw/view?usp=drive_link)
[![Estudo de Viabilidade](https://img.shields.io/badge/Estudo_de_Viabilidade-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/15oZ1eK-IqnNOlrMgaQ4KE0yxy7qsiyaC/view?usp=sharing)
[![Pitch](https://img.shields.io/badge/Pitch-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1V5-ieueWCBRqQHdhDtrm9FqGauXmya8I/view?usp=sharing)
[![Video Pitch](https://img.shields.io/badge/Video_Pitch-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://youtu.be/J3WoFfkqsnA)
[![Testes de Aceitação](https://img.shields.io/badge/Testes_de_aceitacao-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://drive.google.com/file/d/1XUTTI-4w1MHJZLhnVpHnmTpswyASTDa_/view?usp=sharing)
[![Formulario da pesquisa](https://img.shields.io/badge/Formulario_da_pesquisa-2CA5E0?style=for-the-badge&logo=googledrive&logoColor=white)](https://docs.google.com/forms/d/e/1FAIpQLSf2QV89qzNH-1yQRlSspoH_fZAwUnBlSWKUZQHLx8GnDRzCGQ/viewform?usp=sharing&ouid=108929630643745737054)

## 👩‍💻 Equipe

**Geisianny Bernardo**   
📧 geisiannybernardo@gmail.com  

## 🎯 Objetivos
- ✔ **Reduzir a sobrecarga administrativa** do DRCA e CES, minimizando dúvidas repetitivas
- ✔ **Melhorar o acesso à informação** para estudantes, tornando documentos técnicos mais acessíveis
- ✔ **Automatizar respostas** com base em fontes confiáveis, garantindo precisão e eficiência

## 🛠 Tecnologias Utilizadas

### Front-end
- **React** (Interface dinâmica e responsiva)
- **TypeScript** (Tipagem estática para maior robustez)

### Back-end
- **FastAPI** (API em Python para processamento de perguntas)
- **LangChain** (Integração com LLMs e RAG)
- **FAISS** (Facebook AI Similarity Search para busca semântica)
- **SQLite** (Armazenamento de interações para análise de FAQs)

## 📊 Funcionalidades
- Chat Interativo – Interface intuitiva para perguntas e respostas

- Busca Semântica – Respostas baseadas em documentos oficiais do DRCA

- Registro de Interações – Armazenamento em SQLite para análise de FAQs

- Citações de Fontes – Exibição da origem da informação para maior transparência


## 🚀 Como Executar o Projeto

Siga as instruções abaixo para configurar e executar o ambiente de desenvolvimento localmente.

### Pré-requisitos

- [Python](https://www.python.org/downloads/) 3.8 ou superior
- [Node.js](https://nodejs.org/) e [npm](https://www.npmjs.com/) (ou um gerenciador de pacotes compatível)

### 1. Configuração do Backend

Primeiro, configure o servidor da API.

**a. Chave de API do GROQ:**

1.  Acesse [https://console.groq.com/keys](https://console.groq.com/keys) e crie uma nova chave de API.
2.  Na raiz do projeto, crie um arquivo chamado `.env`.
3.  Adicione a sua chave ao arquivo da seguinte forma:

    ```.env
    GROQ_API_KEY=SUA_CHAVE_DE_API_AQUI
    ```

**b. Instalação das dependências Python:**

Navegue até a pasta raiz do projeto e execute o seguinte comando para instalar as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

### 2. Configuração do Frontend

Agora, vamos configurar a interface do usuário.

**a. Acesse a pasta do frontend:**

```bash
cd frontend
```

**b. Instale as dependências:**

Execute o comando abaixo para instalar todas as dependências do projeto frontend.

```bash
npm install
```

### 3. Executando a Aplicação

Com tudo configurado, você precisará de dois terminais para executar o backend e o frontend simultaneamente.

**a. Para iniciar o servidor FastAPI (Backend):**

No **primeiro terminal**, a partir da **raiz do projeto**, execute:

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

O servidor estará disponível em `http://localhost:8000`.

**b. Para iniciar o cliente (Frontend):**

No **segundo terminal**, a partir da pasta `/frontend`, execute:

```bash
npm run dev
```

A aplicação frontend estará acessível em `http://localhost:8080` .


## 📄 Licença
Este projeto está sob a licença MIT.


## ✨ DRIACA – Transformando a comunicação acadêmica na UFAPE!

### 🔗 Links Úteis

- Protótipo no Figma: [Acessar Protótipo](https://www.figma.com/design/SInoeTBC9UeHqqn0rw5g51/Prototipo-DRIACA?node-id=0-1&t=8qrK2B1f6DQg31tN-1)

- Hospedagem (em breve)

📧 Dúvidas? Entre em contato: geisiannybernardo@gmail.com
