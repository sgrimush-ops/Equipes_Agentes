import os
import sys
import shutil
import urllib.request
import urllib.error
from sqlalchemy import create_engine, text

# Garante suporte a UTF-8 no Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_origem = os.path.join(base_dir, 'query.parquet')
    
    if not os.path.exists(arquivo_origem):
        print(f"[X] ERRO: O arquivo {arquivo_origem} não foi encontrado.")
        sys.exit(1)
        
    print("=" * 60)
    print("   SINCRONIZADOR DE DADOS - SERVIDOR LOCAL BAKLIZI")
    print("=" * 60)
    
    # 1. Copia para a pasta local do APP_Bak
    app_bak_dir = os.path.join(os.path.dirname(base_dir), 'APP_Bak')
    app_bdados = os.path.join(app_bak_dir, 'bdados')
    os.makedirs(app_bdados, exist_ok=True)
    destino_local = os.path.join(app_bdados, 'query.parquet')
    
    print(f"\n[1/3] Atualizando arquivo local em APP_Bak/bdados...")
    shutil.copy2(arquivo_origem, destino_local)
    print(f"      -> Copiado com sucesso para: {destino_local}")
    
    # 2. Atualiza tabela arquivos_sync no SQLite local
    sqlite_db = os.path.join(app_bdados, 'baklizi.db')
    if os.path.exists(sqlite_db):
        print(f"\n[2/3] Atualizando tabela arquivos_sync no banco local (SQLite)...")
        try:
            with open(arquivo_origem, 'rb') as f:
                conteudo_binario = f.read()
                
            engine_sqlite = create_engine(f"sqlite:///{sqlite_db.replace('\\', '/')}")
            with engine_sqlite.begin() as conn:
                try:
                    conn.execute(text("ALTER TABLE arquivos_sync ADD COLUMN conteudo BLOB;"))
                except Exception:
                    pass
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_arquivos_sync_nome ON arquivos_sync(nome);"))
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS arquivos_sync (
                        nome VARCHAR(255) PRIMARY KEY,
                        conteudo BLOB,
                        data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.execute(text("""
                    INSERT INTO arquivos_sync (nome, conteudo, data_atualizacao)
                    VALUES ('query.parquet', :conteudo, CURRENT_TIMESTAMP)
                    ON CONFLICT (nome) DO UPDATE
                    SET conteudo = EXCLUDED.conteudo,
                        data_atualizacao = CURRENT_TIMESTAMP;
                """), {"conteudo": conteudo_binario})
            print(f"      -> Banco SQLite local sincronizado com sucesso!")
        except Exception as e:
            print(f"      -> [!] Aviso ao atualizar SQLite local: {e}")
            
    # 3. Envia via API para o Servidor Moderno na VM (192.168.50.211:8000)
    server_url = "http://192.168.50.211:8000/api/admin/upload-query"
    print(f"\n[3/3] Enviando query.parquet para o Servidor Moderno ({server_url})...")
    try:
        with open(arquivo_origem, 'rb') as f:
            conteudo_binario = f.read()
            
        req = urllib.request.Request(
            server_url,
            data=conteudo_binario,
            headers={"Content-Type": "application/octet-stream"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                print(f"      -> [OK] Servidor interno atualizado e cache de produtos recarregado na RAM!")
            else:
                print(f"      -> [!] Resposta do servidor: {resp.status}")
    except urllib.error.URLError as e:
        print(f"      -> [!] Servidor VM 192.168.50.211 offline ou não alcançável no momento: {e}")
        print("         (Os arquivos locais já foram atualizados perfeitamente)")
        
    print("\n" + "=" * 60)
    print("[OK] SUCESSO: Sincronização de dados do servidor concluída!")
    print("=" * 60)

if __name__ == "__main__":
    main()
