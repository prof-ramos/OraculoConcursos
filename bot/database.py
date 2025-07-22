"""
Gerenciador de banco de dados SQLite para o Oráculo de Concursos Públicos
"""

import sqlite3
import asyncio
import aiosqlite
import logging
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class UserInteraction:
    """Classe para representar uma interação do usuário"""
    user_id: int
    username: str
    guild_id: int
    channel_id: int
    message_content: str
    bot_response: str
    confidence_score: float
    timestamp: datetime
    context_used: bool = False
    response_time_ms: int = 0


@dataclass
class ConversationContext:
    """Classe para representar contexto de conversa"""
    user_id: int
    guild_id: int
    messages: List[Dict[str, Any]]
    last_updated: datetime
    total_messages: int = 0


class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "oraculo_concursos.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Inicializa o banco de dados e cria as tabelas necessárias"""
        async with aiosqlite.connect(self.db_path) as db:
            await self._create_tables(db)
            await self._create_indexes(db)
            await db.commit()
        logger.info(f"✅ Banco de dados inicializado: {self.db_path}")
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """Cria as tabelas do banco de dados"""
        
        # Tabela de usuários
        await db.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                user_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_interactions INTEGER DEFAULT 0,
                avg_confidence_score REAL DEFAULT 0.0
            )
        """)
        
        # Tabela de interações
        await db.execute("""
            CREATE TABLE IF NOT EXISTS interacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_content TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                context_used BOOLEAN DEFAULT FALSE,
                response_time_ms INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (user_id)
            )
        """)
        
        # Tabela de contexto de conversas
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contexto_conversas (
                user_id INTEGER,
                guild_id INTEGER,
                messages TEXT NOT NULL,  -- JSON string
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        
        # Tabela de logs do sistema
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs_sistema (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de métricas de performance
        await db.execute("""
            CREATE TABLE IF NOT EXISTS metricas_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _create_indexes(self, db: aiosqlite.Connection):
        """Cria índices para otimização de consultas"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_interacoes_user_id ON interacoes(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_interacoes_timestamp ON interacoes(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_interacoes_confidence ON interacoes(confidence_score)",
            "CREATE INDEX IF NOT EXISTS idx_contexto_last_updated ON contexto_conversas(last_updated)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_last_seen ON usuarios(last_seen)"
        ]
        
        for index in indexes:
            await db.execute(index)
    
    async def add_user_interaction(self, interaction: UserInteraction):
        """Adiciona uma nova interação do usuário"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # Inserir ou atualizar usuário
                    await db.execute("""
                        INSERT OR REPLACE INTO usuarios 
                        (user_id, username, first_seen, last_seen, total_interactions, avg_confidence_score)
                        VALUES (
                            ?, ?, 
                            COALESCE((SELECT first_seen FROM usuarios WHERE user_id = ?), ?),
                            ?, 
                            COALESCE((SELECT total_interactions FROM usuarios WHERE user_id = ?), 0) + 1,
                            ?
                        )
                    """, (
                        interaction.user_id, interaction.username, interaction.user_id,
                        interaction.timestamp, interaction.timestamp, interaction.user_id,
                        interaction.confidence_score
                    ))
                    
                    # Inserir interação
                    await db.execute("""
                        INSERT INTO interacoes 
                        (user_id, username, guild_id, channel_id, message_content, 
                         bot_response, confidence_score, context_used, response_time_ms, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        interaction.user_id, interaction.username, interaction.guild_id,
                        interaction.channel_id, interaction.message_content, interaction.bot_response,
                        interaction.confidence_score, interaction.context_used, 
                        interaction.response_time_ms, interaction.timestamp
                    ))
                    
                    await db.commit()
                    logger.debug(f"💾 Interação salva para usuário {interaction.username}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao salvar interação: {e}")
    
    async def get_conversation_context(self, user_id: int, guild_id: int, limit: int = 10) -> Optional[ConversationContext]:
        """Recupera contexto de conversa para um usuário"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT messages, last_updated, total_messages 
                    FROM contexto_conversas 
                    WHERE user_id = ? AND guild_id = ?
                """, (user_id, guild_id))
                
                row = await cursor.fetchone()
                if row:
                    messages = json.loads(row[0])[-limit:]  # Limitar mensagens
                    return ConversationContext(
                        user_id=user_id,
                        guild_id=guild_id,
                        messages=messages,
                        last_updated=datetime.fromisoformat(row[1]),
                        total_messages=row[2]
                    )
                    
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar contexto: {e}")
        
        return None
    
    async def update_conversation_context(self, user_id: int, guild_id: int, 
                                        user_message: str, bot_response: str):
        """Atualiza o contexto de conversa"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # Recuperar contexto existente
                    cursor = await db.execute("""
                        SELECT messages, total_messages FROM contexto_conversas 
                        WHERE user_id = ? AND guild_id = ?
                    """, (user_id, guild_id))
                    
                    row = await cursor.fetchone()
                    current_messages = []
                    total_messages = 0
                    
                    if row:
                        current_messages = json.loads(row[0])
                        total_messages = row[1]
                    
                    # Adicionar nova mensagem
                    new_message = {
                        "timestamp": datetime.now().isoformat(),
                        "user_message": user_message,
                        "bot_response": bot_response
                    }
                    
                    current_messages.append(new_message)
                    
                    # Manter apenas as últimas 20 mensagens para evitar contexto muito longo
                    if len(current_messages) > 20:
                        current_messages = current_messages[-20:]
                    
                    # Salvar contexto atualizado
                    await db.execute("""
                        INSERT OR REPLACE INTO contexto_conversas 
                        (user_id, guild_id, messages, last_updated, total_messages)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        user_id, guild_id, json.dumps(current_messages, ensure_ascii=False),
                        datetime.now(), total_messages + 1
                    ))
                    
                    await db.commit()
                    logger.debug(f"🔄 Contexto atualizado para usuário {user_id}")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao atualizar contexto: {e}")
    
    async def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Recupera estatísticas de um usuário"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        username,
                        total_interactions,
                        avg_confidence_score,
                        first_seen,
                        last_seen
                    FROM usuarios 
                    WHERE user_id = ?
                """, (user_id,))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        "username": row[0],
                        "total_interactions": row[1],
                        "avg_confidence_score": round(row[2], 2),
                        "first_seen": row[3],
                        "last_seen": row[4]
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar stats do usuário: {e}")
        
        return None
    
    async def log_system_event(self, level: str, message: str, details: str = None):
        """Registra evento do sistema"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO logs_sistema (level, message, details)
                    VALUES (?, ?, ?)
                """, (level, message, details))
                await db.commit()
        except Exception as e:
            logger.error(f"❌ Erro ao registrar log: {e}")
    
    async def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Recupera métricas de performance dos últimos X dias"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        COUNT(*) as total_interactions,
                        AVG(confidence_score) as avg_confidence,
                        AVG(response_time_ms) as avg_response_time,
                        COUNT(DISTINCT user_id) as unique_users
                    FROM interacoes 
                    WHERE timestamp >= datetime('now', '-{} days')
                """.format(days))
                
                row = await cursor.fetchone()
                if row:
                    return {
                        "total_interactions": row[0],
                        "avg_confidence": round(row[1] or 0, 2),
                        "avg_response_time_ms": round(row[2] or 0, 2),
                        "unique_users": row[3],
                        "period_days": days
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erro ao recuperar métricas: {e}")
        
        return {}
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove dados antigos para otimizar performance"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # Limpar logs antigos
                    await db.execute("""
                        DELETE FROM logs_sistema 
                        WHERE timestamp < datetime('now', '-{} days')
                    """.format(days_to_keep))
                    
                    # Limpar contextos não utilizados há muito tempo
                    await db.execute("""
                        DELETE FROM contexto_conversas 
                        WHERE last_updated < datetime('now', '-{} days')
                    """.format(days_to_keep // 2))
                    
                    await db.commit()
                    logger.info(f"🧹 Limpeza de dados antigos concluída")
                    
            except Exception as e:
                logger.error(f"❌ Erro na limpeza de dados: {e}")
