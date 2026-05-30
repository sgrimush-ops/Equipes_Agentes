# Documentation and Conventions — ProtheusDOC, Clean Code, TLPP

Padrões para documentação ProtheusDOC, clean code e revisão TLPP.

---

## ProtheusDOC

Todo elemento público (Função, Classe, Método público) **deve** ter bloco ProtheusDOC completo. Funções estáticas e métodos privados **devem** ter também.

### Estrutura obrigatória

```
/*/{Protheus.doc} <Identificador>
<Descrição>
@type <function|class|method>
[tags adicionais]
/*/
```

### Tags obrigatórias

| Tag       | Obrigatório para                  | Regra                                         |
| --------- | -------------------------------- | --------------------------------------------- |
| `@type`   | Todos os elementos               | `function`, `class`, ou `method`              |
| `@author` | Todos os elementos               | Nome do autor                                 |
| `@since`  | Todos os elementos               | Data ou versão                                |
| `@param`  | Funções/métodos com parâmetros   | Um por parâmetro: nome, tipo, descrição       |
| `@return` | Funções/métodos com retorno      | tipo, descrição                               |

### Checklist de documentação
- [ ] Toda User Function tem bloco Protheus.doc
- [ ] Toda Classe tem bloco Protheus.doc
- [ ] Todo método público tem bloco Protheus.doc
- [ ] Tag @type correta
- [ ] @author e @since presentes
- [ ] @param para cada parâmetro
- [ ] @return para retorno
- [ ] Identificador igual ao elemento
- [ ] Bloco abre/fecha corretamente
