"""Synchronize faqs.json records into the dedicated FAQ Qdrant Cloud collection."""
import argparse

from app.services.faq_service import sync_faqs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--faq-file", help="Optional path to FAQ JSON")
    parser.add_argument("--sync", action="store_true", help="Synchronize changed and removed FAQ records")
    args = parser.parse_args()
    from pathlib import Path
    path = Path(args.faq_file) if args.faq_file else None
    count = sync_faqs(path) if path else sync_faqs()
    print(f"Synchronized {count} FAQ records into Qdrant Cloud.")


if __name__ == "__main__":
    main()
