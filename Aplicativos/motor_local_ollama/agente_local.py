import os
import pandas as pd
from openai import OpenAI
import argparse

# Configuração Padrão do Motor Local apontando para o Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "hermes3") # Modelo recomendado: Hermes 3 / Hermes 2 Pro

def carregar_prompt_agente(agent_file_path: str = None) -> str:
    """
    Lê o arquivo .agent.md e extrai as regras (System Prompt). Se não houver arquivo, usa prompt genérico.
    """
    base_prompt = "Você é um agente especializado do ecossistema Equipe_Agentes.\nATENÇÃO: Você DEVE retornar sua resposta EXCLUSIVAMENTE em formato de objeto JSON válido."
    
    if not agent_file_path or not os.path.exists(agent_file_path):
        return f"{base_prompt}\n\nAnalise e processe os dados conforme a instrução fornecida."
    
    with open(agent_file_path, 'r', encoding='utf-8') as f:
        # Pega todo o arquivo como contexto, ignorando frontmatters vazios
        content = f.read()
    
    return f"{base_prompt}\n\nSiga estritamente as regras definidas abaixo:\n\n{content}"

def inferencia_local_em_lote(csv_path: str, prompt_instrucao: str, agent_file: str = None, batch_size: int = 50, output_path: str = None):
    """
    Processa um CSV enviando lotes de dados para o modelo Hermes rodando no Ollama local.
    """
    print(f"Iniciando Motor Local de Inferência Ollama ({DEFAULT_MODEL})")
    
    # 1. Carrega o system prompt base
    system_prompt = carregar_prompt_agente(agent_file)
    
    # 2. Inicia o Cliente OpenAI apontando pro Localhost
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama" # Requerido pela lib, mas ignorado pelo Ollama
    )
    
    print(f"Lendo base de dados: {csv_path}")
    df = pd.read_csv(csv_path, sep=";") # Padrão Totvs/Consinco é ;
    total_rows = len(df)
    
    print(f"Total de registros a processar: {total_rows}")
    print(f"Fatiando em lotes de {batch_size}...")
    
    resultados = []
    
    # 3. Itera sobre o DataFrame em batches
    for i in range(0, total_rows, batch_size):
        df_batch = df.iloc[i:i+batch_size]
        batch_json = df_batch.to_json(orient='records', force_ascii=False)
        
        user_message = f"{prompt_instrucao}\n\nDados (Lote {i} a {i+len(df_batch)}):\n{batch_json}"
        
        print(f"Enviando lote {i} a {i+len(df_batch)} para o modelo {DEFAULT_MODEL}...")
        
        try:
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1, # Temperatura baixa para processamento de dados e tool use
                response_format={"type": "json_object"}
            )
            
            resposta_texto = response.choices[0].message.content
            resultados.append(resposta_texto)
            print("Lote processado com sucesso.")
            
        except Exception as e:
            print(f"Erro na comunicação com Ollama no lote {i}: {str(e)}")
            resultados.append(f"ERRO: {str(e)}")
            
    # 4. Salva o Log/Saída
    saida_final = "\n\n---\n\n".join(resultados)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(saida_final)
        print(f"Processamento concluído. Resultados salvos em: {output_path}")
    else:
        print("\n\n=== RESULTADO FINAL ===")
        print(saida_final)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor Local de Agentes - Equipes_Agentes (Ollama)")
    parser.add_argument("--csv", type=str, required=True, help="Caminho do CSV de entrada")
    parser.add_argument("--agent", type=str, required=False, help="Caminho para o arquivo .agent.md (Opcional)")
    parser.add_argument("--instrucao", type=str, required=True, help="Instrução do que fazer com os dados")
    parser.add_argument("--out", type=str, help="Caminho para salvar a saída")
    
    args = parser.parse_args()
    
    inferencia_local_em_lote(
        csv_path=args.csv,
        prompt_instrucao=args.instrucao,
        agent_file=args.agent,
        output_path=args.out
    )
