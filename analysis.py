from analysis import HierarchicalSchedulabilityAnalyzer
import sys
import os


def main():
    """Main function to run the analysis tool."""
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python analysis.py <test_case_folder>")
        return 1
    
    test_case_folder = sys.argv[1]
    
    try:
        # Create analyzer
        analyzer = HierarchicalSchedulabilityAnalyzer(test_case_folder)
        
        # Run analysis
        analyzer.run_analysis()
        
        return 0
    except Exception as e:
        print(f"Error running analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())