---
name: Integração Google API e AppSheet
description: Regras e padrões para agentes conectarem e reusarem acessos ao Google Drive, Gmail ou AppSheet no ecossistema local.
---

# Integração Google API e AppSheet (Skill)

Como agente operando neste sistema, você deve seguir este fluxo sempre que precisar acessar Drives, e-mails do Gmail ou planilhas via AppSheet.

## Onde encontrar a base
O projeto base que detém as credenciais ativas e a configuração da API do Google fica em:
`C:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\integracao_google`

## Como Autenticar (Google Drive / Gmail)
1. **Credenciais:** Nunca exponha o `token.json` nem crie fluxos OAuth novos do zero (isso forçaria o usuário a logar repetidamente). Se o usuário pedir algo novo com o Drive, direcione para operar **através** ou **copiando a arquitetura** do módulo `/integracao_google/autenticacao_google.py`.
2. **Bibliotecas Necessárias:** O pacote mínimo é `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`.

## Como Integrar (AppSheet)
1. O AppSheet se comunica via chamadas REST (`requests`).
2. Utilize SEMPRE o arquivo `.env` para instanciar as constantes `APPSHEET_APP_ID` e `APPSHEET_ACCESS_KEY`.
3. Nunca insira Chaves fixas/Hardcoded no seu código gerado.

## Boas Práticas
- Só construa pipelines sobre essa estrutura se o arquivo `credentials.json` estiver garantido na pasta (Client ID gerado e Oauth Consent Screen configurado incluindo o e-mail do testador).
- Se encontrar problemas de Autorização no Gmail, possivelmente o projeto no "Google Cloud Platform" precisa ativar manualmente a biblioteca `Gmail API`.
