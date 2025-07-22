#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Anti-Alucinação do Oráculo de Concursos
Implementa estratégias para minimizar informações incorretas ou inventadas
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from utils.config import Config


class ValidadorConfianca:
    """Validador de confiança para respostas do Gemini"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.confianca_minima = Config.CONFIANCA_MINIMA
        
        # Padrões que indicam alta confiança
        self.padroes_alta_confianca = [
            r'(?i)lei\s+(?:nº\s*)?(\d+(?:\.\d+)*(?:/\d+)?)',  # Leis específicas
            r'(?i)decreto\s+(?:nº\s*)?(\d+(?:\.\d+)*(?:/\d+)?)',  # Decretos
            r'(?i)art(?:igo)?\.\s*(\d+)',  # Artigos
            r'(?i)constituição\s+federal',  # CF
            r'(?i)cf(?:/88)?',  # CF abreviada
            r'(?i)clt',  # CLT
            r'(?i)estatuto\s+(?:do\s+)?servidor',  # Estatuto do servidor
            r'(?i)regime\s+jurídico\s+único',  # RJU
        ]
        
        # Padrões que indicam baixa confiança
        self.padroes_baixa_confianca = [
            r'(?i)acredito\s+que',
            r'(?i)possivelmente',
            r'(?i)provavelmente',
            r'(?i)creio\s+que',
            r'(?i)não\s+tenho\s+certeza',
            r'(?i)pode\s+ser\s+que',
            r'(?i)talvez',
            r'(?i)suponho\s+que',
            r'(?i)imagino\s+que',
            r'(?i)(?:em\s+)?geral(?:mente)?',
            r'(?i)normalmente',
            r'(?i)costuma\s+ser',
        ]
        
        # Termos técnicos que aumentam confiança
        self.termos_tecnicos_concursos = [
            'administração pública', 'servidor público', 'estatutário',
            'celetista', 'regime jurídico', 'estabilidade', 'efetividade',
            'concurso público', 'processo seletivo', 'cargo público',
            'função pública', 'remuneração', 'subsídio', 'gratificação',
            'licença', 'afastamento', 'aposentadoria', 'pensão',
            'moralidade', 'legalidade', 'impessoalidade', 'publicidade',
            'eficiência', 'supremacia do interesse público',
            'auto-executoriedade', 'presunção de legitimidade'
        ]
        
        # Fontes confiáveis para concursos
        self.fontes_confiaveis = [
            'constituição federal', 'cf/88', 'lei 8.112/90',
            'lei 8.429/92', 'decreto-lei 5.452/43', 'clt',
            'súmula', 'jurisprudência', 'stf', 'stj', 'tcu'
        ]
    
    def resposta_confiavel(self, resposta_completa: Dict[str, Any]) -> bool:
        """
        Avalia se uma resposta é confiável o suficiente para ser enviada
        
        Args:
            resposta_completa: Dicionário com resposta e metadados
        
        Returns:
            True se a resposta é confiável
        """
        try:
            resposta = resposta_completa.get('resposta', '')
            confianca_gemini = resposta_completa.get('confianca', 0.0)
            fontes = resposta_completa.get('fontes', [])
            
            # Calcular score de confiança próprio
            score_proprio = self._calcular_score_confianca(resposta, fontes)
            
            # Combinar scores (peso maior para o nosso sistema)
            score_final = (score_proprio * 0.7) + (confianca_gemini * 0.3)
            
            resultado_confiavel = score_final >= self.confianca_minima
            
            self.logger.info(
                f"🔍 Validação confiança - Gemini: {confianca_gemini:.2f}, "
                f"Próprio: {score_proprio:.2f}, Final: {score_final:.2f}, "
                f"Confiável: {resultado_confiavel}"
            )
            
            return resultado_confiavel
            
        except Exception as e:
            self.logger.error(f"❌ Erro na validação de confiança: {e}")
            return False  # Em caso de erro, rejeitar resposta
    
    def _calcular_score_confianca(self, resposta: str, fontes: List[str]) -> float:
        """
        Calcula score de confiança baseado no conteúdo da resposta
        
        Args:
            resposta: Texto da resposta
            fontes: Lista de fontes citadas
        
        Returns:
            Score de confiança entre 0 e 1
        """
        score = 0.5  # Score base
        
        # 1. Verificar padrões de alta confiança
        for padrao in self.padroes_alta_confianca:
            if re.search(padrao, resposta):
                score += 0.15
                self.logger.debug(f"🔍 Padrão alta confiança encontrado: {padrao}")
        
        # 2. Penalizar padrões de baixa confiança
        for padrao in self.padroes_baixa_confianca:
            if re.search(padrao, resposta):
                score -= 0.2
                self.logger.debug(f"⚠️ Padrão baixa confiança encontrado: {padrao}")
        
        # 3. Bonificar termos técnicos
        termos_encontrados = 0
        resposta_lower = resposta.lower()
        for termo in self.termos_tecnicos_concursos:
            if termo in resposta_lower:
                termos_encontrados += 1
        
        bonus_termos = min(0.2, termos_encontrados * 0.02)
        score += bonus_termos
        
        # 4. Bonificar citação de fontes
        if fontes:
            bonus_fontes = min(0.15, len(fontes) * 0.03)
            score += bonus_fontes
            
            # Bonus extra para fontes confiáveis
            for fonte in fontes:
                fonte_lower = fonte.lower()
                for fonte_confiavel in self.fontes_confiaveis:
                    if fonte_confiavel in fonte_lower:
                        score += 0.05
                        break
        
        # 5. Verificar estrutura da resposta
        score += self._analisar_estrutura_resposta(resposta)
        
        # 6. Verificar comprimento e detalhamento
        if 100 <= len(resposta) <= 2000:  # Tamanho adequado
            score += 0.05
        elif len(resposta) < 50:  # Muito curta
            score -= 0.1
        
        # Garantir que o score esteja entre 0 e 1
        return max(0.0, min(1.0, score))
    
    def _analisar_estrutura_resposta(self, resposta: str) -> float:
        """
        Analisa a estrutura da resposta para determinar qualidade
        
        Args:
            resposta: Texto da resposta
        
        Returns:
            Bonus de score baseado na estrutura
        """
        bonus = 0.0
        
        # Verificar se há organização (listas, tópicos)
        if re.search(r'(?:\n|^)[\d\-\*\•]\s*', resposta):
            bonus += 0.05
        
        # Verificar se há explicação detalhada
        if re.search(r'(?:ou seja|isto é|em outras palavras|por exemplo)', resposta, re.IGNORECASE):
            bonus += 0.03
        
        # Verificar se menciona aplicação prática
        if re.search(r'(?:na prática|aplicação|exemplo|caso)', resposta, re.IGNORECASE):
            bonus += 0.03
        
        # Verificar se há diferenciação de conceitos
        if re.search(r'(?:diferente|distinto|não confundir|ao contrário)', resposta, re.IGNORECASE):
            bonus += 0.03
        
        return bonus
    
    def identificar_riscos_alucinacao(self, resposta: str) -> List[Dict[str, str]]:
        """
        Identifica possíveis riscos de alucinação na resposta
        
        Args:
            resposta: Texto da resposta
        
        Returns:
            Lista de riscos identificados
        """
        riscos = []
        
        # Verificar números ou datas específicas sem fonte
        numeros_especificos = re.findall(r'\b\d{4}/\d{4}\b|\b\d{1,2}/\d{1,2}/\d{4}\b', resposta)
        if numeros_especificos and not re.search(r'(?:lei|decreto|portaria)', resposta, re.IGNORECASE):
            riscos.append({
                'tipo': 'numeros_sem_fonte',
                'descricao': 'Números específicos mencionados sem citação de fonte',
                'detalhes': f"Números encontrados: {', '.join(numeros_especificos)}"
            })
        
        # Verificar percentuais específicos
        percentuais = re.findall(r'\b\d+(?:\,\d+)?%', resposta)
        if percentuais:
            riscos.append({
                'tipo': 'percentuais_especificos',
                'descricao': 'Percentuais específicos que podem não estar atualizados',
                'detalhes': f"Percentuais: {', '.join(percentuais)}"
            })
        
        # Verificar afirmações muito categóricas
        afirmacoes_categoricas = [
            r'(?i)sempre', r'(?i)nunca', r'(?i)todos', r'(?i)nenhum',
            r'(?i)jamais', r'(?i)invariavelmente'
        ]
        
        for padrao in afirmacoes_categoricas:
            if re.search(padrao, resposta):
                riscos.append({
                    'tipo': 'afirmacao_categorica',
                    'descricao': 'Afirmação muito categórica que pode ter exceções',
                    'detalhes': f"Padrão encontrado: {padrao}"
                })
        
        # Verificar contradições internas
        if self._detectar_contradicoes(resposta):
            riscos.append({
                'tipo': 'possivel_contradicao',
                'descricao': 'Possível contradição interna detectada',
                'detalhes': 'Verificação manual recomendada'
            })
        
        return riscos
    
    def _detectar_contradicoes(self, resposta: str) -> bool:
        """
        Detecta possíveis contradições na resposta
        
        Args:
            resposta: Texto da resposta
        
        Returns:
            True se houver possível contradição
        """
        # Verificar negações próximas a afirmações
        sentencas = re.split(r'[.!?]\s+', resposta)
        
        for i, sentenca in enumerate(sentencas[:-1]):
            sentenca_atual = sentenca.lower()
            proxima_sentenca = sentencas[i + 1].lower()
            
            # Verificar palavras contraditórias
            palavras_contraditorias = [
                ('obrigatório', 'opcional'),
                ('permitido', 'proibido'),
                ('deve', 'não deve'),
                ('sim', 'não'),
                ('sempre', 'nunca')
            ]
            
            for palavra1, palavra2 in palavras_contraditorias:
                if palavra1 in sentenca_atual and palavra2 in proxima_sentenca:
                    return True
                if palavra2 in sentenca_atual and palavra1 in proxima_sentenca:
                    return True
        
        return False
    
    def sugerir_melhorias(self, resposta: str, score: float) -> List[str]:
        """
        Sugere melhorias para aumentar a confiança da resposta
        
        Args:
            resposta: Texto da resposta
            score: Score de confiança atual
        
        Returns:
            Lista de sugestões
        """
        sugestoes = []
        
        if score < 0.7:
            sugestoes.append("Adicionar citações específicas de leis ou regulamentos")
            sugestoes.append("Incluir exemplos práticos da aplicação")
            sugestoes.append("Organizar informações em tópicos ou listas")
        
        if not re.search(r'(?:lei|decreto|artigo)', resposta, re.IGNORECASE):
            sugestoes.append("Referenciar base legal específica")
        
        if len(resposta) < 100:
            sugestoes.append("Expandir explicação com mais detalhes")
        
        # Verificar se usa linguagem de incerteza
        for padrao in self.padroes_baixa_confianca:
            if re.search(padrao, resposta):
                sugestoes.append("Remover expressões de incerteza ou qualificar melhor")
                break
        
        return sugestoes
    
    def gerar_relatorio_confianca(self, resposta_completa: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera relatório completo de confiança da resposta
        
        Args:
            resposta_completa: Dicionário com resposta e metadados
        
        Returns:
            Relatório detalhado de confiança
        """
        resposta = resposta_completa.get('resposta', '')
        fontes = resposta_completa.get('fontes', [])
        
        score = self._calcular_score_confianca(resposta, fontes)
        riscos = self.identificar_riscos_alucinacao(resposta)
        sugestoes = self.sugerir_melhorias(resposta, score)
        
        relatorio = {
            'score_confianca': score,
            'aprovada': score >= self.confianca_minima,
            'timestamp': datetime.now().isoformat(),
            'detalhes': {
                'fontes_citadas': len(fontes),
                'termos_tecnicos': self._contar_termos_tecnicos(resposta),
                'comprimento_resposta': len(resposta),
                'estrutura_organizada': bool(re.search(r'(?:\n|^)[\d\-\*\•]\s*', resposta))
            },
            'riscos_identificados': riscos,
            'sugestoes_melhoria': sugestoes,
            'limiar_configurado': self.confianca_minima
        }
        
        return relatorio
    
    def _contar_termos_tecnicos(self, resposta: str) -> int:
        """Conta quantos termos técnicos estão presentes na resposta"""
        resposta_lower = resposta.lower()
        return sum(1 for termo in self.termos_tecnicos_concursos if termo in resposta_lower)


class MonitorAlucinacao:
    """Monitor para detectar padrões de alucinação ao longo do tempo"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.historico_scores = []
        self.alertas_ativos = []
    
    def registrar_resposta(self, score: float, usuario_id: str, pergunta: str):
        """Registra uma resposta para monitoramento"""
        entrada = {
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'usuario_id': usuario_id,
            'pergunta_hash': hash(pergunta) % 10000  # Hash simplificado
        }
        
        self.historico_scores.append(entrada)
        
        # Manter apenas últimas 100 entradas
        if len(self.historico_scores) > 100:
            self.historico_scores.pop(0)
        
        # Verificar se precisa gerar alerta
        self._verificar_alertas()
    
    def _verificar_alertas(self):
        """Verifica se deve gerar alertas baseado no histórico"""
        if len(self.historico_scores) < 10:
            return
        
        # Calcular média dos últimos 10 scores
        ultimos_scores = [entry['score'] for entry in self.historico_scores[-10:]]
        media_recente = sum(ultimos_scores) / len(ultimos_scores)
        
        # Alerta se média estiver muito baixa
        if media_recente < 0.6:
            alerta = {
                'tipo': 'media_baixa',
                'timestamp': datetime.now().isoformat(),
                'media': media_recente,
                'amostras': len(ultimos_scores)
            }
            
            self.alertas_ativos.append(alerta)
            self.logger.warning(f"⚠️ Alerta: Média de confiança baixa - {media_recente:.2f}")
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Obtém estatísticas do monitoramento"""
        if not self.historico_scores:
            return {'total_respostas': 0}
        
        scores = [entry['score'] for entry in self.historico_scores]
        
        return {
            'total_respostas': len(scores),
            'score_medio': sum(scores) / len(scores),
            'score_minimo': min(scores),
            'score_maximo': max(scores),
            'respostas_confiaveis': sum(1 for s in scores if s >= Config.CONFIANCA_MINIMA),
            'taxa_aprovacao': sum(1 for s in scores if s >= Config.CONFIANCA_MINIMA) / len(scores),
            'alertas_ativos': len(self.alertas_ativos)
        }
