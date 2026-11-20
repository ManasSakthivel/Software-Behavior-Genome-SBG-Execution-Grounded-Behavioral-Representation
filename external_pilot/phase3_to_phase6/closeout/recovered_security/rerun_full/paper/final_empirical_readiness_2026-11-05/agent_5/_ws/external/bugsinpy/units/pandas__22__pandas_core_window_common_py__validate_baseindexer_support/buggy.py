# BugsInPy pandas/22 | https://github.com/pandas-dev/pandas | pandas/core/window/common.py | unit validate_baseindexer_support
# license: BSD-3-Clause (upstream project); extracted verbatim, closure only, no edits
# commit 38b669a206b151e0a2bb985200d4a493c4ac078f (buggy)
from typing import Optional

def validate_baseindexer_support(func_name: Optional[str]) -> None:
    # GH 32865: These functions work correctly with a BaseIndexer subclass
    BASEINDEXER_WHITELIST = {
        "min",
        "max",
        "mean",
        "sum",
        "median",
        "std",
        "var",
        "kurt",
        "quantile",
    }
    if isinstance(func_name, str) and func_name not in BASEINDEXER_WHITELIST:
        raise NotImplementedError(
            f"{func_name} is not supported with using a BaseIndexer "
            f"subclasses. You can use .apply() with {func_name}."
        )
