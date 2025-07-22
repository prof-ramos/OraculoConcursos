# Guia de Uso do `gemini-cli`

Este documento fornece um guia completo para interagir com o projeto Oráculo de Concursos utilizando a interface de linha de comando `gemini-cli`.

## Requisitos

*   `gemini-cli` instalado e configurado.
*   Acesso ao repositório do projeto.

## Configuração do Ambiente

1.  **Clone o repositório:**

    ```bash
    git clone <URL_DO_REPOSITORIO>
    cd OraculoConcursos
    ```

2.  **Crie e configure o arquivo de ambiente:**

    Copie o arquivo de exemplo `.env.example` para `.env` e preencha com suas chaves de API e tokens:

    ```bash
    cp .env.example .env
    ```

    **Conteúdo do `.env`:**

    ```
    DISCORD_TOKEN=seu_token_discord_aqui
    GEMINI_API_KEY=sua_chave_api_gemini_aqui
    ```

## Exemplos de Comandos `gemini-cli`

*   **Listar arquivos do projeto:**

    ```bash
    ls -R
    ```

*   **Ler o conteúdo de um arquivo:**

    ```bash
    cat bot/discord_bot.py
    ```

*   **Executar testes:**

    ```bash
    python test_bot_simple.py
    ```

*   **Instalar dependências:**

    ```bash
    pip install -r requirements.txt
    ```

## Solução de Problemas Comuns

*   **Erro de `ModuleNotFoundError`:** Certifique-se de que todas as dependências do `pyproject.toml` estão instaladas no seu ambiente virtual.
*   **Erro de Autenticação:** Verifique se as suas credenciais no arquivo `.env` estão corretas e se o arquivo está na raiz do projeto.