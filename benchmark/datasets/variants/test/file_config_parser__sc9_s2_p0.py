"""
INI-style configuration file parser with type coercion and validation.

Spec: Parses INI-format configuration from a string:
  - Sections: [section_name]
  - Key-value: key = value  or  key: value
  - Comments: lines starting with '#' or ';' are ignored
  - Multi-value keys: key[] = val1 appended as list
  - Inline comments: stripped after '#' or ';' (unless inside quotes)

Provides:
  - ConfigParser.load(text) : parse INI text
  - get(section, key, default=None) : get value with optional default
  - get_int/get_float/get_bool : typed getters (raises TypeError on failure)
  - sections() : list of section names
  - items(section) : all key-value pairs in a section
  - set(section, key, value) : programmatic modification
  - dump() : serialize back to INI string

Raises ParseError for duplicate section headers (configurable), invalid syntax.
"""
import re
from typing import Any, Dict, List, Optional, Tuple, Union

class ParseError(Exception):
    pass

class ConfigParser:
    _SECTION_RE = re.compile('^\\[([^\\]]+)\\]\\s*(?:[#;].*)?$')
    '\n    INI-file parser with type coercion.\n\n    Parameters\n    ----------\n    allow_duplicate_sections : if False (default), raises ParseError on duplicate sections.\n    '
    _KV_RE = re.compile('^([^=:]+)[=:](.*)$')
    _COMMENT_RE = re.compile('[#;](?=(?:[^\\"\']|[\\"\'][^\\"\']*[\\"\'])*$)')

    def __init__(self, allow_duplicate_sections: bool=False):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._section_order: List[str] = []
        self._allow_dup = allow_duplicate_sections

    def load(self, text: str) -> 'ConfigParser':
        """Parse INI-format text. Chainable."""
        current_section = None
        for (lineno, raw_line) in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line or line.startswith(('#', ';')):
                continue
            m_sec = self._SECTION_RE.match(line)
            if m_sec:
                name = m_sec.group(1).strip()
                if name in self._data and (not self._allow_dup):
                    raise ParseError(f'Line {lineno}: duplicate section [{name}]')
                if name not in self._data:
                    self._data[name] = {}
                    self._section_order.append(name)
                current_section = name
                continue
            m_kv = self._KV_RE.match(line)
            if m_kv:
                if current_section is None:
                    raise ParseError(f'Line {lineno}: key-value outside of any section')
                key = m_kv.group(1).strip()
                value = m_kv.group(2).strip()
                cm = self._COMMENT_RE.search(value)
                if cm:
                    value = value[:cm.start()].strip()
                if key.endswith('[]'):
                    real_key = key[:-2].strip()
                    existing = self._data[current_section].get(real_key, [])
                    if not isinstance(existing, list):
                        existing = [existing]
                    existing.append(value)
                    self._data[current_section][real_key] = existing
                else:
                    self._data[current_section][key] = value
                continue
            raise ParseError(f'Line {lineno}: unrecognized syntax: {raw_line!r}')
        return self

    def sections(self) -> List[str]:
        return list(self._section_order)

    def has_section(self, section: str) -> bool:
        return section in self._data

    def get(self, section: str, key: str, default: Any=None) -> Any:
        return self._data.get(section, {}).get(key, default)

    def get_int(self, section: str, key: str, default: int=None) -> int:
        val = self.get(section, key)
        if val is None:
            if default is not None:
                return default
            raise KeyError(f'[{section}].{key} not found')
        try:
            return int(val)
        except (ValueError, TypeError):
            raise TypeError(f'[{section}].{key} = {val!r} cannot be coerced to int')

    def get_float(self, section: str, key: str, default: float=None) -> float:
        val = self.get(section, key)
        if val is None:
            if default is not None:
                return default
            raise KeyError(f'[{section}].{key} not found')
        try:
            return float(val)
        except (ValueError, TypeError):
            raise TypeError(f'[{section}].{key} = {val!r} cannot be coerced to float')

    def get_bool(self, section: str, key: str, default: bool=None) -> bool:
        val = self.get(section, key)
        if val is None:
            if default is not None:
                return default
            raise KeyError(f'[{section}].{key} not found')
        if isinstance(val, str):
            if val.lower() in ('true', 'yes', '1', 'on'):
                return True
            if val.lower() in ('false', 'no', '0', 'off'):
                return False
        raise TypeError(f'[{section}].{key} = {val!r} is not a boolean')

    def set(self, section: str, key: str, value: Any) -> None:
        if section not in self._data:
            self._data[section] = {}
            self._section_order.append(section)
        self._data[section][key] = value

    def items(self, section: str) -> List[Tuple[str, Any]]:
        if section not in self._data:
            raise KeyError(f'Section [{section}] not found')
        return list(self._data[section].items())

    def dump(self) -> str:
        """Serialize to INI string."""
        lines = []
        for section in self._section_order:
            lines.append(f'[{section}]')
            for (key, val) in self._data[section].items():
                if isinstance(val, list):
                    for v in val:
                        lines.append(f'{key}[] = {v}')
                else:
                    lines.append(f'{key} = {val}')
            lines.append('')
        return '\n'.join(lines)
SAMPLE_INI = '\n[database]\nhost = localhost\nport = 5432\nname = mydb\ndebug = false\n\n[server]\nhost = 0.0.0.0\nport = 8080\nworkers = 4\ntags[] = web\ntags[] = api\ntags[] = prod\n\n[cache]\nenabled = true\nttl = 3600.5   ; seconds\n'

def test_config_parser():
    cfg = ConfigParser().load(SAMPLE_INI)
    assert set(cfg.sections()) == {'database', 'server', 'cache'}
    assert cfg.get('database', 'host') == 'localhost'
    assert cfg.get('database', 'missing', 'default') == 'default'
    assert cfg.get_int('server', 'port') == 8080
    assert cfg.get_int('server', 'workers') == 4
    assert abs(cfg.get_float('cache', 'ttl') - 3600.5) < 1e-09
    assert cfg.get_bool('database', 'debug') == False
    assert cfg.get_bool('cache', 'enabled') == True
    tags = cfg.get('server', 'tags')
    assert isinstance(tags, list)
    assert tags == ['web', 'api', 'prod']
    assert cfg.get('cache', 'ttl') == '3600.5'
    cfg.set('database', 'password', 'secret')
    assert cfg.get('database', 'password') == 'secret'
    try:
        ConfigParser().load('[section]\nkey=1\n[section]\nkey=2\n')
        assert False
    except ParseError:
        pass
    cfg2 = ConfigParser(allow_duplicate_sections=True).load('[s]\na=1\n[s]\nb=2\n')
    assert cfg2.get('s', 'a') == '1'
    assert cfg2.get('s', 'b') == '2'
    try:
        ConfigParser().load('key = value\n[s]\n')
        assert False
    except ParseError:
        pass
    dumped = cfg.dump()
    cfg_rt = ConfigParser().load(dumped)
    assert cfg_rt.get('server', 'port') == '8080'
    print('All config_parser tests passed.')
if __name__ == '__main__':
    test_config_parser()
    cfg = ConfigParser().load(SAMPLE_INI)
    print('Sections:', cfg.sections())
    print('server.port:', cfg.get_int('server', 'port'))
    print('server.tags:', cfg.get('server', 'tags'))