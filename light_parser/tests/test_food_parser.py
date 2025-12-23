"""Tests for FoodParser."""

import pytest
from parsers.food_parser import FoodParser


class TestFoodParser:
    """Test suite for FoodParser."""
    
    @pytest.fixture
    def parser(self):
        """Create a FoodParser instance for testing."""
        return FoodParser()
    
    def test_basic_food_extraction(self, parser):
        """Test basic food item detection."""
        text = "2 eggs + 1 toast"
        foods = parser.parse(text)
        
        assert len(foods) == 2
        food_names = [f['name'] for f in foods]
        assert 'egg' in food_names
        assert 'toast' in food_names
    
    def test_quantity_extraction(self, parser):
        """Test quantity and unit extraction."""
        text = "2 eggs + 1 toast"
        foods = parser.parse(text)
        
        egg_food = next(f for f in foods if f['name'] == 'egg')
        assert egg_food['quantity'] == 2.0
        
        toast_food = next(f for f in foods if f['name'] == 'toast')
        assert toast_food['quantity'] == 1.0
    
    def test_meal_context_detection(self, parser):
        """Test meal context detection."""
        # Explicit breakfast
        text = "2 eggs for breakfast"
        foods = parser.parse(text)
        assert foods[0]['meal'] == 'breakfast'
        
        # Lunch keyword
        text = "dal chawal for lunch"
        foods = parser.parse(text)
        assert foods[0]['meal'] == 'lunch'
        
        # Dinner keyword
        text = "pizza for dinner"
        foods = parser.parse(text)
        assert foods[0]['meal'] == 'dinner'
    
    def test_hinglish_food_detection(self, parser):
        """Test Hinglish food terms."""
        text = "dal chawal + dahi"
        foods = parser.parse(text)
        
        assert len(foods) == 3
        food_names = [f['name'] for f in foods]
        assert 'dal' in food_names
        assert 'chawal' in food_names
        assert 'dahi' in food_names
    
    def test_skipped_meal_detection(self, parser):
        """Test detection of skipped meals."""
        text = "Skipped dinner. Feeling tired."
        foods = parser.parse(text)
        
        assert len(foods) == 1
        assert foods[0]['name'] == 'skipped'
        assert foods[0]['meal'] == 'dinner'
        assert foods[0]['confidence'] >= 0.9
    
    def test_plural_normalization(self, parser):
        """Test that plurals are normalized to singular."""
        text = "had eggs and almonds"
        foods = parser.parse(text)
        
        food_names = [f['name'] for f in foods]
        assert 'egg' in food_names
        assert 'almond' in food_names
        assert 'eggs' not in food_names
        assert 'almonds' not in food_names
    
    def test_unit_extraction(self, parser):
        """Test extraction of units."""
        text = "1 cup oats with milk"
        foods = parser.parse(text)
        
        oats_food = next((f for f in foods if f['name'] == 'oats'), None)
        assert oats_food is not None
        assert oats_food['unit'] == 'cup'
    
    def test_fractional_quantities(self, parser):
        """Test half and quarter quantities."""
        text = "half banana"
        foods = parser.parse(text)
        
        assert len(foods) >= 1
        banana_food = next((f for f in foods if f['name'] == 'banana'), None)
        assert banana_food is not None
        assert banana_food['quantity'] == 0.5
    
    def test_no_false_positive_numbers(self, parser):
        """Test that non-food numbers aren't interpreted as food."""
        text = "Steps 6234 today. Felt good."
        foods = parser.parse(text)
        
        # Should not detect any foods
        assert len(foods) == 0
    
    def test_complex_meal_entry(self, parser):
        """Test parsing of complex meal with multiple items."""
        text = "paneer salad (1 bowl). Feeling good."
        foods = parser.parse(text)
        
        assert len(foods) >= 1
        food_names = [f['name'] for f in foods]
        assert 'paneer' in food_names or 'salad' in food_names
    
    def test_time_based_meal_inference(self, parser):
        """Test meal inference from time words."""
        text = "Had oats in the morning"
        foods = parser.parse(text)
        
        if foods:
            assert foods[0]['meal'] in ['breakfast', 'unknown']
    
    def test_empty_input(self, parser):
        """Test handling of empty input."""
        assert parser.parse("") == []
        assert parser.parse(None) == []
    
    def test_confidence_scores(self, parser):
        """Test that confidence scores are reasonable."""
        text = "2 eggs for breakfast"
        foods = parser.parse(text)
        
        for food in foods:
            assert 0.0 <= food['confidence'] <= 1.0
            # Should have high confidence with quantity and meal context
            assert food['confidence'] >= 0.7
    
    def test_separators(self, parser):
        """Test various food separators."""
        text = "rice + fish curry"
        foods = parser.parse(text)
        
        food_names = [f['name'] for f in foods]
        assert 'rice' in food_names
        assert 'fish' in food_names or 'curry' in food_names
    
    def test_hinglish_skipped_meal(self, parser):
        """Test Hinglish skipped meal detection."""
        text = "Aaj dinner skip kiya"
        foods = parser.parse(text)
        
        assert len(foods) >= 1
        assert any(f['name'] == 'skipped' for f in foods)
