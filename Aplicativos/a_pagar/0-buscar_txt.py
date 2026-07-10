import os
import shutil
import subprocess
import sys

def main():
    source = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\a_pagar.txt"
    destination_folder = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\a_pagar"
    destination_file = os.path.join(destination_folder, "a_pagar.txt")
    
    print(f"Buscando arquivo em: {source}")
    
    if not os.path.exists(source):
        print("Erro: O arquivo de origem não foi encontrado.")
        return
        
    os.makedirs(destination_folder, exist_ok=True)
    
    try:
        shutil.copy2(source, destination_file)
        print(f"Sucesso: Arquivo 'a_pagar.txt' copiado para {destination_folder}")

        scripts = [
            os.path.join(destination_folder, "1-compras_a_pagar.py"),
            os.path.join(destination_folder, "2-dashboard_a_pagar.py"),
        ]

        for script in scripts:
            if not os.path.exists(script):
                print(f"Erro: Script não encontrado: {script}")
                return

            print(f"Executando: {os.path.basename(script)}")
            result = subprocess.run([sys.executable, script], cwd=destination_folder)
            if result.returncode != 0:
                print(f"Erro: {os.path.basename(script)} finalizou com código {result.returncode}")
                return

        print("Sequência concluída com sucesso: 1 e 2 executados após a cópia.")
    except Exception as e:
        print(f"Erro ao copiar o arquivo: {e}")

if __name__ == "__main__":
    main()
