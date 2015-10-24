try:
    from collections.abc import (
        Mapping,
        MutableMapping,
        Sequence,
    )
except ImportError:  # pragma: no cover
    from collections import (
        Mapping,
        MutableMapping,
        Sequence,
    )

import cardinality
import six


# Type normalisation to cater for int/long and str/unicode in Python 2.
NORMALISED_TYPES = {
    bool: bool,
    dict: dict,
    float: float,
    int: six.integer_types,
    list: list,
    str: six.string_types,
}


def normalise_type(t, lookup=NORMALISED_TYPES):
    try:
        return lookup[t]
    except KeyError:
        raise ValueError(
            "type filter must be one of {0}".format(", ".join(
                sorted(t.__name__ for t in lookup))))


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


class StringKeysMapping(Mapping):
    """Mapping type that only accepts strings as keys."""

    __slots__ = ('_mapping')

    def __init__(self, mapping):
        self._mapping = mapping

    def __getitem__(self, key):
        if not isinstance(key, six.string_types):
            raise ValueError("key must be a string")
        return self._mapping[key]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0}({1!r})'.format(self.__class__.__name__, self._mapping)


class StringKeysMutableMapping(StringKeysMapping, MutableMapping):
    """Mutable version of StringKeysMapping."""

    __slots__ = ()

    def __setitem__(self, key, value):
        if not isinstance(key, six.string_types):
            raise ValueError("key must be a string")
        self._mapping[key] = value

    def __delitem__(self, key):
        if not isinstance(key, six.string_types):
            raise ValueError("key must be a string")
        del self._mapping[key]


class StringKeysDict(StringKeysMutableMapping):

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        super(StringKeysDict, self).__init__({})
        self.update(*args, **kwargs)


class TypeFilteredValueMapping(MutableMapping):
    """A mapping proxy that only handles values of a certain type."""

    __slots__ = ('_mapping', '_type')

    def __init__(self, mapping, type):
        self._mapping = mapping
        self._type = type

    def __getitem__(self, key):
        value = self._mapping[key]
        if not isinstance(value, normalise_type(self._type)):
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        if not isinstance(value, normalise_type(self._type)):
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
        normalised_type = normalise_type(self._type)
        for key, value in six.iteritems(self._mapping):
            if isinstance(value, normalised_type):
                yield key

    def __repr__(self):
        return '{0}(mapping={1!r}, type={2} >'.format(
            self.__class__.__name__,
            self._mapping,
            self._type.__name__)


# TODO: silent mode
# TODO: lists
# TODO: how to treat nested container structures?
# FIXME: Python2 has a 'long' type; always use six.integer_types
# FIXME: Python2 has a both 'unicode' and 'str'; always use six.string_types


class MagicMapping(Mapping):

    __slots__ = ('_mapping')

    def __init__(self, mapping):
        self._mapping = mapping

    def __getitem__(self, key):

        # Slice lookups are used for type filtering on the value.
        if isinstance(key, slice):
            sl = key
            key = sl.start

            if sl.step is not None:
                raise NotImplementedError("step specified in slice")

            if sl.start is None:
                # Filtered view of this mapping, e.g. d[:int]
                return TypeFilteredValueMapping(self, sl.stop)

            # Type filtering for a single key, e.g. d['abc':str]
            value = self[key]
            if not isinstance(value, normalise_type(sl.stop)):
                raise ValueError("value is not of {0} type: {1!r}".format(
                    sl.stop.__name__, value))

        # Tuples are a shortcut for nested lookups, e.g. d['a', 'b']
        if isinstance(key, tuple):
            cur = self
            for k in key:
                cur = cur[k]
            return cur

        return self._mapping[key]

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        return '{0}(mapping={1!r})'.format(
            self.__class__.__name__,
            self._mapping)


class MagicMutableMapping(MagicMapping, MutableMapping):

    __slots__ = ()

    _SENTINEL_TYPES = (
        six.integer_types
        + six.string_types
        + (bool, float, type(None)))

    def __setitem__(self, key, value):
        if isinstance(value, self._SENTINEL_TYPES):
            pass
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

    def clear(self):
        # Fast delegation.
        self._mapping.clear()


class MagicDict(MagicMutableMapping):
    """
    Dict-like type for for the JSON data model with added magic.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        super(MagicDict, self).__init__(StringKeysDict())
        self.update(*args, **kwargs)

    def __repr__(self):
        return '{0}(mapping={1!r})'.format(
            self.__class__.__name__,
            dict(self._mapping))


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
