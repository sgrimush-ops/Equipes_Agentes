import os
import shutil

def main():
    source = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\a_pagar_empresa.txt"
    destination_folder = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\a_pagar_empresa"
    destination_file = os.path.join(destination_folder, "a_pagar_empresa.txt")
    
    print(f"Buscando arquivo em: {source}")
    
    if not os.path.exists(source):
        print("Erro: O arquivo de origem 'a_pagar_empresa.txt' não foi encontrado na pasta import_querys.")
        print("Lembre-se de salvar a exportação do Consinco na pasta import_querys antes de executar este script.")
        return
        
    os.makedirs(destination_folder, exist_ok=True)
    
    try:
        shutil.copy2(source, destination_file)
        print(f"Sucesso: Arquivo 'a_pagar_empresa.txt' copiado para {destination_folder}")
    except Exception as e:
        print(f"Erro ao copiar o arquivo: {e}")

if __name__ == "__main__":
    main()
