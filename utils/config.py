#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurações do Oráculo de Concursos
Gerencia todas as configurações do sistema via variáveis de ambiente
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Classe para gerenciar configurações do sistema"""
    
    # Tokens obrigatórios
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Configurações do banco de dados
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/oraculo_concursos.db")
    DATABASE_BACKUP_INTERVAL: int = int(os.getenv("DATABASE_BACKUP_INTERVAL", "24"))  # horas
    
    # Configurações de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/oraculo_concursos.log")
    LOG_ROTATION_MB: int = int(os.getenv("LOG_ROTATION_MB", "10"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Configurações do Gemini
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
    GEMINI_TEMPERATURE: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    GEMINI_MAX_TOKENS: int = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
    GEMINI_TIMEOUT: int = int(os.getenv("GEMINI_TIMEOUT", "30"))  # segundos
    
    # Configurações anti-alucinação
    CONFIANCA_MINIMA: float = float(os.getenv("CONFIANCA_MINIMA", "0.9"))
    VERIFICAR_FONTES: bool = os.getenv("VERIFICAR_FONTES", "true").lower() == "true"
    
    # Configurações do Discord
    COMANDO_PREFIX: str = os.getenv("COMANDO_PREFIX", "!oraculo")
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
    TYPING_DELAY: float = float(os.getenv("TYPING_DELAY", "0.5"))
    
    # Configurações de performance
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # segundos
    MAX_HISTORY_ENTRIES: int = int(os.getenv("MAX_HISTORY_ENTRIES", "5"))
    
    # Configurações de manutenção
    CLEANUP_INTERVAL: int = int(os.getenv("CLEANUP_INTERVAL", "24"))  # horas
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "90"))
    
    # Configurações de desenvolvimento
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false").lower() == "true"
    DEVELOPMENT: bool = os.getenv("DEVELOPMENT", "false").lower() == "true"
    
    # Configurações de segurança
    RATE_LIMIT_PER_USER: int = int(os.getenv("RATE_LIMIT_PER_USER", "10"))  # por minuto
    BLACKLIST_WORDS: str = os.getenv("BLACKLIST_WORDS", "")
    
    @classmethod
    def validar(cls) -> bool:
        """
        Valida se todas as configurações obrigatórias estão presentes
        
        Returns:
            True se todas as configurações são válidas
        """
        logger = logging.getLogger(__name__)
        
        # Verificar tokens obrigatórios
        if not cls.DISCORD_TOKEN:
            logger.error("❌ DISCORD_TOKEN não configurado")
            return False
        
        if not cls.GEMINI_API_KEY:
            logger.error("❌ GEMINI_API_KEY não configurado")
            return False
        
        # Verificar valores numéricos
        try:
            validacoes_numericas = [
                ("CONFIANCA_MINIMA", cls.CONFIANCA_MINIMA, 0.0, 1.0),
                ("GEMINI_TEMPERATURE", cls.GEMINI_TEMPERATURE, 0.0, 2.0),
                ("GEMINI_MAX_TOKENS", cls.GEMINI_MAX_TOKENS, 1, 8192),
                ("MAX_CONCURRENT_REQUESTS", cls.MAX_CONCURRENT_REQUESTS, 1, 100),
                ("RATE_LIMIT_PER_USER", cls.RATE_LIMIT_PER_USER, 1, 100)
            ]
            
            for nome, valor, minimo, maximo in validacoes_numericas:
                if not (minimo <= valor <= maximo):
                    logger.error(f"❌ {nome} deve estar entre {minimo} e {maximo}: {valor}")
                    return False
        
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro na validação de configurações numéricas: {e}")
            return False
        
        # Verificar se o diretório de logs pode ser criado
        try:
            Path(cls.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"❌ Não foi possível criar diretório de logs: {e}")
            return False
        
        # Verificar se o diretório do banco pode ser criado
        try:
            Path(cls.DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"❌ Não foi possível criar diretório do banco: {e}")
            return False
        
        logger.info("✅ Todas as configurações são válidas")
        return True
    
    @classmethod
    def obter_resumo(cls) -> Dict[str, Any]:
        """
        Obtém resumo das configurações (sem informações sensíveis)
        
        Returns:
            Dicionário com resumo das configurações
        """
        return {
            'discord_token_configurado': bool(cls.DISCORD_TOKEN),
            'gemini_api_key_configurado': bool(cls.GEMINI_API_KEY),
            'database_path': cls.DATABASE_PATH,
            'log_level': cls.LOG_LEVEL,
            'gemini_model': cls.GEMINI_MODEL,
            'confianca_minima': cls.CONFIANCA_MINIMA,
            'debug_mode': cls.DEBUG_MODE,
            'development': cls.DEVELOPMENT,
            'max_concurrent_requests': cls.MAX_CONCURRENT_REQUESTS,
            'rate_limit_per_user': cls.RATE_LIMIT_PER_USER
        }
    
    @classmethod
    def carregar_de_arquivo(cls, caminho_arquivo: str) -> bool:
        """
        Carrega configurações de um arquivo .env
        
        Args:
            caminho_arquivo: Caminho para o arquivo de configuração
        
        Returns:
            True se o arquivo foi carregado com sucesso
        """
        logger = logging.getLogger(__name__)
        
        try:
            if not Path(caminho_arquivo).exists():
                logger.warning(f"⚠️ Arquivo de configuração não encontrado: {caminho_arquivo}")
                return False
            
            # Carregar arquivo .env manualmente (sem dependência externa)
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    
                    # Ignorar comentários e linhas vazias
                    if not linha or linha.startswith('#'):
                        continue
                    
                    # Dividir chave=valor
                    if '=' in linha:
                        chave, valor = linha.split('=', 1)
                        chave = chave.strip()
                        valor = valor.strip().strip('"').strip("'")
                        
                        # Definir variável de ambiente se não existir
                        if chave and not os.getenv(chave):
                            os.environ[chave] = valor
            
            logger.info(f"✅ Configurações carregadas de: {caminho_arquivo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar arquivo de configuração: {e}")
            return False
    
    @classmethod
    def salvar_exemplo(cls, caminho_arquivo: str = ".env.example") -> bool:
        """
        Salva um arquivo de exemplo com todas as configurações
        
        Args:
            caminho_arquivo: Caminho onde salvar o arquivo de exemplo
        
        Returns:
            True se o arquivo foi salvo com sucesso
        """
        logger = logging.getLogger(__name__)
        
        try:
            conteudo_exemplo = """# Configurações do Oráculo de Concursos
# Copie este arquivo para .env e configure os valores

# === TOKENS OBRIGATÓRIOS ===
DISCORD_TOKEN=seu_token_discord_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui

# === CONFIGURAÇÕES DO BANCO ===
DATABASE_PATH=data/oraculo_concursos.db
DATABASE_BACKUP_INTERVAL=24

# === CONFIGURAÇÕES DE LOG ===
LOG_LEVEL=INFO
LOG_FILE=logs/oraculo_concursos.log
LOG_ROTATION_MB=10
LOG_BACKUP_COUNT=5

# === CONFIGURAÇÕES DO GEMINI ===
GEMINI_MODEL=gemini-2.5-pro
GEMINI_TEMPERATURE=0.1
GEMINI_MAX_TOKENS=2048
GEMINI_TIMEOUT=30

# === CONFIGURAÇÕES ANTI-ALUCINAÇÃO ===
CONFIANCA_MINIMA=0.9
VERIFICAR_FONTES=true

# === CONFIGURAÇÕES DO DISCORD ===
COMANDO_PREFIX=!oraculo
MAX_MESSAGE_LENGTH=2000
TYPING_DELAY=0.5

# === CONFIGURAÇÕES DE PERFORMANCE ===
MAX_CONCURRENT_REQUESTS=10
CACHE_TTL=300
MAX_HISTORY_ENTRIES=5

# === CONFIGURAÇÕES DE MANUTENÇÃO ===
CLEANUP_INTERVAL=24
DATA_RETENTION_DAYS=90

# === CONFIGURAÇÕES DE DESENVOLVIMENTO ===
DEBUG_MODE=false
DEVELOPMENT=false

# === CONFIGURAÇÕES DE SEGURANÇA ===
RATE_LIMIT_PER_USER=10
BLACKLIST_WORDS=
"""
            
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo_exemplo)
            
            logger.info(f"✅ Arquivo de exemplo salvo em: {caminho_arquivo}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar arquivo de exemplo: {e}")
            return False


# Carregar configurações do arquivo .env se existir
if Path('.env').exists():
    Config.carregar_de_arquivo('.env')

# Configurações específicas para desenvolvimento
if Config.DEVELOPMENT:
    Config.LOG_LEVEL = "DEBUG"
    Config.GEMINI_TEMPERATURE = 0.0  # Mais determinístico em dev
