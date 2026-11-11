import json, sys
from pathlib import Path
from ranklens.analyzer import analyze_records

def main():
    if len(sys.argv) != 2:
        print("Usage: python -m ranklens.cli data.json", file=sys.stderr); return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        print(json.dumps(analyze_records(data), indent=2)); return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr); return 1
if __name__ == "__main__":
    raise SystemExit(main())
