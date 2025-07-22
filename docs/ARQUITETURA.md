# Arquitetura do Sistema Oráculo de Concursos

## Visão Geral

O Oráculo de Concursos é um bot do Discord projetado para fornecer informações precisas e confiáveis sobre concursos públicos, aproveitando o poder da IA generativa do Google Gemini, com um sistema robusto de anti-alucinação para garantir a qualidade das respostas.

## Componentes Principais

1.  **Bot do Discord (`discord_bot.py`):**
    *   Interface principal com o usuário no Discord.
    *   Responsável por receber comandos, interagir com os usuários e apresentar as respostas geradas.
    *   Utiliza a biblioteca `discord.py` para a integração com a API do Discord.

2.  **Cliente Gemini (`gemini_client.py`):**
    *   Módulo que encapsula a lógica de comunicação com a API do Google Gemini.
    *   Envia as perguntas dos usuários para o modelo de IA e recebe as respostas geradas.
    *   Implementa a lógica de tratamento de erros e retentativas de conexão.

3.  **Sistema Anti-Alucinação (`anti_alucinacao.py`):**
    *   Componente crítico que garante a confiabilidade das informações.
    *   Analisa as respostas do Gemini para verificar a presença de informações factualmente incorretas ou "alucinações" da IA.
    *   Utiliza técnicas de verificação de fatos e validação cruzada (a serem implementadas) para garantir a precisão.

4.  **Gerenciador de Banco de Dados (`db_manager.py`):**
    *   Responsável pela interação com o banco de dados SQLite.
    *   Armazena o histórico de interações, feedback dos usuários e outras informações relevantes.
    *   Utiliza o SQLAlchemy para o mapeamento objeto-relacional (ORM).

5.  **Modelos de Dados (`models.py`):**
    *   Define a estrutura das tabelas do banco de dados usando o SQLAlchemy.

6.  **Configuração (`config.py`):**
    *   Centraliza a gestão de configurações da aplicação, como chaves de API e tokens.
    *   Carrega as variáveis de ambiente de um arquivo `.env` para manter a segurança das credenciais.

7.  **Logging (`logger.py` e `debug_logger.py`):**
    *   Sistema de logs para registrar eventos importantes, erros e informações de depuração.
    *   Facilita o monitoramento e a solução de problemas da aplicação.

## Fluxo de Dados

1.  O usuário envia uma pergunta para o bot no Discord.
2.  O `discord_bot.py` recebe a mensagem e a encaminha para o `gemini_client.py`.
3.  O `gemini_client.py` envia a pergunta para a API do Google Gemini.
4.  A API do Gemini retorna uma resposta gerada pela IA.
5.  A resposta é passada para o `anti_alucinacao.py` para validação.
6.  Se a resposta for considerada válida, ela é enviada de volta para o `discord_bot.py`.
7.  O `discord_bot.py` exibe a resposta final para o usuário no canal do Discord.
8.  A interação é registrada no banco de dados pelo `db_manager.py`.

## Segurança

*   **Gerenciamento de Credenciais:** As chaves de API e tokens são gerenciados de forma segura através de variáveis de ambiente, carregadas a partir de um arquivo `.env` que não é versionado no Git.
*   **Validação de Entrada:** A ser implementada para prevenir ataques de injeção e outros tipos de exploração.
