if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pandas as pd
from pathlib import Path
import sys
import subprocess

# O rpcompra.csv não é mais utilizado. O Pipeline agora se alimenta do query.parquet
base_dir = Path(__file__).parent
arquivo_entrada = Path(r'C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

if not arquivo_entrada.exists():
    print(f"Erro: O arquivo Parquet {arquivo_entrada} não foi encontrado!")
    sys.exit(1)

print("Parquet de rupturas localizado!")


def rodar_script(nome, caminho):
    print(f"Executando: {nome}...")
    resultado = subprocess.run([sys.executable, str(caminho)], capture_output=True, text=True)
    if resultado.returncode != 0:
        print(f"[ERRO] Falha ao executar {nome}!")
        print("Saída padrão:")
        print(resultado.stdout)
        print("Saída de erro:")
        print(resultado.stderr)
        sys.exit(1)
    else:
        print(f"{nome} executado com sucesso.")
        print(resultado.stdout)


# 1. Executar a dashboard detalhada
script_detalhado = base_dir / "4-dashboard_detalhado.py"
rodar_script("Dashboard Detalhado", script_detalhado)

# 2. Executar a dashboard de compradores
script_dashboard = base_dir / "2-dashboard_comprador.py"
rodar_script("Dashboard de Compradores", script_dashboard)

# 3. Executar o ranking de lojas
script_loja = base_dir / "3-dashboard_loja.py"
rodar_script("Ranking de Lojas", script_loja)

# limpar tela com cls e depois msg de finalizado
os.system('cls')
print("[OK] Processo concluído!")
