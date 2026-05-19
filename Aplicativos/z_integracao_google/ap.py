from pathlib import Path
from dotenv import load_dotenv
from modulo_drive import listar_arquivos_drive
from modulo_gmail import listar_ultimos_emails
from modulo_appsheet import consultar_tabela_appsheet

def main():
    """
    Função principal do projeto integracao_google.
    Ela carrega as variáveis de ambiente e faz um teste das integrações criadas.
    """
    print("====================================")
    print(" INÍCIO: Integração Google e AppSheet")
    print("====================================")

    # Verifica e carrega o arquivo .env
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        print("Aviso: Arquivo .env não encontrado. Algumas credenciais como AppSheet podem falhar.")

    # Cria diretório temporário seguindo as rules.md
    tmp_dir = Path(__file__).parent / "tmp"
    tmp_dir.mkdir(exist_ok=True)
    
    try:
        print("\n--- 1. Testando Acesso ao Google Drive ---")
        listar_arquivos_drive(limite=3)
        
        print("\n--- 2. Testando Acesso ao Gmail ---")
        listar_ultimos_emails(limite=3)

        print("\n--- 3. Módulo AppSheet ---")
        print("Acesse o arquivo 'modulo_appsheet.py' diretamente ou passe as credenciais e nome de tabela para consultar.")

    except Exception as e:
        print(f"\n[ERRO]: Ocorreu uma exceção genérica no ap.py -> {e}")

if __name__ == "__main__":
    main()
