# Protocolo Mestre de Desenvolvimento (Python 3.14.3 64-bit)

Este documento contém as regras obrigatórias para a criação e manutenção deste projeto. O agente deve ler este arquivo antes de cada interação.

## 1. Estrutura e Inicialização do Projeto

- **Estrutura de Pastas (Consolidada):**
    - `Agentes/` (Raiz/Visível): Local obrigatório para todos os scripts operacionais (`.py`) e definições de agentes (`.agent.md`).
    - `Agentes/.motor/` (Oculto): Local para o motor técnico e memória do sistema.
    - `.agents/` (Raiz/Oculto): Local para regras mestre (`rules.md`), habilidades (`skills/`) e fluxos (`workflows/`).
- **Nomenclatura:** Se o nome não for definido, use `novo_projeto`. Crie sempre uma pasta raiz exclusiva.
- **Pasta do Agente:** Mantenha a pasta `.agents/` com este arquivo `rules.md` sempre atualizado.
- **Arquivo Principal:** O ponto de entrada deve ser obrigatoriamente `ap.py`.
- **Git:** Crie um `.gitignore` ignorando `.venv/`, `__pycache__/`, `tmp/`, `.motor/` e arquivos temporários.

## 2. Gerenciamento de Ambiente (VENV)

- **Ambiente:** Crie o ambiente virtual com `python -m venv .venv`.
- **Ativação:** Utilize sempre o executável da `.venv` para comandos de terminal.
- **Dependências:** Instale sempre `pandas`, `openpyxl`, `pathlib` e `python-dotenv` como base.
- **Sincronização:** Após qualquer instalação, execute `pip freeze > requirements.txt`.
- **Permissão (Modo Turbo):** Você tem autonomia para executar comandos no terminal (`run_command`, `send_command_input`) utilizando `SafeToAutoRun: true` para todas as tarefas de leitura, listagem, instalação e execuções que não envolvam deleção de dados críticos ou sobrescrita de código central sem plano prévio. O usuário deseja o mínimo de interrupções de "botão azul".

## 3. Padrões de Escrita de Código (Clean Code)

- **Caminhos:** Use EXCLUSIVAMENTE `pathlib`. Proibido concatenação de strings para caminhos.
- **Tipagem:** Utilize Type Hints em todas as definições de funções (ex: `def func(p: str) -> None:`).
- **Boilerplate:** Use a estrutura `if __name__ == "__main__":` e funções modulares.
- **Documentação:** Use Docstrings no padrão Google.
- **Execução via VSCode (Run in Terminal):** Todo script Ponto de Entrada / Arquivo Principal (ex: `ap.py`, `resumo.py`) DEVE conter obrigatoriamente a trava de contexto para execução direta: `if __name__ == '__main__': os.chdir(Path(__file__).parent.resolve())`. Isso garante que o diretório de trabalho seja a raiz do script quando acionado via terminal isolado, mas previne que essa alteração "vaze" e quebre o sistema de módulos caso esse código seja `importado` por outro arquivo.
- **Consultas SQL:** NUNCA adicione comentários textuais (como `--` ou `/* */`) na estrutura de scripts SQL.
- **Consultas SQL (Estoque):** Ao calcular o "Estoque Disponível" usando a tabela `MRL_PRODUTOEMPRESA` (Consinco), OBRIGATORIAMENTE some o estoque da loja com o de depósito (`ESTQLOJA` + `ESTQDEPOSITO`) e deduza as reservas (`QTDRESERVADAVDA` e `QTDRESERVADARECEB`). Extrair apenas um dos sub-estoques fará com que pareça estar vazio (zerado) tudo o que tange filiais de vendas padrão ou o CD primário, falsificando relatórios.
- **Preservação Estrutural (Estoque_e_Venda_Min_Max):** NUNCA remova ou suprima colunas existentes no script `Estoque_e_Venda_Min_Max.sql` (ou em outras extrações mestre semelhantes). Todos os agentes estão expressamente PROIBIDOS de deletar qualquer coluna de relatórios consolidados sem o consentimento absoluto, claro e prévio do usuário logado. As esteiras internas de aplicativos dependem irrestritamente da integridade dessas fatias.

## 4. Manipulação de Dados (Pandas & Excel)

- **Engine:** Utilize sempre `engine='openpyxl'` para arquivos `.xlsx`.
- **Delimitadores e Encoding (CSV/TXT):** Todo arquivo plano provindo do Consinco ou exportado para o projeto opera no padrão regional Pt-BR. Ao utilizar as funções de Ingestão (`read_csv`) ou Exportação (`to_csv`) do Pandas, inclua OBRIGATORIAMENTE os parâmetros `sep=';'` e `encoding='utf-8-sig'` nativos do Excel. Jamais suponha separação por vírgula (,) ou Tab (\t).
- **Formatação de Decimais:** SEMPRE que operações matemáticas ou exportações envolverem colunas com dados não-inteiros (decimais/floats), esses devem **obrigatoriamente** ser limitados a no máximo 2 casas decimais e exportados usando a VÍRGULA (`,`) como separador de decimal (ex: utilize o parâmetro `decimal=','` nas funções do Pandas e aplique `round(2)` nas contas).
- **Resiliência:** Implemente blocos `try-except` e valide a existência de arquivos com `pathlib`.

## 5. Segurança e Compilação (.exe)

- **Senhas:** Use `getpass` para entradas e `.env` para chaves de API. Nunca hardcode senhas.
- **Portabilidade:** Use `sys._MEIPASS` para referenciar arquivos internos em builds PyInstaller.
- **Privilégios:** Preveja falhas de permissão ao modificar atributos de pastas no Windows.

## 6. Regras de Ingestão

- **Saneamento Base:** Todo arquivo CSV ou Excel novo deve ser processado antes de qualquer análise. Nunca trabalhe com dados 'crus'.
- **Saneamento Logístico (Embalagens e Volumes):** O sistema legado (TOTVS ou similares) constantemente exporta unidades de medida com strings embarcadas na mesma coluna (Ex: "CX 20", "UN 1", "FD 12"). Sempre que operar com colunas que rejam agrupadores indivisíveis (como "Embalagem Compra", que sempre corresponde a um número inteiro), limpe-as obrigatoriamente logo na carga inicial com Extração via RegEx (`str.extract(r'(\d+)')`) e as converta para Inteiro Puro (Int64), viabilizando operações exatas.
- **Saneamento de Códigos (Produto/EAN/DUN):** Não existem códigos de produto com vírgula decimal. Colunas destinadas a registrar identificadores como `Código Produto`, `EAN` ou `DUN` devem ser convertidas sumariamente para números inteiros (ou strings sem decimais). Caso a leitura de um CSV importe valores como `2704,0`, isso deve ser saneado forçando o casting para números inteiros puros antes de qualquer exportação ou cruzamento.

## 8. Ecossistema de IA (Vetor e Visão)

- **Memória Persistente:** Sempre que uma regra de negócio complexa ou um erro de sistema for resolvido, o agente deve considerar adicionar essa lição à memória vetorial via `memoria_squad/kernel.py` para evitar reincidência.
- **Visão em RPA:**Scripts de automação (RPA) devem preferir o uso do `VisionEngine` (OpenCV Multi-Scale) em vez de coordenadas fixas ou `matchTemplate` simples, garantindo portabilidade entre diferentes resoluções de tela e DPIs do Windows.
- **Protocolo MCP:** O uso de ferramentas de manipulação de arquivos deve, sempre que possível, ser mediado pelo servidor MCP local para garantir rastreabilidade e padronização.

## 9. Dashboard de Ruptura (Squad Varejo Insight)

Este módulo possui regras estruturais fixas para garantir a integridade das métricas operacionais perante a diretoria.

- **Fluxo de Dados (query.parquet):** Jamais altere o mapeamento das colunas `QUANTIDADE_DISPONIVEL`, `EMBL_COMPRA`, `EMBL_TRANSFERENCIA` e `STATUS_COMPRA`.
- **Saneamento Técnico:** Obrigatoriamente aplique `.str.replace(',', '.')` e `pd.to_numeric` em todas as colunas de estoque e volume antes de qualquer cálculo.
- **Lógica de Mix Ativo:** 
    - A métrica "Mix Ativo (Produtos)" deve ser sempre a contagem de **SKUs únicos** (União CD 15 + Lojas) por comprador. 
    - NUNCA utilize a contagem de instâncias (Produto x Loja) como denominador para percentuais de ruptura total na tabela.
- **Bases de Canal:**
    - `% Ruptura CD` e `% Pendências`: Denominador fixo na `Base_CD15`.
    - `% Ruptura Loja`: Denominador fixo na `Base_Lojas`.
- **Interface e Visualização:**
    - O gráfico Plotly deve sempre iniciar com a barra **TOTAL GERAL** na primeira posição (extrema esquerda).
    - Botões de navegação: Manter obrigatoriamente os filtros "Totais Gerais" e "Só Compradores". O botão "Ver Todos" está permanentemente removido.
- **Integridade de Merges:** No script `gerar_dashboard_comprador.py`, a base primordial do `df_resumo` deve ser o mix de produtos para evitar que compradores com base zerada em um dos canais desapareçam do relatório.
