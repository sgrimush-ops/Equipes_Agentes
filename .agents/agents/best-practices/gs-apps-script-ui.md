---
id: gs-apps-script-ui
name: "Apps Script Web App UI/UX & Deployment"
whenToUse: >
  For building Web Apps with Google Apps Script (GAS), especially those embedded in Google Sites, 
  using iframes, or requiring role-based access control (RBAC). 
  Highly recommended for corporate environments with restricted network policies.
  NOT for: Standalone static HTML/CSS sites without GAS backend or locally hosted projects.
version: "1.2.0"
---

# Apps Script Web App UI/UX & Deployment — Melhores Práticas

Este guia estabelece os padrões de engenharia de interface e fluxo de implantação para aplicações baseadas em Google Apps Script (GAS). Foca em superar as limitações de segurança de iframes, garantir a persistência de acesso e otimizar a experiência de usuários em ambientes corporativos (Google Workspace) com alta restrição de segurança e compatibilidade legada.

## Core Principles

1. **Abstração de Diálogos Nativos (No-Prompt Policy)**: Nunca utilize `window.prompt()`, `window.confirm()` ou `window.alert()` em Web Apps que serão incorporados (ex: Google Sites). Navegadores modernos frequentemente bloqueiam esses modais dentro de iframes por motivos de segurança, resultando em uma interface "morta" onde o clique não gera ação. Sempre implemente modais customizados via HTML/CSS.

2. **Persistência de Sessão via LocalStorage**: Como Web Apps GAS são frequentemente acessados via URLs públicas ou incorporadas, não há um sistema de "sessão" tradicional por padrão. Utilize o `localStorage` do navegador para armazenar tokens de acesso, PINs ou estados de login. Isso evita que o usuário precise se autenticar novamente a cada atualização de página ou navegação interna.

3. **Deploy de Nova Versão Obrigatório**: Alterações no código `.gs` ou `.html` salvas no editor do Apps Script NÃO refletem automaticamente na URL de execução (`/exec`). É imperativo criar uma **"Nova Versão"** em cada implantação relevante via "Gerenciar Implantações". O uso do "Link de Teste" (`/dev`) é recomendado apenas para depuração interna, nunca para o usuário final.

4. **Gating de Interface (Security by Visibility)**: Recursos administrativos ou de edição devem ser ocultos do DOM até que a autorização seja confirmada. Não basta desabilitar botões; eles não devem existir ou devem estar com `display: none` para usuários comuns, reduzindo a confusão visual e a superfície de erro.

5. **Robustez na Comparação de Dados (Sanitization)**: Dados vindos do Google Sheets podem conter espaços invisíveis ou variações de caixa (Maiúsculo/Minúsculo). Sempre utilize `.trim()` e `.toLowerCase()` (ou `.toUpperCase()`) tanto no backend (GAS) quanto no frontend (JS) antes de realizar comparações lógicas de status ou categorias.

6. **Feedback Visual de Estado (Banners de Modo)**: Se a aplicação possui diferentes níveis de acesso (ex: Consultor vs Moderador), a interface deve exibir um indicador visual persistente (ex: um banner no topo ou rodapé colorido). Isso evita que o usuário realize ações administrativas por engano ou fique confuso sobre suas permissões atuais.

7. **Sincronização Atômica (Flush Mechanism)**: Após realizar escritas no Spreadsheet via script, utilize `SpreadsheetApp.flush()` para garantir que os dados sejam commitados antes que o script procure ou retorne para o frontend. Isso previne condições de corrida onde o frontend tenta ler um dado que ainda está no buffer do servidor.

8. **Watchdog de Carregamento (Anti-Hang Pattern)**: Nunca permita que a aplicação fique em loop infinito de carregamento (tela branca). Implemente um temporizador (`setTimeout`) no `window.onload` que exiba um botão de diagnóstico ou recarregamento caso o `google.script.run` demore mais de 10-12 segundos para responder. Este padrão é vital em redes corporativas com firewalls restritivos.

9. **Descoberta Dinâmica de Recurso (Dynamic Sheet Discovery)**: Evite falhas fatais por renomeação de abas. Utilize fallbacks lógicos como `ss.getSheetByName('Abas') || ss.getSheets()[0]`. Isso garante que a aplicação continue funcional mesmo que o usuário altere o nome da aba principal por engano.

10. **Compatibilidade Legacy Máxima (Mandatory ES5)**: Ambientes corporativos e iFrames do Google Apps Script frequentemente possuem parsers de JavaScript antigos ou sensíveis. **É proibido o uso de sintaxe ES6+** (let, const, arrow functions, template literals). Utilize exclusivamente o padrão tradicional (var, function, concatenação de strings) para garantir que a aplicação não falhe silenciosamente em redes restritas.

11. **Lei do Layout Vertical 100%**: Para formulários de cadastro e edição, todos os elementos (`label`, `input`, `select`, `textarea`) devem possuir `display: block` e `width: 100%`. Isso previne que o layout "quebre" ou se amontoe horizontalmente em telas menores ou incorporadas, garantindo uma experiência de uso profissional e legível.

12. **Blindagem de Sintaxe (Escaping)**: Sempre passe dados vindos da planilha por uma função de escapamento (`esc()`) no frontend antes de injetá-los no HTML. Aspas simples ou duplas dentro de descrições podem fechar atributos HTML prematuramente e causar erros de sintaxe JS catastróficos que travam o renderizador.

## Techniques & Frameworks

### Custom Modal Framework (Vanilla JS - ES5)
Implementação de modais sem dependências modernas:
1. **Overlay**: `div` com `position: fixed`, `display: none` e `background: rgba(0,0,0,0.8)`.
2. **Box**: `div` interna branca com `border-radius` e preenchimento generoso.
3. **Toggle**: Funções JS tradicionais que alteram o `style.display`. Nunca use animações de bibliotecas externas que podem não carregar por bloqueio de script.

### Role-Based Access Pattern (RBAC - Client Side)
Gerenciamento de permissões sem sessões de servidor:
- No `window.onload`, recupere o segredo do `localStorage`.
- Use uma lógica de `if/else` tradicional para definir variáveis globais `isAdmin` ou `isConsultant`.
- Injete o HTML condicionalmente. Se o usuário não tem permissão, o código do botão administrativo **nem deve ser injetado** no DOM.

### Async Base64 File Upload (ES5 Style)
O upload de arquivos em GAS deve evitar `async/await` se a compatibilidade total for necessária:
1. Capture o arquivo via `input[type="file"]`.
2. Use `new FileReader()`.
3. No evento `onload` do leitor, dispare o `google.script.run` passando o `result`.
4. Garanta que o backend receba o `mimeType` e `fileName` originais para preservação da integridade do arquivo no Drive.

### Deployment Cycle (Rigoroso)
1. Alteração de Código -> 2. Salvar -> 3. "Gerenciar Implantações" -> 4. Editar Ativa -> 5. "Nova Versão" -> 6. Implantar.
**Atenção**: Pular o passo da "Nova Versão" é a causa #1 de usuários relatando que "o erro continua" mesmo após o conserto do desenvolvedor.

## Quality Criteria

- [ ] O Web App utiliza EXCLUSIVAMENTE sintaxe JavaScript ES5 (`var`, `function`, sem crases).
- [ ] Implementou um Watchdog de 12 segundos para prevenir o "Spinner Infinito".
- [ ] Todos os campos de formulário possuem layout vertical 100% (display: block).
- [ ] O Web App não utiliza nenhum modal nativo do navegador (`alert`, `confirm`, `prompt`).
- [ ] O login de Moderador/Consultor persiste no `localStorage` após F5.
- [ ] Os dados vindos da planilha passam por uma função de sanitização (`esc()`) antes da injeção.
- [ ] Existe um indicador visual (Banner) quando o usuário está operando em modo Administrativo.
- [ ] O backend possui fallback para falha de nome de aba (`getSheetByName || getSheets()[0]`).

## Output Examples

### Exemplo 1: Formulário Profissional ES5 com Layout 100%
```html
<style>
  /* Regra 11: Layout Vertical 100% */
  label { display: block; margin-top: 15px; font-weight: bold; color: #333; }
  input, select, textarea { 
    display: block; width: 100%; padding: 10px; border: 1px solid #ccc; 
    border-radius: 5px; box-sizing: border-box; margin-top: 5px;
  }
</style>

<div id="form-container">
  <label>Título da Demanda:</label>
  <input id="titulo" placeholder="Digite o título...">
  
  <label>Categoria:</label>
  <select id="cat">
    <option>Geral</option><option>Supply</option>
  </select>
  
  <button class="btn" onclick="salvarDados()">Enviar</button>
</div>

<script>
  // Regra 10: Sintaxe Tradicional (ES5)
  function salvarDados() {
    var tit = document.getElementById('titulo').value;
    var cat = document.getElementById('cat').value;
    
    if (!tit) { 
      alert("Preencha o título!"); 
      return; 
    }
    
    google.script.run.withSuccessHandler(function() {
      location.reload();
    }).processar(tit, cat);
  }
</script>
```

### Exemplo 2: Watchdog de Resiliência (Boot Seguro)
```javascript
// JS Tradicional no Client
window.onload = function() {
  var carregou = false;
  
  // Watchdog: Se em 10s não tiver resposta, mata o spinner
  var timer = setTimeout(function() {
    if (!carregou) {
      document.getElementById('spinner').style.display = 'none';
      document.getElementById('error-msg').innerHTML = 
        '<p>Conexão lenta. <button onclick="location.reload()">Tentar de Novo</button></p>';
    }
  }, 10000);

  google.script.run.withSuccessHandler(function(dados) {
    carregou = true;
    clearTimeout(timer);
    renderizarInterface(dados);
  }).getMeusDados();
};
```

## Anti-Patterns

### O Que Nunca Fazer
- **Uso de template literals (crases)**: Nunca use `` `Olá ${nome}` ``. Parsers de iFrame do Google Sites frequentemente falham ao encontrar esse caractere, travando a página instantaneamente.
- **Async/Await no Client**: Embora suportado em alguns navegadores modernos, falha em ambientes de rede restritos ou navegadores corporativos legados. Prefira callbacks no `.withSuccessHandler()`.
- **Dependência de Aba Fixa**: Nunca assuma que a aba 'Config' nunca mudará de nome. Use `getSheets()[0]` como proteção final.
- **Layout Inline em Cadastro**: Nunca coloque Label e Input lado a lado se o input for longo. Isso gera rolagem lateral e poluição visual.

### O Que Sempre Fazer
- **Hard-Testing em Aba Anônima**: Sempre teste a versão publicada em aba anônima para garantir que o cache do Google não está mascarando erros.
- **Vincular Versão ao Deploy**: Sempre crie uma "Nova Versão" em cada mudança de lógica. Sem isso, o usuário verá o código antigo.
- **Escaping Manual**: Sempre crie uma função `function esc(s) { return s.replace(/'/g, "&#039;"); }` para proteger injecções de texto.

## Vocabulary Guidance

### Termos para Sempre Usar
- **Legacy Compatibility**: Garantia de funcionamento em ambientes restritos.
- **Watchdog Timer**: Cronômetro de segurança para falhas de rede.
- **Manual Sanitization**: Limpeza de strings e caracteres especiais.
- **ES5 Standard**: Uso de sintaxe JavaScript tradicional (var/function).
- **Vertical Stack**: Layout de formulário onde campos ocupam a largura total.

### Termos para Nunca Usar
- **Arrow Functions**: Substitua por `function()`.
- **Template Strings**: Substitua por concatenação tradicional `'...' + var`.
- **Async Loader**: Substitua por "Watchdog de Carregamento".

### Regras de Tom
- **Segurança Pragmática**: O tom deve desencorajar "novidades" tecnológicas que possam comprometer a estabilidade no Google.
- **Foco em iFrame**: Lembrar sempre que a Wiki vive dentro de uma caixa restritiva do Google.

---
Este guia é o porto seguro para o desenvolvimento de UI em Google Apps Script na squad Equipes_Agentes. Siga-o para evitar os travamentos que já resolvemos historicamente.
