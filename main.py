import argparse
import logging
import os
import struct
import sys

from pychip8 import cpu

def main():
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    parser = argparse.ArgumentParser(
        description='Python CHIP-8 Emulator'
    )

    parser.add_argument(
        'rom_path',
        help='Path to CHIP-8 rom to play'
    )

    parser.add_argument(
        '-r',
        '--resolution',
        dest='resolution',
        help='Window multiplier for window resolution (default 18)',
        type=int,
        default=18
    )

    parser.add_argument(
        '-p',
        '--pitch',
        dest='pitch',
        help='Pitch in Hz for sound to be played (default 440 Hz)',
        type=int,
        default=440
    )

    parser.add_argument(
        '-c',
        '--px-color',
        dest='px_color',
        help='Color for pixels in hex (ex. FFFFFF for white) (default DDDDDD)',
        type=lambda x: struct.unpack('BBB', bytes.fromhex(x)),
        default=(221, 221, 221)
    )

    parser.add_argument(
        '-b',
        '--bg-color',
        dest='bg_color',
        help='Color for background in hex (ex. 000000 for black) (default 222222)',
        type=lambda x: struct.unpack('BBB', bytes.fromhex(x)),
        default=(34, 34, 34)
    )

    parser.add_argument(
        '-f',
        '--framerate',
        dest='framerate',
        help='Framerate in FPS for gameplay (default 120 FPS)',
        type=int,
        default=120
    )

    parser.add_argument(
        '-d',
        '--debug',
        dest='debug',
        help='Debug logging (default false)',
        action='store_true'
    )

    args = parser.parse_args()

    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p',
        level=loglevel
    )

    chip8 = cpu.CPU(
        args.resolution,
        args.pitch,
        args.px_color,
        args.bg_color,
        args.framerate
    )

    chip8.main(args.rom_path)

    return

if __name__ == '__main__':
    main()
