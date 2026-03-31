# Equipes_Agentes — Squad de Automação Varejo

Framework de orquestração multi-agentes especializado em automação operacional de varejo (RPA, BI e integração de dados).

> **Última atualização:** 31/03/2026 — Versão com pipeline `barras.py`, sync Google Sheets (EAN/DUN) e robô Supply com skip logic de comprador.

---

## 🚀 Início Rápido

Abra esta pasta no seu IDE e use o comando:

```
/Equipes_agentes
```

Ou seja direto ao ponto:

```
/run-varejo          — Executa a Squad Varejo Insight
/Equipes_agentes     — Menu principal (criar squads, gerenciar)
```

---

## 📁 Estrutura de Pastas

```
Equipes_Agentes/
├── .agents/                   # Regras mestre, skills e workflows dos agentes
│   ├── rules.md               # ⚡ Protocolo obrigatório — leia antes de codar
│   ├── resumo_projetos.md     # Mapa de todos os projetos locais
│   ├── skills/                # Biblioteca de habilidades especializadas
│   └── workflows/             # Fluxos de execução (/run-varejo, /Equipes_agentes)
│
├── Agentes/                   # Scripts operacionais e definições de agentes (.agent.md)
│
├── Aplicativos/               # Módulos Python operacionais
│   ├── GAM/                   # 🤖 RPA — Automação de interface (Tkinter + OpenCV)
│   ├── import_querys/         # 📊 Pipeline de dados: EAN/DUN, query.parquet, sync Sheets
│   ├── ruptura/               # 📈 Dashboard de ruptura (HTML < 10MB, No-Server)
│   ├── min_e_max/             # 📦 Cálculo e parametrização de Min/Max de estoque
│   ├── integracao_google/     # ☁️ OAuth Google Drive, Gmail, AppSheet
│   ├── memoria_squad/         # 🧠 Memória vetorial (ChromaDB)
│   ├── mcp_squad/             # 🔌 Servidor MCP local (office_server.py)
│   ├── gerenciamento_sql/     # 🗃️ Geração assistida de queries Oracle/Consinco
│   ├── cruzamento/            # 🔀 Conciliação gerencial via Parquet
│   ├── consumo/               # 🔄 Conversão consumo.xlsx → consumo.parquet
│   ├── pendencias/            # 📋 Consolidação de relatórios por loja
│   └── mix_site/              # 🛒 Dados de Mix de produtos
│
├── doc/                       # Documentação técnica das Squads
├── requirements.txt           # Dependências Python (gerado via pip freeze)
├── .env.example               # Exemplo de variáveis de ambiente (.env não comitado)
└── .gitignore
```

---

## 🏪 Squads Ativas

### [Varejo Insight](doc/README-varejo-insight.md)
Otimização de abastecimento com foco no Centro de Distribuição (**Filial 15**) e análise de ruptura.

**Componentes principais:**
| Módulo | Script Principal | Função |
|--------|-----------------|--------|
| Dashboard Ruptura | `ruptura/rp.py` | Painel HTML interativo < 10MB |
| Pipeline EAN/DUN | `import_querys/barras.py` | `ean_dun.txt` → `ean_dun.parquet` |
| Sync Google Sheets | `import_querys/sync_google_sheet.py` | Envio de EAN/DUN (formato TEXT) ao Sheets |
| Robô Supply | `GAM/actions/acao_digitar_pedido_supply.py` | Digitação automatizada com skip logic |
| Min/Max | `min_e_max/acao_preparar_manual_supply.py` | Pedidos com base em Min/Max × embalagem |

---

## 🔑 Regras Críticas do Ecossistema

> Leia o arquivo [`.agents/rules.md`](.agents/rules.md) **obrigatoriamente** antes de qualquer desenvolvimento.

Destaques principais:
- **pathlib** obrigatória para todos os caminhos (proibido concatenação de strings)
- **sep=';', encoding='utf-8-sig'** em todos os CSVs Pt-BR do Consinco
- **EAN/DUN** → sempre como `TEXT` no Google Sheets (preserva zeros à esquerda)
- **pynput** obrigatório para cliques calibrados em RPA (pyautogui causa miss-clicks por DPI)
- **Min/Max Consinco** → sempre em CAIXAS; converter para unidades multiplicando por `EMBL_COMPRA`

---

## ⚙️ Configuração do Ambiente

```bash
# 1. Criar ambiente virtual
python -m venv .venv

# 2. Ativar (Windows PowerShell)
.venv\Scripts\Activate.ps1

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar credenciais
cp .env.example .env
# Editar .env com suas chaves de API
```

---

## 🔗 Links Rápidos

- [Protocolo Mestre (.agents/rules.md)](.agents/rules.md)
- [Mapa de Projetos (.agents/resumo_projetos.md)](.agents/resumo_projetos.md)
- [Squad Varejo Insight](doc/README-varejo-insight.md)
- [Documentação de Aplicativos](Aplicativos/documentacao_aplicativos.md)
