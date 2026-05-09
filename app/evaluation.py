"""Evaluation utilities for the SHL Assessment Recommender."""

from typing import List, Dict, Set
from app.schemas import ChatResponse, Recommendation


def calculate_recall_at_k(
    retrieved: List[str],
    relevant: List[str],
    k: int = 10
) -> float:
    """
    Calculate Recall@K metric.
    
    Args:
        retrieved: List of retrieved assessment names
        relevant: List of relevant assessment names (ground truth)
        k: Number of top results to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant:
        return 0.0
    
    retrieved_at_k = set(retrieved[:k])
    relevant_set = set(relevant)
    
    hits = len(retrieved_at_k & relevant_set)
    recall = hits / len(relevant_set)
    
    return recall


def calculate_precision_at_k(
    retrieved: List[str],
    relevant: List[str],
    k: int = 10
) -> float:
    """
    Calculate Precision@K metric.
    
    Args:
        retrieved: List of retrieved assessment names
        relevant: List of relevant assessment names (ground truth)
        k: Number of top results to consider
        
    Returns:
        Precision@K score (0.0 to 1.0)
    """
    if not retrieved:
        return 0.0
    
    retrieved_at_k = set(retrieved[:k])
    relevant_set = set(relevant)
    
    hits = len(retrieved_at_k & relevant_set)
    precision = hits / min(k, len(retrieved))
    
    return precision


def calculate_groundedness(
    response: ChatResponse,
    retrieved_candidates: List[Dict]
) -> float:
    """
    Calculate groundedness metric (% of recommendations in retrieved evidence).
    
    Args:
        response: ChatResponse with recommendations
        retrieved_candidates: List of candidate dictionaries from retriever
        
    Returns:
        Groundedness score (0.0 to 1.0)
    """
    if not response.recommendations:
        return 1.0  # No recommendations to validate
    
    # Extract URLs from retrieved candidates
    retrieved_urls = {
        candidate.get('url', '').strip().lower()
        for candidate in retrieved_candidates
    }
    
    # Check how many recommendation URLs are in retrieved evidence
    grounded_count = 0
    for rec in response.recommendations:
        if rec.url.strip().lower() in retrieved_urls:
            grounded_count += 1
    
    groundedness = grounded_count / len(response.recommendations)
    
    return groundedness


def validate_schema_compliance(response: ChatResponse) -> bool:
    """
    Validate that response complies with schema requirements.
    
    Args:
        response: ChatResponse to validate
        
    Returns:
        True if compliant, False otherwise
    """
    try:
        # Check reply is not empty
        if not response.reply or not response.reply.strip():
            return False
        
        # Check recommendations count (0 to 10)
        if len(response.recommendations) > 10:
            return False
        
        # Check each recommendation has required fields
        for rec in response.recommendations:
            if not rec.name or not rec.url or not rec.test_type:
                return False
            
            # Check test_type is valid
            if rec.test_type not in ['K', 'A', 'P', 'B']:
                return False
            
            # Check URL is from shl.com
            if 'shl.com' not in rec.url.lower():
                return False
        
        # Check end_of_conversation is boolean
        if not isinstance(response.end_of_conversation, bool):
            return False
        
        return True
        
    except Exception:
        return False


def calculate_average_turns(conversations: List[List[Dict]]) -> float:
    """
    Calculate average number of turns to conversation completion.
    
    Args:
        conversations: List of conversation histories (each is a list of message dicts)
        
    Returns:
        Average number of turns
    """
    if not conversations:
        return 0.0
    
    total_turns = sum(len(conv) for conv in conversations)
    avg_turns = total_turns / len(conversations)
    
    return avg_turns


def evaluate_refusal_correctness(
    off_topic_queries: List[str],
    responses: List[ChatResponse]
) -> float:
    """
    Evaluate correctness of refusal for off-topic queries.
    
    Args:
        off_topic_queries: List of off-topic query strings
        responses: List of ChatResponse objects for those queries
        
    Returns:
        Refusal correctness score (0.0 to 1.0)
    """
    if not off_topic_queries or not responses:
        return 0.0
    
    if len(off_topic_queries) != len(responses):
        raise ValueError("Number of queries and responses must match")
    
    correct_refusals = 0
    
    for query, response in zip(off_topic_queries, responses):
        # Check if response refused (empty recommendations and end_of_conversation=True)
        if not response.recommendations and response.end_of_conversation:
            # Check if reply mentions scope limitation
            reply_lower = response.reply.lower()
            refusal_keywords = ['only', 'scope', 'cannot', 'can\'t', 'unable', 'shl assessment']
            if any(keyword in reply_lower for keyword in refusal_keywords):
                correct_refusals += 1
    
    correctness = correct_refusals / len(off_topic_queries)
    
    return correctness


class EvaluationReport:
    """Container for evaluation metrics."""
    
    def __init__(self):
        self.recall_at_10: List[float] = []
        self.precision_at_10: List[float] = []
        self.groundedness: List[float] = []
        self.schema_compliance: List[bool] = []
        self.conversation_turns: List[int] = []
        self.refusal_correctness: float = 0.0
    
    def add_retrieval_metrics(self, recall: float, precision: float):
        """Add retrieval quality metrics."""
        self.recall_at_10.append(recall)
        self.precision_at_10.append(precision)
    
    def add_groundedness(self, score: float):
        """Add groundedness score."""
        self.groundedness.append(score)
    
    def add_schema_compliance(self, is_compliant: bool):
        """Add schema compliance result."""
        self.schema_compliance.append(is_compliant)
    
    def add_conversation_turns(self, turns: int):
        """Add conversation turn count."""
        self.conversation_turns.append(turns)
    
    def set_refusal_correctness(self, score: float):
        """Set refusal correctness score."""
        self.refusal_correctness = score
    
    def get_summary(self) -> Dict[str, float]:
        """
        Get summary statistics.
        
        Returns:
            Dictionary with metric summaries
        """
        summary = {}
        
        if self.recall_at_10:
            summary['avg_recall_at_10'] = sum(self.recall_at_10) / len(self.recall_at_10)
        
        if self.precision_at_10:
            summary['avg_precision_at_10'] = sum(self.precision_at_10) / len(self.precision_at_10)
        
        if self.groundedness:
            summary['avg_groundedness'] = sum(self.groundedness) / len(self.groundedness)
        
        if self.schema_compliance:
            summary['schema_compliance_rate'] = sum(self.schema_compliance) / len(self.schema_compliance)
        
        if self.conversation_turns:
            summary['avg_conversation_turns'] = sum(self.conversation_turns) / len(self.conversation_turns)
        
        summary['refusal_correctness'] = self.refusal_correctness
        
        return summary
    
    def print_report(self):
        """Print formatted evaluation report."""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("EVALUATION REPORT")
        print("="*50)
        
        if 'avg_recall_at_10' in summary:
            print(f"\nRetrieval Quality:")
            print(f"  Recall@10:    {summary['avg_recall_at_10']:.2%}")
            print(f"  Precision@10: {summary['avg_precision_at_10']:.2%}")
        
        if 'avg_groundedness' in summary:
            print(f"\nResponse Quality:")
            print(f"  Groundedness: {summary['avg_groundedness']:.2%}")
        
        if 'schema_compliance_rate' in summary:
            print(f"  Schema Compliance: {summary['schema_compliance_rate']:.2%}")
        
        if 'avg_conversation_turns' in summary:
            print(f"\nConversation Efficiency:")
            print(f"  Avg Turns: {summary['avg_conversation_turns']:.1f}")
        
        if 'refusal_correctness' in summary:
            print(f"\nSecurity:")
            print(f"  Refusal Correctness: {summary['refusal_correctness']:.2%}")
        
        print("\n" + "="*50 + "\n")
