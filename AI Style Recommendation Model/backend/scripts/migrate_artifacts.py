"""Move local model trees without overwriting an existing destination."""
import argparse
from pathlib import Path


def migrate_artifacts(source: Path, destination: Path) -> None:
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise FileExistsError(destination)
    if not source.is_dir():
        raise FileNotFoundError(source)
    if source == destination or source.is_relative_to(destination) or destination.is_relative_to(source):
        raise ValueError("Source and destination must be separate directory trees")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # On the same filesystem rename is atomic and includes ignored files.
    source.rename(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    migrate_artifacts(args.source, args.destination)


if __name__ == "__main__":
    main()
