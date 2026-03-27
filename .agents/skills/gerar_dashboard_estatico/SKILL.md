---
name: Gerar Dashboards Estáticos Interativos Multi-Abas
description: Estratégia de arquitetura No-Server para embutir dezenas de visões de um Dataset (ex uma aba por Loja) em um único arquivo HTML gerado por Python (Plotly/Pandas) e controlado nativamente via JavaScript, eliminando dependências como Streamlit ou Dash.
---

# 🧠 Padrão Arquitetural: Single-File Python Dashboard (No-Server)

É extremamente comum que os usuários de negócios e equipes locais precisem de Dashboards interativos (com filtros de unidade, loja, ou diretoria), mas sem a burocracia de configurar e manter instâncias de um servidor `Dash` ou `Streamlit` ligados na máquina.

Este padrão ensina o Agente a isolar lógicas visuais do Python em "Bandejas HTML" (Divs) dentro de um único arquivão, alternáveis instantaneamente pelo front-end. O arquivo resultante pode ser passado via pendrive ou e-mail, e funcionará 100% offline em qualquer navegador.

## ⚙️ Os 3 Pilares da Arquitetura

### 1. Encapsulamento da Engenharia em Função
Ao invés de processar o Pipeline em formato espaguete procedural, crie uma função "Fábrica" que recebe um `DataFrame` filtrado, processa as contagens essenciais e devolve estritamente as strings HTML do Gráfico e da Tabela correspondente àquele recorte populacional **sem importar o arquivo gigante JS do backend do Plotly a cada chamada**.
```python
def compilar_visao(nome_visao, curr_df):
    ... # Contagens, Agrupamentos, Filtros e Criação da Tabela detalhada baseada EXCLUSIVAMENTE no "curr_df"
    
    # ⚠️ IMPORTANTE: include_plotlyjs=False poupa 3.5 Megabytes PARA CADA ITERAÇÃO
    grafico_html = fig.to_html(full_html=False, include_plotlyjs=False) 
    tabela_html = "<table>...</table>"

    return grafico_html, tabela_html
```

### 2. O Loop Multi-Views (Geração Pre-Renderizada)
Construa um Laço "For" circulando a sua coluna de Segmento (Ex: Número da Loja, Vendedor, Região). A cada volta, armazene as strings extraídas da sua Função Fábrica dentro de uma caixa `div` exclusiva, ocultando as secundárias  (`display: none`).
```python
visoes_html = ""
opcoes_select = ""

# Visão 1: Global Genérica (Aberta por Padrão)
gf, tb = compilar_visao("Todas as Filiais", df)
visoes_html += f'<div id="view_global" class="sub-view" style="display:block;">{gf}{tb}</div>'
opcoes_select += '<option value="global">Todas as Filiais</option>'

# Visão N: Repetida Estruturalmente
for polo in df['CODIGO_POLO'].unique():
    df_polo = df[df['CODIGO_POLO'] == polo]
    gf, tb = compilar_visao(f"Polo {polo}", df_polo)
    
    visoes_html += f'<div id="view_polo_{polo}" class="sub-view" style="display:none;">{gf}{tb}</div>'
    opcoes_select += f'<option value="polo_{polo}">Métrica do Polo {polo}</option>'
```

### 3. A Casca HTML e Interatividade Javascript Mestra
Agrupe a importação oficial global da biblioteca Plotly no topo do documento (Head) e crie o painel de seleção:
```html
<!DOCTYPE html>
<html>
<head>
    <!-- Um Único JS para governar todos os mais de 40 gráficos pré-renderizados gerados pelo Python abaixo-->
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
</head>
<body>
    <select id="FiltroMestre" onchange="trocarVisao()">
        {opcoes_select}
    </select>
    
    {visoes_html}

    <script>
    function trocarVisao() {
        var selecionado = document.getElementById("FiltroMestre").value;
        var abas = document.getElementsByClassName("sub-view");
        for(var i=0; i < abas.length; i++) {
            abas[i].style.display = (abas[i].id === "view_" + selecionado) ? "block" : "none";
        }
        // 👉 TRUQUE DE MESTRE: Força evento de renderização (Resize) no Window para impedir que os gráficos Plotly ocultos encolham e se tornem ilegíveis após retirar o display:none
        window.dispatchEvent(new Event('resize')); 
    }
    </script>
</body>
</html>
```

---
**💡 Benefícios Exclusivos da Lógica Analítica (Clickable Matrix UX)**
1. **Contagem Mestra Baseada em Nunique:** Não realize contagens diretas `.size()` se a granularidade temporal/física exigir **Produtos Únicos** através de múltiplas referências. Identifique sempre a Chave Mestra para o seu `groupby(['Vendedor'])['Produto_ID'].nunique()`.
2. **Matrix Cells Onclick:** Para não sobrecarregar listas visuais num PDF/App ou HTML denso, substitua o obsoleto clique que despeja listas únicas indiscriminadas por Células Customizadas. Programe Javascripts que abram abas que se refiram EXCLUSIVAMENTE ao compartimento de dados que o humano clicou, permitindo rastrear o porquê de cada algarismo matemático isolado renderizado pela sua Python Engine.
