from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(description="CNC tool RUL research CLI")
    parser.add_argument("--config", default="default.yaml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("audit", help="Run dataset and target feasibility audit")
    sub.add_parser("run", help="Run full LOTO experiments and figures")
    p_dash = sub.add_parser("dashboard", help="Launch Streamlit demonstrator")

    args = parser.parse_args(argv)
    root = _root()
    sys.path.insert(0, str(root / "src"))

    from cnc_rul.config import load_config

    cfg = load_config(root, args.config)

    if args.command == "audit":
        from cnc_rul.audit import run_audit

        run_audit(cfg)
        return 0

    if args.command == "run":
        from cnc_rul.pipeline import run_pipeline

        summary = run_pipeline(cfg)
        print(summary)
        return 0

    if args.command == "dashboard":
        import subprocess

        app = root / "dashboard" / "app.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(app)], check=False)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())