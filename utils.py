import os
import magic

FILE_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif'
}


def file_type(path: str):
    filename, ext = os.path.splitext(path)

    if ext in FILE_TYPES:
        return FILE_TYPES[ext]

    return magic.Magic(mime=True).from_file(path)


DEPTHS = {'1': 1, 'L': 8, 'P': 8, 'RGB': 24, 'RGBA': 32, 'CMYK': 32, 'YCbCr': 24, 'I': 32, 'F': 32}


def mode_to_depth(mode: str):
    return DEPTHS[mode]