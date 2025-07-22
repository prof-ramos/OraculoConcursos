#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Discord do Oráculo de Concursos
Gerencia interações com Discord e coordena respostas
"""

import asyncio
import logging
import re
import time
from typing import Optional, Dict, Any

import discord
from discord.ext import commands

from bot.gemini_client import GeminiClient
from database.db_manager import DatabaseManager
from utils.anti_alucinacao import ValidadorConfianca
from bot.config import Config


class OraculoBot(commands.Bot):
    """Bot principal do Oráculo de Concursos"""
    
    def __init__(self, db_manager: DatabaseManager):
        # Configurar intents necessários
        intents = discord.Intents.default()
        intents.message_content = True  # Necessário para ler conteúdo das mensagens
        intents.guilds = True
        intents.guild_messages = True
        
        super().__init__(
            command_prefix='!oraculo ',  # Prefix opcional para comandos futuros
            intents=intents,
            help_command=None,  # Desabilitar comando de ajuda padrão
            case_insensitive=True
        )
        
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Inicializar componentes depois da conexão para evitar bloqueios
        self.gemini_client = None
        self.validador = None
        
        # Cache de contexto de conversas ativas
        self.contextos_ativos: Dict[str, Dict[str, Any]] = {}
        
        # Estatísticas de uso
        self.estatisticas = {
            'mensagens_processadas': 0,
            'respostas_enviadas': 0,
            'erros_ocorridos': 0,
            'tempo_inicio': time.time()
        }
    
    async def setup_hook(self):
        """Configurações iniciais do bot"""
        self.logger.info("🔧 Configurando hooks do bot...")
        
        # Desabilitar sincronização de comandos por enquanto para testar
        # try:
        #     await self.tree.sync()
        #     self.logger.info("✅ Comandos sincronizados com Discord")
        # except Exception as e:
        #     self.logger.warning(f"⚠️ Erro ao sincronizar comandos: {e}")
    
    async def on_ready(self):
        """Evento chamado quando o bot está pronto"""
        self.logger.info(f"🤖 {self.user} está online!")
        self.logger.info(f"📊 Conectado a {len(self.guilds)} servidor(es)")
        
        # Log de debug para servidores
        for guild in self.guilds:
            self.logger.info(f"📋 Servidor: {guild.name} (ID: {guild.id})")
        
        # Inicializar componentes após conexão
        try:
            self.logger.info("🔧 Inicializando Gemini Client...")
            self.gemini_client = GeminiClient()
            
            self.logger.info("🛡️ Inicializando Validador de Confiança...")
            self.validador = ValidadorConfianca()
            
            self.logger.info("✅ Todos os componentes inicializados")
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar componentes: {e}")
        
        # Configurar status do bot
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="concursos públicos | @me para dúvidas"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        self.logger.info("✅ Status configurado com sucesso")
    
    async def on_message(self, message: discord.Message):
        """Processa mensagens recebidas"""
        # Ignorar mensagens do próprio bot
        if message.author == self.user:
            return
        
        # Verificar se o bot foi mencionado
        if not self.user in message.mentions:
            return
        
        # Ignorar mensagens de outros bots
        if message.author.bot:
            return
        
        self.estatisticas['mensagens_processadas'] += 1
        
        try:
            await self._processar_mencao(message)
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar mensagem: {e}")
            self.estatisticas['erros_ocorridos'] += 1
            await self._enviar_erro_generico(message)
    
    async def _processar_mencao(self, message: discord.Message):
        """Processa menção ao bot"""
        self.logger.info(f"💬 Processando menção de {message.author} em #{message.channel}")
        
        # Verificar se componentes estão inicializados
        if not self.gemini_client or not self.validador:
            await message.reply("⚠️ Bot ainda inicializando, tente novamente em alguns segundos.")
            return
        
        # Extrair texto da mensagem removendo menção
        texto_limpo = self._limpar_mencao(message.content)
        
        if not texto_limpo.strip():
            await self._enviar_ajuda(message)
            return
        
        # Registrar interação no banco
        await self.db_manager.registrar_interacao(
            usuario_id=str(message.author.id),
            servidor_id=str(message.guild.id) if message.guild else None,
            canal_id=str(message.channel.id),
            mensagem=texto_limpo,
            tipo='pergunta'
        )
        
        # Obter contexto da conversa
        contexto = await self._obter_contexto_conversa(message.author.id, message.channel.id)
        
        # Mostrar que está digitando
        async with message.channel.typing():
            try:
                # Gerar resposta usando Gemini
                resposta_completa = await self.gemini_client.gerar_resposta_concurso(
                    pergunta=texto_limpo,
                    contexto=contexto,
                    usuario_id=str(message.author.id)
                )
                
                # Validar confiança da resposta
                if not self.validador.resposta_confiavel(resposta_completa):
                    await self._enviar_resposta_baixa_confianca(message)
                    return
                
                # Enviar resposta em streaming
                await self._enviar_resposta_streaming(message, resposta_completa)
                
                # Atualizar contexto
                await self._atualizar_contexto(message.author.id, message.channel.id, 
                                             texto_limpo, resposta_completa['resposta'])
                
                self.estatisticas['respostas_enviadas'] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Erro ao gerar resposta: {e}")
                await self._enviar_erro_generico(message)
    
    def _limpar_mencao(self, texto: str) -> str:
        """Remove menção do bot do texto"""
        # Remover menção direta
        texto = re.sub(r'<@!?\d+>', '', texto)
        # Remover espaços extras
        return texto.strip()
    
    async def _obter_contexto_conversa(self, usuario_id: int, canal_id: int) -> Dict[str, Any]:
        """Obtém contexto da conversa do usuário"""
        chave_contexto = f"{usuario_id}_{canal_id}"
        
        # Verificar cache primeiro
        if chave_contexto in self.contextos_ativos:
            return self.contextos_ativos[chave_contexto]
        
        # Buscar histórico no banco
        historico = await self.db_manager.obter_historico_conversa(
            usuario_id=str(usuario_id),
            canal_id=str(canal_id),
            limite=5  # Últimas 5 interações
        )
        
        contexto = {
            'historico': historico,
            'usuario_id': str(usuario_id),
            'canal_id': str(canal_id),
            'timestamp': time.time()
        }
        
        # Armazenar no cache
        self.contextos_ativos[chave_contexto] = contexto
        
        return contexto
    
    async def _atualizar_contexto(self, usuario_id: int, canal_id: int, 
                                 pergunta: str, resposta: str):
        """Atualiza contexto da conversa"""
        chave_contexto = f"{usuario_id}_{canal_id}"
        
        if chave_contexto not in self.contextos_ativos:
            self.contextos_ativos[chave_contexto] = {
                'historico': [],
                'usuario_id': str(usuario_id),
                'canal_id': str(canal_id)
            }
        
        # Adicionar nova interação ao histórico
        nova_interacao = {
            'pergunta': pergunta,
            'resposta': resposta,
            'timestamp': time.time()
        }
        
        self.contextos_ativos[chave_contexto]['historico'].append(nova_interacao)
        
        # Manter apenas últimas 5 interações
        if len(self.contextos_ativos[chave_contexto]['historico']) > 5:
            self.contextos_ativos[chave_contexto]['historico'].pop(0)
        
        # Registrar resposta no banco
        await self.db_manager.registrar_interacao(
            usuario_id=str(usuario_id),
            servidor_id=None,  # Será atualizado se necessário
            canal_id=str(canal_id),
            mensagem=resposta,
            tipo='resposta'
        )
    
    async def _enviar_resposta_streaming(self, message: discord.Message, 
                                       resposta_completa: Dict[str, Any]):
        """Envia resposta usando streaming para melhor UX"""
        resposta = resposta_completa['resposta']
        fontes = resposta_completa.get('fontes', [])
        
        # Dividir resposta em chunks para simular streaming
        chunks = self._dividir_texto_chunks(resposta)
        
        # Enviar primeiro chunk
        if chunks:
            mensagem_atual = await message.reply(chunks[0])
            
            # Atualizar com chunks restantes
            for chunk in chunks[1:]:
                await asyncio.sleep(0.5)  # Pequena pausa para efeito de streaming
                try:
                    await mensagem_atual.edit(content=mensagem_atual.content + chunk)
                except discord.errors.HTTPException:
                    # Se a mensagem ficou muito longa, criar nova mensagem
                    mensagem_atual = await message.channel.send(chunk)
            
            # Adicionar fontes se disponíveis
            if fontes:
                embed_fontes = self._criar_embed_fontes(fontes)
                await message.channel.send(embed=embed_fontes)
    
    def _dividir_texto_chunks(self, texto: str, tamanho_chunk: int = 200) -> list:
        """Divide texto em chunks para streaming"""
        if len(texto) <= tamanho_chunk:
            return [texto]
        
        chunks = []
        palavras = texto.split()
        chunk_atual = ""
        
        for palavra in palavras:
            if len(chunk_atual + " " + palavra) <= tamanho_chunk:
                chunk_atual += " " + palavra if chunk_atual else palavra
            else:
                if chunk_atual:
                    chunks.append(chunk_atual)
                chunk_atual = palavra
        
        if chunk_atual:
            chunks.append(chunk_atual)
        
        return chunks
    
    def _criar_embed_fontes(self, fontes: list) -> discord.Embed:
        """Cria embed com fontes das informações"""
        embed = discord.Embed(
            title="📚 Fontes Consultadas",
            color=0x00ff00,
            description="Informações baseadas nas seguintes fontes:"
        )
        
        for i, fonte in enumerate(fontes[:5], 1):  # Máximo 5 fontes
            embed.add_field(
                name=f"Fonte {i}",
                value=fonte,
                inline=False
            )
        
        return embed
    
    async def _enviar_ajuda(self, message: discord.Message):
        """Envia mensagem de ajuda sobre como usar o bot"""
        embed = discord.Embed(
            title="🔮 Oráculo de Concursos - Como usar",
            color=0x0099ff,
            description="Sou seu assistente especializado em concursos públicos brasileiros!"
        )
        
        embed.add_field(
            name="💡 Como fazer perguntas",
            value="Me mencione (@Oráculo) seguido da sua dúvida sobre concursos públicos",
            inline=False
        )
        
        embed.add_field(
            name="📖 Exemplos de uso",
            value="• @Oráculo O que é regime jurídico estatutário?\n"
                  "• @Oráculo Explique os princípios da administração pública\n"
                  "• @Oráculo Como funciona a estabilidade do servidor público?",
            inline=False
        )
        
        embed.add_field(
            name="🎯 Especialidades",
            value="Direito Administrativo, Constitucional, Legislação específica, "
                  "Regimes jurídicos, Processos seletivos e muito mais!",
            inline=False
        )
        
        embed.set_footer(text="💪 Desenvolvido para sua aprovação em concursos públicos!")
        
        await message.reply(embed=embed)
    
    async def _enviar_resposta_baixa_confianca(self, message: discord.Message):
        """Envia mensagem quando a confiança da resposta é baixa"""
        embed = discord.Embed(
            title="⚠️ Confiança Insuficiente",
            color=0xff9900,
            description="Desculpe, não tenho informações suficientemente confiáveis "
                       "para responder sua pergunta no momento."
        )
        
        embed.add_field(
            name="💡 Sugestões",
            value="• Tente reformular sua pergunta\n"
                  "• Seja mais específico sobre o tema\n"
                  "• Verifique a ortografia da pergunta",
            inline=False
        )
        
        embed.add_field(
            name="📚 Fontes Recomendadas",
            value="Para essa dúvida, recomendo consultar:\n"
                  "• Legislação oficial\n"
                  "• Manuais de concursos atualizados\n"
                  "• Sites oficiais dos órgãos",
            inline=False
        )
        
        await message.reply(embed=embed)
    
    async def _enviar_erro_generico(self, message: discord.Message):
        """Envia mensagem de erro genérico"""
        embed = discord.Embed(
            title="❌ Ops! Algo deu errado",
            color=0xff0000,
            description="Ocorreu um erro interno. Tente novamente em alguns instantes."
        )
        
        embed.add_field(
            name="🔧 Se o problema persistir",
            value="Entre em contato com os administradores do servidor",
            inline=False
        )
        
        await message.reply(embed=embed)
    
    async def on_error(self, event: str, *args, **kwargs):
        """Handler global de erros"""
        self.logger.error(f"❌ Erro no evento {event}: {args}, {kwargs}")
        self.estatisticas['erros_ocorridos'] += 1
    
    async def close(self):
        """Finaliza o bot graciosamente"""
        self.logger.info("🔄 Finalizando bot Discord...")
        await super().close()
