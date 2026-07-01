import pandas as pd
import os
import json
import time
from pydantic import BaseModel
from google import genai
from google.genai import types

class ItemMatch(BaseModel):
    codigo_produto: str
    chave_categoria: int

class MatchResult(BaseModel):
    matches: list[ItemMatch]

def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("ERRO: A variável de ambiente GEMINI_API_KEY não foi encontrada.")
        print("Defina a variável antes de rodar, ex: set GEMINI_API_KEY=sua_chave")
        exit(1)
    return key

def classificar_lote(client, prompt_system, produtos_lote):
    # produtos_lote é uma lista de dicts com 'CODIGO_PRODUTO' e 'DESCRICAO_PRODUTO'
    texto_lote = "Lista de Produtos:\n"
    for p in produtos_lote:
        texto_lote += f"Código: {p['CODIGO_PRODUTO']} | Descrição: {p['DESCRICAO_PRODUTO']}\n"
        
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=texto_lote,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_system,
                    response_mime_type="application/json",
                    response_schema=MatchResult,
                    temperature=0.0
                ),
            )
            return json.loads(response.text)['matches']
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"Aviso: Limite da API Gratuita atingido. Aguardando 65 segundos antes de tentar novamente... (Tentativa {tentativa+1}/{tentativas})")
                time.sleep(65)
            else:
                print(f"Erro na API Gemini: {e}")
                return None
    
    print("Falha após múltiplas tentativas devido a rate limit.")
    return None

def main():
    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    
    print("Carregando planilhas...")
    df_fusao = pd.read_excel('fusao.xlsx')
    df_classificador = pd.read_excel('classificador.xlsx')
    
    # Montar a string de categorias para o system prompt
    categorias_texto = "CATEGORIAS DISPONÍVEIS (chave: categoria - departamento):\n"
    for _, row in df_classificador.iterrows():
        categorias_texto += f"{row['chave']}: {row['categoria']} - {row['departamento']}\n"
    
    prompt_system = (
        "Você é um especialista em classificação de produtos de supermercado/varejo.\n"
        "Abaixo está a lista de categorias disponíveis, mapeadas por uma 'chave' numérica.\n"
        "Sua tarefa é receber uma lista de produtos (código e descrição) e determinar a categoria mais adequada.\n"
        "Mesmo que a descrição possua abreviações (ex: CHOC PO = Cacau em pó), encontre a melhor correspondência.\n"
        "Sempre retorne APENAS a lista no formato JSON solicitado, vinculando o codigo_produto com a chave_categoria.\n"
        "Se não encontrar uma correspondência óbvia, tente a categoria mais próxima ou genérica.\n\n"
        + categorias_texto
    )
    
    # Preparar dados
    # Para o teste, vamos usar apenas os primeiros 20 itens.
    # Quando for para valer, processaremos tudo.
    TESTE_MODO = False
    if TESTE_MODO:
        produtos = df_fusao.head(20).to_dict('records')
        print("MODO TESTE ATIVADO: Processando apenas os primeiros 20 produtos.")
    else:
        produtos = df_fusao.to_dict('records')
    
    tamanho_lote = 50
    resultados_totais = []
    
    print(f"Iniciando classificação de {len(produtos)} produtos em lotes de {tamanho_lote}...")
    
    for i in range(0, len(produtos), tamanho_lote):
        lote = produtos[i:i+tamanho_lote]
        print(f"Processando lote {i//tamanho_lote + 1}...")
        
        matches = classificar_lote(client, prompt_system, lote)
        if matches:
            resultados_totais.extend(matches)
        
        time.sleep(4) # Espera 4 segundos para não estourar o rate limit
        
    print(f"Classificação concluída. {len(resultados_totais)} resultados recebidos.")
    
    # Mesclar resultados
    df_resultados = pd.DataFrame(resultados_totais)
    if not df_resultados.empty:
        df_resultados['chave_categoria'] = df_resultados['chave_categoria'].astype(float)
        # Forçar o código do produto para inteiro para bater com a planilha
        df_resultados['codigo_produto'] = pd.to_numeric(df_resultados['codigo_produto'], errors='coerce')
        
        # Faz um merge com df_fusao
        df_fusao_atualizado = df_fusao.merge(df_resultados, left_on='CODIGO_PRODUTO', right_on='codigo_produto', how='left')
        
        # Atualiza a coluna 'chave' original com a nova 'chave_categoria'
        df_fusao_atualizado['chave'] = df_fusao_atualizado['chave_categoria']
        
        # Faz um merge com o classificador para trazer as descrições de categoria e departamento
        df_fusao_atualizado = df_fusao_atualizado.merge(df_classificador, on='chave', how='left', suffixes=('', '_classificador'))
        
        # Preenche as colunas categoria e departamento originais
        df_fusao_atualizado['categoria'] = df_fusao_atualizado['categoria_classificador']
        df_fusao_atualizado['departamento'] = df_fusao_atualizado['departamento_classificador']
        
        # Remove colunas auxiliares
        colunas_para_remover = ['codigo_produto', 'chave_categoria', 'categoria_classificador', 'departamento_classificador']
        df_fusao_atualizado.drop(columns=[col for col in colunas_para_remover if col in df_fusao_atualizado.columns], inplace=True)
        
        nome_arquivo = 'fusao_classificada_ia_TESTE.xlsx' if TESTE_MODO else 'fusao_classificada_ia.xlsx'
        df_fusao_atualizado.to_excel(nome_arquivo, index=False)
        print(f"Arquivo salvo com sucesso em {nome_arquivo}!")
    else:
        print("Nenhum resultado foi retornado com sucesso.")

if __name__ == "__main__":
    main()
