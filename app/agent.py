"""Conversational agent for SHL assessment recommendations."""

import logging
import re
from typing import List, Dict, Tuple, Optional
from urllib.parse import urlparse

from app.schemas import Message, Recommendation, ChatResponse
from app.retriever import SemanticRetriever
from app.llm_client import LLMClient
from app.prompts import (
    SYSTEM_PROMPT,
    create_clarification_prompt,
    create_recommendation_prompt,
    create_comparison_prompt,
    create_refusal_prompt,
    format_evidence
)
from app.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationalAgent:
    """Manages conversational flow and generates recommendations."""
    
    # Off-topic keywords
    OFF_TOPIC_KEYWORDS = [
        'weather', 'recipe', 'movie', 'music', 'sports', 'politics',
        'news', 'stock', 'crypto', 'game', 'joke', 'story'
    ]
    
    # Comparison keywords
    COMPARISON_KEYWORDS = [
        'compare', 'difference', 'versus', 'vs', 'better',
        'which one', 'what\'s the difference'
    ]
    
    # Refinement keywords
    REFINEMENT_KEYWORDS = [
        'shorter', 'longer', 'duration', 'remote', 'online',
        'language', 'different', 'another', 'alternative'
    ]
    
    def __init__(self, retriever: SemanticRetriever, llm_client: LLMClient):
        """
        Initialize the conversational agent.
        
        Args:
            retriever: Semantic retriever instance
            llm_client: LLM client instance
        """
        self.retriever = retriever
        self.llm_client = llm_client
        logger.info("Conversational agent initialized")
    
    def _detect_intent(self, messages: List[Message]) -> str:
        """
        Detect user intent from conversation.
        
        Args:
            messages: Conversation history
            
        Returns:
            Intent string: 'off_topic', 'comparison', 'refinement', 'clarification', or 'recommendation'
        """
        last_user_message = messages[-1].content.lower()
        
        # Check for off-topic
        if any(keyword in last_user_message for keyword in self.OFF_TOPIC_KEYWORDS):
            return 'off_topic'
        
        # Check for comparison
        if any(keyword in last_user_message for keyword in self.COMPARISON_KEYWORDS):
            return 'comparison'
        
        # Check for refinement (if there are previous recommendations)
        if len(messages) > 2:  # Has conversation history
            if any(keyword in last_user_message for keyword in self.REFINEMENT_KEYWORDS):
                return 'refinement'
        
        # Check if query is too vague (needs clarification)
        if self._is_vague(last_user_message):
            return 'clarification'
        
        return 'recommendation'
    
    def _is_vague(self, query: str) -> bool:
        """
        Determine if a query is too vague and needs clarification.
        
        Args:
            query: User query
            
        Returns:
            True if vague, False otherwise
        """
        query_lower = query.lower()
        
        # Very short queries are likely vague
        if len(query.split()) < 3:
            return True
        
        # Generic hiring terms without specifics
        vague_patterns = [
            r'^(hire|hiring|need|looking for|want)\s+(a|an|some)?\s*\w+\s*$',
            r'^(developer|engineer|manager|analyst)\s*$',
            r'^(test|assessment|evaluate)\s+(for|a|an)?\s*\w+\s*$'
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, query_lower):
                return True
        
        return False
    
    def _count_clarifications(self, messages: List[Message]) -> int:
        """
        Count how many clarifying questions have been asked.
        
        Args:
            messages: Conversation history
            
        Returns:
            Number of clarifications
        """
        count = 0
        for msg in messages:
            if msg.role == 'assistant' and '?' in msg.content:
                count += 1
        return count
    
    def _extract_filters(self, query: str) -> Dict[str, str]:
        """
        Extract metadata filters from user query.
        
        Args:
            query: User query
            
        Returns:
            Dictionary of filters
        """
        filters = {}
        query_lower = query.lower()
        
        # Extract test type
        if 'knowledge' in query_lower:
            filters['test_type'] = 'K'
        elif 'ability' in query_lower:
            filters['test_type'] = 'A'
        elif 'personality' in query_lower:
            filters['test_type'] = 'P'
        elif 'behavioral' in query_lower or 'behaviour' in query_lower:
            filters['test_type'] = 'B'
        
        # Extract job level
        if 'entry' in query_lower or 'junior' in query_lower:
            filters['job_level'] = 'entry'
        elif 'mid' in query_lower or 'intermediate' in query_lower:
            filters['job_level'] = 'mid'
        elif 'senior' in query_lower:
            filters['job_level'] = 'senior'
        elif 'executive' in query_lower or 'leadership' in query_lower:
            filters['job_level'] = 'executive'
        
        # Extract remote testing preference
        if 'remote' in query_lower or 'online' in query_lower:
            filters['remote_testing'] = 'yes'
        
        return filters
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate that URL belongs to shl.com domain.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            is_valid = config.VALID_DOMAIN in parsed.netloc.lower()
            if not is_valid:
                logger.warning(f"Invalid URL detected (not {config.VALID_DOMAIN}): {url}")
            return is_valid
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False
    
    def _hybrid_rerank(self, candidates: List[Dict], query: str) -> List[Dict]:
        """
        Re-rank candidates using hybrid scoring (semantic + keyword overlap).
        
        Args:
            candidates: List of candidate assessments
            query: User query
            
        Returns:
            Re-ranked list of candidates
        """
        query_words = set(query.lower().split())
        
        for candidate in candidates:
            # Get semantic score (already in candidate)
            semantic_score = candidate.get('similarity_score', 0.0)
            
            # Calculate keyword overlap score
            text = f"{candidate.get('name', '')} {candidate.get('description', '')}".lower()
            text_words = set(text.split())
            overlap = len(query_words & text_words)
            keyword_score = overlap / max(len(query_words), 1)
            
            # Combine scores (70% semantic, 30% keyword)
            candidate['hybrid_score'] = 0.7 * semantic_score + 0.3 * keyword_score
        
        # Sort by hybrid score
        candidates.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        return candidates
    
    def _create_recommendations(self, candidates: List[Dict]) -> List[Recommendation]:
        """
        Create recommendation objects from candidates.
        
        Args:
            candidates: List of candidate assessments
            
        Returns:
            List of Recommendation objects
        """
        recommendations = []
        
        for candidate in candidates:
            # Validate URL
            url = candidate.get('url', '')
            if not url or not self._validate_url(url):
                logger.warning(f"Skipping candidate with invalid URL: {candidate.get('name')}")
                continue
            
            recommendations.append(Recommendation(
                name=candidate.get('name', 'Unknown'),
                url=url,
                test_type=candidate.get('test_type', 'K')
            ))
        
        return recommendations
    
    def _should_end_conversation(self, messages: List[Message], has_recommendations: bool) -> bool:
        """
        Determine if conversation should end.
        
        Args:
            messages: Conversation history
            has_recommendations: Whether recommendations were provided
            
        Returns:
            True if conversation should end
        """
        # Check turn count
        if len(messages) >= config.MAX_CONVERSATION_TURNS:
            return True
        
        # Check for satisfaction expressions
        last_message = messages[-1].content.lower()
        satisfaction_keywords = ['thank', 'thanks', 'perfect', 'great', 'good', 'that\'s all', 'no more']
        if any(keyword in last_message for keyword in satisfaction_keywords):
            return True
        
        return False
    
    def process_conversation(self, messages: List[Message]) -> ChatResponse:
        """
        Process conversation and generate response.
        
        Args:
            messages: Conversation history
            
        Returns:
            ChatResponse with reply, recommendations, and end_of_conversation flag
        """
        logger.info(f"Processing conversation with {len(messages)} messages")
        
        # Detect intent
        intent = self._detect_intent(messages)
        logger.info(f"Detected intent: {intent}")
        
        # Get last user message
        last_user_message = messages[-1].content
        
        # Convert messages to dict format for LLM
        llm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Handle off-topic requests
        if intent == 'off_topic':
            prompt = create_refusal_prompt(last_user_message)
            reply = self.llm_client.generate_with_fallback(
                SYSTEM_PROMPT,
                [{"role": "user", "content": prompt}],
                fallback_message="I apologize, but I can only help with SHL assessment recommendations for hiring purposes."
            )
            return ChatResponse(
                reply=reply,
                recommendations=[],
                end_of_conversation=True
            )
        
        # Handle comparison requests
        if intent == 'comparison':
            # Extract assessment names from query
            # Simple extraction - look for quoted names or capitalized phrases
            names = re.findall(r'"([^"]+)"', last_user_message)
            if not names:
                names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', last_user_message)
            
            if names:
                assessments = self.retriever.retrieve_by_names(names)
                if assessments:
                    evidence = format_evidence(assessments)
                    prompt = create_comparison_prompt(evidence)
                    reply = self.llm_client.generate_with_fallback(
                        SYSTEM_PROMPT,
                        [{"role": "user", "content": prompt}]
                    )
                    return ChatResponse(
                        reply=reply,
                        recommendations=[],
                        end_of_conversation=False
                    )
            
            # Fallback if can't extract names
            reply = "I'd be happy to compare assessments for you. Could you please specify which assessments you'd like me to compare?"
            return ChatResponse(
                reply=reply,
                recommendations=[],
                end_of_conversation=False
            )
        
        # Handle clarification
        if intent == 'clarification':
            clarification_count = self._count_clarifications(messages)
            
            if clarification_count >= config.MAX_CLARIFICATIONS:
                # Too many clarifications, provide best-effort recommendations
                intent = 'recommendation'
            else:
                # Retrieve candidates for context
                candidates = self.retriever.retrieve(last_user_message, k=config.RETRIEVAL_K)
                evidence = format_evidence(candidates[:10])
                
                prompt = create_clarification_prompt(last_user_message, evidence)
                reply = self.llm_client.generate_with_fallback(
                    SYSTEM_PROMPT,
                    [{"role": "user", "content": prompt}]
                )
                
                return ChatResponse(
                    reply=reply,
                    recommendations=[],
                    end_of_conversation=False
                )
        
        # Handle recommendation or refinement
        if intent in ['recommendation', 'refinement']:
            # Extract filters
            filters = self._extract_filters(last_user_message)
            logger.info(f"Extracted filters: {filters}")
            
            # Retrieve candidates
            candidates = self.retriever.retrieve(
                last_user_message,
                k=config.RETRIEVAL_K,
                filters=filters if filters else None
            )
            
            if not candidates:
                reply = "I couldn't find any assessments matching your criteria. Could you provide more details or try different requirements?"
                return ChatResponse(
                    reply=reply,
                    recommendations=[],
                    end_of_conversation=False
                )
            
            # Re-rank using hybrid scoring
            candidates = self._hybrid_rerank(candidates, last_user_message)
            
            # Select top N (between 1 and 10)
            num_recommendations = min(len(candidates), config.MAX_RECOMMENDATIONS)
            selected_candidates = candidates[:num_recommendations]
            
            # Format evidence
            evidence = format_evidence(selected_candidates)
            
            # Build conversation context
            context = ""
            if len(messages) > 1:
                context = "\n".join([f"{msg.role}: {msg.content}" for msg in messages[:-1]])
            
            # Generate response
            prompt = create_recommendation_prompt(last_user_message, evidence, context)
            reply = self.llm_client.generate_with_fallback(
                SYSTEM_PROMPT,
                [{"role": "user", "content": prompt}]
            )
            
            # Create recommendations
            recommendations = self._create_recommendations(selected_candidates)
            
            # Determine if conversation should end
            end_conversation = self._should_end_conversation(messages, bool(recommendations))
            
            return ChatResponse(
                reply=reply,
                recommendations=recommendations,
                end_of_conversation=end_conversation
            )
        
        # Fallback
        reply = "I'm here to help you find relevant SHL assessments. What kind of role are you hiring for?"
        return ChatResponse(
            reply=reply,
            recommendations=[],
            end_of_conversation=False
        )
