import os

def listar_paths_projeto(diretorio_raiz, arquivo_saida):
    # Pastas para ignorar completamente
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.env', '.idea', '.vscode'}
    
    with open(arquivo_saida, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(diretorio_raiz):
            # Filtra as pastas para não entrar nelas
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                # Pega o caminho absoluto
                caminho_absoluto = os.path.abspath(os.path.join(root, file))
                outfile.write(caminho_absoluto + '\n')

if __name__ == "__main__":
    # Roda no diretório atual
    diretorio_atual = os.getcwd()
    nome_arquivo = "lista_caminhos_projeto.txt"
    
    print(f"Mapeando caminhos em: {diretorio_atual}")
    listar_paths_projeto(diretorio_atual, nome_arquivo)
    print(f"Pronto! Lista salva em: {nome_arquivo}")