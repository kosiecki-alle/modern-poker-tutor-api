"""Publish the implemented contract snapshot without starting or resetting SQLite."""
import json
from pathlib import Path

from poker_tutor.api import app


def main():
    specification = app.openapi()
    Path("openapi-backend.json").write_text(json.dumps(specification, indent=2) + "\n")
    print("Published openapi-backend.json version " + specification["info"]["version"])


if __name__ == "__main__":
    main()
