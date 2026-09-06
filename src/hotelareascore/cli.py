"""CLI: `hotelareascore ingest|score|validate|report` — backs `make
ingest/score/validate` (docs/strategy.md §5 Phase 1 deliverable)."""
from __future__ import annotations

import argparse
import sys

from . import ingest as ingest_mod
from . import overture
from . import report as report_mod
from . import scoring as scoring_mod
from . import validate as validate_mod
from . import webdata as webdata_mod
from .config import ETL_DIR, load_cities

ALL_CITY_IDS = list(load_cities().keys())


def _cities_arg(value: str) -> list[str]:
    if value == "all":
        return ALL_CITY_IDS
    ids = [c.strip() for c in value.split(",") if c.strip()]
    for c in ids:
        if c not in ALL_CITY_IDS:
            raise argparse.ArgumentTypeError(f"unknown city '{c}'. Known: {ALL_CITY_IDS}")
    return ids


def resolve_release(release_arg: str | None) -> overture.Release:
    if release_arg and release_arg != "latest":
        return overture.Release(id=release_arg)
    if ETL_DIR.exists():
        existing = sorted(p.name for p in ETL_DIR.iterdir() if p.is_dir())
        if existing:
            return overture.Release(id=existing[-1])
    return overture.discover_latest_release()


def cmd_ingest(args: argparse.Namespace) -> int:
    release = overture.discover_latest_release() if args.release in (None, "latest") else overture.Release(id=args.release)
    print(f"[ingest] release={release.id}")
    for city_id in args.city:
        print(f"[ingest] {city_id} ...")
        manifest = ingest_mod.ingest_city(city_id, release)
        print(f"[ingest] {city_id}: {manifest}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    release = resolve_release(args.release)
    print(f"[score] release={release.id}")
    for city_id in args.city:
        print(f"[score] {city_id} ...")
        result = scoring_mod.score_city(city_id, release)
        print(f"[score] {city_id}: {result}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    release = resolve_release(args.release)
    print(f"[validate] release={release.id}")
    failed = False
    for city_id in args.city:
        try:
            result = validate_mod.validate_city(city_id, release)
            print(
                f"[validate] {city_id}: OK — {result['n_hotels']} hotels, "
                f"median confidence {result['median_confidence']}, "
                f"dupe rate {result['dupe_rate_pct']}%"
            )
        except validate_mod.ValidationError as e:
            print(f"[validate] {city_id}: FAILED — {e}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


def cmd_report(args: argparse.Namespace) -> int:
    release = resolve_release(args.release)
    path = report_mod.write_report(release.id, args.city)
    print(f"[report] wrote {path}")
    return 0


def cmd_webdata(args: argparse.Namespace) -> int:
    release = resolve_release(args.release)
    webdata_mod.export_web_data(release, args.city)
    print(f"[webdata] exported {', '.join(args.city)} (release {release.id}) to web/src/data + web/public/data")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hotelareascore")
    sub = p.add_subparsers(dest="command", required=True)

    for name, fn, default_city in (
        ("ingest", cmd_ingest, "all"),
        ("score", cmd_score, "all"),
        ("validate", cmd_validate, "all"),
        ("report", cmd_report, "all"),
        ("webdata", cmd_webdata, "all"),
    ):
        sp = sub.add_parser(name)
        sp.add_argument("--city", type=_cities_arg, default=_cities_arg(default_city))
        sp.add_argument("--release", default="latest", help="Overture release id, or 'latest' (default)")
        sp.set_defaults(func=fn)

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
