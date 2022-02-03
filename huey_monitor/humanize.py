from bx_django_utils.humanize.time import human_timedelta


def format_sizeof(num, suffix='', divisor=1000):
    """
    Formats a number (greater than unity) with SI Order of Magnitude
    prefixes.

    >>> format_sizeof(10)
    '10.0'
    >>> format_sizeof(2_000)
    '2.00k'
    >>> format_sizeof(3.5*1024*1024, suffix='Bytes', divisor=1024)
    '3.50MBytes'

    Parameters
    ----------
    num  : float
        Number ( >= 1) to format.
    suffix  : str, optional
        Post-postfix [default: ''].
    divisor  : float, optional
        Divisor between prefixes [default: 1000].

    Returns
    -------
    out  : str
        Number with Order of Magnitude SI unit postfix.

    code borrowed from tqdm (MIT License)
    """
    for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 999.5:
            if abs(num) < 99.95:
                if abs(num) < 9.995:
                    return f'{num:1.2f}' + unit + suffix
                return f'{num:2.1f}' + unit + suffix
            return f'{num:3.0f}' + unit + suffix
        num /= divisor

    return f'{num:3.1f}Y' + suffix


def percentage(num, total):
    """
    >>> percentage(25, 100)
    '25%'
    >>> percentage(33.333, 100)
    '33%'
    """
    frac = num / total
    percentage = frac * 100
    return f'{percentage:.0f}%'


def throughput(num, elapsed_sec, suffix='', divisor=1000) -> str:
    """
    Returns throughput in different format depending if rate is higher or lower than 1

    >>> throughput(3.333, 1)
    '3.33/s'
    >>> throughput(2048, 1, suffix='Bytes', divisor=1024)
    '2.00kBytes/s'
    >>> throughput(4, 250, suffix='subtask')
    '1.0\xa0minutes/subtask'
    """
    if num == 0:
        if suffix:
            return f'0/{suffix}'
        return '0'
    rate = num / elapsed_sec

    if rate > 1:
        rate_str = format_sizeof(rate, suffix=suffix, divisor=divisor)
        return f'{rate_str}/s'

    else:
        duration_str = human_timedelta(1 / rate)
        return f'{duration_str}/{suffix}'
