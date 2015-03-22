
import pytest

import earnest


@pytest.fixture()
def sample_object():
    return dict(
        a=1,
        b=2,
        c=['c1', 'c2'],
        d=dict(nested=[1, dict(foo='bar', baz={})]),
    )


def test_walk(sample_object):
    import pprint

    pprint.pprint(sample_object)
    print()

    for path, obj in earnest.walk(sample_object, parent_first=True):
        print('.'.join(map(str, path)))
        print(obj)
        print()


def test_lookup_path(sample_object):

    lookup_path = earnest.lookup_path
    assert lookup_path(sample_object, ['a']) == 1
    assert lookup_path(sample_object, 'a') == 1
    assert lookup_path(sample_object, ['d', 'nested', 1, 'foo']) == 'bar'
    assert lookup_path(sample_object, 'd.nested.1.foo') == 'bar'

    with pytest.raises(KeyError):
        lookup_path(sample_object, 'd.nested.1.too-bad')

    assert lookup_path(sample_object, 'd.nested.1.too-bad', 'x') == 'x'
