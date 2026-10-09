"""CLI entry point: python main.py run --dry-run --no-notify"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jobscraper.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
