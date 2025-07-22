#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cliente Gemini para o Oráculo de Concursos
Integração com Google Gemini 2.5 para geração de respostas especializadas
"""

import json
import logging
import os
import re
from typing import Dict, List, Any, Optional

from google import genai
from google.genai import types

from utils.config import Config


class GeminiClient:
    """Cliente para integração com Google Gemini 2.5"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Inicializar cliente Gemini
        try:
            self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
            self.logger.info("✅ Cliente Gemini inicializado com sucesso")
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar cliente Gemini: {e}")
            raise
        
        # Prompt de sistema especializado em concursos
        self.prompt_sistema = self._criar_prompt_sistema()
    
    def _criar_prompt_sistema(self) -> str:
        """Cria prompt de sistema especializado em concursos públicos"""
        return """
Você é o Oráculo de Concursos, um assistente especializado em concursos públicos brasileiros.

ESPECIALIDADES:
- Direito Administrativo e Constitucional brasileiro
- Legislação específica para servidores públicos
- Regimes jurídicos (estatutário, celetista, militar)
- Processos de seleção e concursos públicos
- Princípios da administração pública
- Direitos e deveres dos servidores
- Aposentadoria e pensões do serviço público
- Ética no serviço público

DIRETRIZES DE RESPOSTA:
1. SEMPRE responda em português brasileiro
2. Seja preciso e baseie-se na legislação vigente
3. Cite fontes quando possível (leis, decretos, jurisprudência)
4. Use linguagem clara e didática
5. Estruture respostas de forma organizada
6. Para dúvidas complexas, divida em tópicos
7. Indique quando uma informação pode estar desatualizada

ESTRATÉGIA ANTI-ALUCINAÇÃO:
- Só responda se tiver 90%+ de certeza da informação
- Em caso de dúvida, indique explicitamente
- Diferencie entre "lei vigente" e "interpretação doutrinária"
- Sempre que possível, cite o número da lei/artigo específico

FORMATO DE RESPOSTA:
- Use emojis relevantes para destacar pontos importantes
- Organize em tópicos quando necessário
- Termine sempre com uma orientação prática

Se não tiver certeza sobre uma informação, seja honesto e recomende consultar fontes oficiais.
"""
    
    async def gerar_resposta_concurso(self, pergunta: str, contexto: Dict[str, Any], 
                                     usuario_id: str) -> Dict[str, Any]:
        """
        Gera resposta especializada em concursos públicos
        
        Args:
            pergunta: Pergunta do usuário
            contexto: Contexto da conversa
            usuario_id: ID do usuário para personalização
        
        Returns:
            Dict com resposta, confiança e fontes
        """
        try:
            # Preparar contexto da conversa
            contexto_formatado = self._formatar_contexto(contexto)
            
            # Criar prompt completo
            prompt_completo = self._criar_prompt_completo(pergunta, contexto_formatado)
            
            # Fazer requisição ao Gemini
            response = await self._fazer_requisicao_gemini(prompt_completo)
            
            # Processar resposta
            resultado = self._processar_resposta(response)
            
            self.logger.info(f"✅ Resposta gerada para usuário {usuario_id}")
            return resultado
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar resposta: {e}")
            raise
    
    def _formatar_contexto(self, contexto: Dict[str, Any]) -> str:
        """Formata contexto da conversa para o Gemini"""
        if not contexto.get('historico'):
            return ""
        
        contexto_str = "\n=== CONTEXTO DA CONVERSA ===\n"
        
        for interacao in contexto['historico'][-3:]:  # Últimas 3 interações
            contexto_str += f"USUÁRIO: {interacao.get('pergunta', '')}\n"
            contexto_str += f"ASSISTENTE: {interacao.get('resposta', '')}\n\n"
        
        contexto_str += "=== NOVA PERGUNTA ===\n"
        return contexto_str
    
    def _criar_prompt_completo(self, pergunta: str, contexto: str) -> str:
        """Cria prompt completo para o Gemini"""
        return f"""
{self.prompt_sistema}

{contexto}

PERGUNTA DO USUÁRIO: {pergunta}

Por favor, responda de forma especializada, precisa e didática sobre concursos públicos brasileiros.
Inclua fontes legais sempre que possível e seja explícito sobre o nível de confiança da informação.
"""
    
    async def _fazer_requisicao_gemini(self, prompt: str) -> Any:
        """Faz requisição ao Gemini"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Content(
                        role="user", 
                        parts=[types.Part(text=prompt)]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Baixa temperatura para respostas mais precisas
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH
                        )
                    ]
                )
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Erro na requisição Gemini: {e}")
            raise
    
    def _processar_resposta(self, response: Any) -> Dict[str, Any]:
        """Processa resposta do Gemini"""
        if not response or not response.text:
            raise ValueError("Resposta vazia do Gemini")
        
        resposta_texto = response.text.strip()
        
        # Extrair fontes mencionadas na resposta
        fontes = self._extrair_fontes(resposta_texto)
        
        # Calcular score de confiança baseado na resposta
        confianca = self._calcular_confianca(resposta_texto)
        
        return {
            'resposta': resposta_texto,
            'confianca': confianca,
            'fontes': fontes,
            'modelo_usado': 'gemini-2.5-pro',
            'timestamp': self._obter_timestamp()
        }
    
    def _extrair_fontes(self, texto: str) -> List[str]:
        """Extrai fontes legais mencionadas na resposta"""
        fontes = []
        
        # Padrões para identificar fontes legais
        padroes = [
            r'Lei\s+(?:nº\s*)?(\d+(?:\.\d+)*(?:/\d+)?)',
            r'Decreto\s+(?:nº\s*)?(\d+(?:\.\d+)*(?:/\d+)?)',
            r'Art(?:igo)?\.\s*(\d+)',
            r'CF(?:/88)?(?:\s*,?\s*art\.\s*(\d+))?',
            r'Constituição\s+Federal',
            r'CLT(?:\s*,?\s*art\.\s*(\d+))?'
        ]
        
        for padrao in padroes:
            matches = re.finditer(padrao, texto, re.IGNORECASE)
            for match in matches:
                fontes.append(match.group(0))
        
        # Remover duplicatas e limitar a 5 fontes
        fontes_unicas = list(set(fontes))[:5]
        
        return fontes_unicas
    
    def _calcular_confianca(self, resposta: str) -> float:
        """Calcula score de confiança da resposta"""
        confianca_base = 0.7
        
        # Aumentar confiança se há citações legais
        if self._extrair_fontes(resposta):
            confianca_base += 0.15
        
        # Aumentar confiança se usa termos técnicos apropriados
        termos_tecnicos = [
            'administração pública', 'servidor público', 'estatutário',
            'princípio', 'lei', 'decreto', 'constitucional'
        ]
        
        for termo in termos_tecnicos:
            if termo.lower() in resposta.lower():
                confianca_base += 0.02
        
        # Diminuir confiança se há expressões de incerteza
        expressoes_incerteza = [
            'possivelmente', 'provavelmente', 'creio que',
            'não tenho certeza', 'pode ser que'
        ]
        
        for expressao in expressoes_incerteza:
            if expressao.lower() in resposta.lower():
                confianca_base -= 0.1
        
        # Garantir que a confiança esteja entre 0 e 1
        return max(0.0, min(1.0, confianca_base))
    
    def _obter_timestamp(self) -> str:
        """Obtém timestamp atual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def validar_conexao(self) -> bool:
        """Valida se a conexão com Gemini está funcionando"""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Teste de conexão. Responda apenas 'OK'."
            )
            
            return bool(response and response.text and 'ok' in response.text.lower())
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao validar conexão Gemini: {e}")
            return False
