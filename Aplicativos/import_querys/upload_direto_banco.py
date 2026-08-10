import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Carrega as variáveis de ambiente do .env na mesma pasta
    env_path = os.path.join(base_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        print("[ALERTA] Arquivo .env não encontrado.")
    
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ ERRO: A variável DATABASE_URL não foi encontrada. Configure-a no arquivo .env.")
        sys.exit(1)
        
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
        
    arquivo_origem = os.path.join(base_dir, 'query.parquet')
    
    if not os.path.exists(arquivo_origem):
        print(f"❌ ERRO: O arquivo {arquivo_origem} não foi encontrado.")
        sys.exit(1)
        
    print("="*60)
    print(" Upload Automático para ProjetoBak (Via Banco de Dados) ")
    print("="*60)
    print(f"\n[INFO] Conectando ao banco de dados e preparando envio de query.parquet...")
    
    try:
        engine = create_engine(
            db_url,
            connect_args={"sslmode": "require"},
            pool_size=5,
            max_overflow=2
        )
        
        with open(arquivo_origem, 'rb') as f:
            conteudo_binario = f.read()
            
        with engine.begin() as conn:
            # Garante que a tabela existe caso seja a primeira vez e o site ainda não tenha criado
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS arquivos_sync (
                    nome VARCHAR(255) PRIMARY KEY,
                    conteudo BYTEA NOT NULL,
                    data_atualizacao TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """))
            
            # Atualiza ou insere o arquivo
            query = text("""
                INSERT INTO arquivos_sync (nome, conteudo, data_atualizacao)
                VALUES (:nome, :conteudo, NOW())
                ON CONFLICT (nome) DO UPDATE 
                SET conteudo = EXCLUDED.conteudo,
                    data_atualizacao = EXCLUDED.data_atualizacao;
            """)
            
            conn.execute(query, {"nome": "query.parquet", "conteudo": conteudo_binario})
            
        print(f"\n✅ SUCESSO: O arquivo query.parquet foi enviado para a base de dados!")
        print("Da próxima vez que o site ProjetoBak for carregado, ele vai extrair esse novo arquivo.")
        
    except Exception as e:
        print(f"\n❌ ERRO FATAL: Falha ao sincronizar arquivo com o banco de dados. {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
