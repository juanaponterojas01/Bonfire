"""CLI entry point for the Bonfire job application generator.

Usage examples::

    python main.py --file data/fake_job_german.txt --language de
    python main.py --job-text "We are hiring a CFD engineer..." --language en
    python main.py --url "https://example.com/careers/software-engineer" --language es
    python main.py --clean-output
"""

import argparse
import shutil
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

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--job-text",
        type=str,
        help="Raw job description text",
    )
    input_group.add_argument(
        "--file",
        type=str,
        help="Path to a file containing the job description",
    )
    input_group.add_argument(
        "--url",
        type=str,
        help="URL of a job posting to fetch and scrape",
    )

    parser.add_argument(
        "--language",
        type=str,
        default="de",
        choices=["en", "de", "es"],
        help="Output language (default: de)",
    )

    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Remove all generated output folders and exit",
    )

    return parser


def main() -> None:
    """Main entry point for the CLI."""
    parser = _build_argument_parser()
    args = parser.parse_args()

    # --- Handle --clean-output standalone flag ---
    if args.clean_output:
        if args.url or args.file or args.job_text:
            print(
                "Error: --clean-output cannot be combined with --url, "
                "--file, or --job-text.",
                file=sys.stderr,
            )
            sys.exit(1)

        output_dir = Path("output")
        if output_dir.exists():
            for item in output_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
        print("All output folders removed.")
        sys.exit(0)

    # --- Require exactly one input source when not using --clean-output ---
    if not args.url and not args.file and not args.job_text:
        print(
            "Error: one of --url, --file, or --job-text is required "
            "(or use --clean-output alone).",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.url:
        try:
            from src.job_scraper import fetch_job_text
            job_text = fetch_job_text(args.url)
        except ImportError:
            print(
                "Error: URL scraping requires 'requests'. "
                "Install it with: pip install requests",
                file=sys.stderr,
            )
            sys.exit(1)
        except (ValueError, RuntimeError) as e:
            print(f"Error fetching URL: {e}", file=sys.stderr)
            sys.exit(1)
        source = args.url
    elif args.file:
        job_text = _read_job_file(args.file)
        source = args.file
    else:
        job_text = args.job_text
        source = args.job_text[:80]

    result = run_job_pipeline(job_text, args.language, source=source)

    if result["success"]:
        print("Application generated successfully!")
        print(f"   Company:      {result['company']}")
        print(f"   Job:          {result['job_title']}")
        print(f"   Output:       {result['output_dir']}")
        print(f"   Cover letter: {result['cover_letter']}")
        print(f"   CV:           {result['cv']}")
        sys.exit(0)
    else:
        print(f"Pipeline failed: {result['reason']}")
        if "recommendation" in result:
            print(f"   Recommendation: {result['recommendation']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
