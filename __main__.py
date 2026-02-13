import argparse
import sys
from utils import repl, server

# ==========================================


def handle_arguments():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    subparsers.add_parser("repl", help="Run the mini-CSVQL REPL").set_defaults(
        func=repl
    )
    subparsers.add_parser("server", help="Run the mini-CSVQL server").set_defaults(
        func=server
    )

    if len(sys.argv) == 1:
        parser.print_help()
        exit(0)

    parser.parse_args().func()


# ==========================================

if __name__ == "__main__":
    handle_arguments()
