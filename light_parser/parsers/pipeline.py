"""Light parsing pipeline orchestrator.

This module coordinates the FoodParser and SymptomParser to produce
a unified output for each journal entry.
"""

from typing import Dict, List, Any
from .food_parser import FoodParser
from .symptom_parser import SymptomParser


class LightParsePipeline:
    """
    Orchestrator for running both food and symptom parsers.
    
    This pipeline maintains separation of concerns by delegating to
    independent parsers and merging their results.
    """
    
    VERSION = "v1.0"
    
    def __init__(self):
        """Initialize the pipeline with both parsers."""
        self.food_parser = FoodParser()
        self.symptom_parser = SymptomParser()
    
    def run(self, entry: Dict[str, str]) -> Dict[str, Any]:
        """
        Run both parsers on a single entry and merge results.
        
        Args:
            entry: Dictionary with 'entry_id' and 'text' keys
            
        Returns:
            Dictionary containing:
                - entry_id
                - foods (list)
                - symptoms (list)
                - parse_errors (list)
                - parser_version
        """
        entry_id = entry.get('entry_id', 'unknown')
        text = entry.get('text', '')
        
        parse_errors = []
        
        # Validate input
        if not text:
            parse_errors.append({
                'error': 'empty_text',
                'message': 'Entry text is empty'
            })
        
        # Run both parsers independently
        try:
            foods = self.food_parser.parse(text) if text else []
        except Exception as e:
            foods = []
            parse_errors.append({
                'error': 'food_parser_error',
                'message': str(e)
            })
        
        try:
            symptoms = self.symptom_parser.parse(text) if text else []
        except Exception as e:
            symptoms = []
            parse_errors.append({
                'error': 'symptom_parser_error',
                'message': str(e)
            })
        
        # Assemble result
        result = {
            'entry_id': entry_id,
            'foods': foods,
            'symptoms': symptoms,
            'parse_errors': parse_errors,
            'parser_version': self.VERSION
        }
        
        return result
    
    def run_batch(self, entries: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Run pipeline on multiple entries.
        
        Args:
            entries: List of entry dictionaries
            
        Returns:
            List of parsed results
        """
        return [self.run(entry) for entry in entries]
    
    def get_parser_info(self) -> Dict[str, str]:
        """
        Get version information for all components.
        
        Returns:
            Dictionary with version info for pipeline and parsers
        """
        return {
            'pipeline_version': self.VERSION,
            'food_parser_version': self.food_parser.VERSION,
            'symptom_parser_version': self.symptom_parser.VERSION
        }
