
from earnest.magic import (
    StringKeysOnlyMapping,
    MagicMapping,
)

import pytest


def test_string_keys_only_mapping():
    d = StringKeysOnlyMapping({'a': 1}, b=2, c=3)
    assert d['a'] == 1
    assert 'b' in d
    assert len(d) == 3
    d['foo'] = 'bar'
    assert len(d) == 4
    assert d['foo'] == 'bar'
    assert d.pop('foo') == 'bar'
    assert 'foo' not in d
    assert sorted(d) == ['a', 'b', 'c']
    with pytest.raises(ValueError):
        d[123]
    with pytest.raises(ValueError):
        d[123] = 456
    with pytest.raises(ValueError):
        del d[123]


def test_magic():
    original = {
        's1': 'hello',
        's2': 'world',
        'i1': 123,
        'i2': 456,
        'b1': True,
        'b2': False,
        'd': {
            'foo': 'bar',
        },
    }
    d = MagicMapping(original)
    print(d)
    assert len(d) == len(original)

    # Normal access
    assert d['s1'] == 'hello'

    # Type filtered view
    d2 = d[str]
    print(d2)
    assert d2 is not d
    assert d2['s1'] == 'hello'
    assert 'i1' not in d2
    assert len(d2) == 2
    d2['s3'] = 'hi'
    assert d2['s3'] == 'hi'
    assert sorted(d2) == ['s1', 's2', 's3']
    del d2['s3']
    with pytest.raises(KeyError):
        d2['i1']
    with pytest.raises(ValueError):
        d2['s3'] = 123
    with pytest.raises(KeyError):
        # Key exists in underlying mapping, but wrong type so doesn't
        # show up in the filtered proxy.
        del d2['i1']

    # Type filtered single item access
    assert d['s1':str] == 'hello'
    assert d['i1':int] == 123
    with pytest.raises(KeyError):
        assert d['s1':bool]
    with pytest.raises(KeyError):
        assert d['b1':str]
