def bar(percentage: float, size: int = 40):
    percentage = int(percentage)
    hori_char = '━'
    left_char = '╸'
    pink = (249, 38, 114)
    grey = (58, 58, 58)
    green = (114, 156, 31)
    start_pink = '\033[38;2;%d;%d;%dm' % pink
    start_grey = '\033[38;2;%d;%d;%dm' % grey
    start_green = '\033[38;2;%d;%d;%dm' % green
    reset_color = '\033[39m'
    if percentage >= 100:
        return f'{start_green}{hori_char * size}{reset_color}'
    filled = hori_char * (size * percentage // 100)
    not_filled = hori_char * (size - len(filled) - 1)
    return f'{start_pink}{filled}{left_char}{start_grey}{not_filled}{reset_color}'


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def get_type(schema):
    if schema.get('internalType', '').startswith('struct'):
        postfix = '[]' if schema['internalType'].endswith('[]') else ''
        return '(' + ','.join(get_type(x) for x in schema['components']) + ')' + postfix
    elif schema.get('internalType', '').startswith('enum'):
        return schema['type']
    return schema.get('internalType', schema['type'])
