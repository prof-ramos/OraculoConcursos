# 🔮 Oráculo de Concursos - Bot Discord

**Um bot inteligente para Discord, especializado na preparação para concursos públicos brasileiros.**

Este projeto integra a poderosa API Gemini do Google com um bot do Discord para fornecer assistência de alta qualidade a estudantes de concursos. Ele é construído com Python, usando `discord.py`, e incorpora estratégias avançadas para garantir a confiabilidade das informações.

## ✅ Status do Projeto: Funcional com Observações

O bot está **operacional**, mas enfrenta um desafio de conectividade específico no ambiente Replit que impede a inicialização completa do framework. Os componentes individuais foram testados e funcionam perfeitamente.

Para mais detalhes técnicos sobre os desafios e soluções, consulte o documento [DESAFIOS_TECNICO.md](DESAFIOS_TECNICO.md).

## 📋 Funcionalidades Principais

- **🎯 Especialização Profunda**: Foco exclusivo em legislação, jurisprudência e doutrina para concursos públicos no Brasil.
- **🧠 Inteligência Artificial Avançada**: Utiliza o modelo Gemini do Google para gerar respostas precisas e contextualmente relevantes.
- **🛡️ Sistema Anti-Alucinação**: Implementa um mecanismo de verificação de confiança e credibilidade para minimizar informações incorretas, citando fontes sempre que possível.
- **💬 Interação Intuitiva**: O bot responde diretamente a menções (`@bot`), mantendo os canais organizados.
- **📊 Memória Conversacional**: Mantém o contexto das interações para oferecer uma experiência de diálogo fluida e coerente.
- **⚡ Respostas em Tempo Real**: A funcionalidade de streaming de respostas simula uma digitação em tempo real, melhorando a experiência do usuário.

## 🏗️ Arquitetura e Tecnologias

O bot é construído sobre uma arquitetura modular e robusta, utilizando as seguintes tecnologias:

- **Linguagem**: Python 3.10+
- **Framework Discord**: `discord.py`
- **Inteligência Artificial**: Google Gemini API
- **Banco de Dados**: `aiosqlite` para persistência de dados assíncrona.
- **Gerenciamento de Pacotes**: `uv`

A estrutura do projeto inclui:
- **`main.py`**: Ponto de entrada da aplicação.
- **`bot/`**: Módulos principais do bot, incluindo a lógica de interação com o Discord (`discord_bot.py`) e a comunicação com a API do Gemini (`gemini_client.py`).
- **`database/`**: Gerenciamento do banco de dados (`db_manager.py`) e modelos (`models.py`).
- **`utils/`**: Ferramentas auxiliares, como o sistema de logging e o módulo anti-alucinação.

## 🚀 Instalação e Configuração

Siga os passos abaixo para configurar e executar o bot em seu ambiente local.

### Pré-requisitos

- Python 3.10 ou superior
- Uma conta de desenvolvedor no Discord com um aplicativo de bot criado.
- Uma chave de API do Google Gemini.

### Passos de Instalação

1.  **Clone o Repositório**
    ```bash
    git clone https://github.com/seu-usuario/oraculo-concursos.git
    cd oraculo-concursos
    ```

2.  **Instale as Dependências**
    O projeto utiliza `uv` para gerenciamento de pacotes.
    ```bash
    pip install uv
    uv sync
    ```

3.  **Configure as Variáveis de Ambiente**
    Copie o arquivo de exemplo `.env.example` para `.env` e preencha com suas chaves de API e tokens:
    ```bash
    cp .env.example .env
    ```
    Edite o arquivo `.env` com as seguintes informações:
    ```
    DISCORD_TOKEN=SEU_TOKEN_DO_DISCORD
    GEMINI_API_KEY=SUA_CHAVE_DA_API_GEMINI
    ```

4.  **Execute o Bot**
    ```bash
    python main.py
    ```

Para uma configuração detalhada do bot no Discord, incluindo a criação do aplicativo e a obtenção do token, consulte o guia [CONFIGURACAO_DISCORD.md](CONFIGURACAO_DISCORD.md).

## 🤝 Como Contribuir

Contribuições são bem-vindas! Se você deseja melhorar o Oráculo de Concursos, siga os passos abaixo:

1.  **Faça um Fork** do repositório.
2.  **Crie uma Nova Branch**: `git checkout -b feature/sua-feature`.
3.  **Faça suas Alterações**: Implemente suas melhorias ou correções.
4.  **Faça o Commit**: `git commit -m 'feat: Adiciona nova funcionalidade'`.
5.  **Envie para o GitHub**: `git push origin feature/sua-feature`.
6.  **Abra um Pull Request**.

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.