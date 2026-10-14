# NORMATIVA ESTRITA DE SEGURANÇA: CONTROLE DE DEPLOYS E INVIOLABILIDADE DE ORDENS RESTRITIVAS

Este documento estabelece normas operacionais permanentes, inegociáveis e de prioridade máxima para a atuação de qualquer agente neste workspace.

---

## 1. INVIOLABILIDADE DE ORDENS RESTRITIVAS DO USUÁRIO
* **Peso Infinito de Instruções Negativas:** Sempre que o usuário utilizar termos proibitivos ou restritivos como:
  - *"NÃO envie"*
  - *"NÃO altere"*
  - *"NÃO faça deploy"*
  - *"NÃO delete"*
  - *"NÃO reinicie"*
  - *"Apenas envie o arquivo X e nada mais"*
* **Regra de Cumprimento:** Essa ordem atua como uma barreira de segurança rígida (Hard Constraint). O agente está **terminantemente proibido** de executar qualquer ação, script, comando ou requisição que toque, envie ou modifique o escopo proibido, independentemente de boas intenções técnicas, rotinas prévias ou conceitos de "proatividade".

---

## 2. PROIBIÇÃO PERMANENTE DE DEPLOYS DESTA MÁQUINA LOCAL
* **APP_Bak reside e opera exclusivamente no Servidor de Produção (`192.168.50.211`):**
  - O código-fonte, atualizações de sistema, front-end, rotas e regras do APP_Bak são gerenciados **diretamente no servidor**.
  - Esta máquina local é **apenas um nó de extração e tratamento de dados brutos**.
* **Ações Estritamente Proibidas nesta Máquina:**
  1. É proibido executar qualquer script com nome ou função de deploy (ex: `PUBLICAR_NO_SERVIDOR.py`, `PUBLICAR_NO_SERVIDOR.bat` ou similares).
  2. É proibido fazer requisições HTTP do tipo POST para endpoints de pacote de código, tais como `/api/admin/deploy`.
  3. É proibido empacotar pastas locais em ZIP e transferir código para o servidor remoto.
* **Única Comunicação Autorizada com o Servidor do Aplicativo (`192.168.50.211`):**
  - Envio exclusivo do binário de dados do dia ([query.parquet](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet)) através do script [upload_direto_banco.py](file:///c:/Users/usr/Downloads/Equipes_Agentes/Aplicativos/import_querys/upload_direto_banco.py) via POST para `/api/admin/upload-query`.
  - Nenhuma outra rota de escrita no servidor pode ser acionada.

---

## 3. CHECKLIST PRÉ-EXECUÇÃO OBRIGATÓRIO PARA ENVIO DE DADOS / SCRIPTS
Antes de rodar qualquer script que faça comunicação de rede (`urllib`, `requests`, `subprocess`, `git push`), o agente deve validar internamente:
1. O comando ou script toca em algum servidor externo/remoto?
2. O que exatamente está sendo transmitido? (É estritamente dados brutos autorizados ou há código/arquivos de sistema no meio?)
3. O usuário autorizou expressamente esse envio na mensagem recente?
4. Há alguma instrução restritiva em vigor?

Se houver qualquer divergência ou dúvida sobre o escopo, **NÃO execute** e restrinja-se unicamente ao que foi solicitado.
