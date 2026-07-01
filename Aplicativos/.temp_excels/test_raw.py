import pandas as pd
import requests
import json
import time

def main():
    df_fusao = pd.read_excel('fusao_classificada_ia.xlsx')
    df_pendentes = df_fusao[df_fusao['chave'].isna() | (df_fusao['chave'] == 0) | (df_fusao['chave'] == '')]
    lote = df_pendentes.head(3).to_dict('records')
    
    df_classificador = pd.read_excel('classificador.xlsx')
    cats = [f"{row['chave']} -> {row['categoria']} | {row['departamento']}" for _, row in df_classificador.iterrows()]
    
    prompt_system = (
        "Você é um assistente especialista em classificação de produtos de supermercado/varejo.\n"
        "CATEGORIAS DISPONÍVEIS (chave -> categoria | departamento):\n"
        + "\n".join(cats) +
        "\n\nRegra: Para cada produto da lista, responda APENAS com o formato EXATO em uma nova linha:\nID_<CODIGO_PRODUTO>: <CHAVE>"
    )
    
    texto_lote = "\n".join([f"ID_{p['CODIGO_PRODUTO']}: {p['DESCRICAO_PRODUTO']}" for p in lote])
    print("Itens enviados:")
    print(texto_lote)
    print("\nEnviando para o Ollama (sem stream)...", flush=True)
    
    t0 = time.time()
    res = requests.post(
        "http://localhost:11434/api/generate",
        json={
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
    ).json()
    t1 = time.time()
    
    print(f"\nTempo: {t1-t0:.1f}s")
    print("RESPOSTA CRUA DO MODELO:")
    print(repr(res.get('response')))
    print("\nRESPOSTA IMPRESSA:")
    print(res.get('response'))

if __name__ == '__main__':
    main()
