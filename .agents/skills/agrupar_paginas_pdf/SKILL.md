---
name: Agrupar Páginas e Linhas de PDF
description: Extrair informações iterativas de PDFs longos através do pdfplumber usando um rastreador em memória contínuo por páginas.
---

# Instruções da Skill

Esta skill visa evitar um erro comum ao extrair relatórios longos em PDF, onde um bloco lógico de informações (ex: Filial/Loja) é declarado apenas no início do bloco e os produtos/itens subsequentes atravessam para as próximas páginas sem que o nome do bloco seja repetido no corpo do texto.

## Problema Clássico de PDF
Quando o `pdfplumber` exibe o texto de uma lauda, a "chave" (nome da loja, vendedor, ou departamento) geralmente só consta uma vez. Nas páginas seguintes, se o agente não salvar o estado anterior em uma variável, ele pode "perder" a quem pertencem os próximos itens. Outro agravante comum é o **cabeçalho de página** conter códigos que enganam as *Expressões Regulares (Regex)*.

## Diretrizes de Resolução para o Agente

1. **Rastreador de Estado (`current_key`)**
   Declare uma variável *fora* do loop das páginas do PDF (ex: `current_loja = "000"`). Essa variável rastreeia a qual identidade pertence a leitura atual.
2. **Uso de DefaultDict (`collections.defaultdict`)**
   Utilize `dicionarios_de_listas = defaultdict(list)` para aglomerar linhas lidas a uma matriz usando a `current_key` como chave. Assim você extrai relatórios massivos de várias seções mesclados no mesmo PDF.
3. **Regex de Cabeçalhos e Finais de Linha (`$`)**
   Tenha extrema certeza de ancorar o final de linha (`$`) nas expressões regulares que capturam a quebra de seção (como a identificação de Lojas/Departamentos). Como os PDFs de relatórios geralmente possuem cabeçalhos persistentes em todas as páginas contendo datas ou strings parecidas com os dados, a âncora `$` garante que o cabeçalho seja ignorado enquanto a linha de interesse é capturada.

**Exemplo de integração no código:**
```python
import pdfplumber
import re
from collections import defaultdict

def skill_parse_pdf_contínuo(pdf_path: str):
    # Regex rigorosa da linha que declara a Seção (ex: 001-LOJA). Note o $ no fim.
    secao_patt = re.compile(r"^\d+\s+.+?\s+(\d{3})-[A-Za-z0-9]+$")
    produto_patt = re.compile(r"^(\d+)\s+([\s\S]+?)\s+(\d+).*$")
    
    dados_por_secao = defaultdict(list)
    current_secao = "indefinido" # Variável declarada fora do loop das páginas
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            linhas = page.extract_text().split('\n')
            for linha in linhas:
                linha = linha.strip()
                
                # Checa se a linha é o abridor de nova Seção
                m_secao = secao_patt.match(linha)
                if m_secao:
                    current_secao = m_secao.group(1)
                    continue
                
                # Checa se é um item. Se for, atrela à Seção atualmente rastreada.
                m_prod = produto_patt.match(linha)
                if m_prod:
                    dados_por_secao[current_secao].append({
                        "Codigo": m_prod.group(1),
                        "Descricao": m_prod.group(2)
                    })
                    
    return dados_por_secao
```
