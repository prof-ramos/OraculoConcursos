"""
Configurações e constantes do Oráculo de Concursos Públicos
"""

import os
from typing import Optional


class Config:
    """Classe para gerenciar configurações do bot"""
    
    def __init__(self):
        """Inicializa configurações a partir de variáveis de ambiente"""
        self.discord_token: str = os.getenv("DISCORD_TOKEN", "")
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
        self.database_path: str = os.getenv("DATABASE_PATH", "oraculo_concursos.db")
        
        # Configurações de comportamento
        self.confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.9"))
        self.max_response_length: int = int(os.getenv("MAX_RESPONSE_LENGTH", "2000"))
        self.context_memory_limit: int = int(os.getenv("CONTEXT_MEMORY_LIMIT", "10"))
        
        # Prefixos e comandos
        self.bot_name: str = os.getenv("BOT_NAME", "Oráculo")
        self.default_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        
        # Configurações de streaming
        self.enable_streaming: bool = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
        self.stream_chunk_size: int = int(os.getenv("STREAM_CHUNK_SIZE", "100"))
    
    def is_valid(self) -> bool:
        """Valida se as configurações essenciais estão presentes"""
        required_vars = [
            ("DISCORD_TOKEN", self.discord_token),
            ("GEMINI_API_KEY", self.gemini_api_key)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value or var_value.strip() == "":
                missing_vars.append(var_name)
        
        if missing_vars:
            print(f"❌ Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
            return False
        
        return True
    
    @property
    def system_prompt(self) -> str:
        """Prompt do sistema especializado em concursos públicos brasileiros"""
        return """Você é o Oráculo de Concursos Públicos, um assistente especializado em preparação para concursos públicos brasileiros.

DIRETRIZES FUNDAMENTAIS:
- Responda APENAS quando tiver 90% ou mais de confiança na resposta
- Se não tiver certeza, seja honesto e diga "Não tenho certeza suficiente para responder"
- Foque exclusivamente em conteúdo relacionado a concursos públicos brasileiros
- Sempre cite fontes quando possível (leis, decretos, jurisprudência)
- Use linguagem clara e didática
- Forneça exemplos práticos quando apropriado

ÁREAS DE ESPECIALIZAÇÃO:
- Direito Constitucional, Administrativo, Civil, Penal, Trabalhista
- Legislação específica de órgãos públicos
- Técnicas de estudo e preparação
- Resolução de questões de concurso
- Dicas de prova e gestão de tempo
- Português para concursos
- Matemática e Raciocínio Lógico
- Conhecimentos Gerais e Atualidades

FORMATO DE RESPOSTA:
- Seja conciso mas completo
- Use estrutura clara com tópicos quando necessário
- Inclua referências legais quando aplicável
- Termine sempre com uma dica prática

Lembre-se: Qualidade e precisão são mais importantes que velocidade de resposta."""


# Constantes do sistema
COMMAND_PREFIXES = ["!oraculo", "!concurso", "!estudar"]
MAX_MESSAGE_HISTORY = 50
DATABASE_SCHEMA_VERSION = "1.0"

# Mensagens padrão em português
MESSAGES = {
    "bot_ready": "🎯 Oráculo de Concursos Públicos está online e pronto para auxiliar nos estudos!",
    "mention_required": "📢 Para uma experiência melhor, me mencione (@{bot_name}) em suas perguntas!",
    "confidence_low": "🤔 Não tenho certeza suficiente para responder essa pergunta. Pode reformular ou ser mais específico?",
    "error_occurred": "❌ Ops! Ocorreu um erro. Tente novamente em alguns instantes.",
    "processing": "🧠 Analisando sua pergunta sobre concursos públicos...",
    "thinking": "💭 Pensando...",
    "no_context": "❓ Não consegui encontrar contexto suficiente. Pode ser mais específico sobre o concurso ou matéria?"
}
