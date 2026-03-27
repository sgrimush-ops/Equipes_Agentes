if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pandas as pd
from pathlib import Path



# O rpcompra.csv não é mais utilizado. O Pipeline agora se alimenta do query.parquet
base_dir = Path(__file__).parent

arquivo_entrada = Path('c:/Users/Alessandro.soares.BAKLIZI/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet')

import sys
import subprocess

if not arquivo_entrada.exists():
    print(f"Erro: O arquivo Parquet {arquivo_entrada} não foi encontrado!")
    sys.exit(1)

print("Parquet de rupturas localizado!")

# Executar a dashboard logo em sequência
print("Executando a geração do Dashboard...")
try:
    script_dashboard = base_dir / "gerar_dashboard_comprador.py"
    subprocess.run([sys.executable, str(script_dashboard)], check=True)
    print("Dashboard gerado e atualizado.")
except Exception as e:
    print(f"Ocorreu um erro ao encadear o dashboard: {e}")
<<<<<<< HEAD

# Executar a dashboard detalhada
print("Executando a geração do Dashboard Detalhado...")
try:
    script_detalhado = base_dir / "dashboard_detalhado.py"
    subprocess.run([sys.executable, str(script_detalhado)], check=True)
    print("Dashboard detalhado gerado e atualizado.")
except Exception as e:
    print(f"Ocorreu um erro ao encadear o dashboard detalhado: {e}")
=======
>>>>>>> c0d55e2759e64d63ae0ea39839df6f48aa226883
