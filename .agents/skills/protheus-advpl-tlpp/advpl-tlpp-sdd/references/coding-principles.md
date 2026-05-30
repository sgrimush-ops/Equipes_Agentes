# Coding Principles

Princípios comportamentais para implementação e revisão.

## Antes de codar
- Declare suposições explicitamente
- Apresente todas as interpretações possíveis
- Prefira abordagens simples
- Pare e questione se algo estiver confuso
- Se discordar do pedido, explique

## Durante a implementação
- Não adicione recursos não solicitados
- Não crie abstrações para uso único
- Não trate erros impossíveis
- Prefira 50 linhas a 200
- Não "melhore" código adjacente sem pedido
- Siga o estilo existente
- Só remova código órfão gerado pela sua alteração

## Testes
- Nunca enfraqueça um teste para passar
- Nunca delete teste para reduzir falha
- Nunca use skip/disable para burlar teste
- Se o teste estiver errado, pare e confirme
- Testes são a especificação

## Objetividade
- Transforme tarefas vagas em metas verificáveis
- Cada linha alterada deve rastrear ao pedido

## Após cada alteração
- Pergunte: "Um sênior chamaria isso de overengineering?"