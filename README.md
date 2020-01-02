# pychip8
A CHIP-8 emulator written in Python

# Usage

To use, you need some CHIP-8 ROMs, which can be downloaded here: https://www.zophar.net/pdroms/chip8/chip-8-games-pack.html. Simply run `main.py` with the path to a CHIP-8 ROM as a positional argument, like so:

```
$ python3 main.py c8games/PONG
2020-01-01 05:55:26 PM - root - INFO - Initializing display
2020-01-01 05:55:26 PM - root - INFO - Initializing sound mixer
2020-01-01 05:55:26 PM - root - INFO - Initialized!
2020-01-01 05:55:26 PM - root - INFO - Loading c8games/PONG
2020-01-01 05:55:26 PM - root - INFO - Loaded c8games/PONG into memory!
2020-01-01 05:55:26 PM - root - INFO - Begin main event loop
```

# Arguments
Of course, there are additional arguments for customization:
```
positional arguments:
  rom_path              Path to CHIP-8 rom to play

optional arguments:
  -h, --help            show this help message and exit
  -r RESOLUTION, --resolution RESOLUTION
                        Window multiplier for window resolution (default 18)
  -p PITCH, --pitch PITCH
                        Pitch in Hz for sound to be played (default 440 Hz)
  -c PX_COLOR, --px-color PX_COLOR
                        Color for pixels in hex (ex. FFFFFF for white)
                        (default DDDDDD)
  -b BG_COLOR, --bg-color BG_COLOR
                        Color for background in hex (ex. 000000 for black)
                        (default 222222)
  -f FRAMERATE, --framerate FRAMERATE
                        Framerate in FPS for gameplay (default 120 FPS)
  -d, --debug           Debug logging (default false)
```

# Installation

To install dependencies, clone the repository and run `pip install -r requirements.txt`.
