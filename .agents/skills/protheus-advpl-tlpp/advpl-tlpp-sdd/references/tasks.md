# Tasks

Como quebrar em tarefas atômicas e paralelizáveis.

## Por que granular?
- Foco único
- Fácil de testar
- Paralelismo
- Isolamento de erros

## Regra
- Uma tarefa = uma função/classe/camada/endpoint/teste/arquivo

## Processo
1. Revise o design
2. Carregue matriz de cobertura de testes
3. Quebre em tarefas atômicas
4. Marque dependências e paralelismo

## Exemplo
| Tarefa vaga | Tarefas granulares |
| --- | --- |
| "Criar tela MVC" | T1: ModelDef, T2: ViewDef, T3: BrowseDef, T4: MenuDef, T5: Validações |
| "Implementar endpoint REST" | T1: Classe TLPP, T2: GET, T3: POST, T4: Teste TIR |