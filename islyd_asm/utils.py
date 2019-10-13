def int_to_split_hex(value):
    """ Given an integer converts it into a tuple of hex digits """
    parsed = int(value)
    hi = (parsed >> 8) & 0xFF
    lo = parsed & 0xFF
    return [hi, lo]
