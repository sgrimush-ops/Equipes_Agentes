# Aprendizado — Orquestração Híbrida IA Online + Ollama Local (CPU sem GPU)

- **Data:** 2026-11-19
- **Regra Principal:** A **REGRA #0 — Orquestração Híbrida Obrigatória** deve permanecer no **topo absoluto** de `.agents/AGENTS.md` (primeiras linhas), pois arquivos muito grandes (> ~24 KB) têm o final truncado no carregamento automático de `<user_rules>`.

## Roteamento Otimizado para CPU (Sem GPU Dedicada)

Benchmark local medido em `http://127.0.0.1:11434`:
- `qwen2.5-coder:1.5b` (0,92 GB): **~11,75 tok/s** — padrão para `sql`, `python` e `codigo_rapido`.
- `hermes3:latest` (4,34 GB): **~3,03 tok/s** — padrão para `var_f7`, `dados` e `geral`.
- `gemma4:latest` (8,95 GB): **~4,30 tok/s** — uso sob demanda via `--modelo gemma4:latest`.

## Boas Práticas do Fluxo Híbrido
1. **Delegação de Digitação:** Toda geração de arquivo novo ou bloco extenso (SQL, Python, `Var - F7`, templates, resumos) vai para `python orquestracao/scripts/executor_ollama.py executar`.
2. **Edições Pontuais:** Ajustes cirúrgicos pequenos (`edit_file`) em arquivos existentes permanecem na IA Online.
3. **Keep-Alive:** O `executor_ollama.py` usa `keep_alive: "10m"`, `num_ctx: 3072`, `num_predict: 1536` e `timeout: 300` para evitar recarregamento constante da RAM e timeouts em CPU.
4. **Revisão Obrigatória:** A IA Online sempre lê e valida o arquivo gerado pelo Ollama (especialmente regras Consinco como `SELECT * FROM (...)` e ausência de `;` ou `--`) e usa `ensinar` quando houver desvio.
