#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerenciador de Banco de Dados do Oráculo de Concursos
Responsável por todas as operações com SQLite
"""

import aiosqlite
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

from database.models import Interacao, Usuario, EstatisticaUso


class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "oraculo_concursos.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Garantir que o diretório existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def inicializar(self):
        """Inicializa o banco de dados e cria as tabelas"""
        try:
            await self._criar_tabelas()
            await self._criar_indices()
            self.logger.info("✅ Banco de dados inicializado com sucesso")
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar banco: {e}")
            raise
    
    async def _criar_tabelas(self):
        """Cria todas as tabelas necessárias"""
        async with aiosqlite.connect(self.db_path) as db:
            # Tabela de usuários
            await db.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL,
                    discriminator TEXT,
                    avatar_url TEXT,
                    primeiro_uso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_uso TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_interacoes INTEGER DEFAULT 0,
                    preferencias TEXT DEFAULT '{}',
                    ativo BOOLEAN DEFAULT 1
                )
            """)
            
            # Tabela de interações
            await db.execute("""
                CREATE TABLE IF NOT EXISTS interacoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    servidor_id TEXT,
                    canal_id TEXT NOT NULL,
                    mensagem TEXT NOT NULL,
                    resposta TEXT,
                    tipo TEXT NOT NULL CHECK (tipo IN ('pergunta', 'resposta')),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confianca REAL,
                    tempo_resposta REAL,
                    fontes_utilizadas TEXT,
                    processada BOOLEAN DEFAULT 1,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                )
            """)
            
            # Tabela de estatísticas
            await db.execute("""
                CREATE TABLE IF NOT EXISTS estatisticas_uso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data DATE NOT NULL,
                    total_usuarios_ativos INTEGER DEFAULT 0,
                    total_perguntas INTEGER DEFAULT 0,
                    total_respostas INTEGER DEFAULT 0,
                    tempo_medio_resposta REAL DEFAULT 0.0,
                    confianca_media REAL DEFAULT 0.0,
                    erros_ocorridos INTEGER DEFAULT 0,
                    UNIQUE(data)
                )
            """)
            
            # Tabela de contextos de conversa (para otimização)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS contextos_conversa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id TEXT NOT NULL,
                    canal_id TEXT NOT NULL,
                    contexto TEXT NOT NULL,
                    ultimo_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ativo BOOLEAN DEFAULT 1,
                    UNIQUE(usuario_id, canal_id)
                )
            """)
            
            # Tabela de logs de sistema
            await db.execute("""
                CREATE TABLE IF NOT EXISTS logs_sistema (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nivel TEXT NOT NULL,
                    modulo TEXT NOT NULL,
                    mensagem TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dados_extras TEXT
                )
            """)
            
            await db.commit()
    
    async def _criar_indices(self):
        """Cria índices para otimização das consultas"""
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_interacoes_usuario ON interacoes(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_interacoes_timestamp ON interacoes(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_interacoes_tipo ON interacoes(tipo)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_uso ON usuarios(ultimo_uso)",
            "CREATE INDEX IF NOT EXISTS idx_contextos_usuario_canal ON contextos_conversa(usuario_id, canal_id)",
            "CREATE INDEX IF NOT EXISTS idx_estatisticas_data ON estatisticas_uso(data)"
        ]
        
        async with aiosqlite.connect(self.db_path) as db:
            for indice in indices:
                await db.execute(indice)
            await db.commit()
    
    async def registrar_usuario(self, usuario_id: str, nome: str, 
                               discriminator: Optional[str] = None, avatar_url: Optional[str] = None) -> bool:
        """Registra ou atualiza informações do usuário"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Verificar se usuário já existe
                cursor = await db.execute(
                    "SELECT id FROM usuarios WHERE id = ?", (usuario_id,)
                )
                existe = await cursor.fetchone()
                
                if existe:
                    # Atualizar informações
                    await db.execute("""
                        UPDATE usuarios 
                        SET nome = ?, discriminator = ?, avatar_url = ?, ultimo_uso = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (nome, discriminator, avatar_url, usuario_id))
                else:
                    # Inserir novo usuário
                    await db.execute("""
                        INSERT INTO usuarios (id, nome, discriminator, avatar_url)
                        VALUES (?, ?, ?, ?)
                    """, (usuario_id, nome, discriminator, avatar_url))
                
                await db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao registrar usuário {usuario_id}: {e}")
            return False
    
    async def registrar_interacao(self, usuario_id: str, servidor_id: Optional[str],
                                 canal_id: str, mensagem: str, tipo: str,
                                 resposta: Optional[str] = None, confianca: Optional[float] = None,
                                 tempo_resposta: Optional[float] = None, fontes: Optional[List[str]] = None) -> bool:
        """Registra uma interação do usuário"""
        try:
            # Primeiro, garantir que o usuário está registrado
            await self.registrar_usuario(usuario_id, f"Usuário_{usuario_id}")
            
            async with aiosqlite.connect(self.db_path) as db:
                # Inserir interação
                fontes_json = ','.join(fontes) if fontes else None
                
                await db.execute("""
                    INSERT INTO interacoes 
                    (usuario_id, servidor_id, canal_id, mensagem, resposta, tipo, 
                     confianca, tempo_resposta, fontes_utilizadas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (usuario_id, servidor_id, canal_id, mensagem, resposta, 
                      tipo, confianca, tempo_resposta, fontes_json))
                
                # Atualizar contador de interações do usuário
                await db.execute("""
                    UPDATE usuarios 
                    SET total_interacoes = total_interacoes + 1, ultimo_uso = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (usuario_id,))
                
                await db.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao registrar interação: {e}")
            return False
    
    async def obter_historico_conversa(self, usuario_id: str, canal_id: str, 
                                      limite: int = 10) -> List[Dict[str, Any]]:
        """Obtém histórico de conversa do usuário"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT mensagem, resposta, tipo, timestamp, confianca
                    FROM interacoes
                    WHERE usuario_id = ? AND canal_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (usuario_id, canal_id, limite * 2))  # *2 porque cada pergunta gera 2 registros
                
                rows = await cursor.fetchall()
                
                # Organizar em pares pergunta-resposta
                historico = []
                pergunta_atual = None
                
                for row in reversed(rows):  # Reverter para ordem cronológica
                    if row[2] == 'pergunta':
                        pergunta_atual = {
                            'pergunta': row[0],
                            'timestamp': row[3]
                        }
                    elif row[2] == 'resposta' and pergunta_atual:
                        pergunta_atual.update({
                            'resposta': row[0],
                            'confianca': row[4]
                        })
                        historico.append(pergunta_atual)
                        pergunta_atual = None
                
                return historico[:limite]
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter histórico: {e}")
            return []
    
    async def obter_estatisticas_usuario(self, usuario_id: str) -> Dict[str, Any]:
        """Obtém estatísticas de uso do usuário"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Informações básicas do usuário
                cursor = await db.execute("""
                    SELECT nome, primeiro_uso, ultimo_uso, total_interacoes
                    FROM usuarios
                    WHERE id = ?
                """, (usuario_id,))
                
                info_usuario = await cursor.fetchone()
                
                if not info_usuario:
                    return {}
                
                # Estatísticas de interações
                cursor = await db.execute("""
                    SELECT 
                        COUNT(CASE WHEN tipo = 'pergunta' THEN 1 END) as total_perguntas,
                        AVG(CASE WHEN confianca IS NOT NULL THEN confianca END) as confianca_media,
                        COUNT(CASE WHEN timestamp >= datetime('now', '-7 days') THEN 1 END) as interacoes_semana
                    FROM interacoes
                    WHERE usuario_id = ?
                """, (usuario_id,))
                
                stats_interacoes = await cursor.fetchone()
                
                return {
                    'nome': info_usuario[0],
                    'primeiro_uso': info_usuario[1],
                    'ultimo_uso': info_usuario[2],
                    'total_interacoes': info_usuario[3],
                    'total_perguntas': stats_interacoes[0] or 0,
                    'confianca_media': round(stats_interacoes[1] or 0, 2),
                    'interacoes_semana': stats_interacoes[2] or 0
                }
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estatísticas do usuário: {e}")
            return {}
    
    async def atualizar_estatisticas_diarias(self):
        """Atualiza estatísticas diárias do sistema"""
        try:
            hoje = datetime.now().date()
            
            async with aiosqlite.connect(self.db_path) as db:
                # Calcular estatísticas do dia
                cursor = await db.execute("""
                    SELECT 
                        COUNT(DISTINCT usuario_id) as usuarios_ativos,
                        COUNT(CASE WHEN tipo = 'pergunta' THEN 1 END) as total_perguntas,
                        COUNT(CASE WHEN tipo = 'resposta' THEN 1 END) as total_respostas,
                        AVG(CASE WHEN tempo_resposta IS NOT NULL THEN tempo_resposta END) as tempo_medio,
                        AVG(CASE WHEN confianca IS NOT NULL THEN confianca END) as confianca_media
                    FROM interacoes
                    WHERE date(timestamp) = ?
                """, (hoje,))
                
                stats = await cursor.fetchone()
                
                # Inserir ou atualizar estatísticas
                await db.execute("""
                    INSERT OR REPLACE INTO estatisticas_uso 
                    (data, total_usuarios_ativos, total_perguntas, total_respostas, 
                     tempo_medio_resposta, confianca_media)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (hoje, stats[0] or 0, stats[1] or 0, stats[2] or 0, 
                      stats[3] or 0, stats[4] or 0))
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao atualizar estatísticas diárias: {e}")
    
    async def limpar_dados_antigos(self, dias: int = 90):
        """Remove dados antigos para otimização"""
        try:
            data_limite = datetime.now() - timedelta(days=dias)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Limpar interações antigas
                cursor = await db.execute("""
                    DELETE FROM interacoes 
                    WHERE timestamp < ?
                """, (data_limite,))
                
                removidas = cursor.rowcount
                
                # Limpar contextos inativos
                await db.execute("""
                    DELETE FROM contextos_conversa 
                    WHERE ultimo_update < ? OR ativo = 0
                """, (data_limite,))
                
                # Limpar logs antigos
                await db.execute("""
                    DELETE FROM logs_sistema 
                    WHERE timestamp < ?
                """, (data_limite,))
                
                await db.commit()
                
                self.logger.info(f"🧹 Limpeza concluída: {removidas} registros removidos")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza de dados: {e}")
    
    async def fechar(self):
        """Fecha conexões do banco de dados"""
        self.logger.info("📊 Finalizando conexões do banco de dados")
        # SQLite com aiosqlite não mantém conexões persistentes
        # Esta função é para compatibilidade futura
