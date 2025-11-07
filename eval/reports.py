"""Report generation for SpendSense evaluation."""

from typing import Dict, Any
from datetime import datetime


class ReportGenerator:
    """Generate evaluation reports."""
    
    def generate_summary_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a summary report from metrics.
        
        Args:
            metrics: Dictionary with all calculated metrics
        
        Returns:
            Formatted report text
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = []
        report.append("=" * 80)
        report.append("SpendSense Evaluation Report")
        report.append("=" * 80)
        report.append(f"Generated: {timestamp}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 80)
        report.append("")
        report.append(f"Overall Score: {metrics['overall_score']:.3f} / 1.000")
        report.append("")
        
        targets_met = sum(1 for v in metrics['targets_met'].values() if v)
        total_targets = len(metrics['targets_met'])
        report.append(f"Targets Met: {targets_met}/{total_targets}")
        report.append("")
        
        # Coverage
        report.append("1. COVERAGE METRIC")
        report.append("-" * 80)
        coverage = metrics['coverage']
        report.append(f"Percentage: {coverage['coverage_percentage']:.2f}%")
        report.append(f"Target: 100%")
        report.append(f"Status: {'✓ PASS' if metrics['targets_met']['coverage_100pct'] else '✗ FAIL'}")
        report.append("")
        report.append(f"  Total Users: {coverage['total_users']}")
        report.append(f"  Users with Persona: {coverage['users_with_persona']}")
        report.append(f"  Users with ≥3 Behaviors: {coverage['users_with_3plus_behaviors']}")
        report.append(f"  Users Meeting Coverage: {coverage['users_with_persona_and_3plus_behaviors']}")
        report.append("")
        
        # Explainability
        report.append("2. EXPLAINABILITY METRIC")
        report.append("-" * 80)
        explainability = metrics['explainability']
        report.append(f"Percentage: {explainability['explainability_percentage']:.2f}%")
        report.append(f"Target: 100%")
        report.append(f"Status: {'✓ PASS' if metrics['targets_met']['explainability_100pct'] else '✗ FAIL'}")
        report.append("")
        report.append(f"  Total Recommendations: {explainability['total_recommendations']}")
        report.append(f"  With Rationales: {explainability['recommendations_with_rationales']}")
        report.append("")
        
        # Relevance
        report.append("3. RELEVANCE METRIC")
        report.append("-" * 80)
        relevance = metrics['relevance']
        report.append(f"Percentage: {relevance['relevance_percentage']:.2f}%")
        report.append(f"Target: ≥80%")
        report.append(f"Status: {'✓ PASS' if metrics['targets_met']['relevance_high'] else '✗ FAIL'}")
        report.append("")
        report.append(f"  Total Recommendations: {relevance['total_recommendations']}")
        report.append(f"  Relevant Recommendations: {relevance['relevant_recommendations']}")
        report.append("")
        
        # Latency
        report.append("4. LATENCY METRIC")
        report.append("-" * 80)
        latency = metrics['latency']
        report.append(f"Average: {latency['average_latency_seconds']:.3f} seconds")
        report.append(f"Target: <5 seconds")
        report.append(f"Status: {'✓ PASS' if metrics['targets_met']['latency_under_5s'] else '✗ FAIL'}")
        report.append("")
        report.append(f"  Users Tested: {latency['total_users_tested']}")
        report.append(f"  Min: {latency['min_latency_seconds']:.3f}s")
        report.append(f"  Max: {latency['max_latency_seconds']:.3f}s")
        report.append(f"  P95: {latency['p95_latency_seconds']:.3f}s")
        report.append(f"  P99: {latency['p99_latency_seconds']:.3f}s")
        report.append("")
        
        # Fairness
        report.append("5. FAIRNESS METRIC")
        report.append("-" * 80)
        fairness = metrics['fairness']
        report.append(f"Fairness Score: {fairness['fairness_score']:.3f}")
        report.append(f"Target: ≥0.7")
        report.append(f"Status: {'✓ PASS' if metrics['targets_met']['fairness_good'] else '✗ FAIL'}")
        report.append(f"Interpretation: {fairness['fairness_interpretation']}")
        report.append("")
        report.append("Persona Distribution:")
        for persona, count in fairness['persona_distribution'].items():
            pct = fairness['persona_percentages'][persona]
            report.append(f"  {persona}: {count} users ({pct}%)")
        report.append("")
        
        # Targets Summary
        report.append("TARGET SUMMARY")
        report.append("-" * 80)
        for target_name, met in metrics['targets_met'].items():
            status = "✓ PASS" if met else "✗ FAIL"
            report.append(f"  {target_name.replace('_', ' ').title()}: {status}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        if not metrics['targets_met']['coverage_100pct']:
            report.append("• Improve coverage: Ensure all users have assigned personas and ≥3 behaviors")
        if not metrics['targets_met']['explainability_100pct']:
            report.append("• Improve explainability: Ensure all recommendations include rationales")
        if not metrics['targets_met']['relevance_high']:
            report.append("• Improve relevance: Better match education content to user personas")
        if not metrics['targets_met']['latency_under_5s']:
            report.append("• Improve latency: Optimize recommendation generation performance")
        if not metrics['targets_met']['fairness_good']:
            report.append("• Improve fairness: Ensure balanced persona distribution")
        
        if all(metrics['targets_met'].values()):
            report.append("• All targets met! System is performing well.")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)




