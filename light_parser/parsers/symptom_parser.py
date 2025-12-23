"""Symptom extraction parser for health journal entries.

This parser is responsible for identifying symptoms, severity levels, timing,
and negations from free-text journal entries. It operates independently of other parsers.
"""

import re
from typing import List, Dict, Optional, Any


class SymptomParser:
    """Deterministic rule-based parser for extracting symptom-related signals."""
    
    VERSION = "v1.0"
    
    # Symptom lexicon - women's health focused
    SYMPTOM_LEXICON = {
        # Pain-related
        'pain', 'cramps', 'cramping', 'ache', 'aching', 'sore', 'soreness',
        'discomfort', 'tenderness',
        
        # Digestive
        'bloating', 'bloated', 'gas', 'gassy', 'nausea', 'nauseous',
        'stomach pain', 'stomach ache', 'constipation', 'diarrhea',
        
        # Head & Neurological
        'headache', 'migraine', 'dizziness', 'dizzy', 'lightheaded',
        
        # Energy & Mood (when clearly symptomatic)
        'fatigue', 'tired', 'exhausted', 'exhaustion', 'weakness',
        'low energy', 'sleepy', 'sleepiness',
        
        # Emotional (when presented as symptoms)
        'anxiety', 'anxious', 'stress', 'stressed', 'jittery',
        
        # Circulatory & Physical
        'heart racing', 'palpitations', 'sweating', 'hot flash',
        'hot flashes', 'chills',
        
        # Reproductive Health
        'spotting', 'bleeding', 'discharge',
        
        # Skin
        'breakout', 'acne', 'rash',
        
        # Respiratory & Throat
        'sore throat', 'cough', 'congestion',
        
        # Temperature
        'fever', 'warm',
        
        # Specific body parts + pain
        'back pain', 'pelvic pain', 'breast pain', 'joint pain',
        'lower back pain',
    }
    
    # Negation words - must appear before symptom
    NEGATION_WORDS = [
        'no', 'not', 'without', 'zero', 'never', 'none',
        'nahi', 'nahin'  # Hinglish
    ]
    
    # Severity pattern (e.g., "8/10", "mild", "severe")
    SEVERITY_PATTERN = re.compile(
        r'\b(?:(\d+)\s*/\s*10|'  # numeric: 6/10
        r'(mild|light|slight|moderate|severe|extreme|intense|bahut))\b',
        re.IGNORECASE
    )
    
    # Time hint patterns
    TIME_HINTS = {
        'morning': r'\b(morning|subah|AM|am)\b',
        'afternoon': r'\b(afternoon|dopahar|noon)\b',
        'evening': r'\b(evening|shaam)\b',
        'night': r'\b(night|raat|PM|pm)\b',
        'after_meal': r'\b(after\s+(?:eating|lunch|dinner|breakfast|meal))\b',
    }
    
    def __init__(self):
        """Initialize the SymptomParser."""
        self._build_symptom_patterns()
    
    def _build_symptom_patterns(self):
        """Build regex patterns for symptom detection."""
        # Sort by length (longest first) to match multi-word symptoms first
        symptom_words = '|'.join(
            re.escape(symptom) for symptom in sorted(self.SYMPTOM_LEXICON, key=len, reverse=True)
        )
        self.symptom_pattern = re.compile(r'\b(' + symptom_words + r')\b', re.IGNORECASE)
    
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse symptoms from text.
        
        Args:
            text: Input journal entry text
            
        Returns:
            List of symptom dictionaries with name, severity, time_hint, negated, confidence
        """
        if not text or not isinstance(text, str):
            return []
        
        symptoms = []
        matches = self.symptom_pattern.finditer(text)
        
        seen_positions = set()
        for match in matches:
            start, end = match.span()
            
            # Avoid duplicate overlapping matches (only check actual overlap)
            if start in seen_positions:
                continue
            seen_positions.add(start)
            
            symptom_name = match.group(1).lower()
            
            # Normalize symptom name
            normalized_name = self._normalize_symptom_name(symptom_name)
            
            # Check for negation
            is_negated = self._check_negation(text, start)
            
            # Extract severity
            severity = self._extract_severity_near(text, start, end)
            
            # Extract time hint
            time_hint = self._extract_time_hint(text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                symptom_name, severity, is_negated, time_hint
            )
            
            symptom_item = {
                'name': normalized_name,
                'severity': severity,
                'time_hint': time_hint,
                'negated': is_negated,
                'confidence': confidence
            }
            
            symptoms.append(symptom_item)
        
        return symptoms
    
    def _check_negation(self, text: str, symptom_start: int) -> bool:
        """Check if symptom is negated by looking at preceding context."""
        # Look in window before symptom (up to 30 characters)
        window_start = max(0, symptom_start - 30)
        preceding_text = text[window_start:symptom_start].lower()
        
        # Check if any negation word appears in the preceding context
        for neg_word in self.NEGATION_WORDS:
            # Use word boundary to avoid partial matches
            if re.search(r'\b' + re.escape(neg_word) + r'\b', preceding_text):
                return True
        
        return False
    
    def _extract_severity_near(self, text: str, symptom_start: int, symptom_end: int) -> Optional[str]:
        """Extract severity information near a symptom mention."""
        # Look in a window around the symptom (before and after)
        window_start = max(0, symptom_start - 30)
        window_end = min(len(text), symptom_end + 30)
        window_text = text[window_start:window_end]
        
        match = self.SEVERITY_PATTERN.search(window_text)
        
        if match:
            # Numeric severity (e.g., "6/10")
            if match.group(1):
                return match.group(1) + '/10'
            # Descriptive severity
            elif match.group(2):
                severity_word = match.group(2).lower()
                # Normalize "bahut" (Hinglish for "very/severe")
                if severity_word == 'bahut':
                    return 'severe'
                return severity_word
        
        return None
    
    def _extract_time_hint(self, text: str) -> Optional[str]:
        """Extract time context for when symptom occurred."""
        text_lower = text.lower()
        
        for time_type, pattern in self.TIME_HINTS.items():
            if re.search(pattern, text):
                return time_type
        
        return None
    
    def _normalize_symptom_name(self, name: str) -> str:
        """Normalize symptom name."""
        name = name.lower().strip()
        
        # Handle variations
        synonym_map = {
            'cramping': 'cramps',
            'aching': 'ache',
            'bloated': 'bloating',
            'gassy': 'gas',
            'nauseous': 'nausea',
            'dizzy': 'dizziness',
            'anxious': 'anxiety',
            'stressed': 'stress',
            'exhausted': 'fatigue',
            'exhaustion': 'fatigue',
            'tired': 'fatigue',
            'sleepy': 'sleepiness',
        }
        
        if name in synonym_map:
            return synonym_map[name]
        
        return name
    
    def _calculate_confidence(
        self, symptom_name: str, severity: Optional[str], 
        is_negated: bool, time_hint: Optional[str]
    ) -> float:
        """Calculate confidence score for symptom detection."""
        confidence = 0.75  # Base confidence for lexicon match
        
        # Boost if severity is specified
        if severity is not None:
            confidence += 0.15
        
        # Boost if time hint is present
        if time_hint is not None:
            confidence += 0.05
        
        # Negated symptoms are still confident detections
        if is_negated:
            confidence = max(confidence, 0.9)
        
        # High confidence for clear symptom terms
        clear_symptoms = {
            'cramps', 'migraine', 'headache', 'nausea', 'bloating',
            'pain', 'fever', 'dizziness'
        }
        if symptom_name.lower() in clear_symptoms:
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def _is_likely_false_positive(self, text: str, symptom_start: int) -> bool:
        """
        Check if symptom mention is likely a false positive.
        
        This method can be extended to filter out non-symptomatic mentions,
        e.g., "feeling good" shouldn't extract "feeling" as a symptom.
        """
        # Current implementation: minimal filtering
        # Could be extended based on observed false positives
        return False
