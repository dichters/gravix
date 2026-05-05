"""
Command-line interface for gravix
"""
import sys


def hello() -> None:
    """Print a greeting message"""
    print("Hi! Thank you for choosing gravix.")


def main() -> None:
    """Main entry point for the gravix CLI"""
    if len(sys.argv) < 2:
        print("Usage: gravix <command>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "hello":
        hello()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
