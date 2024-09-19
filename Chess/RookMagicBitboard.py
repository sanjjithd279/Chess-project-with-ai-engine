'''
A file to generate rook moves based on the magic bitboard
testing stage
'''

# Simple magic numbers for each square on the chessboard (for rooks)
ROOK_MAGIC_NUMBERS = [
    0xA8002C000108020, 0x6C00049B0002001, 0x100200010090040, 0x2480041000800801,
    0x280028004000800, 0x900410008040022, 0x280020001001080, 0x2880002041000080,
    0xA000800080400034, 0x4808020004000, 0x2290802004801000, 0x411000D00100020,
    0x402800800040080, 0xB000401004208, 0x2409000100040200, 0x1002100004082,
    0x4084100010010C0, 0x401201400080080, 0x410010004200, 0x140081040004008,
    0x900100410008040, 0x8000400801980, 0x100030008010008, 0x801000802000,
    0x402000400808020, 0x2001101000801, 0x8040002811040200, 0x220008400840012,
    0x20484000420020, 0x180900008020420, 0x1001048200020, 0x100088020040800,
    0x40080900200080, 0x800008041000C0, 0x20002002005000C0, 0x4000040840402001,
    0x2400200041000400, 0x100040080080080, 0x8000800041000200, 0x200200080100040,
    0x1002000100080410, 0x8002000200840100, 0x8004100020820201, 0x200800400880200,
    0x400020804080200, 0x2801808080204000, 0x1204104000840080, 0x4000C02008208400,
    0x1000040080840420, 0x8000800080401000, 0x1040080044101002, 0x8084000040008080,
    0x20800400800400, 0x2400400080012080, 0x1000010020402004, 0x8020004000400,
    0x800820000820008, 0x400200040000210, 0x40100400008000, 0x400080200080800,
    0x200040000008020, 0x2080010002008080, 0x1001000200008020, 0x1080000080204008
]
def rook_occupancy_mask(square):
    rank = square // 8
    file = square % 8
    mask = 0

    # Horizontal mask (rank)
    for i in range(8):
        if i != file:
            mask |= (1 << (rank * 8 + i))

    # Vertical mask (file)
    for i in range(8):
        if i != rank:
            mask |= (1 << (i * 8 + file))

    return mask


def generate_rook_attack_table(square, magic_number):
    occupancy_mask = rook_occupancy_mask(square)
    num_relevant_bits = bin(occupancy_mask).count('1')

    attack_table_size = 1 << num_relevant_bits  # Calculate the size of the attack table
    attack_table = [0] * attack_table_size      # Initialize the attack table

    for index in range(attack_table_size):
        occupancy = index_to_occupancy(index, occupancy_mask)
        magic_index = get_magic_index(occupancy, magic_number, num_relevant_bits)  # Get magic index

        # Magic index is guaranteed to be in bounds due to the masking in get_magic_index
        attack_table[magic_index] = compute_rook_attacks(square, occupancy)

    return attack_table



def index_to_occupancy(index, mask):
    occupancy = 0
    mask_bits = bin(mask)[2:][::-1]
    index_bits = bin(index)[2:][::-1]

    for i, bit in enumerate(mask_bits):
        if bit == '1':
            if i < len(index_bits) and index_bits[i] == '1':
                occupancy |= (1 << i)
    return occupancy

def get_magic_index(occupancy, magic_number, num_relevant_bits):
    # Multiply the occupancy by the magic number, shift right, and apply a mask
    return ((occupancy * magic_number) >> (64 - num_relevant_bits)) & ((1 << num_relevant_bits) - 1)



def compute_rook_attacks(square, occupancy):
    attacks = 0
    # Add sliding attacks in 4 directions (left, right, up, down)
    # Stop sliding when hitting an occupied square
    # Left
    for i in range((square % 8) - 1, -1, -1):
        attacks |= (1 << ((square // 8) * 8 + i))
        if occupancy & (1 << ((square // 8) * 8 + i)):  # Stop on occupied
            break
    # Right
    for i in range((square % 8) + 1, 8):
        attacks |= (1 << ((square // 8) * 8 + i))
        if occupancy & (1 << ((square // 8) * 8 + i)):
            break
    # Up
    for i in range((square // 8) - 1, -1, -1):
        attacks |= (1 << (i * 8 + square % 8))
        if occupancy & (1 << (i * 8 + square % 8)):
            break
    # Down
    for i in range((square // 8) + 1, 8):
        attacks |= (1 << (i * 8 + square % 8))
        if occupancy & (1 << (i * 8 + square % 8)):
            break

    return attacks
