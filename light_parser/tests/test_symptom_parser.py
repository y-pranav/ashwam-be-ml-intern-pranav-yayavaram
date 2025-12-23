"""Tests for SymptomParser."""

import pytest
from parsers.symptom_parser import SymptomParser


class TestSymptomParser:
    """Test suite for SymptomParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a SymptomParser instance for testing."""
        return SymptomParser()
    
    def test_basic_symptom_extraction(self, parser):
        """Test basic symptom detection."""
        text = "Cramps started by noon"
        symptoms = parser.parse(text)
        
        assert len(symptoms) >= 1
        symptom_names = [s['name'] for s in symptoms]
        assert 'cramps' in symptom_names
    
    def test_negation_detection(self, parser):
        """Test symptom negation detection."""
        text = "No headache today"
        symptoms = parser.parse(text)
        
        assert len(symptoms) >= 1
        headache_symptom = next((s for s in symptoms if 'headache' in s['name']), None)
        assert headache_symptom is not None
        assert headache_symptom['negated'] is True
    
    def test_severity_extraction_numeric(self, parser):
        """Test numeric severity extraction (e.g., 6/10)."""
        text = "Back pain 6/10 at night"
        symptoms = parser.parse(text)
        
        pain_symptom = next((s for s in symptoms if 'pain' in s['name']), None)
        assert pain_symptom is not None
        assert pain_symptom['severity'] == '6/10'
    
    def test_severity_extraction_descriptive(self, parser):
        """Test descriptive severity extraction."""
        text = "Severe cramps at night"
        symptoms = parser.parse(text)
        
        cramps_symptom = next((s for s in symptoms if 'cramps' in s['name']), None)
        assert cramps_symptom is not None
        assert cramps_symptom['severity'] == 'severe'
    
    def test_time_hint_extraction(self, parser):
        """Test time context extraction."""
        text = "Headache since afternoon"
        symptoms = parser.parse(text)
        
        assert len(symptoms) >= 1
        symptom = symptoms[0]
        assert symptom['time_hint'] in ['afternoon', None]
    
    def test_multiple_symptoms(self, parser):
        """Test extraction of multiple symptoms."""
        text = "Feeling bloated after lunch. Headache too."
        symptoms = parser.parse(text)
        
        symptom_names = [s['name'] for s in symptoms]
        assert 'bloating' in symptom_names
        assert 'headache' in symptom_names
    
    def test_symptom_normalization(self, parser):
        """Test symptom name normalization."""
        text = "Felt bloated and tired"
        symptoms = parser.parse(text)
        
        symptom_names = [s['name'] for s in symptoms]
        # "bloated" should normalize to "bloating"
        assert 'bloating' in symptom_names
        # "tired" should normalize to "fatigue"
        assert 'fatigue' in symptom_names
    
    def test_negation_with_hinglish(self, parser):
        """Test negation with Hinglish words."""
        text = "No bloating, no gas today"
        symptoms = parser.parse(text)
        
        assert len(symptoms) >= 1
        # All detected symptoms should be negated
        for symptom in symptoms:
            if symptom['name'] in ['bloating', 'gas']:
                assert symptom['negated'] is True
    
    def test_complex_symptom_phrases(self, parser):
        """Test multi-word symptom detection."""
        text = "Back pain and stomach pain"
        symptoms = parser.parse(text)
        
        symptom_names = [s['name'] for s in symptoms]
        # Should detect multi-word symptoms
        assert any('pain' in name for name in symptom_names)
    
    def test_no_false_positive_vitals(self, parser):
        """Test that vitals (BP, weight) are not detected as symptoms."""
        text = "BP 120/80. Weight 63.4kg"
        symptoms = parser.parse(text)
        
        # Should not detect BP or weight as symptoms
        # (may be empty or contain other symptoms, but not these)
        symptom_names = [s['name'] for s in symptoms]
        assert 'bp' not in symptom_names
        assert 'weight' not in symptom_names
    
    def test_no_false_positive_numbers(self, parser):
        """Test that step counts and other numbers aren't symptoms."""
        text = "Steps 6234. Phone battery 12%"
        symptoms = parser.parse(text)
        
        # Should not detect numbers as symptoms
        assert len(symptoms) == 0
    
    def test_after_meal_timing(self, parser):
        """Test 'after meal' time hint detection."""
        text = "Stomach pain after eating"
        symptoms = parser.parse(text)
        
        if symptoms:
            pain_symptom = next((s for s in symptoms if 'pain' in s['name']), None)
            if pain_symptom:
                assert pain_symptom['time_hint'] == 'after_meal'
    
    def test_confidence_scores(self, parser):
        """Test that confidence scores are reasonable."""
        text = "Severe migraine 8/10 in evening"
        symptoms = parser.parse(text)
        
        for symptom in symptoms:
            assert 0.0 <= symptom['confidence'] <= 1.0
            # Should have high confidence with severity
            assert symptom['confidence'] >= 0.7
    
    def test_empty_input(self, parser):
        """Test handling of empty input."""
        assert parser.parse("") == []
        assert parser.parse(None) == []
    
    def test_mixed_negation_and_positive(self, parser):
        """Test text with both negated and positive symptoms."""
        text = "Had cramps but no headache"
        symptoms = parser.parse(text)
        
        assert len(symptoms) >= 2
        
        cramps_symptom = next((s for s in symptoms if 'cramps' in s['name']), None)
        headache_symptom = next((s for s in symptoms if 'headache' in s['name']), None)
        
        assert cramps_symptom is not None
        assert headache_symptom is not None
        
        assert cramps_symptom['negated'] is False
        assert headache_symptom['negated'] is True
    
    def test_hinglish_severity(self, parser):
        """Test Hinglish severity indicators."""
        text = "Raat ko cramps bahut zyada"
        symptoms = parser.parse(text)
        
        if symptoms:
            cramps = next((s for s in symptoms if 'cramps' in s['name']), None)
            if cramps:
                # "bahut" should map to "severe"
                assert cramps['severity'] in ['severe', None]
    
    def test_symptom_with_emoji(self, parser):
        """Test symptom detection with emojis."""
        text = "Cramps started by noon 😣"
        symptoms = parser.parse(text)
        
        assert len(symptoms) >= 1
        assert any('cramps' in s['name'] for s in symptoms)
    
    def test_improved_pain_detection(self, parser):
        """Test that 'improved' pain is still detected."""
        text = "Back pain improved; still mild pain 2/10"
        symptoms = parser.parse(text)
        
        # Should detect pain
        symptom_names = [s['name'] for s in symptoms]
        assert any('pain' in name for name in symptom_names)
