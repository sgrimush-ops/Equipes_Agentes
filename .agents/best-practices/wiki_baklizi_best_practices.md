# 🛡️ Manual de Blindagem: Wiki Baklizi v2.0

Este documento fixa os padrões técnicos obrigatórios da aplicação Wiki Interna para evitar regressões ou quebras de estrutura em futuras atualizações.

## 📊 1. Estrutura Rígida de Dados (12 Colunas)
A planilha `Topicos` **DEVE** manter exatamente 12 colunas (Mapeamento A-L). Alterar a ordem ou deletar colunas quebrará o backend e a visualização de prioridades.

| Letra | Índice | Campo | Descrição |
| :--- | :--- | :--- | :--- |
| **A** | 0 | ID | Gerado automaticamente (ex: T1775...) |
| **B** | 1 | Categoria | Filtro principal de visualização |
| **C** | 2 | Título | Nome da demanda técnica |
| **D** | 3 | Descrição | Detalhamento do problema/sugestão |
| **E** | 4 | Status | `Sugerida`, `Aberta` ou `Concluida` |
| **F** | 5 | Data | Carimbo de tempo da criação |
| **G** | 6 | Imagem | URL do anexo principal (evidência da abertura) |
| **H** | 7 | Repórter | Nome de quem abriu o chamado (Obrigatório) |
| **I** | 8 | Responsável | Técnico presumido (ex: Walace, Alessandro...) |
| **J** | 9 | Solução | Texto da resolução técnica (preenchido pelo Consultor) |
| **K** | 10 | Img Solução | URL do anexo da resolução (evidência do fechamento) |
| **L** | 11 | Prioridade | Nível 1 a 4 (definido pelo Moderador) |

## 🏗️ 2. Arquitetura SPA (Single Page Application)
- **Zero Refresh**: Não utilizar `location.reload()`. Use `initApp(true)` para atualizar dados sem recarregar o navegador.
- **Loader Dinâmico**: Toda transição de tela deve chamar `showLoader()` para reinjetar o HTML do loader e evitar erros de nulo.
- **Watchdog**: Tempo de timeout fixo em **40 segundos** para garantir estabilidade em conexões externas.

## 🔐 3. Regras de Acesso por PIN (RBAC)
- **PIN 0104 (Moderador)**: Banners vermelhos. Pode Priorizar e Excluir. Não pode registrar solução.
- **PIN 2512 (Consultor)**: Banners azuis. Exclusivo para preencher Campo `J` e `K` (Solução). Não pode priorizar nem excluir.
- **Visitante**: Apenas leitura e criação de novas sugestões (Status sempre `Sugerida`).

## ⚠️ 4. Regra Anti-Regressão
> **DIRETIVA**: É proibido automatizar o nome do solicitante ou remover a barra de banners de login no topo. O sistema deve sempre forçar a identificação do usuário para manter a auditoria.

---
*Documento registrado em: 02/04/2026 às 17:13 (GMT-3).*
