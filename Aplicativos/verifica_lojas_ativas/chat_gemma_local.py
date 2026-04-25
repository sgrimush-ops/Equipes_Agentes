import requests
import sys

def chat_com_gemma():
    print("=========================================")
    print("🤖 Chat com Gemma 2 Local (via Ollama)")
    print("=========================================")
    print("-> Digite 'sair' para encerrar a conversa.\n")
    
    # O Ollama abre um servidor local nesta porta padrao
    url = "http://localhost:11434/api/generate"
    
    # Troque para "gemma" se baixou a versao 1 do modelo
    modelo = "gemma2" 
    
    while True:
        pergunta = input("\nVocê: ")
        
        if pergunta.strip().lower() in ['sair', 'exit', 'quit']:
            print("Até mais!")
            break
            
        if not pergunta.strip():
            continue
            
        payload = {
            "model": modelo,
            "prompt": pergunta,
            "stream": True # Mantemos stream pra ele responder digitando
        }
        
        try:
            print("Gemma: ", end="", flush=True)
            resposta = requests.post(url, json=payload, stream=True)
            
            if resposta.status_code == 200:
                # O Ollama responde em pedaços (stream)
                for linha in resposta.iter_lines():
                    if linha:
                        dicionario = __import__('json').loads(linha)
                        pedaco_texto = dicionario.get('response', '')
                        print(pedaco_texto, end="", flush=True)
                print() # Pular linha ao final
            else:
                print(f"[Erro: Ollama retornou o status {resposta.status_code}. O modelo {modelo} está baixado?]")
                
        except requests.exceptions.ConnectionError:
            print("\n\n[ERRO DE CONEXÃO] Não consegui achar o Gemma.")
            print("1. O programa Ollama está rodando na bandeja do seu Windows?")
            print("2. Você rodou 'ollama run gemma2' no terminal pelo menos uma vez?")
            sys.exit(1)

if __name__ == "__main__":
    chat_com_gemma()
