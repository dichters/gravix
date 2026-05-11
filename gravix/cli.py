import argparse

from loguru import logger as log

from gravix.app import Gravix
from gravix.config import load_config


def cmd_init(args: argparse.Namespace) -> None:
    config = load_config(config_file=args.conf)
    gravix = Gravix(config)
    gravix.init()


def cmd_topic(args: argparse.Namespace) -> None:
    config = load_config(config_file=args.conf)
    gravix = Gravix(config)
    gravix.set_topic(text=args.text, file=args.file)


def main() -> None:
    parser = argparse.ArgumentParser(prog="gravix", description="Gravix CLI")
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize a gravix workspace")
    init_parser.add_argument(
        "-conf", default=None, help="Path to config JSON file"
    )
    init_parser.set_defaults(func=cmd_init)

    topic_parser = subparsers.add_parser("topic", help="Set topic for the knowledge base")
    topic_parser.add_argument(
        "text", nargs="?", default=None, help="Topic description text"
    )
    topic_parser.add_argument(
        "-file", default=None, help="Path to a file containing the topic description"
    )
    topic_parser.add_argument(
        "-conf", default=None, help="Path to config JSON file"
    )
    topic_parser.set_defaults(func=cmd_topic)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
