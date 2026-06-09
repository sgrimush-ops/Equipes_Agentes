import os
import math
from pathlib import Path
from datetime import datetime
import pandas as pd

# Função para converter arquivo intermediário para CSV
def converter_para_csv(arquivo_parquet=None):
    """
    Lê o arquivo query.parquet e exporta resultado.csv, sem recalcular mínimos/máximos.
    """
    if arquivo_parquet is None:
        arquivo_parquet = Path(__file__).parent.parent / 'query.parquet'
    else:
        arquivo_parquet = Path(arquivo_parquet)
    if not arquivo_parquet.exists():
        print(f"ERRO: O arquivo '{arquivo_parquet}' não foi encontrado.")
        return
    print(f"Lendo dados de '{arquivo_parquet.name}'...")
    try:
        df = pd.read_parquet(arquivo_parquet)
    except Exception as e:
        print(f"Erro ao ler Parquet: {e}")
        return
    # Ordena se possível
    if 'CODIGO_PRODUTO' in df.columns and 'CODIGO_EMPRESA' in df.columns:
        df = df.sort_values(by=['CODIGO_PRODUTO', 'CODIGO_EMPRESA'], ascending=[True, True])
    arquivo_saida = Path('resultado.csv')
    try:
        df.to_csv(
            arquivo_saida,
            sep=';',
            encoding='utf-8-sig',
            index=False,
            decimal=',',
        )
        print(f"Exportação concluída: {arquivo_saida.name}")

    except Exception as e:
        print(f"Erro ao exportar CSV: {e}")

# --- TRAVA DE CONTEXTO ---
if __name__ == '__main__':
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

def calcular_min_max(row, dias_relatorio, capacidade_lookup, dias_seguranca_lookup):
    """
    Função dedicada a calcular as novas propriedades de Estoque Mínimo e Máximo.
    """
    try:
        embalagem = int(row['EMBL_TRANSFERENCIA_NUM'])
    except:
        embalagem = 1
    if embalagem <= 0:
        embalagem = 1
        
    try:
        venda_periodo = float(row['QTD_VENDIDA_NUM'])
    except:
        venda_periodo = 0.0

    try:
        codigo_produto = int(float(str(row['CODIGO_PRODUTO']).strip()))
    except:
        codigo_produto = -1

    try:
        codigo_empresa = int(float(str(row['CODIGO_EMPRESA']).strip()))
    except:
        codigo_empresa = -1

    venda_media = venda_periodo / dias_relatorio

    # 1. Obter estoque mínimo de segurança com base nas vendas (Regra 7: X dias de venda dependendo do departamento)
    dept = str(row.get('DEPARTAMENTO', '')).strip().upper()
    dias_seguranca = 5
    if dias_seguranca_lookup:
        dias_seguranca = dias_seguranca_lookup.get(dept, 5)

    minimo_dias = dias_seguranca * venda_media

    # 2. Definir o piso mínimo do produto (Regras 4 e 10)
    if embalagem == 1:
        min_floor = 5.0
        regra_minimo = 'UNITARIO_PISO_5'
    else:
        min_floor = 0.60 * embalagem
        regra_minimo = 'PISO_60_EMBALAGEM'

    # Mínimo obrigatório antes do ajuste de paridade
    min_floor_or_sales = max(minimo_dias, min_floor)

    # 3. Obter capacidade
    usa_semelhanca = False
    capacity = capacidade_lookup.get((codigo_produto, codigo_empresa), None)
    if capacity is None or capacity <= 0:
        # Tentar obter por semelhança de lojas
        STORE_TO_GROUP = {
            1: 'PP',
            4: 'P', 5: 'P', 7: 'P',
            8: 'M', 13: 'M', 14: 'M',
            2: 'G', 6: 'G', 11: 'G', 12: 'G', 17: 'G', 18: 'G',
            3: 'GG'
        }
        GROUP_STORES = {
            'PP': [1],
            'P': [4, 5, 7],
            'M': [8, 13, 14],
            'G': [2, 6, 11, 12, 17, 18],
            'GG': [3]
        }
        group = STORE_TO_GROUP.get(codigo_empresa, None)
        if group in ['P', 'M', 'G']:
            caps = [capacidade_lookup.get((codigo_produto, s)) for s in GROUP_STORES[group] if capacidade_lookup.get((codigo_produto, s), 0) > 0]
            if caps:
                capacity = int(round(sum(caps) / len(caps)))
                usa_semelhanca = True
        elif group == 'GG':
            caps = [capacidade_lookup.get((codigo_produto, s)) for s in GROUP_STORES['G'] if capacidade_lookup.get((codigo_produto, s), 0) > 0]
            if caps:
                capacity = int(round((sum(caps) / len(caps)) * 1.25))
                usa_semelhanca = True

    # Regra 8 & 9 & 10: Máximo
    usar_capacidade = False
    if capacity is not None and capacity > 0:
        # Regra 9: Venda média maior que a capacidade -> a venda deve ser respeitada (ignora capacidade)
        # E se o estoque mínimo for maior ou igual à capacidade, também devemos ignorar a capacidade
        if venda_media <= capacity and min_floor_or_sales < capacity:
            usar_capacidade = True

    if usar_capacidade:
        # Tentar encaixar o mínimo dentro da capacidade respeitando a margem de 30% a 40% (alvo 35%)
        # K_max é o maior número de embalagens que podemos retirar da capacidade sem violar o mínimo/piso
        if embalagem == 1:
            K_max = int(math.floor(capacity - min_floor_or_sales))
            K_target = int(round(0.35 * capacity))
        else:
            K_max = int(math.floor((capacity - min_floor_or_sales) / embalagem))
            K_target = int(round((0.35 * capacity) / embalagem))

        if K_max >= 1:
            # Conseguimos respeitar a capacidade como máximo!
            K = max(1, min(K_max, K_target))
            if embalagem == 1:
                min_novo = capacity - K
            else:
                min_novo = capacity - K * embalagem
            max_novo = capacity
            regra_maximo = 'CAPACIDADE_DIRETA_SEMELHANCA' if usa_semelhanca else 'CAPACIDADE_DIRETA'
        else:
            # Conflito: para manter o estoque mínimo/piso, precisamos de mais espaço que a capacidade.
            # O máximo deve subir além da capacidade por pelo menos 1 embalagem.
            min_novo = math.ceil(min_floor_or_sales)
            if embalagem == 1:
                max_novo = min_novo + 1
            else:
                max_novo = min_novo + embalagem
            regra_maximo = 'CAPACIDADE_ESTOURADA_MIN_ALTO_SEMELHANCA' if usa_semelhanca else 'CAPACIDADE_ESTOURADA_MIN_ALTO'
    else:
        # Sem capacidade cadastrada, ou capacidade ignorada por conta de venda alta/mínimo alto
        if capacity is not None and capacity > 0:
            if venda_media > capacity:
                regra_maximo = 'CAP_IGNORADA_VENDA_ALTA_SEMELHANCA' if usa_semelhanca else 'CAP_IGNORADA_VENDA_ALTA'
            else:
                regra_maximo = 'CAP_IGNORADA_MINIMO_ALTO_SEMELHANCA' if usa_semelhanca else 'CAP_IGNORADA_MINIMO_ALTO'
        else:
            regra_maximo = 'SEM_CAPACIDADE'

        # Formação padrão de estoque de segurança (alvo 35% de diferença do máximo, ou seja, max = min / 0.65)
        min_novo = math.ceil(min_floor_or_sales)
        if embalagem == 1:
            target_diff = math.ceil((0.35 / 0.65) * min_novo)
            max_novo = min_novo + target_diff
            max_novo = max(10, max_novo) # Piso de máximo para unitários (Regra 4)
            regra_maximo += '_ESTOQUE_SEGURANCA'
        else:
            target_diff = (0.35 / 0.65) * min_novo
            K = max(1, math.ceil(target_diff / embalagem))
            max_novo = min_novo + K * embalagem
            regra_maximo += '_ESTOQUE_SEGURANCA'

    # 4. Regras de paridade da embalagem (arredondamento do mínimo para cima)
    if embalagem % 2 == 0:
        if min_novo % 2 != 0:
            min_novo += 1
            regra_minimo += '_PAR'
    else:
        if min_novo % 2 == 0:
            min_novo += 1
            regra_minimo += '_IMPAR'

    # Se o mínimo subiu por conta de paridade ou arredondamento, garantir que o máximo é atualizado
    # para que a diferença continue múltipla da embalagem
    if embalagem == 1:
        if max_novo < min_novo + 1:
            max_novo = min_novo + 1
    else:
        diff = max_novo - min_novo
        if diff < embalagem:
            max_novo = min_novo + embalagem
        else:
            K = math.ceil(diff / embalagem)
            max_novo = min_novo + K * embalagem

    if min_novo > min_floor:
        regra_minimo += f'_VENDA_{dias_seguranca}_DIAS'

    cap_out = int(capacity) if (capacity is not None and capacity > 0 and not usa_semelhanca) else None

    return pd.Series([
        round(venda_media, 2),
        int(min_novo),
        int(max_novo),
        regra_minimo,
        regra_maximo,
        cap_out,
    ])

def solicitar_dias_relatorio():
    print("\n" + "=" * 50)
    print("          BASE DO RELATORIO DE VENDAS")
    print("=" * 50)
    print("Informe quantos dias de venda o relatorio traz.")
    print("Exemplos: 30 para venda de 30 dias, 60 para venda de 60 dias.")
    print("=" * 50)

    while True:
        entrada_dias = input("-> Digite a quantidade de dias do relatorio: ").strip()
        try:
            dias_relatorio = int(entrada_dias)
        except ValueError:
            print("x Valor invalido. Digite um numero inteiro maior que zero.")
            continue

        if dias_relatorio <= 0:
            print("x Valor invalido. Digite um numero inteiro maior que zero.")
            continue

        return dias_relatorio

def processar_calculos():
    dias_relatorio = solicitar_dias_relatorio()

    # Caminho corporativo centralizado
    arquivo_query = Path(__file__).parent.parent / 'import_querys' / 'query.parquet'
    
    if not arquivo_query.exists():
        print(f"Erro fatal: Não foi encontrado o arquivo fonte de dados no caminho corporativo: {arquivo_query}")
        return
        
    print(f"Carregando base volumosa corporativa '{arquivo_query.name}'...")
    df = pd.read_parquet(arquivo_query)
    df.columns = df.columns.astype(str).str.strip()
    
    # Filtro de Ativos (Garante que só produtos em linha na loja recebam sugestão)
    if 'ATIVO_COMPRA' in df.columns:
        print("Filtrando apenas produtos ATIVOS para as lojas...")
        df = df[df['ATIVO_COMPRA'] == 'A'].copy()
    else:
        print("[AVISO] Coluna 'ATIVO_COMPRA' não encontrada. Todos os itens serão considerados ativos!")

    # Remove CDs (empresa 15) do cálculo e exportação
    if 'CODIGO_EMPRESA' in df.columns:
        antes = len(df)
        df = df[df['CODIGO_EMPRESA'] != 15].copy()
        depois = len(df)
        print(f"Removidos {antes - depois} registros de CDs (empresa 15) do cálculo e exportação.")
    else:
        print("[AVISO] Coluna 'CODIGO_EMPRESA' não encontrada. Não foi possível remover CDs.")
    
    # Aplicando Regra Global nº 6 (Saneamento de Inteiros)
    print("Saneando extração de embalagens e ajustando preenchimentos...")
    df['EMBL_TRANSFERENCIA_NUM'] = df['EMBL_TRANSFERENCIA'].astype(str).str.extract(r'(\d+)')[0].fillna(1).astype(int)

    colunas_venda_possiveis = [
        'QTD_VENDIDA_PERIODO',
        'QTD_VENDIDA',
    ]
    coluna_venda = next((c for c in colunas_venda_possiveis if c in df.columns), None)

    if not coluna_venda:
        print(
            'Erro: coluna de venda nao encontrada. '
            'Esperado uma entre: QTD_VENDIDA_PERIODO, QTD_VENDIDA.'
        )
        return

    if pd.api.types.is_numeric_dtype(df[coluna_venda]):
        df['QTD_VENDIDA_NUM'] = pd.to_numeric(
            df[coluna_venda],
            errors='coerce',
        ).fillna(0.0)
    else:
        venda_txt = (
            df[coluna_venda]
            .astype(str)
            .str.strip()
            .str.replace(',', '.', regex=False)
        )
        df['QTD_VENDIDA_NUM'] = pd.to_numeric(
            venda_txt,
            errors='coerce',
        ).fillna(0.0)

    print(
        f"Venda media sera calculada as {coluna_venda} / {dias_relatorio} dias."
    )
    df['DIAS_RELATORIO_VENDA'] = dias_relatorio

    # Carregar capacidade.xlsx para construir o lookup de gôndola
    capacidade_path = Path(__file__).parent / 'capacidade.xlsx'
    capacidade_lookup = {}
    if capacidade_path.exists():
        print(f"Carregando capacidade de gôndola de '{capacidade_path.name}'...")
        try:
            df_cap = pd.read_excel(capacidade_path)
            df_cap.columns = df_cap.columns.astype(str).str.strip()
            df_cap['CODIGO_PRODUTO_INT'] = pd.to_numeric(df_cap['CODIGO_PRODUTO'], errors='coerce').fillna(-1).astype(int)
            df_cap['EMPRESA_INT'] = pd.to_numeric(df_cap['EMPRESA'], errors='coerce').fillna(-1).astype(int)
            df_cap['CAPACIDADE_GONDOLA_VAL'] = pd.to_numeric(df_cap['CAPACIDADE_GONDOLA'], errors='coerce').fillna(0).astype(int)
            
            for idx, row_cap in df_cap.iterrows():
                p_code = row_cap['CODIGO_PRODUTO_INT']
                e_code = row_cap['EMPRESA_INT']
                cap_val = row_cap['CAPACIDADE_GONDOLA_VAL']
                if p_code != -1 and e_code != -1:
                    capacidade_lookup[(p_code, e_code)] = cap_val
            print(f"Sucesso: {len(capacidade_lookup)} registros de capacidade mapeados.")
        except Exception as e:
            print(f"Erro ao carregar capacidade.xlsx: {e}")
    else:
        print(f"[AVISO] Arquivo '{capacidade_path.name}' não encontrado no diretório local. A regra de capacidade será ignorada.")
    
    # Carregar dias_seguranca.json para construir o lookup de segurança por departamento
    import json
    dias_seguranca_path = Path(__file__).parent / 'dias_seguranca.json'
    dias_seguranca_lookup = {}
    if dias_seguranca_path.exists():
        print(f"Carregando dias de segurança por departamento de '{dias_seguranca_path.name}'...")
        try:
            with open(dias_seguranca_path, 'r', encoding='utf-8') as f:
                dias_seguranca_lookup = json.load(f)
            # Normalizar chaves para maiúsculas
            dias_seguranca_lookup = {k.strip().upper(): v for k, v in dias_seguranca_lookup.items()}
            print(f"Sucesso: {len(dias_seguranca_lookup)} departamentos mapeados.")
        except Exception as e:
            print(f"Erro ao carregar dias_seguranca.json: {e}")
    else:
        print(f"[AVISO] Arquivo '{dias_seguranca_path.name}' não encontrado. O padrão de 5 dias será adotado.")
    
    # 2. Computar mínimos e máximos por linha
    print("Rodando cálculos matemáticos matriz...")
    df[
        [
            'VENDA_MEDIA',
            'NOVO_MINIMO',
            'NOVO_MAXIMO',
            'REGRA_MINIMO',
            'REGRA_MAXIMO',
            'CAPACIDADE_GONDOLA_SUG',
        ]
    ] = df.apply(
        lambda row: calcular_min_max(row, dias_relatorio, capacidade_lookup, dias_seguranca_lookup),
        axis=1,
    )
    
    # 3. Aplicar Filtro de Diferença Mínima de 3 unidades do original
    print("Filtrando alterações irrelevantes (< 3 unidades de diferença do original)...")
    df['NOVO_MINIMO'] = pd.to_numeric(df['NOVO_MINIMO'], errors='coerce').fillna(0).astype(int)
    df['NOVO_MAXIMO'] = pd.to_numeric(df['NOVO_MAXIMO'], errors='coerce').fillna(0).astype(int)
    df['QUANTIDADE_ESTOQUE_MINIMO'] = pd.to_numeric(df['QUANTIDADE_ESTOQUE_MINIMO'], errors='coerce').fillna(0).astype(int)
    df['QUANTIDADE_ESTOQUE_MAXIMO'] = pd.to_numeric(df['QUANTIDADE_ESTOQUE_MAXIMO'], errors='coerce').fillna(0).astype(int)

    # Se a sugestão diferir por menos de 3 unidades do original, revertemos para o valor original,
    # EXCETO se o valor original estiver violando o piso mínimo (60% da embalagem ou 5 para unitários)
    min_floor = df['EMBL_TRANSFERENCIA_NUM'].apply(lambda emb: 5.0 if emb == 1 else math.ceil(0.60 * emb))
    muda_min = ((df['NOVO_MINIMO'] - df['QUANTIDADE_ESTOQUE_MINIMO']).abs() >= 3) | (df['QUANTIDADE_ESTOQUE_MINIMO'] < min_floor)
    df.loc[~muda_min, 'NOVO_MINIMO'] = df.loc[~muda_min, 'QUANTIDADE_ESTOQUE_MINIMO']
    
    muda_max = (df['NOVO_MAXIMO'] - df['QUANTIDADE_ESTOQUE_MAXIMO']).abs() >= 3
    df.loc[~muda_max, 'NOVO_MAXIMO'] = df.loc[~muda_max, 'QUANTIDADE_ESTOQUE_MAXIMO']

    # Re-aplicar regras de paridade e proporcionalidade no resultado final
    print("Re-aplicando regras de paridade e proporcionalidade no resultado final...")
    is_even_emb = (df['EMBL_TRANSFERENCIA_NUM'] % 2 == 0)
    is_odd_emb = ~is_even_emb

    # 1. Paridade do Mínimo
    # Embalagem par -> Minimo deve ser par
    df.loc[is_even_emb & (df['NOVO_MINIMO'] % 2 != 0), 'NOVO_MINIMO'] += 1
    # Embalagem impar -> Minimo deve ser impar
    df.loc[is_odd_emb & (df['NOVO_MINIMO'] % 2 == 0), 'NOVO_MINIMO'] += 1

    # 2. Proporcionalidade do Máximo
    # Para cada linha, recalcular o Maximo para manter a proporcionalidade da embalagem
    for idx, row in df.iterrows():
        emb = int(row['EMBL_TRANSFERENCIA_NUM'])
        n_min = int(row['NOVO_MINIMO'])
        n_max = int(row['NOVO_MAXIMO'])
        
        if emb == 1:
            if n_max < n_min + 1:
                df.at[idx, 'NOVO_MAXIMO'] = n_min + 1
        else:
            diff = n_max - n_min
            if diff < emb:
                df.at[idx, 'NOVO_MAXIMO'] = n_min + emb
            else:
                K = math.ceil(diff / emb)
                df.at[idx, 'NOVO_MAXIMO'] = n_min + K * emb

    # 3. Conversão para inteiros
    df['NOVO_MINIMO'] = df['NOVO_MINIMO'].astype(int)
    df['NOVO_MAXIMO'] = df['NOVO_MAXIMO'].astype(int)

    # Filtrar produtos sem alteração (onde tanto o novo min quanto o novo max são iguais aos originais)
    sem_mudanca = (df['NOVO_MINIMO'] == df['QUANTIDADE_ESTOQUE_MINIMO']) & (df['NOVO_MAXIMO'] == df['QUANTIDADE_ESTOQUE_MAXIMO'])
    df = df[~sem_mudanca].copy()
    print(f"Itens sem alteração relevante expurgados. Itens com alteração: {len(df)}")
    
    # 4. Input Terminal
    print("\n" + "="*50)
    print("           OPÇÕES DE RELATÓRIO / EXPORTAÇÃO")
    print("="*50)
    print("[1] - Gerar APENAS sugestões para AUMENTAR")
    print("      (Filtra os casos onde o Novo Mínimo Calculado é maior que o Atual (origem))")
    print("\n[2] - Gerar TOTAL")
    print("      (Exporta a base total, englobando altas e baixas com alteração relevante)")
    print("="*50)
    
    while True:
        opcao = input("-> Digite a opção escolhida (1 ou 2): ").strip()
        if opcao in ['1', '2']:
            break
        print("x Opção inválida. Digite 1 ou 2.")
        
    if opcao == '1':
        print("\n=> Filtrando exclusivamente os produtos apontando para AUMENTO...")
        df_resultado = df[df['NOVO_MINIMO'] > df['QUANTIDADE_ESTOQUE_MINIMO']].copy()
    else:
        print("\n=> Exportando todos os produtos com alteração relevante...")
        df_resultado = df.copy()

    print(f"Total de linhas prontas para exportação: {len(df_resultado)}")
    
    # 5. Refaz o filtro de ativos para garantir que só exporta produtos ativos
    if 'ATIVO_COMPRA' in df_resultado.columns:
        antes = len(df_resultado)
        df_resultado = df_resultado[df_resultado['ATIVO_COMPRA'] == 'A'].copy()
        depois = len(df_resultado)
        print(f"Filtro final de ativos: de {antes} para {depois} linhas ativas exportadas.")
    else:
        print("[AVISO] Coluna 'ATIVO_COMPRA' não encontrada no resultado. Exportando todos os itens!")

    # Adiciona coluna 'Status' como última coluna, baseada em STATUS_COMPRA da query.parquet
    colunas_finais = [
        'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'EMBL_TRANSFERENCIA',
        'CODIGO_EMPRESA', 'NOVO_MINIMO', 'NOVO_MAXIMO',
        'DIAS_RELATORIO_VENDA', 'VENDA_MEDIA','QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO',
        'REGRA_MINIMO', 'REGRA_MAXIMO', 'CAPACIDADE_GONDOLA_SUG'
    ]
    cols_existentes = [c for c in colunas_finais if c in df_resultado.columns]
    df_export = df_resultado[cols_existentes].copy()
    df_export = df_export.rename(columns={'CAPACIDADE_GONDOLA_SUG': 'capacidade_gondola'})
    
    if 'STATUS_COMPRA' in df.columns:
        if 'CODIGO_PRODUTO' in df_export.columns and 'CODIGO_EMPRESA' in df_export.columns:
            df_export = df_export.merge(
                df[['CODIGO_PRODUTO', 'CODIGO_EMPRESA', 'STATUS_COMPRA']],
                on=['CODIGO_PRODUTO', 'CODIGO_EMPRESA'],
                how='left',
                suffixes=('', '_orig')
            )
            df_export['Status'] = df_export['STATUS_COMPRA']
            df_export = df_export.drop(columns=[c for c in df_export.columns if c.startswith('STATUS_COMPRA') and c != 'Status'])
        else:
            df_export['Status'] = df['STATUS_COMPRA']
    else:
        df_export['Status'] = 'DESCONHECIDO'
        
    # Reordenar colunas para garantir que 'capacidade_gondola' seja a última
    cols_order = [c for c in df_export.columns if c != 'capacidade_gondola'] + ['capacidade_gondola']
    df_export = df_export[cols_order]
        
    # Ordena pelo código do produto e depois pela empresa
    if 'CODIGO_PRODUTO' in df_export.columns and 'CODIGO_EMPRESA' in df_export.columns:
        df_export = df_export.sort_values(by=['CODIGO_PRODUTO', 'CODIGO_EMPRESA'], ascending=[True, True])
    
    print("Exportando os resultados para 'resultado.csv'...")
    arquivo_saida = Path('resultado.csv')

    try:
        df_export.to_csv(
            arquivo_saida,
            sep=';',
            encoding='utf-8-sig',
            index=False,
            decimal=',',
        )
    except PermissionError:
        arquivo_saida = Path(
            f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        print(
            "Aviso: 'resultado.csv' está em uso. "
            f"Exportando em '{arquivo_saida.name}'."
        )
        df_export.to_csv(
            arquivo_saida,
            sep=';',
            encoding='utf-8-sig',
            index=False,
            decimal=',',
        )
    
    print("\n[SUCESSO] Trabalho finalizado com sucesso!")

if __name__ == "__main__":
    os.system('cls')
    print("\n" + "="*50)
    print("       GERENCIADOR DE ESTOQUE MÍNIMO E MÁXIMO")
    print("="*50)
    print("Executando cálculo completo (Cálculos + Exportação)...")
    processar_calculos()
