"""CLI entry point for the Bonfire job application generator.

Usage examples::

    python main.py --job-file data/fake_job_german.txt --language de
    python main.py --job-text "We are hiring a CFD engineer..." --language de
"""

import argparse
import sys
from pathlib import Path

from src.orchestrator import run_job_pipeline


def _read_job_file(file_path: str) -> str:
    """Read the contents of a job description file.

    Args:
        file_path: Path to the job description file.

    Returns:
        The file contents as a string.

    Raises:
        SystemExit: If the file is not found.
    """
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"Error: Job file not found: {file_path}", file=sys.stderr)
        sys.exit(1)


def _build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        A configured :class:`argparse.ArgumentParser`.
    """
    parser = argparse.ArgumentParser(
        description="Bonfire AI Job Application Generator"
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--job-text",
        type=str,
        help="Raw job description text",
    )
    input_group.add_argument(
        "--job-file",
        type=str,
        help="Path to a file containing the job description",
    )

    parser.add_argument(
        "--language",
        type=str,
        default="de",
        choices=["en", "de", "es"],
        help="Output language (default: de)",
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = _build_argument_parser()
    args = parser.parse_args()

    if args.job_file:
        job_text = _read_job_file(args.job_file)
    else:
        job_text = args.job_text

    result = run_job_pipeline(job_text, args.language)

    if result["success"]:
        print("Application generated successfully!")
        print(f"   Company: {result['company']}")
        print(f"   Job: {result['job_title']}")
        print(f"   Output: {result['output_dir']}")
        print(f"   Cover letter: {result['cover_letter']}")
        print(f"   CV: {result['cv']}")
        sys.exit(0)
    else:
        print(f"Pipeline failed: {result['reason']}")
        if "recommendation" in result:
            print(f"   Recommendation: {result['recommendation']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
