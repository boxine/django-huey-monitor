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

def format_duration(num):
    """
    Formats a number of seconds into s, min, h or days depending on the duration.

    >>> format_duration(15.525)
    '15.5 s'
    >>> format_duration(115.565)
    '1.9 min'
    >>> format_duration(11115.565)
    '3.1 h'
    >>> format_duration(1111005.565)
    '12.9 days'

    Returns
    -------
    out  : str

    """
    if abs(num)<60:
        return f'{num:1.1f} s'
    elif abs(num)<60*60:
        return f'{num/60:1.1f} min'
    elif abs(num)<60*60*24:
        return f'{num/3600:1.1f} h'
    else:
        return f'{num/3600/24:1.1f} days'



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


def throughput(num, elapsed_sec, suffix='', divisor=1000):
    """
    Returns throughput in different format depending if rate is higher or lower than 1
    
    >>> throughput(3.333, 1)
    '3.33/s'
    >>> throughput(2048, 1, suffix='Bytes', divisor=1024)
    '2.00kBytes/s'
    >>> throughput(4, 250, suffix='subtask')
    '1.1 min/subtask '
    """
    rate = num / elapsed_sec
    
    if rate > 1:
        rate_str = format_sizeof(rate, suffix=suffix, divisor=divisor)
        return f'{rate_str}/s'

    else:
        duration_str = format_duration(1/rate)
        return f'{duration_str}/{suffix}'
