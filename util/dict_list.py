def dictToList(source: dict) -> list:
    """
    Convert a dictionary to a list of tuples.
    """
    return list(source.items())


def listToDict(source: list) -> dict:
    """
    Convert a list of tuples to a dictionary.
    """
    return {item[0]: item[1] for item in source}


def listKey(source: list or tuple, key) -> int or None:
    source = {i[0]: i[1] for i in list(source)}

    for i in range(len(list(source.keys()))):
        if list(source.keys())[i] == key:
            return i
    return None
