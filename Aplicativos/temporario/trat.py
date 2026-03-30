import pandas as pd
from pathlib import Path
import os

def main():
    base_dir = Path(__file__).parent.resolve()
    os.chdir(base_dir)

    arquivo_excel = base_dir / "temp.xlsx"

    if not arquivo_excel.exists():
        print(f"Erro: Arquivo {arquivo_excel.name} não encontrado.")
        return

    print(f"Lendo {arquivo_excel.name}...")
    df = pd.read_excel(arquivo_excel)

    # Identificar nome exato das colunas
    col_codigo = next((c for c in df.columns if 'cod' in str(c).lower()), 'Codigo')
    col_mercadoria = next((c for c in df.columns if 'merc' in str(c).lower() or 'desc' in str(c).lower()), 'Mercadoria')

    # Agrupamentos de lojas conforme a regra de negócio
    lojas_pequenas = [4, 5, 7, 8, 14]
    lojas_medias = [12, 13, 18]
    lojas_grandes = [2, 3, 6, 11, 17]
    todas_lojas = lojas_pequenas + lojas_medias + lojas_grandes

    rows = []

    for idx, row in df.iterrows():
        codigo = row.get(col_codigo, '')
        merc = str(row.get(col_mercadoria, '')).strip()

        # Função auxiliar para verificar presença de 'A' (ou 'X' por robustez) na loja
        def is_active(col):
            val = row.get(col) if col in df.columns else row.get(str(col), '')
            return str(val).strip().upper() in ['A', 'X']

        # Loja 1 é tratada individualmente independente do agrupamento
        val_loja_1 = 'A' if is_active(1) else 'I'
        rows.append({
            'Código Empresa': '1', 
            'Empresa : Produto': merc,
            'Código Produto': codigo,
            'Status': val_loja_1
        })

        # Contagens de ativos por agrupamento
        peq_a = sum(1 for c in lojas_pequenas if is_active(c))
        med_a = sum(1 for c in lojas_medias if is_active(c))
        gra_a = sum(1 for c in lojas_grandes if is_active(c))

        # Teste das condicões macro definidas
        is_TA = (peq_a == len(lojas_pequenas)) and (med_a == len(lojas_medias)) and (gra_a == len(lojas_grandes))
        is_TIP = (peq_a == 0) and (med_a == len(lojas_medias)) and (gra_a == len(lojas_grandes))
        is_TIM = (peq_a == 0) and (med_a == 0) and (gra_a == len(lojas_grandes))

        if is_TA:
            rows.append({
                'Código Empresa': 'G', 
                'Empresa : Produto': merc,
                'Código Produto': codigo,
                'Status': 'TA'
            })
        elif is_TIP:
            rows.append({
                'Código Empresa': 'P', 
                'Empresa : Produto': merc,
                'Código Produto': codigo,
                'Status': 'TIP'
            })
        elif is_TIM:
            rows.append({
                'Código Empresa': 'M', 
                'Empresa : Produto': merc,
                'Código Produto': codigo,
                'Status': 'TIM'
            })
        else:
            # Sem agrupamento padrão claro -> registrar individualmente para cada filial do interior
            for loc in todas_lojas:
                st = 'A' if is_active(loc) else 'I'
                rows.append({
                    'Código Empresa': str(loc), 
                    'Empresa : Produto': merc,
                    'Código Produto': codigo,
                    'Status': st
                })

    df_out = pd.DataFrame(rows)
    arquivo_saida = base_dir / "mix_tratado_agrupado.xlsx"
    print(f"\nTotal processado: {len(df_out)} registros.")
    print(f"Salvando resultados em {arquivo_saida.name}...")
    df_out.to_excel(arquivo_saida, index=False)
    print("Sucesso! Planilha pronta para o robô ou avaliação.")

if __name__ == '__main__':
    main()
