import os
import shutil
import subprocess
import sys

def build():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    spec_file = os.path.join(base_dir, "Mini-GAM.spec")
    
    # 1. Garante que a planilha de amostra (.xlsx) está criada
    print("GERANDO PLANILHA DE AMOSTRA...")
    try:
        from create_sample_excel import gerar_planilha
        gerar_planilha()
    except Exception as e:
        print(f"Aviso ao gerar .xlsx: {e}")

    # 2. Executa PyInstaller
    print("EMPACOTANDO COM PYINSTALLER...")
    cmd = [sys.executable, "-m", "PyInstaller", "--clean", "-y", spec_file]
    subprocess.run(cmd, check=True, cwd=base_dir)

    # 3. Prepara a pasta final do Pendrive com todos os arquivos necessários
    dist_dir = os.path.join(base_dir, "dist", "Mini-GAM_Pendrive")
    
    # Copia a pasta 'Dados' e arquivos avulsos para dentro do pacote do pendrive
    dados_src = os.path.join(base_dir, "Dados")
    dados_dst = os.path.join(dist_dir, "Dados")
    if os.path.exists(dados_src):
        os.makedirs(dados_dst, exist_ok=True)
        for item in os.listdir(dados_src):
            if item.startswith("~$") or item.endswith(".lock"):
                continue
            s = os.path.join(dados_src, item)
            d = os.path.join(dados_dst, item)
            if os.path.isfile(s):
                try:
                    shutil.copy2(s, d)
                except Exception as err:
                    print(f"Aviso ao copiar {item}: {err}")

    for f in ["conferencia.xlsx", "conferencia.csv", "README_MINI_GAM.md"]:
        if f.startswith("~$"): continue
        src = os.path.join(base_dir, f)
        if os.path.exists(src):
            try:
                shutil.copy2(src, dist_dir)
            except Exception:
                pass

    print("\n" + "="*60)
    print("[SUCESSO] PACOTE PARA PENDRIVE GERADO COM SUCESSO!")
    print(f"[PACOTE] Copie todo o conteudo da pasta abaixo diretamente para seu Pendrive:")
    print(f"         {dist_dir}")
    print("="*60)

if __name__ == "__main__":
    build()
