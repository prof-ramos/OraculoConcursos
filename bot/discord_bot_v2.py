#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Discord do Oráculo de Concursos - Versão Simplificada
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

from bot.gemini_client import GeminiClient
from database.db_manager import DatabaseManager
from utils.anti_alucinacao import ValidadorConfianca


class OraculoBotV2(commands.Bot):
    """Bot principal do Oráculo de Concursos - Versão Simplificada"""
    
    def __init__(self, db_manager: DatabaseManager):
        # Configurar intents necessários
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!oraculo ',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Componentes serão inicializados após conexão
        self.gemini_client = None
        self.validador = None
        self.components_ready = False
        
        # Estatísticas
        self.estatisticas = {
            'mensagens_processadas': 0,
            'respostas_enviadas': 0,
            'erros_ocorridos': 0,
            'tempo_inicio': time.time()
        }
    
    async def on_ready(self):
        """Evento chamado quando o bot está pronto"""
        self.logger.info(f"🤖 {self.user} está online!")
        self.logger.info(f"📊 Conectado a {len(self.guilds)} servidor(es)")
        
        # Listar servidores conectados
        for guild in self.guilds:
            self.logger.info(f"📋 Servidor: {guild.name} (ID: {guild.id})")
        
        # Inicializar componentes AI
        await self._inicializar_componentes()
        
        # Configurar status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="concursos públicos | @me para dúvidas"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        self.logger.info("✅ Bot totalmente inicializado e pronto!")
    
    async def _inicializar_componentes(self):
        """Inicializa componentes AI após conexão Discord"""
        try:
            self.logger.info("🔧 Inicializando componentes AI...")
            
            # Inicializar Gemini Client
            self.gemini_client = GeminiClient()
            
            # Inicializar Validador
            self.validador = ValidadorConfianca()
            
            self.components_ready = True
            self.logger.info("✅ Componentes AI inicializados com sucesso")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar componentes: {e}")
            self.components_ready = False
    
    async def on_message(self, message: discord.Message):
        """Processa mensagens recebidas"""
        # Ignorar próprias mensagens
        if message.author == self.user:
            return
        
        # Ignorar outros bots
        if message.author.bot:
            return
        
        # Verificar se foi mencionado
        if not self.user in message.mentions:
            return
        
        self.estatisticas['mensagens_processadas'] += 1
        
        try:
            await self._processar_mencao(message)
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar mensagem: {e}")
            self.estatisticas['erros_ocorridos'] += 1
            await message.reply("❌ Ocorreu um erro ao processar sua mensagem. Tente novamente.")
    
    async def _processar_mencao(self, message: discord.Message):
        """Processa menção ao bot"""
        self.logger.info(f"💬 Processando menção de {message.author} em #{message.channel}")
        
        # Verificar se componentes estão prontos
        if not self.components_ready:
            await message.reply("⚠️ Bot ainda inicializando componentes AI. Tente novamente em alguns segundos.")
            return
        
        # Extrair texto limpo
        texto_limpo = self._limpar_mencao(message.content)
        
        if not texto_limpo.strip():
            await message.reply("📚 Olá! Sou o Oráculo de Concursos Públicos. Faça uma pergunta sobre concursos e eu te ajudo!")
            return
        
        # Processar com indicador de digitação
        async with message.channel.typing():
            try:
                # Por enquanto, resposta simples para testar
                resposta = f"Recebi sua pergunta: '{texto_limpo}'\n\n🔮 Estou processando usando IA especializada em concursos públicos..."
                
                # Registrar no banco
                await self.db_manager.registrar_interacao(
                    usuario_id=str(message.author.id),
                    servidor_id=str(message.guild.id) if message.guild else None,
                    canal_id=str(message.channel.id),
                    mensagem=texto_limpo,
                    tipo='pergunta',
                    resposta=resposta
                )
                
                # Enviar resposta
                await message.reply(resposta)
                self.estatisticas['respostas_enviadas'] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao gerar resposta: {e}")
                await message.reply("❌ Erro ao processar pergunta. Tente reformular ou tente novamente.")
    
    def _limpar_mencao(self, content: str) -> str:
        """Remove menções do texto"""
        # Remover menção ao bot
        texto_limpo = content.replace(f'<@{self.user.id}>', '').strip()
        texto_limpo = content.replace(f'<@!{self.user.id}>', '').strip()
        return texto_limpo