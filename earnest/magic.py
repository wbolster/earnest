try:
    from collections.abc import (
        Mapping,
        MutableMapping,
        MutableSequence,
        Sequence,
    )
except ImportError:  # pragma: no cover
    from collections import (
        Mapping,
        MutableMapping,
        MutableSequence,
        Sequence,
    )

import cardinality
import six


ATOMIC_TYPES = (
    six.integer_types
    + six.string_types
    + (bool, float, type(None)))


def enchant_value(value):
    if isinstance(value, ATOMIC_TYPES):
        return value
    if isinstance(value, Mapping):
        return MagicDict(value)
    if isinstance(value, Sequence):
        return MagicList(value)
    raise ValueError(
        "values of type '{0}' are not allowed".format(
            value.__class__.__name__))


# Type normalisation to cater for int/long and str/unicode in Python 2.
NORMALISED_TYPES = {
    bool: bool,
    dict: Mapping,
    float: float,
    int: six.integer_types,
    list: Sequence,  # FIXME: this also matches strings :-(
    str: six.string_types,
}


def generalise_type(t, lookup=NORMALISED_TYPES):
    try:
        return lookup[t]
    except KeyError:
        raise ValueError(
            "type filter must be one of {0}".format(", ".join(
                sorted(t.__name__ for t in lookup))))


class TypeFilteredValueMapping(MutableMapping):
    """A mapping proxy that only handles values of a certain type."""

    __slots__ = ('_mapping', '_type')

    def __init__(self, mapping, type):
        self._mapping = mapping
        self._type = type

    def __getitem__(self, key):
        value = self._mapping[key]
        if not isinstance(value, generalise_type(self._type)):
            raise KeyError(key)
        return value

    def __setitem__(self, key, value):
        if not isinstance(value, generalise_type(self._type)):
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
        normalised_type = generalise_type(self._type)
        for key, value in six.iteritems(self._mapping):
            if isinstance(value, normalised_type):
                yield key

    def __repr__(self):
        return '{0}(mapping={1!r}, type={2})'.format(
            self.__class__.__name__,
            self._mapping,
            self._type.__name__)


# TODO: silent mode


class MagicMapping(Mapping):

    __slots__ = ('_mapping')

    def __init__(self, mapping):
        self._mapping = mapping

    def __getitem__(self, key):

        # String lookups work as with dicts.
        if isinstance(key, six.string_types):
            return self._mapping[key]

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
            if not isinstance(value, generalise_type(sl.stop)):
                raise ValueError("value is not of {0} type: {1!r}".format(
                    sl.stop.__name__, value))
            return value

        # Tuples are a shortcut for deep lookups in nested containers
        # (and not into strings which also can be indexed by number).
        # Examples:
        # - d['a', 0, 'b']
        # - d['a', 0, 'b':str]
        if isinstance(key, tuple):
            path = key
            if not path:
                raise TypeError("path cannot be empty")

            # Anything up to the last component must be either str or
            # int to be valid container lookups. Check this before even
            # trying to evaluate the path to consistently raise
            # TypeError if the path is malformed.
            if not all(isinstance(key, (six.string_types + six.integer_types))
                       for key in path[:-1]):
                raise TypeError(
                    "malformed path (path must contain only str and int): "
                    "{!r}".format(path))
            container = self
            for pos, key in enumerate(path[:-1], 1):
                types_are_correct = (
                    (isinstance(container, MagicDict)
                        and isinstance(key, six.string_types))
                    or (isinstance(container, MagicList)
                        and isinstance(key, six.integer_types)))
                if not types_are_correct:
                    raise KeyError(path[:pos])
                try:
                    container = container[key]
                except (KeyError, IndexError):
                    raise KeyError(path[:pos])

                if not isinstance(container, (MagicDict, MagicList)):
                    # Found something but it's not a container.
                    raise KeyError(path[:pos])

            # Delegate the last lookup (possibly a slice with a type
            # specification) to the nested container.
            try:
                return container[path[-1]]
            except (KeyError, IndexError):
                raise KeyError(path)

        raise TypeError("unsupported key: {!r}".format(key))

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)


class MagicDict(MagicMapping, MutableMapping):
    """
    Dict-like type for for the JSON data model with added magic.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        super(MagicDict, self).__init__({})
        self.update(*args, **kwargs)

    def __repr__(self):
        return repr(self._mapping)

    def __setitem__(self, key, value):
        if not isinstance(key, six.string_types):
            raise TypeError("key must be a string")
        self._mapping[key] = enchant_value(value)

    def __delitem__(self, key):
        if not isinstance(key, six.string_types):
            raise TypeError("key must be a string")
        del self._mapping[key]

    def clear(self):
        # Fast delegation.
        self._mapping.clear()


class MagicSequence(Sequence):

    __slots__ = ('_sequence')

    def __init__(self, sequence):
        self._sequence = sequence

    def __getitem__(self, key):
        return self._sequence[key]

    def __len__(self):
        return len(self._sequence)


class MagicList(MagicSequence, MutableSequence):

    __slots__ = ()

    def __init__(self, *args):
        super(MagicList, self).__init__([])
        if args:
            if len(args) != 1:
                raise TypeError(
                    "expected at most 1 argument, got {0:d}".format(len(args)))
            self.extend(args[0])

    def __repr__(self):
        return repr(self._sequence)

    def __setitem__(self, index, value):
        self._sequence[index] = enchant_value(value)

    def __delitem__(self, index):
        del self._sequence[index]

    def insert(self, index, value):
        self._sequence.insert(index, enchant_value(value))


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
