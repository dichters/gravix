import argparse

from loguru import logger as log

from gravix.config import load_config
from gravix.storage import init_ladybug, init_raw_dir, init_sqlite, init_work_dir


def cmd_init(args: argparse.Namespace) -> None:
    config = load_config(config_file=args.conf)
    work_dir = init_work_dir(config.work_dir)
    init_ladybug(work_dir)
    init_sqlite(work_dir)
    init_raw_dir(work_dir)
    log.info("Gravix workspace initialized at: {}", work_dir)


def main() -> None:
    parser = argparse.ArgumentParser(prog="gravix", description="Gravix CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a gravix workspace")
    init_parser.add_argument(
        "-conf", default=None, help="Path to config YAML file"
    )
    init_parser.set_defaults(func=cmd_init)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
