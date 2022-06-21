def listKey(source: list or tuple, key) -> int or None:
    source = {i[0]: i[1] for i in list(source)}

    for i in range(len(list(source.keys()))):
        if list(source.keys())[i] == key:
            return i
    return None


def listToDict(source) -> dict:
    """\
[(12345,[(12345,"data"),(54321,"data2")])]

to

{12345:{12345:"data", 54321:"data2"}}"""
    temp = {}
    source = dict(source)
    for i in list(source.keys()):
        if i not in temp:
            temp[i] = {}
        temp[i].update(dict(source[i]))
    return temp


def dictToList(source: dict) -> list:
    """\
{12345:{12345:"data", 54321:"data2"}}

to

[(12345,[(12345,"data"),(54321,"data2")])]"""
    temp = []
    for i in source.keys():
        temp.append((i, list(source[i].items())))
    return temp
