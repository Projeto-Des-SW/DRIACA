import os
import shutil
import unicodedata
import re
import argparse
from typing import List

def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres especiais, acentos e espaços do nome do arquivo.
    Substitui espaços por underscores e remove caracteres não-ASCII.
    """
    # Normaliza os caracteres (remove acentos)
    filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove caracteres especiais, mantendo apenas letras, números, pontos e underscores
    filename = re.sub(r'[^\w\.-]', '_', filename)
    
    # Remove múltiplos underscores consecutivos
    filename = re.sub(r'_{2,}', '_', filename)
    
    # Remove underscores no início e no final
    filename = filename.strip('_')
    
    return filename

def get_all_files(directory: str, extensions: List[str] = None) -> List[str]:
    """
    Retorna uma lista com todos os arquivos no diretório e subdiretórios.
    Se extensions for fornecido, apenas arquivos com essas extensões serão incluídos.
    """
    all_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if extensions:
                if any(file.lower().endswith(ext.lower()) for ext in extensions):
                    all_files.append(os.path.join(root, file))
            else:
                all_files.append(os.path.join(root, file))
    
    return all_files

def copy_files_to_output(files: List[str], output_dir: str) -> None:
    """
    Copia os arquivos para o diretório de saída, tratando os nomes.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for file_path in files:
        try:
            # Obtém o nome do arquivo original
            original_filename = os.path.basename(file_path)
            
            # Sanitiza o nome do arquivo
            sanitized_filename = sanitize_filename(original_filename)
            
            # Constrói o caminho completo de destino
            dest_path = os.path.join(output_dir, sanitized_filename)
            
            # Verifica se o arquivo já existe no destino para evitar sobrescrita
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(sanitized_filename)
                dest_path = os.path.join(output_dir, f"{name}_{counter}{ext}")
                counter += 1
            
            # Copia o arquivo
            shutil.copy2(file_path, dest_path)
            print(f"Copiado: {original_filename} -> {os.path.basename(dest_path)}")
            
        except Exception as e:
            print(f"Erro ao copiar {file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Copia arquivos de um diretório para outro, tratando nomes com caracteres especiais.')
    parser.add_argument('source_dir', help='Diretório de origem para varrer')
    parser.add_argument('output_dir', help='Diretório de destino para copiar os arquivos')
    parser.add_argument('--extensions', nargs='+', default=None, 
                        help='Extensões de arquivo para incluir (ex: .pdf .docx)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.source_dir):
        print(f"Erro: O diretório de origem '{args.source_dir}' não existe.")
        return
    
    print(f"Varrendo diretório: {args.source_dir}")
    files = get_all_files(args.source_dir, args.extensions)
    
    if not files:
        print("Nenhum arquivo encontrado.")
        return
    
    print(f"\nEncontrados {len(files)} arquivos para copiar.")
    print(f"Copiando para: {args.output_dir}\n")
    
    copy_files_to_output(files, args.output_dir)
    
    print("\nConcluído!")

if __name__ == "__main__":
    main()