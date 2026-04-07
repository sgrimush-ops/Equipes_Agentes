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
arquivo_entrada = Path(r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

if not arquivo_entrada.exists():
    print(f"Erro: O arquivo Parquet {arquivo_entrada} não foi encontrado!")
    sys.exit(1)

print("Parquet de rupturas localizado!")

# 1A. Executar a dashboard de compradores
print("Executando a geração do Dashboard de Compradores...")
try:
    script_dashboard = base_dir / "dashboard_comprador.py"
    subprocess.run([sys.executable, str(script_dashboard)], check=True)
    print("Dashboard de compradores gerado e atualizado.")
except Exception as e:
    print(f"Ocorreu um erro ao encadear o dashboard de compradores: {e}")

# 1B. Executar o ranking de lojas
print("Executando a geração do Ranking de Lojas...")
try:
    script_loja = base_dir / "dashboard_loja.py"
    subprocess.run([sys.executable, str(script_loja)], check=True)
    print("Ranking de lojas gerado e atualizado.")
except Exception as e:
    print(f"Ocorreu um erro ao encadear o ranking de lojas: {e}")

# 2. Executar a dashboard detalhada
print("Executando a geração do Dashboard Detalhado...")
try:
    script_detalhado = base_dir / "dashboard_detalhado.py"
    subprocess.run([sys.executable, str(script_detalhado)], check=True)
    print("Dashboard detalhado gerado e atualizado.")
except Exception as e:
    print(f"Ocorreu um erro ao encadear o dashboard detalhado: {e}")
