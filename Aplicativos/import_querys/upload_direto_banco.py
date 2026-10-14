import os
import sys
import urllib.request
import urllib.error
import json

# Garante suporte a UTF-8 no Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_origem = os.path.join(base_dir, 'query.parquet')
    
    if not os.path.exists(arquivo_origem):
        print(f"[X] ERRO: O arquivo {arquivo_origem} não foi encontrado.")
        sys.exit(1)
        
    tamanho_mb = round(os.path.getsize(arquivo_origem) / (1024 * 1024), 2)
    print("=" * 60)
    print("   SINCRONIZADOR SILENCIOSO - SERVIDOR APP_BAK (192.168.50.211)")
    print("=" * 60)
    print(f"[*] Arquivo detectado: {arquivo_origem} ({tamanho_mb} MB)")
    
    server_url = "http://192.168.50.211:8000/api/admin/upload-query"
    print(f"\n[1/1] Enviando query.parquet diretamente para o Servidor ({server_url})...")
    
    try:
        with open(arquivo_origem, 'rb') as f:
            conteudo_binario = f.read()
            
        req = urllib.request.Request(
            server_url,
            data=conteudo_binario,
            headers={"Content-Type": "application/octet-stream"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            if resp.status == 200:
                corpo = resp.read().decode('utf-8')
                try:
                    res_json = json.loads(corpo)
                    msg = res_json.get("message", "Atualizado com sucesso")
                except Exception:
                    msg = corpo
                print(f"      -> [OK] Sucesso! {msg}")
                print(f"      -> [OK] Servidor atualizado silenciosamente (cache recarregado e ruptura disparada no servidor)!")
            else:
                print(f"      -> [!] Resposta do servidor: {resp.status}")
                sys.exit(1)
    except urllib.error.URLError as e:
        print(f"      -> [X] Erro ao conectar ao servidor 192.168.50.211:8000: {e}")
        print("         Verifique se o servidor do APP_Bak está ativo na rede.")
        sys.exit(1)
    except Exception as e:
        print(f"      -> [X] Falha inesperada durante o upload: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[OK] Sincronização concluída com sucesso e sem interrupção de usuários!")
    print("=" * 60)

if __name__ == "__main__":
    main()
