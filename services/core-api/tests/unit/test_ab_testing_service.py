"""
Unit tests for A/B Testing Service
Tests variant assignment logic, statistical analysis, and experiment management
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.services.ab_testing_service import ABTestingService
from src.repositories.campaign_repository import CampaignRepository


class TestABTestingService:
    
    @pytest.fixture
    def mock_campaign_repo(self):
        repo = Mock(spec=CampaignRepository)
        return repo
    
    @pytest.fixture
    def ab_service(self, mock_campaign_repo):
        return ABTestingService(mock_campaign_repo)
    
    @pytest.fixture
    def sample_experiment_config(self):
        return {
            'name': 'Greeting Style Test',
            'description': 'Testing formal vs casual messaging',
            'variants': [
                {
                    'id': 'formal',
                    'name': 'Formal Greeting',
                    'weight': 0.5,
                    'parameters': {
                        'template': 'greeting_formal',
                        'tone': 'formal',
                        'emoji': False
                    }
                },
                {
                    'id': 'casual',
                    'name': 'Casual Greeting',
                    'weight': 0.5,
                    'parameters': {
                        'template': 'greeting_casual',
                        'tone': 'casual',
                        'emoji': True
                    }
                }
            ],
            'metrics': ['response_rate', 'completion_rate', 'avg_rating'],
            'min_sample_size': 100,
            'confidence_level': 0.95
        }
    
    def test_validate_experiment_config_valid(self, ab_service, sample_experiment_config):
        """Test validation of valid experiment configuration"""
        result = ab_service.validate_experiment_config(sample_experiment_config)
        
        assert result['valid'] is True
        assert result['errors'] == []
    
    def test_validate_experiment_config_invalid_weights(self, ab_service, sample_experiment_config):
        """Test validation fails with invalid weight distribution"""
        sample_experiment_config['variants'][0]['weight'] = 0.3
        sample_experiment_config['variants'][1]['weight'] = 0.3  # Total = 0.6 != 1.0
        
        result = ab_service.validate_experiment_config(sample_experiment_config)
        
        assert result['valid'] is False
        assert 'sum to 1.0' in result['errors'][0]
    
    def test_validate_experiment_config_missing_required_fields(self, ab_service):
        """Test validation fails with missing required fields"""
        invalid_config = {
            'name': 'Test',
            # Missing variants
        }
        
        result = ab_service.validate_experiment_config(invalid_config)
        
        assert result['valid'] is False
        assert any('variants' in error for error in result['errors'])
    
    def test_validate_experiment_config_too_few_variants(self, ab_service):
        """Test validation fails with insufficient variants"""
        invalid_config = {
            'name': 'Test',
            'variants': [
                {'id': 'single', 'weight': 1.0, 'parameters': {}}
            ]
        }
        
        result = ab_service.validate_experiment_config(invalid_config)
        
        assert result['valid'] is False
        assert 'at least 2 variants' in result['errors'][0]
    
    def test_validate_experiment_config_duplicate_variant_ids(self, ab_service, sample_experiment_config):
        """Test validation fails with duplicate variant IDs"""
        sample_experiment_config['variants'][1]['id'] = 'formal'  # Duplicate ID
        
        result = ab_service.validate_experiment_config(sample_experiment_config)
        
        assert result['valid'] is False
        assert 'duplicate variant IDs' in result['errors'][0]
    
    def test_assign_variant_weighted_distribution(self, ab_service, sample_experiment_config):
        """Test variant assignment follows weight distribution"""
        experiment_id = str(uuid.uuid4())
        assignments = {}
        
        # Run many assignments to test distribution
        for i in range(1000):
            customer_id = f"customer_{i}"
            variant = ab_service.assign_variant(
                experiment_id,
                customer_id,
                sample_experiment_config['variants']
            )
            assignments[variant['id']] = assignments.get(variant['id'], 0) + 1
        
        # Check distribution is roughly equal (50/50 with some tolerance)
        formal_count = assignments.get('formal', 0)
        casual_count = assignments.get('casual', 0)
        
        # Allow 10% tolerance for randomness
        assert abs(formal_count - casual_count) / 1000 < 0.1
        assert formal_count + casual_count == 1000
    
    def test_assign_variant_consistent_for_same_customer(self, ab_service, sample_experiment_config):
        """Test same customer always gets same variant for same experiment"""
        experiment_id = str(uuid.uuid4())
        customer_id = "consistent_customer"
        
        # Get variant multiple times
        variant1 = ab_service.assign_variant(
            experiment_id,
            customer_id,
            sample_experiment_config['variants']
        )
        variant2 = ab_service.assign_variant(
            experiment_id,
            customer_id,
            sample_experiment_config['variants']
        )
        variant3 = ab_service.assign_variant(
            experiment_id,
            customer_id,
            sample_experiment_config['variants']
        )
        
        assert variant1['id'] == variant2['id'] == variant3['id']
    
    def test_assign_variant_uneven_weights(self, ab_service):
        """Test variant assignment with uneven weight distribution"""
        variants = [
            {'id': 'heavy', 'weight': 0.8, 'parameters': {}},
            {'id': 'light', 'weight': 0.2, 'parameters': {}}
        ]
        
        experiment_id = str(uuid.uuid4())
        assignments = {}
        
        # Run many assignments
        for i in range(1000):
            customer_id = f"customer_{i}"
            variant = ab_service.assign_variant(experiment_id, customer_id, variants)
            assignments[variant['id']] = assignments.get(variant['id'], 0) + 1
        
        # Check distribution follows weights (80/20 with tolerance)
        heavy_ratio = assignments.get('heavy', 0) / 1000
        light_ratio = assignments.get('light', 0) / 1000
        
        assert abs(heavy_ratio - 0.8) < 0.05  # 5% tolerance
        assert abs(light_ratio - 0.2) < 0.05
    
    def test_calculate_statistical_significance_significant_difference(self, ab_service):
        """Test statistical significance calculation with significant difference"""
        metrics_a = {
            'conversions': 120,
            'total': 1000,
            'rate': 0.12
        }
        
        metrics_b = {
            'conversions': 180,
            'total': 1000,
            'rate': 0.18
        }
        
        result = ab_service.calculate_statistical_significance(
            metrics_a,
            metrics_b,
            confidence_level=0.95
        )
        
        assert result['is_significant'] is True
        assert result['p_value'] < 0.05
        assert result['confidence_level'] == 0.95
        assert 'improvement' in result
    
    def test_calculate_statistical_significance_no_difference(self, ab_service):
        """Test statistical significance calculation with no significant difference"""
        metrics_a = {
            'conversions': 120,
            'total': 1000,
            'rate': 0.12
        }
        
        metrics_b = {
            'conversions': 125,
            'total': 1000,
            'rate': 0.125
        }
        
        result = ab_service.calculate_statistical_significance(
            metrics_a,
            metrics_b,
            confidence_level=0.95
        )
        
        assert result['is_significant'] is False
        assert result['p_value'] >= 0.05
    
    def test_calculate_statistical_significance_insufficient_data(self, ab_service):
        """Test statistical significance calculation with insufficient data"""
        metrics_a = {
            'conversions': 5,
            'total': 10,
            'rate': 0.5
        }
        
        metrics_b = {
            'conversions': 3,
            'total': 10,
            'rate': 0.3
        }
        
        result = ab_service.calculate_statistical_significance(
            metrics_a,
            metrics_b,
            confidence_level=0.95
        )
        
        assert result['is_significant'] is False
        assert result['insufficient_data'] is True
        assert result['min_sample_size_recommendation'] > 10
    
    def test_determine_winning_variant_clear_winner(self, ab_service):
        """Test determining winning variant with clear statistical winner"""
        experiment_data = {
            'variants': [
                {'id': 'a', 'name': 'Variant A'},
                {'id': 'b', 'name': 'Variant B'}
            ]
        }
        
        metrics = {
            'a': {
                'conversions': 120,
                'total': 1000,
                'rate': 0.12,
                'avg_rating': 4.2
            },
            'b': {
                'conversions': 180,
                'total': 1000,
                'rate': 0.18,
                'avg_rating': 4.5
            }
        }
        
        result = ab_service.determine_winning_variant(experiment_data, metrics)
        
        assert result['has_winner'] is True
        assert result['winning_variant'] == 'b'
        assert result['is_statistically_significant'] is True
        assert result['confidence'] > 0.95
    
    def test_determine_winning_variant_no_clear_winner(self, ab_service):
        """Test determining winning variant with no statistical difference"""
        experiment_data = {
            'variants': [
                {'id': 'a', 'name': 'Variant A'},
                {'id': 'b', 'name': 'Variant B'}
            ]
        }
        
        metrics = {
            'a': {
                'conversions': 120,
                'total': 1000,
                'rate': 0.12,
                'avg_rating': 4.2
            },
            'b': {
                'conversions': 125,
                'total': 1000,
                'rate': 0.125,
                'avg_rating': 4.25
            }
        }
        
        result = ab_service.determine_winning_variant(experiment_data, metrics)
        
        assert result['has_winner'] is False
        assert result['is_statistically_significant'] is False
        assert result['recommendation'] == 'continue_testing'
    
    def test_calculate_required_sample_size(self, ab_service):
        """Test sample size calculation for experiments"""
        # Test for detecting 5% improvement with 95% confidence and 80% power
        sample_size = ab_service.calculate_required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.05,
            confidence_level=0.95,
            power=0.80
        )
        
        # Should be reasonable sample size (typically thousands for 5% effect)
        assert sample_size > 100
        assert sample_size < 100000
        assert isinstance(sample_size, int)
    
    def test_calculate_required_sample_size_large_effect(self, ab_service):
        """Test sample size calculation for large effect size"""
        # Large effect should require smaller sample
        large_effect_size = ab_service.calculate_required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.20,  # 20% improvement
            confidence_level=0.95,
            power=0.80
        )
        
        small_effect_size = ab_service.calculate_required_sample_size(
            baseline_rate=0.10,
            minimum_detectable_effect=0.05,  # 5% improvement
            confidence_level=0.95,
            power=0.80
        )
        
        assert large_effect_size < small_effect_size
    
    @pytest.mark.asyncio
    async def test_create_experiment(self, ab_service, mock_campaign_repo, sample_experiment_config):
        """Test experiment creation"""
        campaign_id = str(uuid.uuid4())
        mock_campaign_repo.create_experiment = AsyncMock(return_value={
            'id': str(uuid.uuid4()),
            'campaign_id': campaign_id,
            **sample_experiment_config,
            'status': 'running',
            'created_at': datetime.now().isoformat()
        })
        
        result = await ab_service.create_experiment(campaign_id, sample_experiment_config)
        
        assert 'id' in result
        assert result['status'] == 'running'
        mock_campaign_repo.create_experiment.assert_called_once_with(
            campaign_id,
            sample_experiment_config
        )
    
    @pytest.mark.asyncio
    async def test_create_experiment_invalid_config(self, ab_service, mock_campaign_repo):
        """Test experiment creation with invalid configuration"""
        campaign_id = str(uuid.uuid4())
        invalid_config = {'name': 'Test'}  # Missing required fields
        
        with pytest.raises(ValueError, match="Invalid experiment configuration"):
            await ab_service.create_experiment(campaign_id, invalid_config)
    
    def test_hash_assignment_consistency(self, ab_service):
        """Test that hash-based assignment is consistent"""
        experiment_id = "exp123"
        customer_id = "customer456"
        
        # Multiple calls should return same hash
        hash1 = ab_service._hash_assignment(experiment_id, customer_id)
        hash2 = ab_service._hash_assignment(experiment_id, customer_id)
        hash3 = ab_service._hash_assignment(experiment_id, customer_id)
        
        assert hash1 == hash2 == hash3
        assert 0 <= hash1 <= 1
    
    def test_hash_assignment_different_inputs(self, ab_service):
        """Test that different inputs produce different hashes"""
        experiment_id = "exp123"
        
        hash_customer1 = ab_service._hash_assignment(experiment_id, "customer1")
        hash_customer2 = ab_service._hash_assignment(experiment_id, "customer2")
        
        # Should be different (very high probability)
        assert hash_customer1 != hash_customer2
    
    def test_calculate_confidence_interval(self, ab_service):
        """Test confidence interval calculation"""
        # Test with known values
        conversions = 100
        total = 1000
        confidence = 0.95
        
        ci = ab_service.calculate_confidence_interval(conversions, total, confidence)
        
        assert 'lower' in ci
        assert 'upper' in ci
        assert ci['lower'] < ci['upper']
        assert ci['lower'] >= 0
        assert ci['upper'] <= 1
        assert ci['confidence'] == confidence
        
        # The true rate (0.1) should be within the interval
        true_rate = conversions / total
        assert ci['lower'] <= true_rate <= ci['upper']
    
    def test_format_experiment_results(self, ab_service):
        """Test experiment results formatting"""
        experiment_data = {
            'name': 'Test Experiment',
            'variants': [
                {'id': 'a', 'name': 'Variant A'},
                {'id': 'b', 'name': 'Variant B'}
            ]
        }
        
        metrics = {
            'a': {
                'conversions': 100,
                'total': 1000,
                'rate': 0.10,
                'avg_rating': 4.0
            },
            'b': {
                'conversions': 150,
                'total': 1000,
                'rate': 0.15,
                'avg_rating': 4.2
            }
        }
        
        result = ab_service.format_experiment_results(experiment_data, metrics)
        
        assert result['experiment_name'] == 'Test Experiment'
        assert len(result['variants']) == 2
        assert 'statistical_analysis' in result
        assert 'recommendation' in result
        
        # Check variant data formatting
        for variant in result['variants']:
            assert 'conversion_rate' in variant
            assert 'confidence_interval' in variant
            assert 'sample_size' in variant
    
    def test_multi_variant_assignment(self, ab_service):
        """Test variant assignment with multiple variants"""
        variants = [
            {'id': 'a', 'weight': 0.25, 'parameters': {}},
            {'id': 'b', 'weight': 0.25, 'parameters': {}},
            {'id': 'c', 'weight': 0.25, 'parameters': {}},
            {'id': 'd', 'weight': 0.25, 'parameters': {}}
        ]
        
        experiment_id = str(uuid.uuid4())
        assignments = {}
        
        # Run assignments
        for i in range(1000):
            customer_id = f"customer_{i}"
            variant = ab_service.assign_variant(experiment_id, customer_id, variants)
            assignments[variant['id']] = assignments.get(variant['id'], 0) + 1
        
        # Check all variants are assigned
        assert len(assignments) == 4
        
        # Check roughly equal distribution (25% each with tolerance)
        for variant_id in ['a', 'b', 'c', 'd']:
            ratio = assignments.get(variant_id, 0) / 1000
            assert abs(ratio - 0.25) < 0.05  # 5% tolerance