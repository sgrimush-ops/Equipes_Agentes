import mcp.server.fastmcp as fastmcp
import pandas as pd
from pathlib import Path

# Inicializa o servidor MCP
mcp_server = fastmcp.FastMCP("Squad Office Server")

@mcp_server.tool()
def ler_planilha_estoque(caminho: str) -> str:
    """Lê um arquivo Excel e retorna um resumo das colunas e linhas."""
    path = Path(caminho)
    if not path.exists():
        return f"Erro: Arquivo {caminho} não encontrado."
    
    df = pd.read_excel(path, engine='openpyxl')
    return f"Planilha lida com sucesso. Colunas: {df.columns.tolist()}. Total de linhas: {len(df)}"

@mcp_server.tool()
def exportar_csv_formatado(dados_json: str, destino: str) -> str:
    """Converte uma string JSON em CSV seguindo o Protocolo Mestre do Varejo."""
    import json
    try:
        data = json.loads(dados_json)
        df = pd.DataFrame(data)
        df.to_csv(destino, sep=';', encoding='utf-8-sig', index=False, decimal=',')
        return f"Arquivo exportado com SUCESSO para {destino}"
    except Exception as e:
        return f"Erro na exportação: {e}"

if __name__ == "__main__":
    # Inicia o servidor em modo STDIO (padrão para conexão com Claude/Desktop)
    mcp_server.run()
