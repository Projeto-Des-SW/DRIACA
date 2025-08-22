import os
import re
import pickle
from pathlib import Path
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langchain_core.documents import Document
from dotenv import load_dotenv

# --- Novas importações necessárias para a função de reconstrução ---
from pypdf import PdfReader
from fpdf import FPDF

# --- Configurações ---
load_dotenv()
DOCUMENTS_DIR =  os.getenv("DOCUMENTS_DIR")
OUTPUT_DOCS_FILE = os.getenv("OUTPUT_DOCS_FILE")

def load_all_files_from_directory(directory: str) -> list[str]:
    """Carrega todos os arquivos de um diretório."""
    if not os.path.isdir(directory):
        raise ValueError(f"O diretório '{directory}' não existe ou não é um diretório")
    # Filtra para não processar arquivos já reconstruídos no início
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and "_REBUILT_FROM_" not in f]

def preprocess_text(text: str) -> str:
    """Uma função simples de pré-processamento para limpar o texto."""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def rebuild_pdf_from_text(input_pdf_path: str, output_pdf_path: str) -> bool:
    """
    Extrai o texto de um PDF problemático e o insere em um PDF novo e limpo.
    Retorna True se bem-sucedido, False se ocorrer um erro.
    """
    print(f"   -> Reconstruindo '{os.path.basename(input_pdf_path)}' a partir do texto...")
    try:
        reader = PdfReader(input_pdf_path)
        text_pages = [page.extract_text() for page in reader.pages]
        
        pdf = FPDF()
        pdf.set_font("Arial", "", 10)

        for text in text_pages:
            pdf.add_page()
            encoded_text = text.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 5, encoded_text)

        pdf.output(output_pdf_path)
        print(f"   -> PDF reconstruído com sucesso em '{os.path.basename(output_pdf_path)}'")
        return True

    except Exception as e:
        print(f"   -> ERRO durante a reconstrução do PDF: {e}")
        return False

def main():
    """
    Carrega, processa e salva os documentos de origem em um arquivo intermediário.
    """
    print("🚀 Etapa 1: Iniciando o carregamento dos documentos de origem...")

    try:
        file_paths = load_all_files_from_directory(DOCUMENTS_DIR)
        if not file_paths:
            raise ValueError(f"Nenhum arquivo encontrado no diretório {DOCUMENTS_DIR}")
        
        print(f"✅ Encontrados {len(file_paths)} arquivos para processar.")
    except Exception as e:
        print(f"❌ Erro ao listar arquivos: {str(e)}")
        return

    all_docs = []
    failed_files = []

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        print(f"📄 Processando arquivo: {file_name}...")

        # --- TENTATIVA 1: Carregar o arquivo original ---
        try:
            loader = DoclingLoader(file_path=file_path, export_type=ExportType.MARKDOWN)
            docs_from_file = loader.load()
            all_docs.extend(docs_from_file)
            print(f"   ✅ Sucesso! Ao carregar {file_name}...")
        
        # --- PLANO B: Se a TENTATIVA 1 falhar, reconstruir e tentar de novo ---
        except Exception as e:
            print(f"   ❌ ERRO no processamento inicial de '{file_name}': {str(e)}")
            
            base_name, ext = os.path.splitext(file_path)
            rebuilt_file_path = f"{base_name}_REBUILT_FROM_TEXT{ext}"
            
            # Chama a função de reconstrução
            if rebuild_pdf_from_text(file_path, rebuilt_file_path):
                # --- TENTATIVA 2: Carregar o arquivo reconstruído ---
                print(f"   🛠️  Tentando carregar o arquivo reconstruído...")
                try:
                    loader = DoclingLoader(file_path=rebuilt_file_path, export_type=ExportType.MARKDOWN)
                    docs_from_file = loader.load()
                    all_docs.extend(docs_from_file)
                    print(f"   ✅ Sucesso na segunda tentativa! Carregados {len(docs_from_file)} documento(s).")
                except Exception as e2:
                    print(f"   ❌ ERRO FINAL: Falha ao processar até mesmo o arquivo reconstruído de '{file_name}': {str(e2)}")
                    failed_files.append(file_name)
            else:
                # Se a própria reconstrução falhar
                print(f"   ❌ ERRO FINAL: Falha ao reconstruir o arquivo '{file_name}'.")
                failed_files.append(file_name)
    
    # Aplicar pré-processamento nos documentos que foram carregados com sucesso
    print("\n✨ Aplicando pré-processamento nos textos...")
    processed_docs = []
    for doc in all_docs:
        cleaned_content = preprocess_text(doc.page_content)
        if cleaned_content:
            processed_docs.append(Document(page_content=cleaned_content, metadata=doc.metadata))
    
    print(f"✨ {len(processed_docs)} documentos válidos após o pré-processamento.")
    if failed_files:
        print(f"⚠️ Arquivos que falharam no carregamento final: {', '.join(failed_files)}")

    # Salvar a lista de documentos processados
    print(f"\n💾 Salvando documentos processados em '{OUTPUT_DOCS_FILE}'...")
    with open(OUTPUT_DOCS_FILE, "wb") as f:
        pickle.dump(processed_docs, f)
    
    print(f"🎉 Etapa 1 concluída! Documentos salvos com sucesso.")

if __name__ == "__main__":
    main()