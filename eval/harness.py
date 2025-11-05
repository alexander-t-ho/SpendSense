"""Evaluation harness for running SpendSense evaluation."""

import json
import csv
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ingest.schema import get_session
from eval.metrics import MetricsCalculator
from eval.reports import ReportGenerator


class EvaluationHarness:
    """Run evaluation and generate reports."""
    
    def __init__(self, db_path: str = "data/spendsense.db"):
        """Initialize evaluation harness.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.session = get_session()
        self.metrics_calculator = MetricsCalculator(self.session, db_path)
        self.report_generator = ReportGenerator()
    
    def run_evaluation(
        self,
        output_dir: str = "eval/results",
        latency_sample_size: Optional[int] = None,
        generate_csv: bool = True,
        generate_json: bool = True,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """Run full evaluation and generate outputs.
        
        Args:
            output_dir: Directory to save output files
            latency_sample_size: Number of users to test for latency (None = all)
            generate_csv: Whether to generate CSV output
            generate_json: Whether to generate JSON output
            generate_report: Whether to generate summary report
        
        Returns:
            Dictionary with all metrics
        """
        # Create output directory if provided
        output_path = Path(output_dir) if output_dir else None
        if output_path:
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Calculate all metrics
        print("=" * 80)
        print("SpendSense Evaluation Harness")
        print("=" * 80)
        print()
        
        metrics = self.metrics_calculator.calculate_all_metrics(
            latency_sample_size=latency_sample_size
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate outputs
        if generate_json and output_path:
            json_path = output_path / f"metrics_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"✓ JSON metrics saved to: {json_path}")
        
        if generate_csv and output_path:
            csv_path = output_path / f"metrics_{timestamp}.csv"
            self._generate_csv(metrics, csv_path)
            print(f"✓ CSV metrics saved to: {csv_path}")
        
        if generate_report and output_path:
            report_path = output_path / f"evaluation_report_{timestamp}.txt"
            report_text = self.report_generator.generate_summary_report(metrics)
            with open(report_path, 'w') as f:
                f.write(report_text)
            print(f"✓ Summary report saved to: {report_path}")
        
        print()
        print("=" * 80)
        print("Evaluation Complete")
        print("=" * 80)
        
        return metrics
    
    def _generate_csv(self, metrics: Dict[str, Any], csv_path: Path):
        """Generate CSV output from metrics.
        
        Args:
            metrics: Metrics dictionary
            csv_path: Path to save CSV file
        """
        rows = []
        
        # Summary metrics
        rows.append(['Metric', 'Value', 'Target', 'Status'])
        rows.append(['Coverage (%)', metrics['coverage']['coverage_percentage'], '100%', '✓' if metrics['targets_met']['coverage_100pct'] else '✗'])
        rows.append(['Explainability (%)', metrics['explainability']['explainability_percentage'], '100%', '✓' if metrics['targets_met']['explainability_100pct'] else '✗'])
        rows.append(['Relevance (%)', metrics['relevance']['relevance_percentage'], '≥80%', '✓' if metrics['targets_met']['relevance_high'] else '✗'])
        rows.append(['Latency (avg, s)', metrics['latency']['average_latency_seconds'], '<5s', '✓' if metrics['targets_met']['latency_under_5s'] else '✗'])
        rows.append(['Fairness Score', metrics['fairness']['fairness_score'], '≥0.7', '✓' if metrics['targets_met']['fairness_good'] else '✗'])
        rows.append(['Overall Score', metrics['overall_score'], '≥0.8', '✓' if metrics['overall_score'] >= 0.8 else '✗'])
        rows.append([])
        
        # Coverage details
        rows.append(['Coverage Details'])
        rows.append(['Total Users', metrics['coverage']['total_users']])
        rows.append(['Users with Persona', metrics['coverage']['users_with_persona']])
        rows.append(['Users with ≥3 Behaviors', metrics['coverage']['users_with_3plus_behaviors']])
        rows.append(['Users Meeting Coverage', metrics['coverage']['users_with_persona_and_3plus_behaviors']])
        rows.append([])
        
        # Explainability details
        rows.append(['Explainability Details'])
        rows.append(['Total Recommendations', metrics['explainability']['total_recommendations']])
        rows.append(['With Rationales', metrics['explainability']['recommendations_with_rationales']])
        rows.append([])
        
        # Relevance details
        rows.append(['Relevance Details'])
        rows.append(['Total Recommendations', metrics['relevance']['total_recommendations']])
        rows.append(['Relevant Recommendations', metrics['relevance']['relevant_recommendations']])
        rows.append([])
        
        # Latency details
        rows.append(['Latency Details'])
        rows.append(['Users Tested', metrics['latency']['total_users_tested']])
        rows.append(['Average (s)', metrics['latency']['average_latency_seconds']])
        rows.append(['Min (s)', metrics['latency']['min_latency_seconds']])
        rows.append(['Max (s)', metrics['latency']['max_latency_seconds']])
        rows.append(['P95 (s)', metrics['latency']['p95_latency_seconds']])
        rows.append(['P99 (s)', metrics['latency']['p99_latency_seconds']])
        rows.append([])
        
        # Fairness details
        rows.append(['Fairness Details'])
        rows.append(['Total Users', metrics['fairness']['total_users']])
        for persona, count in metrics['fairness']['persona_distribution'].items():
            rows.append([f'Persona: {persona}', count, f"{metrics['fairness']['persona_percentages'][persona]}%"])
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    def close(self):
        """Close database connections."""
        self.metrics_calculator.close()
        self.session.close()


def main():
    """CLI entry point for evaluation harness."""
    parser = argparse.ArgumentParser(description='Run SpendSense evaluation')
    parser.add_argument(
        '--db-path',
        type=str,
        default='data/spendsense.db',
        help='Path to SQLite database'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='eval/results',
        help='Directory for output files'
    )
    parser.add_argument(
        '--latency-sample-size',
        type=int,
        default=None,
        help='Number of users to test for latency (default: all users with consent)'
    )
    parser.add_argument(
        '--no-csv',
        action='store_true',
        help='Skip CSV output generation'
    )
    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Skip JSON output generation'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip summary report generation'
    )
    
    args = parser.parse_args()
    
    harness = EvaluationHarness(db_path=args.db_path)
    try:
        metrics = harness.run_evaluation(
            output_dir=args.output_dir,
            latency_sample_size=args.latency_sample_size,
            generate_csv=not args.no_csv,
            generate_json=not args.no_json,
            generate_report=not args.no_report
        )
        
        # Print summary to console
        print()
        print("Summary:")
        print(f"  Coverage: {metrics['coverage']['coverage_percentage']}%")
        print(f"  Explainability: {metrics['explainability']['explainability_percentage']}%")
        print(f"  Relevance: {metrics['relevance']['relevance_percentage']}%")
        print(f"  Latency: {metrics['latency']['average_latency_seconds']}s (avg)")
        print(f"  Fairness: {metrics['fairness']['fairness_score']}")
        print(f"  Overall Score: {metrics['overall_score']}")
        
    finally:
        harness.close()


if __name__ == '__main__':
    main()

