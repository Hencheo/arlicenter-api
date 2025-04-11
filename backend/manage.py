#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arlicenter.settings")
        try:
            from django.core.management import execute_from_command_line
        except ImportError as exc:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed?"
            ) from exc
        execute_from_command_line(sys.argv)
    except Exception as e:
        print(f"Erro ao executar manage.py: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()