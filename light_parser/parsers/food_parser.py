"""Food extraction parser for health journal entries.

This parser is responsible for identifying food items, quantities, and meal contexts
from free-text journal entries. It operates independently of other parsers.
"""

import re
from typing import List, Dict, Optional, Any


class FoodParser:
    """Deterministic rule-based parser for extracting food-related signals."""
    
    VERSION = "v1.0"
    
    # Food lexicon - includes common Indian/Hinglish foods
    FOOD_LEXICON = {
        # Grains & Staples
        'rice', 'chawal', 'bread', 'toast', 'roti', 'paratha', 'naan',
        'pasta', 'noodles', 'pizza', 'khichdi', 'biryani',
        
        # Proteins
        'egg', 'eggs', 'chicken', 'fish', 'paneer', 'tofu', 'dal', 'daal',
        'rajma', 'moong', 'chana', 'protein shake',
        
        # Dairy
        'milk', 'dahi', 'yogurt', 'curd', 'cheese', 'butter', 'ghee',
        
        # Fruits & Vegetables
        'banana', 'apple', 'berries', 'salad', 'vegetables',
        
        # South Indian
        'idli', 'dosa', 'sambar', 'chutney', 'poha', 'upma', 'vada',
        
        # Snacks & Others
        'chips', 'cookies', 'chocolate', 'ice cream', 'sushi', 'wrap',
        'sandwich', 'burger', 'curry', 'almond', 'almonds', 'nuts',
        
        # Beverages (food context)
        'tea', 'chai', 'coffee', 'coke', 'shake', 'juice',
        
        # Prepared dishes
        'oats', 'porridge', 'soup', 'stew',
    }
    
    # Meal keywords
    MEAL_KEYWORDS = {
        'breakfast': ['breakfast'],
        'lunch': ['lunch', 'lunch mein'],
        'dinner': ['dinner'],
        'snack': ['snack'],
    }
    
    # Skip indicators (meals that didn't happen)
    SKIP_INDICATORS = ['skip', 'skipped', 'skip kiya']
    
    # Quantity patterns
    QUANTITY_PATTERN = re.compile(
        r'\b(\d+(?:\.\d+)?|half|quarter)\s*(?:(bowl|cup|piece|pieces|plate|plates|slice|slices|spoon|spoons|glass|glasses|g|kg|ml|l))?\b',
        re.IGNORECASE
    )
    
    def __init__(self):
        """Initialize the FoodParser."""
        self._build_food_patterns()
    
    def _build_food_patterns(self):
        """Build regex patterns for food detection."""
        # Sort by length (longest first) to match multi-word items like "protein shake" before "shake"
        # This prevents partial matches from blocking complete ones
        food_words = '|'.join(re.escape(food) for food in sorted(self.FOOD_LEXICON, key=len, reverse=True))
        self.food_pattern = re.compile(r'\b(' + food_words + r')(?:s)?\b', re.IGNORECASE)
    
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse food items from text.
        
        Args:
            text: Input journal entry text
            
        Returns:
            List of food dictionaries with name, quantity, unit, meal, confidence
        """
        if not text or not isinstance(text, str):
            return []
        
        # Check for skipped meals first
        skipped_meal = self._detect_skipped_meal(text)
        if skipped_meal:
            return [skipped_meal]
        
        # Detect meal context
        meal_context = self._detect_meal_context(text)
        
        # Extract food items
        foods = []
        matches = self.food_pattern.finditer(text)
        
        seen_positions = set()
        for match in matches:
            start, end = match.span()
            
            # Avoid duplicate overlapping matches (only check actual overlap)
            if start in seen_positions:
                continue
            seen_positions.add(start)
            
            food_name = match.group(1).lower()
            
            # Normalize plural forms
            normalized_name = self._normalize_food_name(food_name)
            
            # Try to extract quantity near this food
            quantity_info = self._extract_quantity_near(text, start, end)
            
            # Determine confidence
            confidence = self._calculate_confidence(food_name, quantity_info, meal_context)
            
            food_item = {
                'name': normalized_name,
                'quantity': quantity_info.get('quantity'),
                'unit': quantity_info.get('unit'),
                'meal': meal_context,
                'confidence': confidence
            }
            
            foods.append(food_item)
        
        return foods
    
    def _detect_skipped_meal(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect if a meal was explicitly skipped."""
        text_lower = text.lower()
        
        for skip_word in self.SKIP_INDICATORS:
            if skip_word in text_lower:
                # Try to find which meal was skipped
                for meal_type, keywords in self.MEAL_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in text_lower:
                            return {
                                'name': 'skipped',
                                'quantity': None,
                                'unit': None,
                                'meal': meal_type,
                                'confidence': 0.95
                            }
                
                # If no specific meal mentioned, mark as unknown
                return {
                    'name': 'skipped',
                    'quantity': None,
                    'unit': None,
                    'meal': 'unknown',
                    'confidence': 0.9
                }
        
        return None
    
    def _detect_meal_context(self, text: str) -> str:
        """Detect meal context (breakfast, lunch, dinner, snack)."""
        text_lower = text.lower()
        
        for meal_type, keywords in self.MEAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return meal_type
        
        # Time-based heuristics
        time_patterns = {
            'breakfast': r'\b(morning|AM|am|subah)\b',
            'lunch': r'\b(noon|afternoon|lunch|dopahar)\b',
            'dinner': r'\b(evening|night|dinner|raat|PM|pm)\b',
        }
        
        for meal_type, pattern in time_patterns.items():
            if re.search(pattern, text):
                return meal_type
        
        return 'unknown'
    
    def _extract_quantity_near(self, text: str, food_start: int, food_end: int) -> Dict[str, Optional[Any]]:
        """Extract quantity information near a food mention."""
        # Look in a window before the food (e.g., "2 eggs")
        window_start = max(0, food_start - 30)
        window_end = food_start  # Only look BEFORE the food
        window_text = text[window_start:window_end]
        
        matches = list(self.QUANTITY_PATTERN.finditer(window_text))
        
        if matches:
            # Take the last match before the food (closest to the food)
            closest = matches[-1]
            quantity_str = closest.group(1)
            unit = closest.group(2)
            
            # Normalize quantity
            quantity = self._normalize_quantity(quantity_str)
            
            return {
                'quantity': quantity,
                'unit': unit.lower() if unit else None
            }
        
        return {'quantity': None, 'unit': None}
    
    def _normalize_quantity(self, quantity_str: str) -> Optional[float]:
        """Normalize quantity string to float."""
        quantity_str = quantity_str.lower().strip()
        
        if quantity_str == 'half':
            return 0.5
        elif quantity_str == 'quarter':
            return 0.25
        else:
            try:
                return float(quantity_str)
            except ValueError:
                return None
    
    def _normalize_food_name(self, name: str) -> str:
        """Normalize food name (handle plurals, synonyms)."""
        name = name.lower().strip()
        
        # Handle plurals
        plural_map = {
            'eggs': 'egg',
            'almonds': 'almond',
            'cookies': 'cookie',
            'pieces': 'piece',
            'slices': 'slice',
            'berries': 'berry',
        }
        
        if name in plural_map:
            return plural_map[name]
        
        # Remove trailing 's' for common plurals
        if name.endswith('s') and len(name) > 3 and name[:-1] in self.FOOD_LEXICON:
            return name[:-1]
        
        return name
    
    def _calculate_confidence(self, food_name: str, quantity_info: Dict, meal_context: str) -> float:
        """Calculate confidence score for food detection."""
        confidence = 0.7  # Base confidence for lexicon match
        
        # Boost if quantity is present
        if quantity_info.get('quantity') is not None:
            confidence += 0.15
        
        # Boost if meal context is clear
        if meal_context != 'unknown':
            confidence += 0.1
        
        # Boost for very common foods
        common_foods = {'rice', 'egg', 'bread', 'chicken', 'dal', 'milk', 'toast'}
        if food_name.lower() in common_foods:
            confidence += 0.05
        
        return min(confidence, 1.0)
