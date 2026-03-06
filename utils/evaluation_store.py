"""
Evaluation Store
Author: Sarath

SQLite-backed persistent storage for quality evaluation traces.
Provides storage, retrieval, and querying of quality traces across jobs.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from utils.quality_trace import QualityTrace, QualityTraceReport


# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent / "backend" / "data" / "nell.db"


@dataclass
class JobRecord:
    """Represents a job in the evaluation store."""
    id: str
    mode: str
    prompt: Optional[str] = None
    status: str = "running"
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    overall_score: Optional[int] = None
    overall_grade: Optional[str] = None
    output_dir: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class TraceRecord:
    """Represents a trace record in the evaluation store."""
    job_id: str
    dimension: str
    sequence: int
    score: int
    grade: str
    reasoning: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    raw_metrics: Optional[Dict[str, Any]] = None
    enhanced: bool = False
    evaluated_at: Optional[str] = None


@dataclass
class IssueRecord:
    """Represents an issue in the evaluation store."""
    job_id: str
    dimension: str
    severity: str
    message: str
    created_at: Optional[str] = None


class EvaluationStore:
    """
    SQLite-backed storage for quality evaluation traces.

    Provides persistent storage for:
    - Job metadata (mode, prompt, status, overall score)
    - Per-dimension traces (score, grade, reasoning, strengths/weaknesses)
    - Quality issues for quick filtering
    """

    # SQL schema for quality tables
    SCHEMA = """
    -- Quality job tracking (extends existing jobs table)
    CREATE TABLE IF NOT EXISTS quality_jobs (
        id TEXT PRIMARY KEY,
        mode TEXT NOT NULL,
        prompt TEXT,
        status TEXT NOT NULL DEFAULT 'running',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        overall_score INTEGER,
        overall_grade TEXT,
        output_dir TEXT,
        duration_seconds REAL
    );

    -- Per-dimension traces (8 rows per job)
    CREATE TABLE IF NOT EXISTS quality_traces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        dimension TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        score INTEGER NOT NULL,
        grade TEXT NOT NULL,
        reasoning TEXT,
        strengths TEXT,
        weaknesses TEXT,
        suggestions TEXT,
        raw_metrics TEXT,
        enhanced BOOLEAN DEFAULT FALSE,
        evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(job_id, dimension),
        FOREIGN KEY (job_id) REFERENCES quality_jobs(id)
    );

    -- Individual issues for quick filtering
    CREATE TABLE IF NOT EXISTS quality_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        dimension TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES quality_jobs(id)
    );

    -- Indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_quality_jobs_status ON quality_jobs(status);
    CREATE INDEX IF NOT EXISTS idx_quality_jobs_mode ON quality_jobs(mode);
    CREATE INDEX IF NOT EXISTS idx_quality_jobs_created ON quality_jobs(created_at);
    CREATE INDEX IF NOT EXISTS idx_quality_traces_job ON quality_traces(job_id);
    CREATE INDEX IF NOT EXISTS idx_quality_traces_dimension ON quality_traces(dimension);
    CREATE INDEX IF NOT EXISTS idx_quality_traces_score ON quality_traces(score);
    CREATE INDEX IF NOT EXISTS idx_quality_issues_job ON quality_issues(job_id);
    CREATE INDEX IF NOT EXISTS idx_quality_issues_severity ON quality_issues(severity);
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the evaluation store.

        Args:
            db_path: Path to SQLite database. Defaults to backend/data/nell.db
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_schema()

    @contextmanager
    def _get_connection(self):
        """Get a database connection with context management."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _ensure_schema(self):
        """Ensure all required tables exist."""
        with self._get_connection() as conn:
            conn.executescript(self.SCHEMA)
            conn.commit()

    # =========================================================================
    # Job Operations
    # =========================================================================

    def create_job(
        self,
        job_id: str,
        mode: str,
        prompt: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> JobRecord:
        """
        Create a new job record.

        Args:
            job_id: Unique job identifier
            mode: Pipeline mode (normal, pro, ultra)
            prompt: Original prompt
            output_dir: Path to output directory

        Returns:
            Created JobRecord
        """
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO quality_jobs
                (id, mode, prompt, status, created_at, output_dir)
                VALUES (?, ?, ?, 'running', ?, ?)
            """, (job_id, mode, prompt, now, output_dir))
            conn.commit()

        return JobRecord(
            id=job_id,
            mode=mode,
            prompt=prompt,
            status="running",
            created_at=now,
            output_dir=output_dir
        )

    def complete_job(
        self,
        job_id: str,
        overall_score: int,
        overall_grade: str,
        duration_seconds: float
    ) -> None:
        """
        Mark a job as completed with final scores.

        Args:
            job_id: Job identifier
            overall_score: Final overall score (0-100)
            overall_grade: Final grade (A, B+, etc.)
            duration_seconds: Total generation time
        """
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE quality_jobs
                SET status = 'completed',
                    completed_at = ?,
                    overall_score = ?,
                    overall_grade = ?,
                    duration_seconds = ?
                WHERE id = ?
            """, (now, overall_score, overall_grade, duration_seconds, job_id))
            conn.commit()

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed."""
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            conn.execute("""
                UPDATE quality_jobs
                SET status = 'failed', completed_at = ?
                WHERE id = ?
            """, (now, job_id))
            conn.commit()

            # Add error as issue
            self.add_issue(job_id, "pipeline", "error", f"Job failed: {error}")

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        """Get a job by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM quality_jobs WHERE id = ?", (job_id,)
            ).fetchone()

            if row:
                return JobRecord(
                    id=row["id"],
                    mode=row["mode"],
                    prompt=row["prompt"],
                    status=row["status"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                    overall_score=row["overall_score"],
                    overall_grade=row["overall_grade"],
                    output_dir=row["output_dir"],
                    duration_seconds=row["duration_seconds"]
                )
        return None

    def list_jobs(
        self,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: int = 50
    ) -> List[JobRecord]:
        """
        List jobs with optional filters.

        Args:
            mode: Filter by pipeline mode
            status: Filter by job status
            min_score: Filter by minimum overall score
            limit: Maximum number of results

        Returns:
            List of matching JobRecord objects
        """
        query = "SELECT * FROM quality_jobs WHERE 1=1"
        params = []

        if mode:
            query += " AND mode = ?"
            params.append(mode)
        if status:
            query += " AND status = ?"
            params.append(status)
        if min_score is not None:
            query += " AND overall_score >= ?"
            params.append(min_score)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        jobs = []
        with self._get_connection() as conn:
            for row in conn.execute(query, params):
                jobs.append(JobRecord(
                    id=row["id"],
                    mode=row["mode"],
                    prompt=row["prompt"],
                    status=row["status"],
                    created_at=row["created_at"],
                    completed_at=row["completed_at"],
                    overall_score=row["overall_score"],
                    overall_grade=row["overall_grade"],
                    output_dir=row["output_dir"],
                    duration_seconds=row["duration_seconds"]
                ))
        return jobs

    # =========================================================================
    # Trace Operations
    # =========================================================================

    def save_trace(self, job_id: str, trace: QualityTrace) -> None:
        """
        Save a quality trace for a dimension.

        Args:
            job_id: Job identifier
            trace: QualityTrace object to save
        """
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO quality_traces
                (job_id, dimension, sequence, score, grade, reasoning,
                 strengths, weaknesses, suggestions, raw_metrics, enhanced, evaluated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                trace.dimension,
                trace.sequence,
                trace.score,
                trace.grade,
                trace.reasoning,
                json.dumps(trace.strengths) if trace.strengths else None,
                json.dumps(trace.weaknesses) if trace.weaknesses else None,
                json.dumps(trace.suggestions) if trace.suggestions else None,
                json.dumps(trace.raw_metrics) if trace.raw_metrics else None,
                trace.enhanced,
                now
            ))
            conn.commit()

    def get_trace(self, job_id: str, dimension: str) -> Optional[TraceRecord]:
        """Get a specific trace for a job dimension."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT * FROM quality_traces
                WHERE job_id = ? AND dimension = ?
            """, (job_id, dimension)).fetchone()

            if row:
                return self._row_to_trace_record(row)
        return None

    def get_traces(self, job_id: str) -> List[TraceRecord]:
        """Get all traces for a job."""
        traces = []
        with self._get_connection() as conn:
            for row in conn.execute("""
                SELECT * FROM quality_traces
                WHERE job_id = ?
                ORDER BY sequence
            """, (job_id,)):
                traces.append(self._row_to_trace_record(row))
        return traces

    def _row_to_trace_record(self, row: sqlite3.Row) -> TraceRecord:
        """Convert a database row to TraceRecord."""
        return TraceRecord(
            job_id=row["job_id"],
            dimension=row["dimension"],
            sequence=row["sequence"],
            score=row["score"],
            grade=row["grade"],
            reasoning=row["reasoning"],
            strengths=json.loads(row["strengths"]) if row["strengths"] else [],
            weaknesses=json.loads(row["weaknesses"]) if row["weaknesses"] else [],
            suggestions=json.loads(row["suggestions"]) if row["suggestions"] else [],
            raw_metrics=json.loads(row["raw_metrics"]) if row["raw_metrics"] else {},
            enhanced=bool(row["enhanced"]),
            evaluated_at=row["evaluated_at"]
        )

    def save_trace_report(self, report: QualityTraceReport) -> None:
        """
        Save a complete trace report (all traces for a job).

        Args:
            report: QualityTraceReport with all dimension traces
        """
        for trace in report.traces:
            self.save_trace(report.job_id, trace)

    # =========================================================================
    # Issue Operations
    # =========================================================================

    def add_issue(
        self,
        job_id: str,
        dimension: str,
        severity: str,
        message: str
    ) -> None:
        """
        Add a quality issue.

        Args:
            job_id: Job identifier
            dimension: Dimension where issue was found
            severity: Issue severity (error, warning, info)
            message: Issue description
        """
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO quality_issues
                (job_id, dimension, severity, message, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (job_id, dimension, severity, message, now))
            conn.commit()

    def get_issues(
        self,
        job_id: Optional[str] = None,
        dimension: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[IssueRecord]:
        """
        Get issues with optional filters.

        Args:
            job_id: Filter by job
            dimension: Filter by dimension
            severity: Filter by severity
            limit: Maximum results

        Returns:
            List of matching IssueRecord objects
        """
        query = "SELECT * FROM quality_issues WHERE 1=1"
        params = []

        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if dimension:
            query += " AND dimension = ?"
            params.append(dimension)
        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        issues = []
        with self._get_connection() as conn:
            for row in conn.execute(query, params):
                issues.append(IssueRecord(
                    job_id=row["job_id"],
                    dimension=row["dimension"],
                    severity=row["severity"],
                    message=row["message"],
                    created_at=row["created_at"]
                ))
        return issues

    # =========================================================================
    # Query Helpers
    # =========================================================================

    def get_full_report(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full quality report for a job (job + traces + issues).

        Args:
            job_id: Job identifier

        Returns:
            Dictionary with complete quality report, or None if job not found
        """
        job = self.get_job(job_id)
        if not job:
            return None

        traces = self.get_traces(job_id)
        issues = self.get_issues(job_id=job_id)

        return {
            "job_id": job.id,
            "mode": job.mode,
            "prompt": job.prompt,
            "status": job.status,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "overall_score": job.overall_score,
            "overall_grade": job.overall_grade,
            "output_dir": job.output_dir,
            "duration_seconds": job.duration_seconds,
            "traces": [
                {
                    "dimension": t.dimension,
                    "score": t.score,
                    "grade": t.grade,
                    "reasoning": t.reasoning,
                    "strengths": t.strengths,
                    "weaknesses": t.weaknesses,
                    "suggestions": t.suggestions,
                    "sequence": t.sequence,
                    "raw_metrics": t.raw_metrics,
                    "enhanced": t.enhanced
                }
                for t in traces
            ],
            "issues": [
                {
                    "dimension": i.dimension,
                    "severity": i.severity,
                    "message": i.message
                }
                for i in issues
            ]
        }

    def check_threshold(self, job_id: str, min_score: int = 80) -> Dict[str, Any]:
        """
        Check if a job meets a quality threshold (for CI/CD).

        Args:
            job_id: Job identifier
            min_score: Minimum acceptable score

        Returns:
            Dict with pass/fail status and details
        """
        job = self.get_job(job_id)
        if not job:
            return {"passed": False, "error": "Job not found"}

        if job.status != "completed":
            return {"passed": False, "error": f"Job status is {job.status}"}

        passed = job.overall_score is not None and job.overall_score >= min_score

        # Find dimensions below threshold
        traces = self.get_traces(job_id)
        failing_dimensions = [
            {"dimension": t.dimension, "score": t.score, "grade": t.grade}
            for t in traces
            if t.score < min_score
        ]

        return {
            "passed": passed,
            "job_id": job_id,
            "overall_score": job.overall_score,
            "overall_grade": job.overall_grade,
            "min_score": min_score,
            "failing_dimensions": failing_dimensions
        }

    def get_stats(
        self,
        mode: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get aggregate statistics for quality scores.

        Args:
            mode: Filter by pipeline mode
            days: Number of days to include

        Returns:
            Dict with aggregate statistics
        """
        with self._get_connection() as conn:
            # Base query
            query = """
                SELECT
                    COUNT(*) as total_jobs,
                    AVG(overall_score) as avg_score,
                    MIN(overall_score) as min_score,
                    MAX(overall_score) as max_score,
                    AVG(duration_seconds) as avg_duration
                FROM quality_jobs
                WHERE status = 'completed'
                AND created_at >= datetime('now', ?)
            """
            params = [f"-{days} days"]

            if mode:
                query += " AND mode = ?"
                params.append(mode)

            row = conn.execute(query, params).fetchone()

            return {
                "total_jobs": row["total_jobs"] or 0,
                "avg_score": round(row["avg_score"], 1) if row["avg_score"] else None,
                "min_score": row["min_score"],
                "max_score": row["max_score"],
                "avg_duration_seconds": round(row["avg_duration"], 1) if row["avg_duration"] else None,
                "period_days": days,
                "mode_filter": mode
            }


# Global instance for convenience
_store: Optional[EvaluationStore] = None


def get_evaluation_store() -> EvaluationStore:
    """Get the global EvaluationStore instance."""
    global _store
    if _store is None:
        _store = EvaluationStore()
    return _store


__all__ = [
    'EvaluationStore',
    'JobRecord',
    'TraceRecord',
    'IssueRecord',
    'get_evaluation_store',
]
