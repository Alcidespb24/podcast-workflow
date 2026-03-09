"""Generate Argon2id password hashes for .env configuration.

Usage: python -m src.hash_password
"""

import getpass
import sys

from argon2 import PasswordHasher


def main() -> None:
    """Prompt for a password and output an Argon2id hash."""
    ph = PasswordHasher()

    password = getpass.getpass("Enter password: ")
    confirm = getpass.getpass("Confirm password: ")

    if not password:
        print("Error: Password cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if password != confirm:
        print("Error: Passwords do not match.", file=sys.stderr)
        sys.exit(1)

    hash_value = ph.hash(password)

    print()
    print(hash_value)
    print()
    print("Add this line to your .env file:")
    print(f"DASHBOARD_PASSWORD_HASH={hash_value}")


if __name__ == "__main__":
    main()
