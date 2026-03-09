from src.exceptions import InputError


def read_md_files(paths: list[str]) -> str:
    if not paths:
        raise InputError("No input files provided.")

    parts = []
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                parts.append(f"### {path}\n{f.read()}")
        except FileNotFoundError:
            raise InputError(f"File not found: {path}")
        except PermissionError:
            raise InputError(f"Permission denied reading file: {path}")
        except UnicodeDecodeError:
            raise InputError(f"File is not valid UTF-8 text: {path}")

    return "\n\n".join(parts)
