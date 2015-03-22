from __future__ import print_function

try:
    # Python 3
    from functools import reduce
    STRING_TYPE = str
except ImportError:
    # Python 2
    STRING_TYPE = basestring  # noqa


_SENTINEL = object()


def walk(obj, parent_first=True):

    # Top down?
    if parent_first:
        yield (), obj

    # For nested objects, the key is the path component.
    if isinstance(obj, dict):
        children = obj.items()

    # For nested lists, the position is the path component.
    elif isinstance(obj, (list, tuple)):
        children = enumerate(obj)

    # Scalar values have no children.
    else:
        children = []

    # Recurse into children
    for key, value in children:
        for child_path, child in walk(value, parent_first):
            yield (key,) + child_path, child

    # Bottom up?
    if not parent_first:
        yield (), obj


def lookup_path(obj, path, default=_SENTINEL):

    if isinstance(path, STRING_TYPE):
        path = path.split('.')

        # Convert integer components into real integers.
        for position, component in enumerate(path):
            try:
                path[position] = int(component)
            except ValueError:
                pass

    try:
        return reduce(lambda x, y: x[y], path, obj)
    except (IndexError, KeyError, TypeError):
        if default is _SENTINEL:
            raise

        return default
