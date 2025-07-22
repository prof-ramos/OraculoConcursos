"""
Módulo de estratégias anti-alucinação para o Oráculo de Concursos Públicos
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class AntiHallucinationManager:
    """Gerenciador de estratégias para reduzir alucinações do modelo"""
    
    def __init__(self, confidence_threshold: float = 0.9):
        self.confidence_threshold = confidence_threshold
        self.known_laws = self._load_known_laws()
        self.forbidden_phrases = self._load_forbidden_phrases()
        self.verification_patterns = self._load_verification_patterns()
    
    def _load_known_laws(self) -> Dict[str, str]:
        """Carrega leis conhecidas para verificação"""
        return {
            "8112": "Lei 8.112/90 - Estatuto dos Servidores Públicos",
            "8666": "Lei 8.666/93 - Licitações e Contratos",
            "9784": "Lei 9.784/99 - Processo Administrativo Federal",
            "12527": "Lei 12.527/11 - Lei de Acesso à Informação",
            "13709": "Lei 13.709/18 - Lei Geral de Proteção de Dados",
            "14133": "Lei 14.133/21 - Nova Lei de Licitações",
            "cf88": "Constituição Federal de 1988",
            "cpc": "Código de Processo Civil - Lei 13.105/15",
            "cc": "Código Civil - Lei 10.406/02",
            "cp": "Código Penal - Decreto-Lei 2.848/40",
            "clt": "Consolidação das Leis do Trabalho - Decreto-Lei 5.452/43"
        }
    
    def _load_forbidden_phrases(self) -> List[str]:
        """Frases que indicam possível alucinação"""
        return [
            "não tenho certeza",
            "pode estar incorreto",
            "creio que",
            "acho que",
            "parece ser",
            "provavelmente",
            "talvez",
            "segundo minha interpretação pessoal",
            "na minha opinião",
            "eu acho",
            "suponho que"
        ]
    
    def _load_verification_patterns(self) -> Dict[str, str]:
        """Padrões para verificação de respostas"""
        return {
            "lei_pattern": r"lei\s+(\d+[./]*\d*)",
            "artigo_pattern": r"art\.?\s*(\d+)",
            "inciso_pattern": r"inciso\s+([ivxlcdm]+|\d+)",
            "paragrafo_pattern": r"§\s*(\d+)",
            "data_pattern": r"(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})",
            "porcentagem_pattern": r"(\d+(?:,\d+)?)\s*%"
        }
    
    async def validate_response(self, response: str, confidence_score: float, 
                              user_question: str) -> Tuple[bool, str, float]:
        """
        Valida uma resposta usando múltiplas estratégias anti-alucinação
        Retorna: (is_valid, validated_response, adjusted_confidence)
        """
        try:
            # 1. Verificar limiar de confiança
            if confidence_score < self.confidence_threshold:
                logger.info(f"❌ Confiança insuficiente: {confidence_score:.2f} < {self.confidence_threshold}")
                return False, "🤔 Não tenho certeza suficiente para responder essa pergunta com precisão.", 0.1
            
            # 2. Verificar frases proibidas
            uncertainty_detected = self._check_uncertainty_phrases(response)
            if uncertainty_detected:
                adjusted_confidence = max(0.1, confidence_score - 0.3)
                logger.warning(f"⚠️ Frases de incerteza detectadas, confiança ajustada para: {adjusted_confidence:.2f}")
                if adjusted_confidence < self.confidence_threshold:
                    return False, "🤔 Detectei incerteza na resposta. Prefiro não responder para manter a qualidade.", adjusted_confidence
            
            # 3. Verificar referências legais
            legal_refs_valid = await self._validate_legal_references(response)
            if not legal_refs_valid:
                logger.warning("⚠️ Possíveis referências legais incorretas detectadas")
                confidence_score *= 0.7  # Reduz confiança
            
            # 4. Verificar consistência contextual
            context_score = await self._check_contextual_consistency(response, user_question)
            final_confidence = confidence_score * context_score
            
            # 5. Verificação de números e datas
            numbers_valid = self._validate_numbers_and_dates(response)
            if not numbers_valid:
                logger.warning("⚠️ Possíveis inconsistências numéricas detectadas")
                final_confidence *= 0.8
            
            # 6. Verificação final
            if final_confidence < self.confidence_threshold:
                return False, self._generate_safe_response(user_question), final_confidence
            
            # 7. Adicionar disclaimer se necessário
            validated_response = self._add_disclaimer_if_needed(response, final_confidence)
            
            logger.info(f"✅ Resposta validada com confiança: {final_confidence:.2f}")
            return True, validated_response, final_confidence
            
        except Exception as e:
            logger.error(f"❌ Erro na validação anti-alucinação: {e}")
            return False, "❌ Erro interno na validação da resposta.", 0.1
    
    def _check_uncertainty_phrases(self, response: str) -> bool:
        """Verifica se há frases que indicam incerteza"""
        response_lower = response.lower()
        for phrase in self.forbidden_phrases:
            if phrase in response_lower:
                logger.debug(f"🔍 Frase de incerteza encontrada: '{phrase}'")
                return True
        return False
    
    async def _validate_legal_references(self, response: str) -> bool:
        """Valida se as referências legais mencionadas são conhecidas"""
        try:
            # Extrair possíveis referências de leis
            lei_matches = re.findall(self.verification_patterns["lei_pattern"], response.lower())
            
            for lei in lei_matches:
                lei_clean = lei.replace(".", "").replace("/", "")
                if lei_clean not in self.known_laws:
                    logger.warning(f"⚠️ Lei não reconhecida: {lei}")
                    # Não falha automaticamente, mas registra a suspeita
                    
            return True  # Por enquanto, apenas registra suspeitas
            
        except Exception as e:
            logger.error(f"❌ Erro na validação de referências legais: {e}")
            return True  # Em caso de erro, não bloqueia
    
    async def _check_contextual_consistency(self, response: str, question: str) -> float:
        """Verifica consistência contextual entre pergunta e resposta"""
        try:
            # Análise básica de palavras-chave
            question_words = set(question.lower().split())
            response_words = set(response.lower().split())
            
            # Palavras-chave importantes para concursos
            important_keywords = {
                'direito', 'lei', 'constituição', 'servidor', 'concurso', 'público',
                'administrativo', 'constitucional', 'penal', 'civil', 'processo',
                'licitação', 'contrato', 'cargo', 'função', 'estabilidade'
            }
            
            question_keywords = question_words.intersection(important_keywords)
            response_keywords = response_words.intersection(important_keywords)
            
            if question_keywords and len(question_keywords.intersection(response_keywords)) == 0:
                logger.warning("⚠️ Possível inconsistência contextual")
                return 0.7  # Reduz score
            
            return 1.0  # Contexto parece consistente
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação contextual: {e}")
            return 1.0  # Em caso de erro, não penaliza
    
    def _validate_numbers_and_dates(self, response: str) -> bool:
        """Valida números e datas mencionados na resposta"""
        try:
            # Verificar datas
            date_matches = re.findall(self.verification_patterns["data_pattern"], response)
            for date_str in date_matches:
                # Verificações básicas de formato de data
                if not self._is_valid_date_format(date_str):
                    logger.warning(f"⚠️ Formato de data suspeito: {date_str}")
                    return False
            
            # Verificar porcentagens
            percent_matches = re.findall(self.verification_patterns["porcentagem_pattern"], response)
            for percent in percent_matches:
                percent_float = float(percent.replace(",", "."))
                if percent_float > 100:
                    logger.warning(f"⚠️ Porcentagem suspeita: {percent}%")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na validação numérica: {e}")
            return True  # Em caso de erro, não bloqueia
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Verifica se o formato de data é válido"""
        try:
            # Formatos comuns brasileiros
            formats = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except:
            return False
    
    def _generate_safe_response(self, question: str) -> str:
        """Gera uma resposta segura quando a validação falha"""
        safe_responses = [
            "🤔 Não tenho certeza suficiente para responder essa pergunta com a precisão necessária para concursos públicos.",
            "📚 Para essa questão específica, recomendo consultar a legislação oficial ou materiais especializados.",
            "⚠️ Prefiro não responder a essa pergunta pois não tenho confiança suficiente na resposta.",
            "🎯 Essa questão requer maior precisão. Sugiro consultar fontes oficiais ou professores especializados."
        ]
        
        # Escolher resposta baseada no tipo de pergunta
        if any(word in question.lower() for word in ['lei', 'artigo', 'legislação']):
            return safe_responses[1]
        elif any(word in question.lower() for word in ['como', 'quando', 'onde']):
            return safe_responses[0]
        else:
            return safe_responses[2]
    
    def _add_disclaimer_if_needed(self, response: str, confidence: float) -> str:
        """Adiciona disclaimer se a confiança não for muito alta"""
        if confidence < 0.95:
            disclaimer = "\n\n⚠️ *Sempre confira informações em fontes oficiais antes de estudar ou tomar decisões baseadas nesta resposta.*"
            return response + disclaimer
        
        return response
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema de validação"""
        return {
            "confidence_threshold": self.confidence_threshold,
            "known_laws_count": len(self.known_laws),
            "forbidden_phrases_count": len(self.forbidden_phrases),
            "verification_patterns_count": len(self.verification_patterns)
        }
    
    def adjust_threshold(self, new_threshold: float):
        """Permite ajustar o limiar de confiança dinamicamente"""
        if 0.5 <= new_threshold <= 1.0:
            old_threshold = self.confidence_threshold
            self.confidence_threshold = new_threshold
            logger.info(f"🎯 Limiar de confiança ajustado: {old_threshold:.2f} → {new_threshold:.2f}")
        else:
            logger.warning(f"❌ Limiar inválido: {new_threshold}. Deve estar entre 0.5 e 1.0")
