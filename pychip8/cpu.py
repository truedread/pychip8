import contextlib
import logging
import os
import random
import sys

import numpy

from pychip8.pixel import Pixel
from pychip8.utils import KEY_MAP, FONTS, CHIP8_WIDTH, CHIP8_HEIGHT

with contextlib.redirect_stdout(None):
    import pygame
    import pygame.locals


class CPU(object):
    def __init__(self, window_multiplier, pitch, px_color, bg_color, fps):
        self.logger = logging.getLogger()
        self.window_multiplier = window_multiplier
        self.bg_color = bg_color
        self.fps = fps

        self.funcmap = {
            0x0000: lambda: None,
            0x00E0: self._00E0,
            0x00EE: self._00EE,
            0x1000: self._1NNN,
            0x2000: self._2NNN,
            0x3000: self._3XKK,
            0x4000: self._4XKK,
            0x5000: self._5XY0,
            0x6000: self._6XKK,
            0x7000: self._7XKK,
            0x8000: self._8XY0,
            0x8001: self._8XY1,
            0x8002: self._8XY2,
            0x8003: self._8XY3,
            0x8004: self._8XY4,
            0x8005: self._8XY5,
            0x8006: self._8XY6,
            0x8007: self._8XY7,
            0x800E: self._8XYE,
            0x9000: self._9XY0,
            0xA000: self._ANNN,
            0xC000: self._CXKK,
            0xD000: self._DXYN,
            0xE09E: self._EX9E,
            0xE0A1: self._EXA1,
            0xF007: self._FX07,
            0xF00A: self._FX0A,
            0xF015: self._FX15,
            0xF018: self._FX18,
            0xF01E: self._FX1E,
            0xF029: self._FX29,
            0xF033: self._FX33,
            0xF055: self._FX55,
            0xF065: self._FX65
        }

        self.key_inputs = bytearray(16)
        self.display_buffer = bytearray(CHIP8_WIDTH * CHIP8_HEIGHT)
        self.memory = bytearray(4096)
        self.gpio = bytearray(16)

        self.memory[0:len(FONTS)] = FONTS  # load fonts into memory

        self.sound_timer = 0
        self.delay_timer = 0
        self.opcode = 0
        self.index = 0
        self.should_draw = False

        self.program_counter = 0x200
        self.stack = []

        self.logger.info('Initializing display')
        self.screen = pygame.display.set_mode((
            CHIP8_WIDTH * self.window_multiplier,
            CHIP8_HEIGHT * self.window_multiplier
        ))

        pygame.display.set_caption('Python CHIP-8 Emulator')
        image_surf = pygame.image.load('pychip8/chip8.ico')
        pygame.display.set_icon(image_surf.convert_alpha())

        self.clock = pygame.time.Clock()
        self.pixel = Pixel(self.window_multiplier, px_color)

        self.logger.info('Initializing sound mixer')
        sample_rate = 44100
        pygame.mixer.init(sample_rate, -16, 1)

        arr = []
        for sample in range(sample_rate):
            arr.append(4096 * numpy.sin(2 * numpy.pi * pitch * sample / sample_rate))

        arr = numpy.array(arr).astype(numpy.int16)
        self.sound = pygame.sndarray.make_sound(arr)
        self.logger.info('Initialized!')

    def main(self, rom_path):
        self.load_rom(rom_path)

        self.logger.info('Begin main event loop')
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                    else:
                        self.on_key_press(event.key)
                if event.type == pygame.KEYUP:
                    self.on_key_release(event.key)

            self.cycle()
            self.draw()

        self.logger.info('Quitting')
        pygame.quit()

        self.logger.info('Closed pygame window')
        sys.exit()

    def cycle(self):
        self.opcode = (self.memory[self.program_counter] << 8) | \
                       self.memory[self.program_counter + 1]

        self.vx = (self.opcode & 0x0F00) >> 8
        self.vy = (self.opcode & 0x00F0) >> 4
        self.program_counter += 2

        extracted_op = self.opcode & 0xF000
        if extracted_op == 0x0000 or extracted_op == 0xE000 or extracted_op == 0xF000:
            extracted_op = self.opcode & 0xF0FF
        elif extracted_op == 0x8000:
            extracted_op = self.opcode & 0xF00F

        method = self.funcmap.get(extracted_op)
        if not method:
            self.logger.error('Unknown instruction %X', self.opcode)
            raise ValueError('Unknown instruction %X' % self.opcode)
        else:
            method()

        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
            if self.sound_timer == 0:
                self.sound.play(maxtime=100)

    def draw(self):
        if self.should_draw:
            self.screen.fill(self.bg_color)
            for pixel, drawn in enumerate(self.display_buffer):
                if drawn:
                    self.screen.blit(
                        self.pixel.surf,
                        (
                            pixel % CHIP8_WIDTH * self.window_multiplier,
                            pixel // CHIP8_WIDTH * self.window_multiplier
                        )
                    )
            self.logger.debug('Updating display')
            pygame.display.update()
            self.clock.tick(self.fps)
            self.should_draw = False

    def get_key(self):
        try:
            return next(i for i, v in enumerate(self.key_inputs) if v == 1)
        except StopIteration:
            return -1

    def load_rom(self, rom_path):
        self.logger.info('Loading %s', rom_path)
        pygame.display.set_caption(os.path.split(rom_path)[-1])
        binary = bytearray(open(rom_path, 'rb').read())
        self.memory[self.program_counter:len(binary)] = binary
        self.logger.info('Loaded %s into memory!', rom_path)

    def on_key_press(self, symbol):
        self.logger.debug('Key pressed: %r', symbol)
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 1

    def on_key_release(self, symbol):
        self.logger.debug('Key released: %r', symbol)
        if symbol in KEY_MAP.keys():
            self.key_inputs[KEY_MAP[symbol]] = 0

    def _00E0(self):
        self.logger.debug('Clearing display')
        self.display_buffer = bytearray(CHIP8_WIDTH * CHIP8_HEIGHT)
        self.should_draw = True

    def _00EE(self):
        self.logger.debug('Returning from subroutine')
        self.program_counter = self.stack.pop()

    def _1NNN(self):
        nnn = self.opcode & 0x0FFF
        self.logger.debug('Jumping to location %X', nnn)
        self.program_counter = nnn

    def _2NNN(self):
        nnn = self.opcode & 0x0FFF
        self.logger.debug('Calling subroutine at %X', nnn)
        self.stack.append(self.program_counter)
        self.program_counter = nnn

    def _3XKK(self):
        kk = self.opcode & 0x00FF
        self.logger.debug('Skipping instruction if Vx == %d', kk)
        if self.gpio[self.vx] == kk:
            self.program_counter += 2

    def _4XKK(self):
        kk = self.opcode & 0x00FF
        self.logger.debug('Skipping instruction if Vx != %d', kk)
        if self.gpio[self.vx] != kk:
            self.program_counter += 2

    def _5XY0(self):
        self.logger.debug('Skipping instruction if Vx == Vy')
        if self.gpio[self.vx] == self.gpio[self.vy]:
            self.program_counter += 2

    def _6XKK(self):
        kk = self.opcode & 0x00FF
        self.logger.debug('Setting Vx to %d', kk)
        self.gpio[self.vx] = kk

    def _7XKK(self):
        kk = self.opcode & 0x00FF
        self.logger.debug('Setting Vx to Vx + %d', kk)
        _sum = self.gpio[self.vx] + kk
        self.gpio[self.vx] = _sum & 0xFF

    def _8XY0(self):
        self.logger.debug('Setting Vx to Vy')
        self.gpio[self.vx] = self.gpio[self.vy]

    def _8XY1(self):
        self.logger.debug('Setting Vx to Vx | Vy')
        self.gpio[self.vx] |= self.gpio[self.vy]

    def _8XY2(self):
        self.logger.debug('Setting Vx to Vx & Vy')
        self.gpio[self.vx] &= self.gpio[self.vy]

    def _8XY3(self):
        self.logger.debug('Setting Vx to Vx ^ Vy')
        self.gpio[self.vx] ^= self.gpio[self.vy]

    def _8XY4(self):
        self.logger.debug('Adding Vy to Vx, setting carry flag if necessary')
        self.gpio[0xF] = 0
        _sum = self.gpio[self.vx] + self.gpio[self.vy]
        if _sum > 0xFF:
            self.gpio[0xF] = 1
        self.gpio[self.vx] = _sum & 0xFF

    def _8XY5(self):
        self.logger.debug('Subtracting Vy from Vx, setting carry flag if necessary')
        self.gpio[0xF] = 1
        if self.gpio[self.vy] > self.gpio[self.vx]:
            self.gpio[0xF] = 0
        self.gpio[self.vx] = (self.gpio[self.vx] - self.gpio[self.vy]) & 0xFF

    def _8XY6(self):
        self.logger.debug('Shifting Vx right one, setting carry flag to LSB of Vx pre-shift')
        self.gpio[0xF] = self.gpio[self.vx] & 0x0001
        self.gpio[self.vx] = (self.gpio[self.vx] >> 1) & 0xFF
        # self.gpio[self.vx] = (self.gpio[self.vy] >> 1) & 0xFF

    def _8XY7(self):
        self.logger.debug('Setting Vx to Vy - Vx, setting carry flag if necessary')
        self.gpio[0xF] = 1
        if self.gpio[self.vx] > self.gpio[self.vy]:
            self.gpio[0xF] = 0
        self.gpio[self.vx] = (self.gpio[self.vy] - self.gpio[self.vx]) & 0xFF

    def _8XYE(self):
        self.logger.debug('Shifting Vx let by one, setting carry flag to MSB of Vx pre-shift')
        self.gpio[0xF] = (self.gpio[self.vx] & 0x00F0) >> 7
        self.gpio[self.vx] = (self.gpio[self.vx] << 1) & 0xFF
        # self.gpio[self.vx] = (self.gpio[self.vy] << 1) & 0xFF

    def _9XY0(self):
        self.logger.debug('Skipping instruction if Vx != Vy')
        if self.gpio[self.vx] != self.gpio[self.vy]:
            self.program_counter += 2

    def _ANNN(self):
        nnn = self.opcode & 0x0FFF
        self.logger.debug('Setting register I to %X', nnn)
        self.index = nnn

    def _CXKK(self):
        kk = self.opcode & 0x00FF
        rand = random.randrange(255)
        self.logger.debug('Setting Vx to random byte %X & %X', rand, kk)
        self.gpio[self.vx] = rand & kk

    def _DXYN(self):
        self.logger.debug('Drawing sprite')
        self.gpio[0xF] = 0 # set VF carry flag to 0
        x = self.gpio[self.vx] & 0xFF
        y = self.gpio[self.vy] & 0xFF
        height = self.opcode & 0x000F
        row = 0

        '''data = self.memory[self.index:self.index + height]
        for row in range(height):
            loc = ((y + 1 + row) * CHIP8_WIDTH) - x - 1
            before = self.display_buffer[loc]
            self.display_buffer[loc] ^= data[0]
            if self.display_buffer[loc] == 0 and before == 1:
                self.gpio[0xF] = 1
            else:
                self.gpio[0xF] = 0'''

        while row < height:
            curr_row = self.memory[row + self.index]
            pixel_offset = 0
            while pixel_offset < 8:
                pixel_offset += 1
                if (y + row) >= CHIP8_HEIGHT:
                    y -= CHIP8_HEIGHT
                    # continue
                if (x + pixel_offset - 1) >= CHIP8_WIDTH:
                    # x -= CHIP8_WIDTH
                    continue
                loc = x + pixel_offset - 1 + ((y + row) * CHIP8_WIDTH)
                mask = 1 << 8-pixel_offset
                curr_pixel = (curr_row & mask) >> (8-pixel_offset)
                before = self.display_buffer[loc]
                self.display_buffer[loc] ^= curr_pixel
                if self.display_buffer[loc] == 0 and before == 1:
                    self.gpio[0xF] = 1
                else:
                    self.gpio[0xF] = 0
            row += 1
        self.should_draw = True

    def _EX9E(self):
        self.logger.debug('Skipping instruction if the key stored in Vx is pressed')
        key = self.gpio[self.vx] & 0xF
        if self.key_inputs[key] == 1:
            self.program_counter += 2

    def _EXA1(self):
        self.logger.debug('Skipping instruction if the key stored in Vx isn\'t pressed')
        key = self.gpio[self.vx] & 0xF
        if self.key_inputs[key] == 0:
            self.program_counter += 2

    def _FX07(self):
        self.logger.debug('Setting Vx to delay timer')
        self.gpio[self.vx] = self.delay_timer

    def _FX0A(self):
        self.logger.debug('Waiting for key press and storing value of key into Vx')
        key = self.get_key()
        if key >= 0:
            self.gpio[self.vx] = key
        else:
            self.program_counter -= 2

    def _FX15(self):
        self.logger.debug('Setting delay timer to Vx')
        self.delay_timer = self.gpio[self.vx]

    def _FX18(self):
        self.logger.debug('Setting sound timer to Vx')
        self.sound_timer = self.gpio[self.vx]

    def _FX1E(self):
        self.logger.debug('Setting I to I + Vx')
        self.index += self.gpio[self.vx]

    def _FX29(self):
        self.logger.debug('Setting register I to location of sprite for Vx')
        self.index = (5 * self.gpio[self.vx]) & 0xFFF

    def _FX33(self):
        self.logger.debug('Storing BCD representation of Vx in I, I+1, and I+2')
        self.memory[self.index] = self.gpio[self.vx] // 100 % 10
        self.memory[self.index + 1] = self.gpio[self.vx] // 10 % 10
        self.memory[self.index + 2] = self.gpio[self.vx] % 10

    def _FX55(self):
        self.logger.debug('Propogating memory with registers V0 through Vx starting at I')
        self.memory[self.index:(self.index + self.vx + 1)] = self.gpio[0:self.vx + 1]
        # self.index += self.vx + 1

    def _FX65(self):
        self.logger.debug('Propogating registers V0 through Vx with memory starting at I')
        self.gpio[0:self.vx + 1] = self.memory[self.index:(self.index + self.vx + 1)]
        # self.index += self.vx + 1
