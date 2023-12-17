import RPi.GPIO as GPIO
from time import sleep
from enum import Enum

class Brightness(Enum):
    HIGH = 0
    LOW = 3

class VFD:
    CMDTIME = 2e-3

    def __init__(self, rs, e, db7, db6, db5, db4, rows, cols):
        self._rs = rs
        self._e = e
        self._db7 = db7
        self._db6 = db6
        self._db5 = db5
        self._db4 = db4

        self._rows = rows
        self._cols = cols
        self._currfb = [' '] * cols * rows
        self.clearbuf()
        self._fbpointer = [0, 0]

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self._rs, GPIO.OUT)
        GPIO.setup(self._e, GPIO.OUT)
        GPIO.setup(self._db7, GPIO.OUT)
        GPIO.setup(self._db6, GPIO.OUT)
        GPIO.setup(self._db5, GPIO.OUT)
        GPIO.setup(self._db4, GPIO.OUT)

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, etyp, ev, etb):
        self.control(display=0, cursor=0, blink=0)

    def __aexit__(self, etyp, ev, etb):
        self.control(display=0, cursor=0, blink=0)

    def _send4(self, rsv, data4):
        GPIO.output(self._rs, rsv)

        GPIO.output(self._db7, data4 >> 3 & 0x1)
        GPIO.output(self._db6, data4 >> 2 & 0x1)
        GPIO.output(self._db5, data4 >> 1 & 0x1)
        GPIO.output(self._db4, data4 & 0x1)

        GPIO.output(self._e, 1)
        GPIO.output(self._e, 0)

    def _send(self, rsv, data8):
        self._send4(rsv, data8 >> 4 & 0xf)
        self._send4(rsv, data8 & 0xf)
        sleep(self.CMDTIME)

    """
    def write(self, string):
        for c in string: self.writechr(c)
    """

    def writechr(self, ch):
        self._send(1, ord(ch))

    def initialize(self):
        self._function_set(i_f=1)
        self._function_set(i_f=1)
        self._function_set(i_f=1)

        self._function_set()
        self.brightness(Brightness.HIGH)
        self.entry_mode_set(idd=1, s=0)
        self.clear()
        self.control(display=1, cursor=0, blink=0)

    def clear(self):
        self._send(0, 0x1)

    def home(self):
        self._send(0, 0x2)

    def clearbuf(self):
        self._newfb = [' '] * len(self._currfb)

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
        addr = row * 0x40 + col
        self._send(0, 0x80 | addr)

    def setpos(self, row, col):
        self._fbpointer = row * self._cols + col

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

            if x % self._cols == 0 or differences[x-1] is None:
                # set position before write
                row = int(x / self._cols)
                col = x % self._cols
                self._cursor_pos(row, col)

            self.writechr(y)

        self._currfb = self._newfb[:]

