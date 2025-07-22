#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Oráculo de Concursos - Bot Discord para Preparação de Concursos Públicos
Ponto de entrada principal da aplicação
"""

import asyncio
import logging
import os
import signal
import sys
import discord
from pathlib import Path

# Adicionar o diretório raiz ao path para imports
sys.path.append(str(Path(__file__).parent))

from bot.discord_bot import OraculoBot
from database.db_manager import DatabaseManager
from utils.logger import configurar_logger
from utils.debug_logger import get_debug_logger, debug_async_func, MonitorDiscord
from bot.config import Config
from bot.gemini_client import GeminiClient
from bot.anti_alucinacao import ValidadorConfianca


class OraculoApp:
    """Classe principal da aplicação Oráculo de Concursos"""
    
    def __init__(self):
        self.bot = None
        self.db_manager = None
        self.logger = None
        self.debug = get_debug_logger()
        self._running = False
    
    @debug_async_func
    async def inicializar(self):
        """Inicializa todos os componentes da aplicação"""
        try:
            # Configurar logging
            self.debug.registrar_evento("INIT_START")
            self.logger = configurar_logger()
            self.logger.info("🚀 Iniciando Oráculo de Concursos...")
            
            # Debug do ambiente
            self.debug.debug_ambiente()
            self.debug.debug_rede()
            
            # Validar configurações
            self.debug.registrar_evento("CONFIG_START")
            config = Config()
            if not config.is_valid():
                self.debug.registrar_evento("CONFIG_INVALID")
                if self.logger:
                    self.logger.error("❌ Configurações inválidas. Verifique as variáveis de ambiente.")
                return False
            self.debug.registrar_evento("CONFIG_VALID")
            
            # Inicializar banco de dados
            self.debug.registrar_evento("DB_INIT_START")
            self.logger.info("📊 Inicializando banco de dados...")
            self.db_manager = DatabaseManager(config.database_path)
            
            # Testar inicialização completa do banco
            try:
                await self.db_manager.inicializar()
                self.debug.registrar_evento("DB_INIT_SUCCESS")
                self.logger.info("📊 Banco de dados inicializado com sucesso")
            except Exception as db_error:
                self.debug.debug_excecao(db_error, "inicialização do banco")
                self.logger.warning("⚠️ Erro no banco, continuando sem persistência: {db_error}")
                self.debug.registrar_evento("DB_INIT_FAILED", {"erro": str(db_error)})

            # Inicializar componentes
            gemini_client = GeminiClient(config)
            validador = ValidadorConfianca(config)
            
            # Inicializar bot Discord
            self.debug.registrar_evento("BOT_INIT_START")
            self.logger.info("🤖 Inicializando bot Discord...")
            self.bot = OraculoBot(self.db_manager, gemini_client, validador, config)
            self.config = config
            
            # Adicionar monitoramento ao bot
            monitor = MonitorDiscord(self.debug)
            monitor.monitorar_bot(self.bot)
            
            self.debug.registrar_evento("BOT_INIT_SUCCESS")
            self.logger.info("✅ Todos os componentes inicializados com sucesso!")
            return True
            
        except Exception as e:
            self.debug.debug_excecao(e, "inicialização da aplicação")
            if self.logger:
                self.logger.error("❌ Erro durante inicialização: {e}")
            else:
                print("❌ Erro durante inicialização: {e}")
            return False
    
    async def executar(self):
        """Executa o bot principal"""
        if not await self.inicializar():
            sys.exit(1)
        
        try:
            self._running = True
            self.logger.info("🎯 Oráculo de Concursos está online e pronto para ajudar!")
            
            # Configurar handlers para shutdown graceful
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, self._signal_handler)
            
            # Executar o bot
            if self.bot:
                self.debug.registrar_evento("DISCORD_CONNECT_START")
                self.logger.info(f"🔌 Conectando com token: {self.config.discord_token[:8]}...")
                
                # Debug do cliente antes da conexão
                self.debug.debug_discord_client(self.bot)
                
                try:
                    # Usar timeout estendido para conexão
                    self.debug.registrar_evento("DISCORD_START_CALL")
                    await asyncio.wait_for(
                        self.bot.start(self.config.discord_token),
                        timeout=60.0  # Aumentado para 60 segundos
                    )
                    self.debug.registrar_evento("DISCORD_CONNECT_SUCCESS")
                    
                except asyncio.TimeoutError:
                    self.debug.registrar_evento("DISCORD_TIMEOUT")
                    self.logger.error("❌ Timeout na conexão Discord após 60 segundos")
                    
                    # Salvar relatório de debug antes de falhar
                    relatorio_path = self.debug.salvar_relatorio()
                    self.logger.error(f"📋 Relatório de debug salvo em: {relatorio_path}")
                    raise
                    
                except discord.LoginFailure as e:
                    self.debug.debug_excecao(e, "autenticação Discord")
                    self.logger.error(f"❌ Falha na autenticação Discord: {e}")
                    raise
                    
                except discord.HTTPException as e:
                    self.debug.debug_excecao(e, "HTTP Discord")
                    self.logger.error(f"❌ Erro HTTP Discord: {e}")
                    raise
                    
                except Exception as e:
                    self.debug.debug_excecao(e, "conexão Discord inesperada")
                    self.logger.error(f"❌ Erro inesperado na conexão Discord: {e}")
                    raise
            
        except KeyboardInterrupt:
            self.debug.registrar_evento("USER_INTERRUPT")
            if self.logger:
                self.logger.info("⏹️ Interrupção pelo usuário...")
        except Exception as e:
            self.debug.debug_excecao(e, "execução principal")
            if self.logger:
                self.logger.error(f"❌ Erro durante execução: {e}")
        finally:
            # Gerar relatório final antes de finalizar
            if self.debug:
                relatorio_path = self.debug.salvar_relatorio()
                if self.logger:
                    self.logger.info(f"📋 Relatório final de debug: {relatorio_path}")
            
            await self.finalizar()
    
    def _signal_handler(self, signum, frame):
        """Handler para sinais de sistema"""
        if self.logger:
            self.logger.info(f"📨 Sinal {signum} recebido. Iniciando shutdown graceful...")
        self._running = False
        
        # Criar task para finalização assíncrona
        asyncio.create_task(self.finalizar())
    
    async def finalizar(self):
        """Finaliza todos os componentes da aplicação"""
        if not self._running:
            return
        
        self._running = False
        if self.logger:
            self.logger.info("🔄 Finalizando Oráculo de Concursos...")
        
        try:
            # Fechar conexão do bot
            if self.bot and not self.bot.is_closed():
                await self.bot.close()
            
            # Fechar conexão do banco
            if self.db_manager:
                # O aiosqlite não tem um método close() explícito no manager
                pass
            
            if self.logger:
                self.logger.info("✅ Shutdown completado com sucesso!")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Erro durante finalização: {e}")


async def main():
    """Função principal"""
    app = OraculoApp()
    await app.executar()


if __name__ == "__main__":
    try:
        # Verificar versão do Python
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ é necessário para executar o Oráculo de Concursos")
            sys.exit(1)
        
        # Executar aplicação
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n⏹️ Aplicação interrompida pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)