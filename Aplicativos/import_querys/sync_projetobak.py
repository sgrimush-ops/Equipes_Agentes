import os
import shutil
import subprocess
from datetime import datetime

def rodar_comando(comando, cwd):
    print(f">> Executando em [{cwd}]: {comando}")
    # shell=True permite os comandos de prompt nativos, check=True faz com que o script falhe se der erro
    subprocess.run(comando, cwd=cwd, shell=True, check=True)

def main():
    pasta_base = r"c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos"
    pasta_querys = os.path.join(pasta_base, 'import_querys')
    arquivo_origem = os.path.join(pasta_querys, 'query.parquet')
    
    # Criaremos um diretório permanente para o clone pra evitar fazer download de 400MB+ todos os dias 
    pasta_temporaria = os.path.join(pasta_base, 'temporario')
    pasta_clone = os.path.join(pasta_temporaria, 'ProjetoBak_Sincronizador')
    
    repo_url = "https://github.com/sgrimush-ops/ProjetoBak.git"
    
    print("="*60)
    print(" Sincronizador Automático de Dados - ProjetoBak ")
    print("="*60)

    # 1. Certificar que o arquivo de origem existe antes de tudo
    if not os.path.exists(arquivo_origem):
        print(f"[ERRO] O arquivo {arquivo_origem} não foi encontrado. O sync falhou.")
        return

    # 2. Se a pasta clone não existir, faz um clone novo. Se já existir, faz um PULL para atualizar rápido
    if not os.path.exists(pasta_clone):
        print("\n[INFO] Baixando Repositório ProjetoBak pela primeira vez (Isso pode demorar um pouquinho)...")
        os.makedirs(pasta_temporaria, exist_ok=True)
        rodar_comando(f"git clone {repo_url} ProjetoBak_Sincronizador", pasta_temporaria)
    else:
        print("\n[INFO] Repositório encontrado! Puxando atualizações recentes (Pull)...")
        try:
            # Reseta estado para evitar falhas manuais e puxa as novidades da nuvem
            rodar_comando("git fetch origin", pasta_clone)
            rodar_comando("git reset --hard origin/main", pasta_clone)
            rodar_comando("git pull origin main", pasta_clone)
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao sincronizar o clone do GitHub. Verifique a internet e as credenciais. Detalhe: {e}")
            return

    # 3. O destino do bdados existe? Se não, a gente cria.
    pasta_bdados_clone = os.path.join(pasta_clone, 'bdados')
    os.makedirs(pasta_bdados_clone, exist_ok=True)

    # 4. Copiando o query.parquet
    destino_arquivo = os.path.join(pasta_bdados_clone, 'query.parquet')
    print(f"\n[INFO] Copiando parquet...\nDe: {arquivo_origem}\nPara: {destino_arquivo}")
    shutil.copy2(arquivo_origem, destino_arquivo)

    # 5. Efetivar Commit e Push
    print("\n[INFO] Preparando envio para o GitHub...")
    hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mensagem_commit = f"update data: auto-sync diario query.parquet - {hoje}"
    
    try:
        # Adiciona alterações
        rodar_comando("git add bdados/query.parquet", pasta_clone)
        
        # Verifica se realmente teve mudança no arquivo
        resultado_status = subprocess.run("git status --porcelain", cwd=pasta_clone, shell=True, capture_output=True, text=True)
        if "bdados/query.parquet" not in resultado_status.stdout:
            print("[SISTEMA] O arquivo query.parquet está idêntico à nuvem. Não há o que subir! Processo encerrado.")
            return
            
        # Commit e Push
        rodar_comando(f'git commit -m "{mensagem_commit}"', pasta_clone)
        rodar_comando("git push origin main", pasta_clone)
        print("\n[SUCESSO] Sincronização com ProjetoBak concluída com sucesso! 🚀🚀")
    
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Ocorreu um problema ao enviar para o repositório no GitHub. Detalhe: {e}")

if __name__ == "__main__":
    main()
