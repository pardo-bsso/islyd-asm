from .utils import int_to_split_hex


IHEX_EOF = ':00000001FF'
RECORD_TYPE_DATA = 0x00


def line_info_to_ihex(line_info):
    if not line_info.instruction.size:
        return None

    address = int_to_split_hex(line_info.instruction.address)
    opcode = line_info.opcode

    record = [len(opcode), *address, RECORD_TYPE_DATA, *opcode]

    record_sum = sum(record) & 0xFF
    checksum = ((0xFF - record_sum) + 1) & 0xFF

    record.append(checksum)
    record = ''.join('{:02x}'.format(b) for b in record)
    return ':{}'.format(record)
