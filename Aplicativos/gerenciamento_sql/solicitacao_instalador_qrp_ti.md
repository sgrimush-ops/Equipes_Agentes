# Solicitacao de Instalador - Editor QRP Consinco

## Objetivo
Solicitar ao TI, suporte Consinco ou fornecedor o instalador oficial da ferramenta usada para abrir e editar arquivos .QRP do relatorio.

## Texto pronto para enviar

Precisamos do instalador oficial da ferramenta que abre e edita arquivos .QRP utilizados pelo Consinco.

Contexto:
- Estamos ajustando o layout de impressao de um relatorio que usa arquivo .QRP.
- O arquivo base e RelProdlojaComp.QRP.
- A copia de trabalho e RelABCCompradorUltCompraCD.QRP.
- O relatorio precisa continuar abrindo dentro do Consinco pelo fluxo normal de impressao.

Precisamos que seja disponibilizado:
1. O instalador oficial do editor de QRP.
2. A confirmacao do nome exato do produto.
3. Eventual licenca, serial ou chave de ativacao.
4. Eventuais DLLs ou componentes adicionais necessarios.
5. A versao compativel com os arquivos .QRP usados pelo Consinco atual.

Suspeita de produto correto:
- OpenText Gupta Report Builder
- Eventualmente algum pacote Gupta/OpenText relacionado ao ecossistema Team Developer ou SQLWindows

Importante:
- Nao encontramos pacote publico confiavel via winget.
- Nao queremos usar fonte nao oficial para evitar risco de malware ou incompatibilidade.
- Precisamos editar localmente o layout e, depois, copiar o QRP final para a pasta do cliente do Consinco.

## Informacoes tecnicas para anexar
- Arquivo base: C:/Users/Alessandro.soares.BAKLIZI/Downloads/RelProdlojaComp.QRP
- Arquivo de trabalho: C:/Users/Alessandro.soares.BAKLIZI/Downloads/RelABCCompradorUltCompraCD.QRP
- A extensao .QRP nao tem associacao valida configurada no Windows desta maquina.
- O arquivo apresenta cabecalho binario serializado, indicando artefato proprio do builder.

## Resultado esperado
- Editor instalado na maquina local.
- Abertura e edicao valida de arquivos .QRP.
- Capacidade de salvar o novo layout e publicar depois na pasta do cliente do Consinco.