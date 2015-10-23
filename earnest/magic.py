try:
    from collections.abc import (
        Mapping,
        MutableMapping,
        Sequence,
    )
except ImportError:
    from collections import Mapping, MutableMapping

import cardinality
import six

if six.PY2:
    from future_builtins import filter  # noqa


def pairs(*args, **kwargs):
    """
    Generator that matches the ``dict()`` constructor. Yields pairs.
    """
    if args:
        if len(args) != 1:
            raise TypeError(
                "expected at most 1 arguments, got {0:d}".format(len(args)))
        try:
            it = six.iteritems(args[0])  # mapping type
        except AttributeError:
            it = iter(args[0])  # sequence of pairs
        for k, v in it:
            yield k, v
    for k, v in six.iteritems(kwargs):
        yield k, v


class StringKeysOnlyMapping(MutableMapping):
    """Mutable mapping type that only accepts strings as keys."""

    __slots__ = ('_mapping')

    def __init__(self, *args, **kwargs):
        self._mapping = {}
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        if not isinstance(key, six.string_types):
            raise ValueError("key must be a string")
        return self._mapping[key]

    def __setitem__(self, key, value):
        if not isinstance(key, six.string_types):
            raise ValueError("key must be a string")
        self._mapping[key] = value

    def __delitem__(self, key):
        if not isinstance(key, six.string_types):
            raise ValueError("key must be a string")
        del self._mapping[key]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self._mapping)


class TypeFilteredValueMapping(MutableMapping):
    """A mapping proxy that only handles values of a certain type."""

    __slots__ = ('_mapping', '_type')

    def __init__(self, mapping, type):
        self._mapping = mapping
        self._type = type

    def __getitem__(self, key):
        value = self._mapping[key]
        if not isinstance(value, self._type):
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        if not isinstance(value, self._type):
            raise ValueError(
                "value must be a {0}".format(self._type.__name__))
        self._mapping[key] = value

    def __delitem__(self, key):
        self[key]  # This checks that the value has the proper type.
        del self._mapping[key]

    def __len__(self):
        # This is O(n), not O(1).
        return cardinality.count(iter(self))

    def __iter__(self):
        for key, value in six.iteritems(self._mapping):
            if isinstance(value, self._type):
                yield key

    def __repr__(self):
        return '<{0} type={1} mapping={2!r}>'.format(
            self.__class__.__name__,
            self._type.__name__,
            self._mapping)


# TODO: silent mode
# TODO: lists
# TODO: how to treat nested container structures?
# FIXME: Python2 has a 'long' type: use six.integer_types


class MagicMapping(MutableMapping):
    """
    Magic mapping type with various bells and whistles for the JSON data model.
    """

    _SENTINEL_TYPES = (
        six.integer_types
        + six.string_types
        + (bool, float, type(None)))

    __slots__ = ('_mapping')

    def __init__(self, *args, **kwargs):
        self._mapping = StringKeysOnlyMapping()
        self.update(*args, **kwargs)

    def filter_values_by_type(self, type):
        return TypeFilteredValueMapping(self, type)

    def __getitem__(self, key):
        # Shorthand to get a filtered view of this mapping: d[int]
        if key in (bool, float, int, str):
            return self.filter_values_by_type(key)

        # Type filtering for a single key: d['abc':str]
        if isinstance(key, slice):
            assert key.step is None  # FIXME: better exception
            return self[key.stop][key.start]

        return self._mapping[key]

    def __setitem__(self, key, value):
        if isinstance(value, self._SENTINEL_TYPES):
            pass
        elif isinstance(value, self.__class__):
            pass  # already magic
        elif isinstance(value, Mapping):
            value = type(self)(value)
        elif isinstance(value, (list, tuple)):
            raise NotImplementedError
        else:
            raise ValueError(
                "values of type '{0}' are not allowed".format(
                    value.__class__.__name__))

        self._mapping[key] = value

    def __delitem__(self, key):
        del self._mapping[key]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0}({1!r})'.format(
            self.__class__.__name__,
            dict(self._mapping))

    def clear(self):
        # Fast delegation.
        self._mapping.clear()


class _NothingContainer(Mapping, Sequence):
    """
    Container type emulating both an empty mapping and sequence.
    """

    def __getitem__(self, key):
        return NothingContainer

    def __len__(self):
        return 0

    def __iter__(self):
        if False:
            yield

    def __repr__(self):
        return '<NothingContainer>'


NothingContainer = _NothingContainer()  # singleton
