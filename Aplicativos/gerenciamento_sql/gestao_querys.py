if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

import pandas as pd

print("=== Gerenciador de Consultas SQL (TOTVS Consinco) ===")
print("Use o agente para criar suas consultas e salve-as na subpasta 'querys'.")
print("Em breve: Você pode expandir este script para rodar as queries diretamente via oracledb e gerar relatórios `.csv` aqui.")
