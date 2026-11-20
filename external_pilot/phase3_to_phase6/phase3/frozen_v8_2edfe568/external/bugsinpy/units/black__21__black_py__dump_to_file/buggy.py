# BugsInPy black/21 | https://github.com/psf/black | black.py | unit dump_to_file
# license: MIT (upstream project); extracted verbatim, closure only, no edits
# commit c071af761e1550c6e4ebab8e5af747d2d8fdd48e (buggy)
def dump_to_file(*output: str) -> str:
    """Dump `output` to a temporary file. Return path to the file."""
    import tempfile

    with tempfile.NamedTemporaryFile(
        mode="w", prefix="blk_", suffix=".log", delete=False
    ) as f:
        for lines in output:
            f.write(lines)
            if lines and lines[-1] != "\n":
                f.write("\n")
    return f.name
