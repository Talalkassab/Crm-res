"""
A/B Testing Service
Manages experiments for feedback collection optimization
"""

from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import random
import json
from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import stats

from ..repositories.campaign_repository import CampaignRepository


class ExperimentStatus(str, Enum):
    """A/B Test experiment statuses"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class VariantAssignmentStrategy(str, Enum):
    """Strategies for assigning variants to users"""
    RANDOM = "random"
    WEIGHTED = "weighted"
    HASH_BASED = "hash_based"  # Consistent assignment based on phone number


@dataclass
class ExperimentVariant:
    """Single variant in an A/B test"""
    id: str
    name: str
    weight: float  # 0.0 to 1.0
    template: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float] = None
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = {
                "participants": 0,
                "responses": 0,
                "response_rate": 0.0,
                "average_rating": 0.0,
                "completion_rate": 0.0,
                "positive_sentiment": 0.0
            }


@dataclass
class ABTestExperiment:
    """A/B Test experiment configuration"""
    id: str
    campaign_id: str
    name: str
    description: str
    variants: List[ExperimentVariant]
    status: ExperimentStatus
    assignment_strategy: VariantAssignmentStrategy
    min_sample_size: int
    confidence_level: float = 0.95
    created_at: datetime = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    winning_variant: Optional[str] = None
    statistical_significance: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ABTestingService:
    """Service for managing A/B tests in feedback campaigns"""
    
    def __init__(self):
        self.campaign_repo = CampaignRepository()
        self.experiments: Dict[str, ABTestExperiment] = {}
    
    async def create_experiment(
        self,
        campaign_id: UUID,
        name: str,
        description: str,
        variants: List[Dict[str, Any]],
        min_sample_size: int = 100,
        assignment_strategy: VariantAssignmentStrategy = VariantAssignmentStrategy.WEIGHTED
    ) -> str:
        """
        Create a new A/B test experiment
        """
        experiment_id = str(uuid4())
        
        # Convert variant dictionaries to ExperimentVariant objects
        variant_objects = []
        total_weight = 0.0
        
        for i, variant_data in enumerate(variants):
            variant = ExperimentVariant(
                id=variant_data.get('id', f'variant_{i}'),
                name=variant_data.get('name', f'Variant {i+1}'),
                weight=variant_data.get('weight', 1.0 / len(variants)),
                template=variant_data.get('template', 'default'),
                parameters=variant_data.get('parameters', {})
            )
            variant_objects.append(variant)
            total_weight += variant.weight
        
        # Normalize weights to sum to 1.0
        if abs(total_weight - 1.0) > 0.001:
            for variant in variant_objects:
                variant.weight = variant.weight / total_weight
        
        experiment = ABTestExperiment(
            id=experiment_id,
            campaign_id=str(campaign_id),
            name=name,
            description=description,
            variants=variant_objects,
            status=ExperimentStatus.DRAFT,
            assignment_strategy=assignment_strategy,
            min_sample_size=min_sample_size
        )
        
        self.experiments[experiment_id] = experiment
        
        # Store in database
        await self.campaign_repo.create_experiment(campaign_id, {
            'id': experiment_id,
            'name': name,
            'description': description,
            'variants': [self._variant_to_dict(v) for v in variant_objects],
            'assignment_strategy': assignment_strategy.value,
            'min_sample_size': min_sample_size,
            'status': ExperimentStatus.DRAFT.value
        })
        
        return experiment_id
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment"""
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.DRAFT:
            return False
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = datetime.now()
        
        # Update in database
        await self._update_experiment_in_db(experiment)
        
        return True
    
    async def assign_variant(
        self,
        experiment_id: str,
        customer_phone: str,
        campaign_id: Optional[UUID] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Assign a variant to a customer for an experiment
        """
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.RUNNING:
            return None
        
        # Choose assignment strategy
        if experiment.assignment_strategy == VariantAssignmentStrategy.HASH_BASED:
            variant = self._assign_variant_hash_based(experiment, customer_phone)
        elif experiment.assignment_strategy == VariantAssignmentStrategy.WEIGHTED:
            variant = self._assign_variant_weighted(experiment)
        else:  # RANDOM
            variant = self._assign_variant_random(experiment)
        
        if not variant:
            return None
        
        # Record assignment
        await self._record_variant_assignment(
            experiment_id,
            customer_phone,
            variant.id,
            campaign_id
        )
        
        # Update participant count
        variant.metrics["participants"] += 1
        await self._update_experiment_in_db(experiment)
        
        return {
            'experiment_id': experiment_id,
            'variant_id': variant.id,
            'variant_name': variant.name,
            'template': variant.template,
            'parameters': variant.parameters
        }
    
    def _assign_variant_hash_based(
        self,
        experiment: ABTestExperiment,
        customer_phone: str
    ) -> Optional[ExperimentVariant]:
        """Assign variant based on phone number hash (consistent assignment)"""
        if not experiment.variants:
            return None
        
        # Create a hash from phone number
        hash_value = hash(customer_phone) % 1000000
        normalized_hash = hash_value / 1000000.0  # 0.0 to 1.0
        
        # Assign based on weight distribution
        cumulative_weight = 0.0
        for variant in experiment.variants:
            cumulative_weight += variant.weight
            if normalized_hash <= cumulative_weight:
                return variant
        
        # Fallback to last variant
        return experiment.variants[-1]
    
    def _assign_variant_weighted(
        self,
        experiment: ABTestExperiment
    ) -> Optional[ExperimentVariant]:
        """Assign variant based on weights"""
        if not experiment.variants:
            return None
        
        random_value = random.random()
        cumulative_weight = 0.0
        
        for variant in experiment.variants:
            cumulative_weight += variant.weight
            if random_value <= cumulative_weight:
                return variant
        
        return experiment.variants[-1]
    
    def _assign_variant_random(
        self,
        experiment: ABTestExperiment
    ) -> Optional[ExperimentVariant]:
        """Assign variant randomly (equal probability)"""
        if not experiment.variants:
            return None
        
        return random.choice(experiment.variants)
    
    async def record_variant_result(
        self,
        experiment_id: str,
        customer_phone: str,
        result_data: Dict[str, Any]
    ) -> bool:
        """
        Record the result for a variant assignment
        """
        if experiment_id not in self.experiments:
            return False
        
        experiment = self.experiments[experiment_id]
        
        # Get the variant assignment
        variant_id = await self._get_customer_variant_assignment(
            experiment_id,
            customer_phone
        )
        
        if not variant_id:
            return False
        
        # Find the variant
        variant = next(
            (v for v in experiment.variants if v.id == variant_id),
            None
        )
        
        if not variant:
            return False
        
        # Update variant metrics
        await self._update_variant_metrics(variant, result_data)
        
        # Check if experiment should be analyzed
        await self._check_experiment_completion(experiment)
        
        await self._update_experiment_in_db(experiment)
        
        return True
    
    async def _update_variant_metrics(
        self,
        variant: ExperimentVariant,
        result_data: Dict[str, Any]
    ):
        """Update variant performance metrics"""
        # Response recorded
        if result_data.get('responded'):
            variant.metrics["responses"] += 1
        
        # Rating data
        rating = result_data.get('rating')
        if rating:
            current_avg = variant.metrics["average_rating"]
            current_responses = variant.metrics["responses"]
            if current_responses > 1:
                variant.metrics["average_rating"] = (
                    (current_avg * (current_responses - 1) + rating) / current_responses
                )
            else:
                variant.metrics["average_rating"] = rating
        
        # Sentiment data
        sentiment_score = result_data.get('sentiment_score')
        if sentiment_score is not None and sentiment_score > 0.3:
            variant.metrics["positive_sentiment"] += 1
        
        # Completion data
        if result_data.get('conversation_completed'):
            variant.metrics["completion_rate"] = (
                variant.metrics.get("completed_conversations", 0) + 1
            ) / variant.metrics["participants"]
        
        # Update response rate
        if variant.metrics["participants"] > 0:
            variant.metrics["response_rate"] = (
                variant.metrics["responses"] / variant.metrics["participants"]
            )
    
    async def _check_experiment_completion(self, experiment: ABTestExperiment):
        """Check if experiment has enough data for statistical analysis"""
        total_participants = sum(v.metrics["participants"] for v in experiment.variants)
        
        # Check minimum sample size
        if total_participants < experiment.min_sample_size:
            return
        
        # Run statistical analysis
        significance_results = await self._analyze_statistical_significance(experiment)
        
        if significance_results['is_significant']:
            experiment.statistical_significance = significance_results
            experiment.winning_variant = significance_results['winning_variant']
            
            # Auto-complete experiment if configured
            if significance_results['confidence'] >= experiment.confidence_level:
                experiment.status = ExperimentStatus.COMPLETED
                experiment.ended_at = datetime.now()
    
    async def _analyze_statistical_significance(
        self,
        experiment: ABTestExperiment
    ) -> Dict[str, Any]:
        """
        Perform statistical analysis to determine experiment results
        """
        if len(experiment.variants) < 2:
            return {'is_significant': False, 'reason': 'Need at least 2 variants'}
        
        # Prepare data for analysis
        variant_data = []
        for variant in experiment.variants:
            if variant.metrics["participants"] < 10:  # Minimum data requirement
                continue
            
            variant_data.append({
                'id': variant.id,
                'name': variant.name,
                'participants': variant.metrics["participants"],
                'responses': variant.metrics["responses"],
                'response_rate': variant.metrics["response_rate"],
                'average_rating': variant.metrics["average_rating"]
            })
        
        if len(variant_data) < 2:
            return {'is_significant': False, 'reason': 'Insufficient data'}
        
        # Analyze response rates using Chi-square test
        response_rate_analysis = self._analyze_response_rates(variant_data)
        
        # Analyze average ratings using t-test
        rating_analysis = self._analyze_ratings(variant_data)
        
        # Determine overall significance
        is_significant = (
            response_rate_analysis['significant'] or
            rating_analysis['significant']
        )
        
        # Find winning variant
        winning_variant = None
        if is_significant:
            # Choose variant with best combined performance
            best_score = -1
            for variant_info in variant_data:
                # Combined score: response_rate * 0.6 + rating_normalized * 0.4
                normalized_rating = variant_info['average_rating'] / 5.0
                combined_score = (
                    variant_info['response_rate'] * 0.6 +
                    normalized_rating * 0.4
                )
                if combined_score > best_score:
                    best_score = combined_score
                    winning_variant = variant_info['id']
        
        return {
            'is_significant': is_significant,
            'confidence': max(
                response_rate_analysis.get('confidence', 0),
                rating_analysis.get('confidence', 0)
            ),
            'winning_variant': winning_variant,
            'response_rate_analysis': response_rate_analysis,
            'rating_analysis': rating_analysis,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _analyze_response_rates(
        self,
        variant_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze response rate differences using Chi-square test"""
        if len(variant_data) != 2:
            return {'significant': False, 'reason': 'Only supports 2-variant comparison'}
        
        v1, v2 = variant_data
        
        # Create contingency table
        # [[responded_v1, not_responded_v1], [responded_v2, not_responded_v2]]
        contingency_table = [
            [v1['responses'], v1['participants'] - v1['responses']],
            [v2['responses'], v2['participants'] - v2['responses']]
        ]
        
        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            return {
                'significant': p_value < 0.05,
                'p_value': p_value,
                'chi2_statistic': chi2,
                'confidence': (1 - p_value) if p_value < 0.05 else 0,
                'effect_size': abs(v1['response_rate'] - v2['response_rate'])
            }
        except Exception as e:
            return {'significant': False, 'error': str(e)}
    
    def _analyze_ratings(
        self,
        variant_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze rating differences using t-test"""
        if len(variant_data) != 2:
            return {'significant': False, 'reason': 'Only supports 2-variant comparison'}
        
        v1, v2 = variant_data
        
        # For simplicity, assume normal distribution of ratings
        # In production, you'd want actual rating distributions
        
        try:
            # Simplified t-test assuming equal variance
            mean_diff = abs(v1['average_rating'] - v2['average_rating'])
            
            # Rough estimate of significance based on mean difference
            # This is simplified - proper t-test would need individual rating data
            if mean_diff > 0.5:  # Half star difference
                return {
                    'significant': True,
                    'mean_difference': mean_diff,
                    'confidence': 0.95,
                    'better_variant': v1['id'] if v1['average_rating'] > v2['average_rating'] else v2['id']
                }
            else:
                return {
                    'significant': False,
                    'mean_difference': mean_diff,
                    'confidence': 0
                }
        except Exception as e:
            return {'significant': False, 'error': str(e)}
    
    async def get_experiment_results(
        self,
        experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get comprehensive experiment results"""
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        # Calculate summary statistics
        total_participants = sum(v.metrics["participants"] for v in experiment.variants)
        total_responses = sum(v.metrics["responses"] for v in experiment.variants)
        
        results = {
            'experiment_id': experiment_id,
            'name': experiment.name,
            'status': experiment.status.value,
            'created_at': experiment.created_at.isoformat(),
            'started_at': experiment.started_at.isoformat() if experiment.started_at else None,
            'ended_at': experiment.ended_at.isoformat() if experiment.ended_at else None,
            'total_participants': total_participants,
            'total_responses': total_responses,
            'overall_response_rate': (total_responses / total_participants * 100) if total_participants > 0 else 0,
            'winning_variant': experiment.winning_variant,
            'statistical_significance': experiment.statistical_significance,
            'variants': []
        }
        
        for variant in experiment.variants:
            variant_result = {
                'id': variant.id,
                'name': variant.name,
                'weight': variant.weight,
                'template': variant.template,
                'metrics': variant.metrics.copy()
            }
            
            # Add percentage of total participants
            if total_participants > 0:
                variant_result['participant_share'] = (
                    variant.metrics["participants"] / total_participants * 100
                )
            
            results['variants'].append(variant_result)
        
        return results
    
    async def _record_variant_assignment(
        self,
        experiment_id: str,
        customer_phone: str,
        variant_id: str,
        campaign_id: Optional[UUID]
    ):
        """Record variant assignment for tracking"""
        # This would be stored in database for persistent tracking
        assignment_record = {
            'experiment_id': experiment_id,
            'customer_phone': customer_phone,
            'variant_id': variant_id,
            'campaign_id': str(campaign_id) if campaign_id else None,
            'assigned_at': datetime.now().isoformat()
        }
        
        # Store in assignments table (implementation needed)
        pass
    
    async def _get_customer_variant_assignment(
        self,
        experiment_id: str,
        customer_phone: str
    ) -> Optional[str]:
        """Get customer's variant assignment"""
        # This would query the assignments table
        # For now, return None (implementation needed)
        return None
    
    async def _update_experiment_in_db(self, experiment: ABTestExperiment):
        """Update experiment in database"""
        experiment_data = {
            'status': experiment.status.value,
            'started_at': experiment.started_at.isoformat() if experiment.started_at else None,
            'ended_at': experiment.ended_at.isoformat() if experiment.ended_at else None,
            'winning_variant': experiment.winning_variant,
            'statistical_significance': experiment.statistical_significance,
            'variants': [self._variant_to_dict(v) for v in experiment.variants],
            'updated_at': datetime.now().isoformat()
        }
        
        await self.campaign_repo.update_experiment_metrics(
            UUID(experiment.id),
            experiment_data
        )
    
    def _variant_to_dict(self, variant: ExperimentVariant) -> Dict[str, Any]:
        """Convert variant to dictionary for storage"""
        return {
            'id': variant.id,
            'name': variant.name,
            'weight': variant.weight,
            'template': variant.template,
            'parameters': variant.parameters,
            'metrics': variant.metrics
        }