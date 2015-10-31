
from earnest.magic import (
    StringKeysDict,
    MagicDict,
    NothingContainer,
)

import pytest


def test_string_keys_dict():
    d = StringKeysDict({'a': 1}, b=2, c=3)
    print(d)
    assert d['a'] == 1
    assert 'b' in d
    assert len(d) == 3
    d['foo'] = 'bar'
    assert len(d) == 4
    assert d['foo'] == 'bar'
    assert d.pop('foo') == 'bar'
    assert 'foo' not in d
    assert sorted(d) == ['a', 'b', 'c']
    with pytest.raises(TypeError):
        d[123]
    with pytest.raises(TypeError):
        d[123] = 456
    with pytest.raises(TypeError):
        del d[123]


def test_magic():
    original = {
        's1': 'hello',
        's2': 'world',
        'i1': 123,
        'i2': 456,
        'i3': 2**64,  # 'long' in python 2
        'b1': True,
        'b2': False,
        'd1': {
            's1': 'v1',
        },
        'l1': [1, 2, 3],
        'l2': [
            {'a': [1, 2]},
            {'b': [3, 4]},
        ]
    }
    d = MagicDict(original)
    print(d)
    assert len(d) == len(original)

    # Normal access
    assert d['s1'] == 'hello'
    assert d.get('s1') == 'hello'
    assert d.get('s3', 'fallback') == 'fallback'

    # Nested access using tuple notation
    assert d['d1', 's1'] == 'v1'
    assert d.get(('d1', 's1')) == 'v1'
    with pytest.raises(KeyError):
        d['d1', 'nonexistent']
    assert d.get(('d1', 'nonexistent'), 'fallback') == 'fallback'
    with pytest.raises(KeyError):
        # FIXME: only recurse into container types, not into strings
        d['s1', 0]

    # Type filtered single item access
    assert d['s1':str] == 'hello'
    assert d['i1':int] == 123
    assert d['i3':int] == 2**64
    assert d['d1', 's1':str] == 'v1'
    with pytest.raises(ValueError):
        assert d['s1':bool]
    with pytest.raises(ValueError):
        assert d['b1':str]
    with pytest.raises(ValueError):
        assert d['s1':'invalid-type-filter']

    # Type filtered view
    d2 = d[:str]
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


def test_nothing_container():
    t = NothingContainer
    assert t['key'] is t
    assert t[0] is t
    assert list(t) == []
    assert not t
    assert t['key1']['key2'][3][4] is t
