"""
program_id: parse_ini_config
category: Parser Implementations
spec_version: 1.0
spec: INI-format config parser supporting sections, key=value, inline comments, multi-word values.
"""
from typing import Dict, Optional

class INIParser:
    """
    Parses INI-format config text.
    - Sections: [section_name]
    - Keys: key = value  or  key: value
    - Comments: lines starting with # or ;
    - Leading/trailing whitespace stripped from keys and values
    - Duplicate keys in same section: last value wins
    """

    def __init__(self):
        self._data: Dict[str, Dict[str, str]] = {'DEFAULT': {}}

    def parse(self, text: str) -> 'INIParser':
        self._data = {'DEFAULT': {}}
        current_section = 'DEFAULT'
        for (lineno, raw_line) in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            if line.startswith('['):
                if not line.endswith(']'):
                    raise ValueError(f'Line {lineno}: malformed section header: {line!r}')
                current_section = line[1:-1].strip()
                if not current_section:
                    raise ValueError(f'Line {lineno}: empty section name')
                if current_section not in self._data:
                    self._data[current_section] = {}
                continue
            for sep in ('=', ':'):
                if sep in line:
                    (key, _, value) = line.partition(sep)
                    key = key.strip()
                    value = value.strip()
                    for comment_char in ('#', ';'):
                        idx = value.find(comment_char)
                        if idx != -1:
                            value = value[:idx].strip()
                    if not key:
                        raise ValueError(f'Line {lineno}: empty key')
                    self._data[current_section][key] = value
                    break
            else:
                raise ValueError(f'Line {lineno}: no separator in {line!r}')
        return self

    def get(self, section: str, key: str, fallback=None) -> Optional[str]:
        s = self._data.get(section, {})
        return s.get(key, self._data.get('DEFAULT', {}).get(key, fallback))

    def sections(self):
        return [s for s in self._data if s != 'DEFAULT']

    def items(self, section: str):
        return list(self._data.get(section, {}).items())
if __name__ == '__main__':
    sample = '\n[database]\nhost = localhost\nport = 5432\nname = mydb  # production db\n\n[cache]\nhost = 127.0.0.1\nport: 6379\n'
    cfg = INIParser().parse(sample)
    assert cfg.get('database', 'host') == 'localhost'
    assert cfg.get('database', 'port') == '5432'
    assert cfg.get('database', 'name') == 'mydb'
    assert cfg.get('cache', 'port') == '6379'
    assert set(cfg.sections()) == {'database', 'cache'}
    sample2 = '[s1]\nkey = val\n'
    cfg2 = INIParser().parse(sample2)
    assert cfg2.get('s1', 'missing', 'default_val') == 'default_val'
    try:
        INIParser().parse('[bad')
    except ValueError:
        pass
    print('parse_ini_config: all tests passed')