import RPi.GPIO as GPIO
from time import sleep
from enum import Enum

class Brightness(Enum):
    HIGH = 0
    LOW = 3

class Direction(Enum):
    LEFT = 0
    RIGHT = 1

class NoritakeCharVFD:
    CMDTIME = 2e-3 # time to complete a command
    LINE_OFFSET = 64 # this is the offset between the first and second line in the HD44780 DDRAM memory mapping
    LINES = 2 # number of framebuffer lines, also defined by the driver memory map.

    def __init__(self, rs, e, db7, db6, db5, db4):
        self._rs = rs
        self._e = e
        self._db7 = db7
        self._db6 = db6
        self._db5 = db5
        self._db4 = db4

        # setup LCD pins
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self._rs, GPIO.OUT)
        GPIO.setup(self._e, GPIO.OUT)
        GPIO.setup(self._db7, GPIO.OUT)
        GPIO.setup(self._db6, GPIO.OUT)
        GPIO.setup(self._db5, GPIO.OUT)
        GPIO.setup(self._db4, GPIO.OUT)

        self.initialize()

    def initialize(self):
        """ Initialize display. """
        self._function_set(i_f=1)
        self._function_set(i_f=1)
        self._function_set(i_f=1)

        self._function_set()
        self.brightness(Brightness.HIGH)
        self.entry_mode_set(idd=1, s=0)
        self.clear_screen()
        self.control(display=1, cursor=0, blink=0)

    def _send4(self, rsv, data4):
        """ Send one nibble (LSB of data). """
        GPIO.output(self._rs, rsv)

        GPIO.output(self._db7, data4 >> 3 & 0x1)
        GPIO.output(self._db6, data4 >> 2 & 0x1)
        GPIO.output(self._db5, data4 >> 1 & 0x1)
        GPIO.output(self._db4, data4 & 0x1)

        GPIO.output(self._e, 1)
        GPIO.output(self._e, 0)

    def _send(self, rsv, data8):
        """ Send an 8-bit command. """
        self._send4(rsv, data8 >> 4 & 0xf)
        self._send4(rsv, data8 & 0xf)
        sleep(self.CMDTIME)

    def shift_display(self, direction):
        """ Display shift. """
        self._send(0, 0x10 | 1 << 3 | direction.value << 2)

    def writechr(self, ch):
        """ Write single character to current cursor position. """
        self._send(1, ord(ch))

    def clear_screen(self):
        self._send(0, 0x1) # display clear

    def home(self):
        self._send(0, 0x2) # send cursor home

    def entry_mode_set(self, idd, s):
        self._send(0, 0x4 | idd << 1 | s)

    def control(self, display, cursor, blink):
        self._send(0, 0x8 | display << 2 | cursor << 1 | blink)

    def _function_set(self, i_f=0):
        self._send4(0, 0x2 | i_f << 4)

    def brightness(self, brightness):
        self._function_set()
        self._send4(0, 0x20)
        self._send(1, brightness.value)

    def _cursor_pos(self, row, col):
        addr = self.LINE_OFFSET * row + col
        self._send(0, 0x80 | addr)

class BufferedVFD(NoritakeCharVFD):
    DDRAM_WIDTH = 40 # number of usable 'virtual' characters on each line (with scrolling)
    LINES = 2 # number of framebuffer lines, also defined by the driver memory map.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # display frame buffers
        self._currfb = [' '] * self.DDRAM_WIDTH * self.LINES
        self._newfb = [' '] * len(self._currfb)
        self._fbpointer = [0, 0] # next character position

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, etyp, ev, etb):
        self.control(display=0, cursor=0, blink=0) # turn off display on exit

    def clear(self):
        self._newfb = [' '] * len(self._currfb)

    def setpos(self, row, col):
        self._fbpointer = self.DDRAM_WIDTH * row + col

    def write(self, st):
        fr = self._fbpointer
        to = fr + len(st)
        self._newfb[fr:to] = list(st)
        self._fbpointer = to

    def update(self):
        differences = [None] * len(self._currfb)
        # find what to update
        for x in range(len(self._currfb)):
            if self._currfb[x] != self._newfb[x]:
                differences[x] = self._newfb[x]

        # update character positions that changed
        for x, y in enumerate(differences):
            if y is None:
                continue

            if x % self.DDRAM_WIDTH == 0 or differences[x-1] is None:
                # set position before write
                row = int(x / self.DDRAM_WIDTH)
                col = x % self.DDRAM_WIDTH
                self._cursor_pos(row, col)

            self.writechr(y)

        self._currfb = self._newfb[:]

