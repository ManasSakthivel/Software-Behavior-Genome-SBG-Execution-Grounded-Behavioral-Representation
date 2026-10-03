from typing import Optional

def fn_validate_baseindexer_support(func_name: Optional[str]) -> None:
    BASEINDEXER_WHITELIST = {'count', 'min', 'max', 'mean', 'sum', 'median', 'std', 'var', 'skew', 'kurt', 'quantile'}
    if isinstance(func_name, str) and func_name not in BASEINDEXER_WHITELIST:
        raise NotImplementedError(f'{func_name} is not supported with using a BaseIndexer subclasses. You can use .apply() with {func_name}.')