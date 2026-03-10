from src.domain.path_validator import validate_path_within
from src.exceptions import InputError


def read_md_files(paths: list[str], vault_base_dir: str | None = None) -> str:
    if not paths:
        raise InputError("No input files provided.")

    parts = []
    for path in paths:
        if vault_base_dir is not None:
            validate_path_within(path, vault_base_dir)
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
