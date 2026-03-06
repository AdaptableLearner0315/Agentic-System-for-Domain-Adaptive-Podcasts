#!/usr/bin/env python3
"""
Nell Quality CLI
Author: Sarath

Command-line interface for querying quality evaluation traces.

Usage:
    python scripts/nell_quality.py show <job_id>
    python scripts/nell_quality.py list [--mode pro] [--min-score 70]
    python scripts/nell_quality.py trace <job_id> <dimension>
    python scripts/nell_quality.py export <job_id> -o trace.json
    python scripts/nell_quality.py issues [--severity error] [--dimension bgm]
    python scripts/nell_quality.py check <job_id> --min-score 80
    python scripts/nell_quality.py stats [--mode pro] [--days 7]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.evaluation_store import get_evaluation_store


def colorize(text: str, color: str) -> str:
    """Add ANSI color to text."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bold": "\033[1m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def grade_color(grade: str) -> str:
    """Get color for grade."""
    if grade.startswith("A"):
        return "green"
    elif grade.startswith("B"):
        return "cyan"
    elif grade.startswith("C"):
        return "yellow"
    elif grade.startswith("D"):
        return "red"
    return "white"


def score_color(score: int) -> str:
    """Get color for score."""
    if score >= 90:
        return "green"
    elif score >= 80:
        return "cyan"
    elif score >= 70:
        return "yellow"
    elif score >= 60:
        return "red"
    return "red"


def cmd_show(args):
    """Show full quality report for a job."""
    store = get_evaluation_store()
    report = store.get_full_report(args.job_id)

    if not report:
        print(colorize(f"Error: Job {args.job_id} not found", "red"))
        sys.exit(1)

    # Header
    print()
    print(colorize("=" * 60, "bold"))
    print(colorize(f"  Quality Report: {report['job_id']}", "bold"))
    print(colorize("=" * 60, "bold"))
    print()

    # Job info
    print(f"  Mode:     {report['mode'].upper()}")
    print(f"  Status:   {report['status']}")
    if report['prompt']:
        print(f"  Prompt:   {report['prompt'][:60]}...")
    if report['duration_seconds']:
        print(f"  Duration: {report['duration_seconds']:.1f}s")
    print()

    # Overall score
    if report['overall_score'] is not None:
        score = report['overall_score']
        grade = report['overall_grade']
        bar = "=" * (score // 2) + "-" * (50 - score // 2)
        print(f"  Overall:  [{colorize(bar, score_color(score))}]")
        print(f"            {colorize(str(score), score_color(score))}/100  "
              f"{colorize(grade, grade_color(grade))}")
    print()

    # Traces
    if report['traces']:
        print(colorize("  Dimension Scores:", "bold"))
        print(colorize("  " + "-" * 50, "white"))
        for trace in sorted(report['traces'], key=lambda t: t['sequence']):
            dim = trace['dimension'].ljust(12)
            score = trace['score']
            grade = trace['grade']
            print(f"  {dim} {colorize(str(score).rjust(3), score_color(score))} "
                  f"{colorize(grade.ljust(3), grade_color(grade))}")
            if args.verbose and trace['reasoning']:
                print(f"             {trace['reasoning'][:60]}...")
        print()

    # Issues
    if report['issues']:
        print(colorize("  Issues:", "bold"))
        print(colorize("  " + "-" * 50, "white"))
        for issue in report['issues'][:5]:
            sev = issue['severity'].upper().ljust(7)
            sev_color = "red" if issue['severity'] == "error" else "yellow"
            print(f"  [{colorize(sev, sev_color)}] [{issue['dimension']}] {issue['message']}")
        if len(report['issues']) > 5:
            print(f"  ... and {len(report['issues']) - 5} more issues")
        print()


def cmd_list(args):
    """List jobs with quality scores."""
    store = get_evaluation_store()
    jobs = store.list_jobs(
        mode=args.mode,
        status=args.status,
        min_score=args.min_score,
        limit=args.limit,
    )

    if not jobs:
        print("No jobs found matching criteria.")
        return

    # Header
    print()
    print(colorize(f"{'ID':<10} {'Mode':<8} {'Status':<12} {'Score':>6} {'Grade':>6} {'Duration':>10}", "bold"))
    print("-" * 60)

    for job in jobs:
        status_color = "green" if job.status == "completed" else ("yellow" if job.status == "running" else "red")
        score_str = str(job.overall_score).rjust(6) if job.overall_score else "    --"
        grade_str = (job.overall_grade or "--").ljust(6)
        dur_str = f"{job.duration_seconds:.1f}s".rjust(10) if job.duration_seconds else "        --"

        print(f"{job.id:<10} {job.mode:<8} "
              f"{colorize(job.status.ljust(12), status_color)} "
              f"{colorize(score_str, score_color(job.overall_score) if job.overall_score else 'white')} "
              f"{colorize(grade_str, grade_color(job.overall_grade) if job.overall_grade else 'white')} "
              f"{dur_str}")

    print()
    print(f"Total: {len(jobs)} jobs")


def cmd_trace(args):
    """Show detailed trace for a dimension."""
    store = get_evaluation_store()
    trace = store.get_trace(args.job_id, args.dimension)

    if not trace:
        print(colorize(f"Error: Trace for {args.dimension} not found in job {args.job_id}", "red"))
        sys.exit(1)

    # Header
    print()
    print(colorize(f"Trace: {trace.dimension.upper()}", "bold"))
    print("-" * 40)
    print()

    # Score
    print(f"Score:    {colorize(str(trace.score), score_color(trace.score))}/100")
    print(f"Grade:    {colorize(trace.grade, grade_color(trace.grade))}")
    print(f"Sequence: {trace.sequence}")
    print(f"Enhanced: {'Yes' if trace.enhanced else 'No'}")
    print()

    # Reasoning
    if trace.reasoning:
        print(colorize("Reasoning:", "bold"))
        print(f"  {trace.reasoning}")
        print()

    # Strengths
    if trace.strengths:
        print(colorize("Strengths:", "green"))
        for s in trace.strengths:
            print(f"  + {s}")
        print()

    # Weaknesses
    if trace.weaknesses:
        print(colorize("Weaknesses:", "yellow"))
        for w in trace.weaknesses:
            print(f"  - {w}")
        print()

    # Suggestions
    if trace.suggestions:
        print(colorize("Suggestions:", "cyan"))
        for s in trace.suggestions:
            print(f"  * {s}")
        print()

    # Raw metrics
    if trace.raw_metrics and args.verbose:
        print(colorize("Raw Metrics:", "bold"))
        print(json.dumps(trace.raw_metrics, indent=2))


def cmd_export(args):
    """Export trace report to JSON."""
    store = get_evaluation_store()
    report = store.get_full_report(args.job_id)

    if not report:
        print(colorize(f"Error: Job {args.job_id} not found", "red"))
        sys.exit(1)

    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Exported trace to: {output_path}")


def cmd_issues(args):
    """List quality issues."""
    store = get_evaluation_store()
    issues = store.get_issues(
        job_id=args.job_id,
        dimension=args.dimension,
        severity=args.severity,
        limit=args.limit,
    )

    if not issues:
        print("No issues found matching criteria.")
        return

    # Header
    print()
    print(colorize(f"{'Job ID':<10} {'Severity':<10} {'Dimension':<12} Message", "bold"))
    print("-" * 70)

    for issue in issues:
        sev_color = "red" if issue.severity == "error" else ("yellow" if issue.severity == "warning" else "white")
        print(f"{issue.job_id:<10} "
              f"{colorize(issue.severity.ljust(10), sev_color)} "
              f"{issue.dimension:<12} "
              f"{issue.message[:40]}")

    print()
    print(f"Total: {len(issues)} issues")


def cmd_check(args):
    """Check if job meets quality threshold (CI/CD)."""
    store = get_evaluation_store()
    result = store.check_threshold(args.job_id, args.min_score)

    if result.get("error"):
        print(colorize(f"Error: {result['error']}", "red"))
        sys.exit(1)

    if result["passed"]:
        print(colorize("PASSED", "green"), end=" ")
        print(f"- Job {args.job_id} scored {result['overall_score']} "
              f"(threshold: {args.min_score})")
        sys.exit(0)
    else:
        print(colorize("FAILED", "red"), end=" ")
        print(f"- Job {args.job_id} scored {result['overall_score']} "
              f"(threshold: {args.min_score})")

        if result.get("failing_dimensions"):
            print()
            print("Failing dimensions:")
            for dim in result["failing_dimensions"]:
                print(f"  - {dim['dimension']}: {dim['score']} ({dim['grade']})")

        sys.exit(1)


def cmd_stats(args):
    """Show aggregate statistics."""
    store = get_evaluation_store()
    stats = store.get_stats(mode=args.mode, days=args.days)

    print()
    print(colorize("Quality Statistics", "bold"))
    print("-" * 30)
    print(f"Period:     Last {stats['period_days']} days")
    if stats['mode_filter']:
        print(f"Mode:       {stats['mode_filter']}")
    print()
    print(f"Total Jobs: {stats['total_jobs']}")

    if stats['avg_score']:
        print(f"Avg Score:  {colorize(str(stats['avg_score']), score_color(int(stats['avg_score'])))}")
    if stats['min_score']:
        print(f"Min Score:  {stats['min_score']}")
    if stats['max_score']:
        print(f"Max Score:  {stats['max_score']}")
    if stats['avg_duration_seconds']:
        print(f"Avg Time:   {stats['avg_duration_seconds']}s")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Nell Quality CLI - Query quality evaluation traces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    nell_quality.py show abc123                  # Full report for job
    nell_quality.py list --mode pro              # List Pro mode jobs
    nell_quality.py trace abc123 script          # Show script trace
    nell_quality.py check abc123 --min-score 80  # CI/CD threshold check
        """
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # show
    show_parser = subparsers.add_parser("show", help="Show full quality report")
    show_parser.add_argument("job_id", help="Job ID")

    # list
    list_parser = subparsers.add_parser("list", help="List jobs with quality scores")
    list_parser.add_argument("--mode", help="Filter by mode (normal, pro, ultra)")
    list_parser.add_argument("--status", help="Filter by status (running, completed, failed)")
    list_parser.add_argument("--min-score", type=int, help="Minimum overall score")
    list_parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")

    # trace
    trace_parser = subparsers.add_parser("trace", help="Show detailed trace for a dimension")
    trace_parser.add_argument("job_id", help="Job ID")
    trace_parser.add_argument("dimension", help="Dimension (script, voice, bgm, etc.)")

    # export
    export_parser = subparsers.add_parser("export", help="Export trace to JSON")
    export_parser.add_argument("job_id", help="Job ID")
    export_parser.add_argument("-o", "--output", required=True, help="Output file path")

    # issues
    issues_parser = subparsers.add_parser("issues", help="List quality issues")
    issues_parser.add_argument("--job-id", help="Filter by job ID")
    issues_parser.add_argument("--dimension", help="Filter by dimension")
    issues_parser.add_argument("--severity", help="Filter by severity (error, warning, info)")
    issues_parser.add_argument("--limit", type=int, default=50, help="Max results (default: 50)")

    # check
    check_parser = subparsers.add_parser("check", help="CI/CD quality threshold check")
    check_parser.add_argument("job_id", help="Job ID")
    check_parser.add_argument("--min-score", type=int, default=80, help="Minimum score (default: 80)")

    # stats
    stats_parser = subparsers.add_parser("stats", help="Show aggregate statistics")
    stats_parser.add_argument("--mode", help="Filter by mode")
    stats_parser.add_argument("--days", type=int, default=7, help="Days to include (default: 7)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "show": cmd_show,
        "list": cmd_list,
        "trace": cmd_trace,
        "export": cmd_export,
        "issues": cmd_issues,
        "check": cmd_check,
        "stats": cmd_stats,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
