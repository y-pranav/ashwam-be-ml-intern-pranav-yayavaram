#!/usr/bin/env python3
"""
CLI interface for the Light Parsing system.

Usage:
    python main.py --in data/entries.jsonl --out parsed.jsonl
"""

import argparse
import json
import sys
from pathlib import Path
from parsers import LightParsePipeline


def load_jsonl(filepath: str) -> list:
    """Load entries from a JSONL file."""
    entries = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON on line {line_num}: {e}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Input file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)
    
    return entries


def save_jsonl(data: list, filepath: str):
    """Save parsed results to a JSONL file."""
    try:
        # Create output directory if it doesn't exist
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
        
        print(f"✓ Successfully wrote {len(data)} entries to {filepath}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def print_summary(results: list):
    """Print a summary of parsing results."""
    total_entries = len(results)
    total_foods = sum(len(r['foods']) for r in results)
    total_symptoms = sum(len(r['symptoms']) for r in results)
    entries_with_errors = sum(1 for r in results if r['parse_errors'])
    
    print("\n" + "="*50)
    print("PARSING SUMMARY")
    print("="*50)
    print(f"Total entries processed: {total_entries}")
    print(f"Total foods extracted: {total_foods}")
    print(f"Total symptoms extracted: {total_symptoms}")
    print(f"Entries with parse errors: {entries_with_errors}")
    print("="*50 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Light parsing system for food and symptom extraction',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --in data/entries.jsonl --out parsed.jsonl
  python main.py --in data/entries.jsonl --out results/output.jsonl --verbose
        """
    )
    
    parser.add_argument(
        '--in', 
        dest='input_file',
        required=True,
        help='Input JSONL file with journal entries'
    )
    
    parser.add_argument(
        '--out',
        dest='output_file',
        required=True,
        help='Output JSONL file for parsed results'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed parsing results'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show parser version information'
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = LightParsePipeline()
    
    # Show version if requested
    if args.version:
        info = pipeline.get_parser_info()
        print("Parser Version Information:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        sys.exit(0)
    
    # Load input
    print(f"Loading entries from {args.input_file}...")
    entries = load_jsonl(args.input_file)
    print(f"✓ Loaded {len(entries)} entries")
    
    # Run pipeline
    print("Running parsers...")
    results = pipeline.run_batch(entries)
    print("✓ Parsing complete")
    
    # Save output
    save_jsonl(results, args.output_file)
    
    # Print summary
    print_summary(results)
    
    # Verbose output
    if args.verbose:
        print("\nDETAILED RESULTS (first 3 entries):")
        print("-" * 50)
        for result in results[:3]:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("-" * 50)


if __name__ == '__main__':
    main()
