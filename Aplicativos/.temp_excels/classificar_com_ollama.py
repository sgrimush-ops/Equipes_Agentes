import pandas as pd
import os
import requests
import time
import re

def classificar_lote_ollama(prompt_system, produtos_lote):
    texto_lote = "\n".join([f"ID_{p['CODIGO_PRODUTO']}: {p['DESCRICAO_PRODUTO']}" for p in produtos_lote])
        
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "gemma4:latest",
        "system": prompt_system,
        "prompt": texto_lote,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192,
            "num_predict": 1024
        }
    }
    
    matches = []
    t0 = time.time()
    
    try:
        response = requests.post(url, json=payload, timeout=900)
        response.raise_for_status()
        
        data = response.json()
        texto_resposta = data.get('response', '')
        
        # Processa cada linha retornada
        for linha in texto_resposta.splitlines():
            linha_limpa = linha.strip()
            if linha_limpa:
                match = re.search(r'(?:ID_)?(\d+)\s*(?:->|[:=-]|\s)\s*(\d+)', linha_limpa)
                if match:
                    cod = int(match.group(1))
                    chave = int(match.group(2))
                    matches.append({'codigo_produto': cod, 'chave_categoria': chave})
                    print(f"    ✔️ ID {cod} -> Categoria {chave}", flush=True)
                else:
                    print(f"    ℹ️ [IA disse]: {linha_limpa}", flush=True)
                
        t1 = time.time()
        print(f"   ⚡ [Fim do Lote] Tempo decorrido: {t1-t0:.1f}s | Classificados com sucesso: {len(matches)} de {len(produtos_lote)} itens\n", flush=True)
        return matches
    except Exception as e:
        print(f"❌ Erro na API Ollama: {e}", flush=True)
        return matches

def main():
    print("Carregando planilhas no sistema...", flush=True)
    arquivo_saida = 'fusao_classificada_ia.xlsx'
    
    if os.path.exists(arquivo_saida):
        df_fusao = pd.read_excel(arquivo_saida)
        print(f"📂 Arquivo {arquivo_saida} carregado para continuar o processamento de onde parou.", flush=True)
    else:
        df_fusao = pd.read_excel('fusao.xlsx')
        
    df_classificador = pd.read_excel('classificador.xlsx')
    
    cats = [f"{row['chave']} -> {row['categoria']} | {row['departamento']}" for _, row in df_classificador.iterrows()]
    prompt_system = (
        "Você é um assistente especialista em classificação de produtos de supermercado/varejo.\n"
        "CATEGORIAS DISPONÍVEIS (chave -> categoria | departamento):\n"
        + "\n".join(cats) +
        "\n\nRegra: Para cada produto da lista, responda APENAS com o formato EXATO em uma nova linha:\nID_<CODIGO_PRODUTO>: <CHAVE>"
    )
    
    # Filtrar apenas os produtos que ainda não possuem chave preenchida ou com chave inválida/vazia
    df_pendentes = df_fusao[df_fusao['chave'].isna() | (df_fusao['chave'] == 0) | (df_fusao['chave'] == '')]
    produtos_pendentes = df_pendentes.to_dict('records')
    
    total_ja_classificado = len(df_fusao) - len(produtos_pendentes)
    print(f"📊 Total de produtos: {len(df_fusao)} | Já classificados: {total_ja_classificado} | Pendentes: {len(produtos_pendentes)}\n", flush=True)
    
    if len(produtos_pendentes) == 0:
        print("🎉 Todos os produtos já estão classificados!", flush=True)
        return

    # Lotes de 15 produtos: estabilidade 100% garantida no modelo local
    tamanho_lote = 15
    
    print(f"🚀 Iniciando classificação de {len(produtos_pendentes)} produtos usando OLLAMA (gemma4:latest) em lotes de {tamanho_lote}...", flush=True)
    
    for i in range(0, len(produtos_pendentes), tamanho_lote):
        lote = produtos_pendentes[i:i+tamanho_lote]
        num_lote = (i // tamanho_lote) + 1
        total_lotes = (len(produtos_pendentes) // tamanho_lote) + 1
        print(f"📦 [Lote {num_lote} de {total_lotes}] Enviando {len(lote)} itens para a IA (tempo estimado: ~2.5 min)...", flush=True)
        
        matches = classificar_lote_ollama(prompt_system, lote)
        
        if matches:
            for match in matches:
                cod = match['codigo_produto']
                chave = match['chave_categoria']
                
                idx = df_fusao[df_fusao['CODIGO_PRODUTO'] == cod].index
                if len(idx) > 0:
                    df_fusao.loc[idx, 'chave'] = chave
                    
                    classif_row = df_classificador[df_classificador['chave'] == chave]
                    if not classif_row.empty:
                        df_fusao.loc[idx, 'categoria'] = classif_row.iloc[0]['categoria']
                        df_fusao.loc[idx, 'departamento'] = classif_row.iloc[0]['departamento']
        else:
            print(f" ⚠️ Aviso: Lote {num_lote} não retornou correspondências válidas.", flush=True)
            
        # Salva o arquivo a cada lote (15 produtos)
        df_fusao.to_excel(arquivo_saida, index=False)
        classificados_agora = df_fusao['chave'].notna().sum()
        porcentagem = (classificados_agora / len(df_fusao)) * 100
        print(f"💾 Progresso salvo com sucesso em {arquivo_saida}! ({classificados_agora} de {len(df_fusao)} itens -> {porcentagem:.1f}% concluído)\n", flush=True)
            
    print("✨ Processamento finalizado completamente!", flush=True)

if __name__ == "__main__":
    main()
