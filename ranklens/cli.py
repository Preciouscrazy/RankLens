"""CLI: read synthetic JSON input and write a deterministic rating explanation."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from ranklens.analyzer import analyze_records


def _same_file(source, destination):
    """Protect input against matching paths, symlinks, and existing hard links."""
    if source.resolve() == destination.resolve():
        return True
    return source.exists() and destination.exists() and source.samefile(destination)


def _atomic_write(destination, content):
    temp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=destination.parent, prefix=f".{destination.name}.",
            suffix=".tmp", delete=False,
        ) as output:
            temp = Path(output.name)
            output.write(content)
        os.replace(temp, destination)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explain hypothetical rating changes from local JSON")
    parser.add_argument("input", help="JSON array of synthetic match records")
    parser.add_argument("--output", help="Optional JSON report path (default: stdout)")
    args = parser.parse_args(argv)
    source = Path(args.input)
    destination = Path(args.output) if args.output is not None else None

    try:
        if destination is not None and _same_file(source, destination):
            raise ValueError("input and output refer to the same file")
        records = json.loads(source.read_text(encoding="utf-8-sig"))
        report = analyze_records(records)
        content = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if destination is None:
            sys.stdout.write(content)
        else:
            _atomic_write(destination, content)
            print(f"Saved {destination}")
    except (OSError, UnicodeError, ValueError, OverflowError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
