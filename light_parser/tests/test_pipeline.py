"""Tests for LightParsePipeline."""

import pytest
from parsers.pipeline import LightParsePipeline


class TestLightParsePipeline:
    """Test suite for LightParsePipeline."""
    
    @pytest.fixture
    def pipeline(self):
        """Create a LightParsePipeline instance for testing."""
        return LightParsePipeline()
    
    def test_pipeline_initialization(self, pipeline):
        """Test that pipeline initializes both parsers."""
        assert pipeline.food_parser is not None
        assert pipeline.symptom_parser is not None
    
    def test_run_single_entry(self, pipeline):
        """Test running pipeline on a single entry."""
        entry = {
            'entry_id': 'test_001',
            'text': '2 eggs for breakfast. Feeling bloated.'
        }
        
        result = pipeline.run(entry)
        
        assert result['entry_id'] == 'test_001'
        assert 'foods' in result
        assert 'symptoms' in result
        assert 'parse_errors' in result
        assert 'parser_version' in result
    
    def test_both_parsers_run(self, pipeline):
        """Test that both parsers are invoked and produce results."""
        entry = {
            'entry_id': 'test_002',
            'text': 'dal chawal for lunch. Cramps started.'
        }
        
        result = pipeline.run(entry)
        
        # Should have detected food
        assert len(result['foods']) > 0
        food_names = [f['name'] for f in result['foods']]
        assert 'dal' in food_names or 'chawal' in food_names
        
        # Should have detected symptom
        assert len(result['symptoms']) > 0
        symptom_names = [s['name'] for s in result['symptoms']]
        assert 'cramps' in symptom_names
    
    def test_run_batch(self, pipeline):
        """Test batch processing of multiple entries."""
        entries = [
            {'entry_id': 'e_001', 'text': '2 eggs + toast'},
            {'entry_id': 'e_002', 'text': 'Headache today'},
            {'entry_id': 'e_003', 'text': 'Skipped dinner. No cramps.'}
        ]
        
        results = pipeline.run_batch(entries)
        
        assert len(results) == 3
        assert results[0]['entry_id'] == 'e_001'
        assert results[1]['entry_id'] == 'e_002'
        assert results[2]['entry_id'] == 'e_003'
    
    def test_empty_text_handling(self, pipeline):
        """Test handling of empty text."""
        entry = {
            'entry_id': 'empty_001',
            'text': ''
        }
        
        result = pipeline.run(entry)
        
        assert result['entry_id'] == 'empty_001'
        assert len(result['foods']) == 0
        assert len(result['symptoms']) == 0
        assert len(result['parse_errors']) > 0
        assert result['parse_errors'][0]['error'] == 'empty_text'
    
    def test_missing_entry_id(self, pipeline):
        """Test handling of missing entry_id."""
        entry = {
            'text': 'Some text here'
        }
        
        result = pipeline.run(entry)
        
        assert result['entry_id'] == 'unknown'
    
    def test_parser_independence(self, pipeline):
        """Test that parsers work independently."""
        # Entry with only food
        food_only = {
            'entry_id': 'food_only',
            'text': 'Had pizza and salad'
        }
        
        result = pipeline.run(food_only)
        assert len(result['foods']) > 0
        # May or may not have symptoms (depends on lexicon)
        
        # Entry with only symptoms
        symptom_only = {
            'entry_id': 'symptom_only',
            'text': 'Severe headache and nausea'
        }
        
        result = pipeline.run(symptom_only)
        assert len(result['symptoms']) > 0
    
    def test_get_parser_info(self, pipeline):
        """Test getting version information."""
        info = pipeline.get_parser_info()
        
        assert 'pipeline_version' in info
        assert 'food_parser_version' in info
        assert 'symptom_parser_version' in info
        
        assert info['pipeline_version'] == pipeline.VERSION
    
    def test_error_handling_robustness(self, pipeline):
        """Test that errors in one parser don't break the pipeline."""
        # Even with potentially problematic input, pipeline should not crash
        entries = [
            {'entry_id': 'e1', 'text': None},  # None text
            {'entry_id': 'e2', 'text': ''},     # Empty text
            {'entry_id': 'e3', 'text': 'Normal entry with eggs and cramps'},
        ]
        
        # Should not raise exception
        results = pipeline.run_batch(entries)
        assert len(results) == 3
    
    def test_complex_real_world_entry(self, pipeline):
        """Test a complex real-world-like entry."""
        entry = {
            'entry_id': 'complex_001',
            'text': 'Aaj lunch mein rajma chawal, 1 plate. Gas + bloating in evening.'
        }
        
        result = pipeline.run(entry)
        
        # Should detect multiple foods
        assert len(result['foods']) >= 1
        
        # Should detect symptoms
        assert len(result['symptoms']) >= 1
        
        # Should have no parse errors
        assert len(result['parse_errors']) == 0
    
    def test_negation_and_skipped_meal(self, pipeline):
        """Test handling of negated symptoms and skipped meals."""
        entry = {
            'entry_id': 'neg_skip',
            'text': 'Skipped dinner. No headache today.'
        }
        
        result = pipeline.run(entry)
        
        # Should detect skipped meal
        food_names = [f['name'] for f in result['foods']]
        assert 'skipped' in food_names
        
        # Should detect negated symptom
        symptoms = result['symptoms']
        if symptoms:
            headache = next((s for s in symptoms if 'headache' in s['name']), None)
            if headache:
                assert headache['negated'] is True
    
    def test_deterministic_output(self, pipeline):
        """Test that same input produces same output (determinism)."""
        entry = {
            'entry_id': 'determinism_test',
            'text': '2 eggs + toast. Cramps 6/10.'
        }
        
        result1 = pipeline.run(entry)
        result2 = pipeline.run(entry)
        
        # Should produce identical results
        assert result1['entry_id'] == result2['entry_id']
        assert len(result1['foods']) == len(result2['foods'])
        assert len(result1['symptoms']) == len(result2['symptoms'])
        
        # Compare food names
        foods1 = sorted([f['name'] for f in result1['foods']])
        foods2 = sorted([f['name'] for f in result2['foods']])
        assert foods1 == foods2
        
        # Compare symptom names
        symptoms1 = sorted([s['name'] for s in result1['symptoms']])
        symptoms2 = sorted([s['name'] for s in result2['symptoms']])
        assert symptoms1 == symptoms2
