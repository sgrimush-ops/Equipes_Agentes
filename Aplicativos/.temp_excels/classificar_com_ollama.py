import pandas as pd
import os
import json
import requests
import time

def classificar_lote_ollama(prompt_system, produtos_lote):
    # produtos_lote é uma lista de dicts com 'CODIGO_PRODUTO' e 'DESCRICAO_PRODUTO'
    texto_lote = "Lista de Produtos:\n"
    for p in produtos_lote:
        texto_lote += f"Código: {p['CODIGO_PRODUTO']} | Descrição: {p['DESCRICAO_PRODUTO']}\n"
        
    url = "http://localhost:11434/api/generate"
    
    # Exemplo esperado de resposta para a IA aprender
    exemplo_resposta = '''
    [
        {"codigo_produto": 123, "chave_categoria": 45},
        {"codigo_produto": 456, "chave_categoria": 12}
    ]
    '''
    
    prompt_completo = prompt_system + "\n\nIMPORTANTE: Responda APENAS com um array JSON válido, usando exatamente este formato:\n" + exemplo_resposta + "\n\n" + texto_lote
    
    payload = {
        "model": "gemma4:latest",
        "prompt": prompt_completo,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        resultado = response.json()['response']
        return json.loads(resultado)
    except Exception as e:
        print(f"Erro na API Ollama: {e}")
        return None

def main():
    print("Carregando planilhas...")
    df_fusao = pd.read_excel('fusao.xlsx')
    df_classificador = pd.read_excel('classificador.xlsx')
    
    categorias_texto = "CATEGORIAS DISPONÍVEIS (chave: categoria - departamento):\n"
    for _, row in df_classificador.iterrows():
        categorias_texto += f"{row['chave']}: {row['categoria']} - {row['departamento']}\n"
    
    prompt_system = (
        "Você é um especialista em classificação de produtos de supermercado/varejo.\n"
        "Abaixo está a lista de categorias disponíveis, mapeadas por uma 'chave' numérica.\n"
        "Sua tarefa é receber uma lista de produtos (código e descrição) e determinar a categoria mais adequada.\n"
        "Mesmo que a descrição possua abreviações (ex: CHOC PO = Cacau em pó), encontre a melhor correspondência.\n"
        "Se não encontrar uma correspondência óbvia, tente a categoria mais próxima ou genérica.\n\n"
        + categorias_texto
    )
    
    # Processa apenas o que falta ou tudo
    produtos = df_fusao.to_dict('records')
    tamanho_lote = 50
    resultados_totais = []
    
    print(f"Iniciando classificação de {len(produtos)} produtos em lotes de {tamanho_lote} usando OLLAMA (gemma4:latest)...")
    
    for i in range(0, len(produtos), tamanho_lote):
        lote = produtos[i:i+tamanho_lote]
        print(f"Processando lote {i//tamanho_lote + 1} de {(len(produtos)//tamanho_lote) + 1}...")
        
        matches = classificar_lote_ollama(prompt_system, lote)
        if matches:
            resultados_totais.extend(matches)
        
    print(f"Classificação concluída. {len(resultados_totais)} resultados recebidos.")
    
    df_resultados = pd.DataFrame(resultados_totais)
    if not df_resultados.empty:
        df_resultados['chave_categoria'] = df_resultados['chave_categoria'].astype(float)
        df_resultados['codigo_produto'] = pd.to_numeric(df_resultados['codigo_produto'], errors='coerce')
        
        df_fusao_atualizado = df_fusao.merge(df_resultados, left_on='CODIGO_PRODUTO', right_on='codigo_produto', how='left')
        df_fusao_atualizado['chave'] = df_fusao_atualizado['chave_categoria']
        df_fusao_atualizado = df_fusao_atualizado.merge(df_classificador, on='chave', how='left', suffixes=('', '_classificador'))
        df_fusao_atualizado['categoria'] = df_fusao_atualizado['categoria_classificador']
        df_fusao_atualizado['departamento'] = df_fusao_atualizado['departamento_classificador']
        
        colunas_para_remover = ['codigo_produto', 'chave_categoria', 'categoria_classificador', 'departamento_classificador']
        df_fusao_atualizado.drop(columns=[col for col in colunas_para_remover if col in df_fusao_atualizado.columns], inplace=True)
        
        nome_arquivo = 'fusao_classificada_ia_ollama.xlsx'
        df_fusao_atualizado.to_excel(nome_arquivo, index=False)
        print(f"Arquivo salvo com sucesso em {nome_arquivo}!")
    else:
        print("Nenhum resultado foi retornado com sucesso.")

if __name__ == "__main__":
    main()
