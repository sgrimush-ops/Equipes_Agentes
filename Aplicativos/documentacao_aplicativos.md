# Guia de Aplicativos (Scripts Principais)

Este guia reflete os aplicativos atuais contidos na pasta `Aplicativos`. Ele documenta a função de cada subdiretório e explica exatamente qual é a função do script Python `.py` principal que você encontra ao entrar.

---

## 📁 Pasta: BancoDadosSW
**Script Principal:** `convert_txt_to_excel.py`
**O que ele faz:** 
Lê um arquivo de texto bruto do sistema (ex: `banco_de_dados_10-02.txt`), filtra os dados (removendo linhas onde o tipo comercial é "I") e exporta os resultados particionados em um arquivo Excel (`bdsw.xlsx`). Como a base de dados pode ser gigante, ele divide os dados em blocos de 900.000 linhas por aba, evitando sobrecarga na memória e no Excel.

---

## 📁 Pasta: GAM (Gerenciador de Automações e Macros)
**Script Principal:** `main.py`
**O que ele faz:**
Ele abre a interface gráfica principal (janela Tkinter) do sistema de RPA (Robotic Process Automation). Ao abrir o programa, o usuário tem acesso a várias ações pré-programadas do lado esquerdo (como bloquear a tela, digitar pedidos, aprovar manuais, etc.), que podem ser enfileiradas do lado direito para criar "Macros" robóticas completas para automatizar tarefas de tela.

---

## 📁 Pasta: consumo
**Script Principal:** `ap.py`
**O que ele faz:**
Lê um relatório em Excel normal chamado `consumo.xlsx`. Em seguida, faz um processo de saneamento na coluna `codigo` (transformando textos inválidos e espaços vazios em valores numéricos forçando a conversão real para formato de "inteiro puro"). Após limpar as sujas, ele compacta a tabela e a salva como `consumo.parquet` – arquivo de big data altamente otimizado para não travar cálculos pesados no futuro.

---

## 📁 Pasta: cruzamento
**Script Principal:** `ap.py` (Módulo Visualizador de Parquet)
**O que ele faz:**
Este script é uma ferramenta para analisar bases otimizadas. Ele lista e lê todos os arquivos `.parquet` guardados na pasta `bd` e "descospe" no terminal as informações centrais de cada um deles: diz quantas colunas há no total, exibe os nomes de todas essas colunas, e mostra o cabeçalho e as três primeiras linhas da tabela, ajudando você a debugar a visualização dos dados consolidados em Parquet.

---

## 📁 Pasta: lojas_colunas
**Script Principal:** `ap.py`
**O que ele faz:**
Responsável por transformar dados verticais fracionados em colunas por Loja. Ele recebe dados logísticos globais listados num tabelão (`manual.xlsx`). Separa os dados de todas as Filiais, afastando o Centro de Distribuição (Empresa 15). Transforma a base (via Pivot Table), criando um espelho onde cada Loja tem sua própria coluna exclusivíssima (`Estoque L001`, `Pendencia L001`, `Estoque L002`... etc). Depois finaliza cruzando todos os dados da matriz horizontal ao lado do estoque do CD, salvando no arquivo `cd.xlsx`.

---

## 📁 Pasta: mix
**Script Principal:** `convert_to_parquet.py`
**O que ele faz:**
Ele lê o relatório fixo extraído (`con5cod.xlsx`), constrói ativamente a pasta de `resultado` (se ela for deletada) e garante a cópia da integridade original desse mix transmutando-o em arquivo binário veloz (`con5cod.parquet`), sem interferir nas colunas, servindo como motor de importação bruta na integração inter-projetos de "Mix".

---

## 📁 Pasta: pendencias
**Script Principal:** `consolidado.py`
**O que ele faz:**
Vasculha a subpasta interna chamada `bd_saida` procurando por arquivos com o padrão `Loja *.xlsx`. Ele lê ativamente as abas de todos os Excels picados achados na pasta, concatena (amontoa todas as filiais sob um mesmo cabeçalho verticalmente), processa ordenando os registros pelo campo número de Loja e finaliza cospe uma versão super-planilha, salvando em CSV separada por ponto-e-vírgula (`consolidado.csv`).

---

## 📁 Pasta: ruptura
**Script Principal:** `rp.py`
**O que ele faz:**
Recebe um relatório de Ruptura comercial (`rpcompra.csv`) onde algumas colunas vêm coladas de origem ("Comprador : Produto", tudo agrupado junto). O robô entra fatiando e particionando essa coluna ao meio (dividindo no caractere ":"), cria as colunas Comprador e Produto separadas. Além disso, elimina textos das Embalagens (`"CX 20"` virando valor limpo `20`). Salva o arquivo de cópia corrigido e logo finaliza dando o gatilho automático (`start`) no Painel Web Dashboard interativo que ele contém na mesma pasta.

---

## 📁 Pasta: min_e_max
**Script Principal:** `ap.py`
**O que ele faz:**
Atualiza estoques mínimos e máximos da empresa via algoritmos matemáticos gerenciais. Ele lê `trabalho.xlsx`. Para cada filial, se a loja tem dados base, calcula que o "Novo Mínimo" necessite suportar no mínimo *5 dias* de Volume de Venda Média. O "Novo Máximo" é engordado + 30% em cima desse mínimo (mas de forma que encaixe no tamanho das Caixas/Embalagens). E depois ele processa as somas consolidadas desses abastecimentos individuais de Lojas para prever automaticamente o novo "Mínimo e Máximo" que deve ser exigido do Centro de Distribuição (Empresa 15). Devolve tudo documentado no `resultado.csv` pra integração.
