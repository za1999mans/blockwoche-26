"""CLI: Hochschuldaten indexieren, Index prüfen, Quellen suchen und Fragen stellen."""
import argparse
import json
import os
import sys
from pathlib import Path

from hs_rag import (DEFAULT_CHUNKS, DEFAULT_MODEL, VectorIndex, answer_question,
                    build_index, database_path, friendly_error, index_plan,
                    index_status, load_environment)


def main() -> int:
    load_environment()
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("index", help="Embeddings erzeugen und dauerhaft speichern")
    build.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    build.add_argument("--db", type=Path, default=database_path())
    build.add_argument("--model", default=os.environ.get("HS_EMBEDDING_MODEL", DEFAULT_MODEL))
    build.add_argument("--batch-size", type=int, default=32)
    build.add_argument("--dry-run", action="store_true", help="Plan prüfen; keine API-Aufrufe oder Schreibzugriffe")
    status = commands.add_parser("status", help="Gespeicherten Index ohne API-Aufruf prüfen")
    status.add_argument("--db", type=Path, default=database_path())
    status.add_argument("--chunks", type=Path, default=DEFAULT_CHUNKS)
    for name in ["search", "ask"]:
        command = commands.add_parser(name, help="Quellen suchen" if name == "search" else "RAG-Antwort erzeugen")
        command.add_argument("question")
        command.add_argument("--db", type=Path, default=database_path())
        command.add_argument("--top-k", type=int, default=6)
        command.add_argument("--campus")
        command.add_argument("--degree")
        command.add_argument("--programme")
        command.add_argument("--min-score", type=float, default=0.25)
        command.add_argument("--include-archived", action="store_true")
        if name == "ask":
            command.add_argument("--chat-model")
            command.add_argument("--provider")
    args = parser.parse_args()
    try:
        if args.command == "index":
            plan = index_plan(args.chunks, args.db, args.model)
            print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
            if args.dry_run:
                return 0
            result = build_index(args.chunks, args.db, args.model, args.batch_size,
                                 progress=lambda done, total: print(
                                     f"Embeddings gespeichert: {done}/{total}", flush=True))
        elif args.command == "status":
            result = index_status(args.db, args.chunks)
        else:
            index = VectorIndex(args.db)
            options = {key: getattr(args, key) for key in
                       ["top_k", "campus", "degree", "programme", "min_score", "include_archived"]}
            if args.command == "search":
                result = [hit.to_dict() for hit in index.search(args.question, **options)]
            else:
                result = answer_question(args.question, index, model=args.chat_model,
                                         provider=args.provider, **options)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print("Fehler: " + friendly_error(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
