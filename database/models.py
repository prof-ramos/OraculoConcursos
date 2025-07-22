#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos de dados para o Oráculo de Concursos
Define estruturas de dados para interações com o banco
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
import json


@dataclass
class Usuario:
    """Modelo para usuários do Discord"""
    id: str
    nome: str
    discriminator: Optional[str] = None
    avatar_url: Optional[str] = None
    primeiro_uso: Optional[datetime] = None
    ultimo_uso: Optional[datetime] = None
    total_interacoes: int = 0
    preferencias: Dict[str, Any] = field(default_factory=dict)
    ativo: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'discriminator': self.discriminator,
            'avatar_url': self.avatar_url,
            'primeiro_uso': self.primeiro_uso.isoformat() if self.primeiro_uso else None,
            'ultimo_uso': self.ultimo_uso.isoformat() if self.ultimo_uso else None,
            'total_interacoes': self.total_interacoes,
            'preferencias': self.preferencias,
            'ativo': self.ativo
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Usuario':
        """Cria instância a partir de dicionário"""
        primeiro_uso = None
        ultimo_uso = None
        
        if data.get('primeiro_uso'):
            primeiro_uso = datetime.fromisoformat(data['primeiro_uso'])
        if data.get('ultimo_uso'):
            ultimo_uso = datetime.fromisoformat(data['ultimo_uso'])
        
        return cls(
            id=data['id'],
            nome=data['nome'],
            discriminator=data.get('discriminator'),
            avatar_url=data.get('avatar_url'),
            primeiro_uso=primeiro_uso,
            ultimo_uso=ultimo_uso,
            total_interacoes=data.get('total_interacoes', 0),
            preferencias=data.get('preferencias', {}),
            ativo=data.get('ativo', True)
        )


@dataclass
class Interacao:
    """Modelo para interações do usuário"""
    usuario_id: str
    canal_id: str
    mensagem: str
    tipo: str  # 'pergunta' ou 'resposta'
    id: Optional[int] = None
    servidor_id: Optional[str] = None
    resposta: Optional[str] = None
    timestamp: Optional[datetime] = None
    confianca: Optional[float] = None
    tempo_resposta: Optional[float] = None
    fontes_utilizadas: List[str] = field(default_factory=list)
    processada: bool = True
    
    def __post_init__(self):
        """Validações após inicialização"""
        if self.tipo not in ['pergunta', 'resposta']:
            raise ValueError(f"Tipo inválido: {self.tipo}. Deve ser 'pergunta' ou 'resposta'")
        
        if self.confianca is not None and not (0 <= self.confianca <= 1):
            raise ValueError(f"Confiança deve estar entre 0 e 1: {self.confianca}")
        
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'servidor_id': self.servidor_id,
            'canal_id': self.canal_id,
            'mensagem': self.mensagem,
            'resposta': self.resposta,
            'tipo': self.tipo,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'confianca': self.confianca,
            'tempo_resposta': self.tempo_resposta,
            'fontes_utilizadas': self.fontes_utilizadas,
            'processada': self.processada
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Interacao':
        """Cria instância a partir de dicionário"""
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        return cls(
            id=data.get('id'),
            usuario_id=data['usuario_id'],
            servidor_id=data.get('servidor_id'),
            canal_id=data['canal_id'],
            mensagem=data['mensagem'],
            resposta=data.get('resposta'),
            tipo=data['tipo'],
            timestamp=timestamp,
            confianca=data.get('confianca'),
            tempo_resposta=data.get('tempo_resposta'),
            fontes_utilizadas=data.get('fontes_utilizadas', []),
            processada=data.get('processada', True)
        )


@dataclass
class EstatisticaUso:
    """Modelo para estatísticas de uso diário"""
    data: datetime
    total_usuarios_ativos: int = 0
    total_perguntas: int = 0
    total_respostas: int = 0
    tempo_medio_resposta: float = 0.0
    confianca_media: float = 0.0
    erros_ocorridos: int = 0
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'data': self.data.date().isoformat(),
            'total_usuarios_ativos': self.total_usuarios_ativos,
            'total_perguntas': self.total_perguntas,
            'total_respostas': self.total_respostas,
            'tempo_medio_resposta': self.tempo_medio_resposta,
            'confianca_media': self.confianca_media,
            'erros_ocorridos': self.erros_ocorridos
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EstatisticaUso':
        """Cria instância a partir de dicionário"""
        data_obj = datetime.fromisoformat(data['data']).date()
        
        return cls(
            id=data.get('id'),
            data=data_obj,
            total_usuarios_ativos=data.get('total_usuarios_ativos', 0),
            total_perguntas=data.get('total_perguntas', 0),
            total_respostas=data.get('total_respostas', 0),
            tempo_medio_resposta=data.get('tempo_medio_resposta', 0.0),
            confianca_media=data.get('confianca_media', 0.0),
            erros_ocorridos=data.get('erros_ocorridos', 0)
        )


@dataclass
class ContextoConversa:
    """Modelo para contexto de conversa"""
    usuario_id: str
    canal_id: str
    contexto: Dict[str, Any]
    ultimo_update: Optional[datetime] = None
    ativo: bool = True
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validações após inicialização"""
        if self.ultimo_update is None:
            self.ultimo_update = datetime.now()
    
    def adicionar_interacao(self, pergunta: str, resposta: str, confianca: float = None):
        """Adiciona nova interação ao contexto"""
        if 'historico' not in self.contexto:
            self.contexto['historico'] = []
        
        nova_interacao = {
            'pergunta': pergunta,
            'resposta': resposta,
            'timestamp': datetime.now().isoformat(),
            'confianca': confianca
        }
        
        self.contexto['historico'].append(nova_interacao)
        
        # Manter apenas últimas 10 interações
        if len(self.contexto['historico']) > 10:
            self.contexto['historico'] = self.contexto['historico'][-10:]
        
        self.ultimo_update = datetime.now()
    
    def obter_historico_recente(self, limite: int = 5) -> List[Dict[str, Any]]:
        """Obtém histórico recente de interações"""
        historico = self.contexto.get('historico', [])
        return historico[-limite:] if historico else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'canal_id': self.canal_id,
            'contexto': json.dumps(self.contexto, ensure_ascii=False),
            'ultimo_update': self.ultimo_update.isoformat() if self.ultimo_update else None,
            'ativo': self.ativo
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextoConversa':
        """Cria instância a partir de dicionário"""
        ultimo_update = None
        if data.get('ultimo_update'):
            ultimo_update = datetime.fromisoformat(data['ultimo_update'])
        
        contexto = {}
        if data.get('contexto'):
            try:
                contexto = json.loads(data['contexto'])
            except json.JSONDecodeError:
                contexto = {}
        
        return cls(
            id=data.get('id'),
            usuario_id=data['usuario_id'],
            canal_id=data['canal_id'],
            contexto=contexto,
            ultimo_update=ultimo_update,
            ativo=data.get('ativo', True)
        )


@dataclass
class LogSistema:
    """Modelo para logs do sistema"""
    nivel: str
    modulo: str
    mensagem: str
    timestamp: Optional[datetime] = None
    dados_extras: Optional[Dict[str, Any]] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Validações após inicialização"""
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.nivel not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Nível de log inválido: {self.nivel}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'nivel': self.nivel,
            'modulo': self.modulo,
            'mensagem': self.mensagem,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'dados_extras': json.dumps(self.dados_extras, ensure_ascii=False) if self.dados_extras else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogSistema':
        """Cria instância a partir de dicionário"""
        timestamp = None
        if data.get('timestamp'):
            timestamp = datetime.fromisoformat(data['timestamp'])
        
        dados_extras = None
        if data.get('dados_extras'):
            try:
                dados_extras = json.loads(data['dados_extras'])
            except json.JSONDecodeError:
                dados_extras = None
        
        return cls(
            id=data.get('id'),
            nivel=data['nivel'],
            modulo=data['modulo'],
            mensagem=data['mensagem'],
            timestamp=timestamp,
            dados_extras=dados_extras
        )
