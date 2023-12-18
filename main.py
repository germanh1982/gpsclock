#!/opt/gpsclock/bin/python3
from time import sleep
import datetime
import gpsd
from vfd import BufferedVFD, Brightness, Direction
from batt_gauge import MAX17040
from enum import Enum
from time import monotonic

State = Enum('State', ['BATT', 'GPSPOS'])

class Main:
    UPDATE_RATE = 0.05
    PAGE_DELAY = 5
    SCROLL_INTERVAL = 0.5

    def __init__(self):
        RS = 4
        E = 27
        DB7 = 19
        DB6 = 13
        DB5 = 6
        DB4 = 5

        self.batt = MAX17040(1)

        self.disp = BufferedVFD(RS, E, DB7, DB6, DB5, DB4)
        self.disp.initialize()
        self.disp.control(display=1, cursor=0, blink=0)
        self.disp.brightness(Brightness.LOW)

        gpsd.connect()

        self._state = State.BATT

    def __enter__(self):
        return self

    def __exit__(self, etyp, ev, etb):
        self.disp.control(display=0, cursor=0, blink=0)

    def render_pos(self):
        packet = gpsd.get_current()

        lat = round(packet.lat, 5)
        lon = round(packet.lon, 5)
        lat_post = "S" if lat < 0 else "N"
        lon_post = "W" if lon < 0 else "E"
        lat = abs(lat)
        lon = abs(lon)
        alt = round(packet.alt)

        return f"{lat}{lat_post} {lon}{lon_post} {alt}m"

    def render_batt(self):
        battlevel = round(self.batt.charge, 1)
        battvolt = round(self.batt.voltage, 1)
        return f"BATT {battlevel}% {battvolt}V"

    def render_datetime(self):
        return datetime.datetime.now().strftime('%c')

    def render(self):
        #self.disp.clear()
        self.disp.clear()
        self.disp.setpos(0, 0)
        self.disp.write(self.render_datetime())

        self.disp.setpos(1,0)
        if self._state is State.BATT:
            self.disp.write(self.render_batt())
        elif self._state is State.GPSPOS:
            self.disp.write(self.render_pos())

        self.disp.update()

    def loop_forever(self):
        last_state_change = monotonic()
        last_shift = monotonic()
        while True:
            if monotonic() - last_state_change > self.PAGE_DELAY:
                last_state_change = monotonic()
                if self._state is State.BATT:
                    self._state = State.GPSPOS
                elif self._state is State.GPSPOS:
                    self._state = State.BATT

            if monotonic() - last_shift > self.SCROLL_INTERVAL:
                last_shift = monotonic()
                self.disp.shift_display(Direction.LEFT)

            self.render()
            sleep(self.UPDATE_RATE)

if __name__ == '__main__':
    try:
        with Main() as main:
            main.loop_forever()
    except KeyboardInterrupt:
        pass

