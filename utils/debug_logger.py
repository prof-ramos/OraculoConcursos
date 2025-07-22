#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Debug Avançado para Oráculo de Concursos
Logging detalhado para investigação de problemas
"""

import asyncio
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import discord


class DebugLogger:
    """Logger especializado para debug do bot Discord"""
    
    def __init__(self, nome: str = "oraculo_debug"):
        self.nome = nome
        self.logger = logging.getLogger(nome)
        self.start_time = time.time()
        self.events = []
        
        # Configurar logger de debug
        self._configurar_logger()
        
    def _configurar_logger(self):
        """Configura logger com máximo detalhamento"""
        # Remover handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Configurar nível máximo
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Handler para arquivo
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Formato detalhado
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Configurar loggers do discord.py para DEBUG
        discord_logger = logging.getLogger('discord')
        discord_logger.setLevel(logging.DEBUG)
        discord_logger.addHandler(file_handler)
        
        asyncio_logger = logging.getLogger('asyncio')
        asyncio_logger.setLevel(logging.DEBUG)
        asyncio_logger.addHandler(file_handler)
        
    def registrar_evento(self, evento: str, dados: Optional[Dict[str, Any]] = None):
        """Registra evento com timestamp para análise de timeline"""
        timestamp = time.time()
        evento_data = {
            'timestamp': timestamp,
            'tempo_relativo': timestamp - self.start_time,
            'evento': evento,
            'dados': dados or {}
        }
        
        self.events.append(evento_data)
        self.logger.debug(f"EVENTO: {evento} | Tempo: {evento_data['tempo_relativo']:.3f}s | Dados: {dados}")
        
    def debug_ambiente(self):
        """Registra informações do ambiente"""
        info_ambiente = {
            'python_version': sys.version,
            'discord_py_version': discord.__version__,
            'platform': sys.platform,
            'working_directory': os.getcwd(),
            'environment_vars': {
                'DISCORD_TOKEN': '***PRESENTE***' if os.getenv('DISCORD_TOKEN') else 'AUSENTE',
                'GEMINI_API_KEY': '***PRESENTE***' if os.getenv('GEMINI_API_KEY') else 'AUSENTE'
            }
        }
        
        self.registrar_evento("DEBUG_AMBIENTE", info_ambiente)
        return info_ambiente
        
    def debug_rede(self):
        """Testa conectividade básica"""
        import subprocess
        
        try:
            # Teste de DNS
            result_dns = subprocess.run(['nslookup', 'discord.com'], 
                                      capture_output=True, text=True, timeout=5)
            
            # Teste de conectividade
            result_ping = subprocess.run(['ping', '-c', '3', 'discord.com'], 
                                       capture_output=True, text=True, timeout=10)
            
            info_rede = {
                'dns_lookup': result_dns.returncode == 0,
                'ping_success': result_ping.returncode == 0,
                'dns_output': result_dns.stdout[:200] if result_dns.stdout else '',
                'ping_output': result_ping.stdout[:200] if result_ping.stdout else ''
            }
            
        except Exception as e:
            info_rede = {
                'erro': str(e),
                'teste_executado': False
            }
        
        self.registrar_evento("DEBUG_REDE", info_rede)
        return info_rede
        
    def debug_discord_client(self, client: discord.Client):
        """Debug específico do cliente Discord"""
        if not client:
            self.registrar_evento("DEBUG_DISCORD", {"erro": "Cliente é None"})
            return
            
        info_client = {
            'closed': client.is_closed(),
            'ready': client.is_ready() if hasattr(client, 'is_ready') else False,
            'user': str(client.user) if client.user else 'None',
            'latency': getattr(client, 'latency', 'N/A'),
            'guilds_count': len(client.guilds) if hasattr(client, 'guilds') else 'N/A'
        }
        
        self.registrar_evento("DEBUG_DISCORD", info_client)
        return info_client
        
    def debug_excecao(self, excecao: Exception, contexto: str = ""):
        """Registra exceção com stack trace completo"""
        erro_data = {
            'tipo': type(excecao).__name__,
            'mensagem': str(excecao),
            'contexto': contexto,
            'stack_trace': traceback.format_exc()
        }
        
        self.registrar_evento("EXCECAO", erro_data)
        self.logger.error(f"EXCEÇÃO em {contexto}: {type(excecao).__name__}: {excecao}")
        self.logger.error(f"Stack trace:\n{traceback.format_exc()}")
        
    def gerar_relatorio(self) -> str:
        """Gera relatório completo de debug"""
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("RELATÓRIO DE DEBUG - ORÁCULO DE CONCURSOS")
        relatorio.append("=" * 80)
        relatorio.append(f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        relatorio.append(f"Duração da sessão: {time.time() - self.start_time:.2f} segundos")
        relatorio.append(f"Total de eventos: {len(self.events)}")
        relatorio.append("")
        
        # Timeline de eventos
        relatorio.append("TIMELINE DE EVENTOS:")
        relatorio.append("-" * 40)
        for evento in self.events:
            relatorio.append(f"[{evento['tempo_relativo']:8.3f}s] {evento['evento']}")
            if evento['dados']:
                for key, value in evento['dados'].items():
                    relatorio.append(f"    {key}: {value}")
        
        relatorio.append("")
        relatorio.append("=" * 80)
        
        return "\n".join(relatorio)
        
    def salvar_relatorio(self, arquivo: Optional[str] = None) -> str:
        """Salva relatório em arquivo"""
        if not arquivo:
            arquivo = f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        caminho = Path("logs") / arquivo
        caminho.parent.mkdir(exist_ok=True)
        
        relatorio = self.gerar_relatorio()
        
        with open(caminho, 'w', encoding='utf-8') as f:
            f.write(relatorio)
        
        self.logger.info(f"Relatório de debug salvo em: {caminho}")
        return str(caminho)


class MonitorDiscord:
    """Monitor específico para eventos Discord"""
    
    def __init__(self, debug_logger: DebugLogger):
        self.debug = debug_logger
        
    def monitorar_bot(self, bot):
        """Adiciona monitoramento a um bot Discord"""
        
        # Monitorar eventos principais
        @bot.event
        async def on_connect():
            self.debug.registrar_evento("DISCORD_CONNECT", {
                'latency': bot.latency,
                'user': str(bot.user) if bot.user else 'None'
            })
            
        @bot.event  
        async def on_ready():
            self.debug.registrar_evento("DISCORD_READY", {
                'user': str(bot.user),
                'guilds': len(bot.guilds),
                'latency': bot.latency
            })
            
        @bot.event
        async def on_disconnect():
            self.debug.registrar_evento("DISCORD_DISCONNECT")
            
        @bot.event
        async def on_error(event, *args, **kwargs):
            self.debug.registrar_evento("DISCORD_ERROR", {
                'event': event,
                'args': str(args)[:200],
                'kwargs': str(kwargs)[:200]
            })


# Singleton global para debug
_debug_instance = None

def get_debug_logger() -> DebugLogger:
    """Obtém instância global do debug logger"""
    global _debug_instance
    if _debug_instance is None:
        _debug_instance = DebugLogger()
    return _debug_instance


# Decorator para debug de funções
def debug_func(func):
    """Decorator para debug automático de funções"""
    def wrapper(*args, **kwargs):
        debug = get_debug_logger()
        debug.registrar_evento(f"FUNC_START", {'function': func.__name__})
        
        try:
            result = func(*args, **kwargs)
            debug.registrar_evento(f"FUNC_END", {'function': func.__name__, 'success': True})
            return result
        except Exception as e:
            debug.debug_excecao(e, f"função {func.__name__}")
            raise
            
    return wrapper


def debug_async_func(func):
    """Decorator para debug de funções assíncronas"""
    async def wrapper(*args, **kwargs):
        debug = get_debug_logger()
        debug.registrar_evento(f"ASYNC_FUNC_START", {'function': func.__name__})
        
        try:
            result = await func(*args, **kwargs)
            debug.registrar_evento(f"ASYNC_FUNC_END", {'function': func.__name__, 'success': True})
            return result
        except Exception as e:
            debug.debug_excecao(e, f"função assíncrona {func.__name__}")
            raise
            
    return wrapper