# BugsInPy black/21 | https://github.com/psf/black | black.py | unit dump_to_file
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit 8e7848c63efe36f09e4651bece8c0efc34a1c3e1 (fixed)
def dump_to_file(*output: str) -> str:
    """Dump `output` to a temporary file. Return path to the file."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", prefix="blk_", suffix=".log", delete=False, encoding="utf8"
    ) as f:
        for lines in output:
            f.write(lines)
            if lines and lines[-1] != "\n":
                f.write("\n")
    return f.name
