from operator import attrgetter
from typing import Any, Iterable, T, Optional


class _MissingSentinel:
    def __eq__(self, other: Any) -> bool:
        return False

    def __hash__(self) -> int:
        return 0

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "..."


MISSING: Any = _MissingSentinel()


def get(iterable: Iterable[T], **attrs: Any) -> Optional[T]:
    """
    Get an element from an iterable that matches the attributes.
    :param iterable: The iterable to search.
    :param attrs: The attributes to match.
    :return: The element that matches the attributes.
    """
    # global -> local
    _all = all
    attrget = attrgetter

    # Special case the single element call
    if len(attrs) == 1:
        k, v = attrs.popitem()
        pred = attrget(k.replace("__", "."))
        for elem in iterable:
            if pred(elem) == v:
                return elem
        return None

    converted = [(attrget(attr.replace("__", ".")), value) for attr, value in attrs.items()]

    for elem in iterable:
        if _all(pred(elem) == value for pred, value in converted):
            return elem
    return None
