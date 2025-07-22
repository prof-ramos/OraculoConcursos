#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Logging do Oráculo de Concursos
Configuração centralizada de logs com rotação e formatação personalizada
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class OraculoFormatter(logging.Formatter):
    """Formatter personalizado para o Oráculo de Concursos"""
    
    # Cores para terminal
    CORES = {
        'DEBUG': '\033[36m',     # Ciano
        'INFO': '\033[32m',      # Verde
        'WARNING': '\033[33m',   # Amarelo
        'ERROR': '\033[31m',     # Vermelho
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    # Emojis para cada nível
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🚨'
    }
    
    def __init__(self, usar_cores: bool = True, usar_emojis: bool = True):
        super().__init__()
        self.usar_cores = usar_cores and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()
        self.usar_emojis = usar_emojis
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatar registro de log"""
        # Timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Nível com cor e emoji
        nivel = record.levelname
        if self.usar_emojis:
            emoji = self.EMOJIS.get(nivel, '')
            nivel = f"{emoji} {nivel}"
        
        if self.usar_cores:
            cor = self.CORES.get(record.levelname, '')
            reset = self.CORES['RESET']
            nivel = f"{cor}{nivel}{reset}"
        
        # Módulo (limitado a 20 caracteres)
        modulo = record.name
        if len(modulo) > 20:
            modulo = f"...{modulo[-17:]}"
        modulo = modulo.ljust(20)
        
        # Mensagem
        mensagem = record.getMessage()
        
        # Informações extras (se existirem)
        extras = ""
        if hasattr(record, 'extra_info'):
            extras = f" [{record.extra_info}]"
        
        # Formatação final
        log_line = f"{timestamp} | {nivel:<12} | {modulo} | {mensagem}{extras}"
        
        # Adicionar exceção se existir
        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"
        
        return log_line


class DatabaseLogHandler(logging.Handler):
    """Handler personalizado para salvar logs no banco de dados"""
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.buffer = []  # Buffer para logs quando DB não está disponível
        self.max_buffer = 100
    
    def emit(self, record: logging.LogRecord):
        """Emite log para o banco de dados"""
        try:
            if self.db_manager:
                # Tentar salvar no banco
                self._salvar_no_banco(record)
                
                # Processar buffer se existir
                if self.buffer:
                    self._processar_buffer()
            else:
                # Adicionar ao buffer
                self._adicionar_ao_buffer(record)
                
        except Exception:
            # Em caso de erro, adicionar ao buffer
            self._adicionar_ao_buffer(record)
    
    def _salvar_no_banco(self, record: logging.LogRecord):
        """Salva log no banco de dados (implementação futura)"""
        # TODO: Implementar salvamento assíncrono no banco
        pass
    
    def _adicionar_ao_buffer(self, record: logging.LogRecord):
        """Adiciona log ao buffer"""
        if len(self.buffer) >= self.max_buffer:
            self.buffer.pop(0)  # Remove o mais antigo
        
        self.buffer.append({
            'nivel': record.levelname,
            'modulo': record.name,
            'mensagem': record.getMessage(),
            'timestamp': datetime.fromtimestamp(record.created),
            'dados_extras': getattr(record, 'extra_info', None)
        })
    
    def _processar_buffer(self):
        """Processa logs em buffer"""
        for log_entry in self.buffer:
            try:
                # TODO: Salvar no banco
                pass
            except Exception:
                break  # Para de processar se houver erro
        
        # Limpar buffer processado
        self.buffer.clear()
    
    def set_db_manager(self, db_manager):
        """Define o gerenciador de banco de dados"""
        self.db_manager = db_manager
        if self.buffer:
            self._processar_buffer()


def configurar_logger(nome: str = 'oraculo_concursos', 
                     nivel: str = 'INFO',
                     arquivo_log: Optional[str] = None,
                     usar_cores: bool = True,
                     usar_emojis: bool = True,
                     rotacao_mb: int = 10,
                     backup_count: int = 5) -> logging.Logger:
    """
    Configura o sistema de logging do Oráculo de Concursos
    
    Args:
        nome: Nome do logger
        nivel: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        arquivo_log: Caminho do arquivo de log (opcional)
        usar_cores: Se deve usar cores no terminal
        usar_emojis: Se deve usar emojis nos logs
        rotacao_mb: Tamanho máximo do arquivo em MB
        backup_count: Número de backups a manter
    
    Returns:
        Logger configurado
    """
    # Criar logger principal
    logger = logging.getLogger(nome)
    
    # Limpar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Definir nível
    numeric_level = getattr(logging, nivel.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Formatter personalizado
    formatter = OraculoFormatter(usar_cores=usar_cores, usar_emojis=usar_emojis)
    
    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para arquivo (se especificado)
    if arquivo_log:
        # Garantir que o diretório existe
        Path(arquivo_log).parent.mkdir(parents=True, exist_ok=True)
        
        # Handler com rotação
        file_handler = logging.handlers.RotatingFileHandler(
            arquivo_log,
            maxBytes=rotacao_mb * 1024 * 1024,  # Converter MB para bytes
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        # Formatter sem cores para arquivo
        file_formatter = OraculoFormatter(usar_cores=False, usar_emojis=usar_emojis)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(numeric_level)
        logger.addHandler(file_handler)
    
    # Handler para banco de dados
    db_handler = DatabaseLogHandler()
    db_handler.setLevel(logging.WARNING)  # Apenas warnings e erros no banco
    logger.addHandler(db_handler)
    
    # Evitar propagação para o logger raiz
    logger.propagate = False
    
    # Log de inicialização
    logger.info("🚀 Sistema de logging inicializado")
    logger.info(f"📊 Nível de log configurado: {nivel}")
    
    if arquivo_log:
        logger.info(f"📁 Logs salvos em: {arquivo_log}")
    
    return logger


def obter_logger(nome: str) -> logging.Logger:
    """
    Obtém um logger filho com configuração herdada
    
    Args:
        nome: Nome do módulo/componente
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(f'oraculo_concursos.{nome}')


class LogContextManager:
    """Context manager para adicionar informações extras aos logs"""
    
    def __init__(self, logger: logging.Logger, extra_info: str):
        self.logger = logger
        self.extra_info = extra_info
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            record.extra_info = self.extra_info
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_com_contexto(logger: logging.Logger, contexto: str):
    """
    Retorna context manager para logs com informações extras
    
    Args:
        logger: Logger a ser usado
        contexto: Informação extra para adicionar aos logs
    
    Returns:
        Context manager para logging
    """
    return LogContextManager(logger, contexto)


# Configurar logging básico se executado diretamente
if __name__ == "__main__":
    # Teste do sistema de logging
    logger = configurar_logger(
        arquivo_log="logs/teste_oraculo.log",
        nivel="DEBUG"
    )
    
    logger.debug("🔍 Teste de log DEBUG")
    logger.info("ℹ️ Teste de log INFO")
    logger.warning("⚠️ Teste de log WARNING")
    logger.error("❌ Teste de log ERROR")
    
    # Teste com contexto
    with log_com_contexto(logger, "TESTE_CONTEXTO"):
        logger.info("Log com contexto adicional")
    
    # Teste de exceção
    try:
        raise ValueError("Erro de teste")
    except Exception:
        logger.exception("Teste de logging de exceção")
