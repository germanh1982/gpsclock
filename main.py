#!/opt/gpsclock/bin/python3
from time import sleep
import datetime
import gpsd
from vfd import BufferedVFD, Brightness, Direction
from enum import Enum
from time import monotonic
import signal

class Main:
    UPDATE_RATE = 0.05
    PAGE_DELAY = 5
    SCROLL_INTERVAL = 0.5

    def __init__(self):
        self.stopped = False

        RS = 4
        E = 17
        DB4 = 22
        DB5 = 23
        DB6 = 24
        DB7 = 25

        self.disp = BufferedVFD(RS, E, DB7, DB6, DB5, DB4)
        self.disp.initialize()
        self.disp.control(display=1, cursor=0, blink=0)
        self.disp.brightness(Brightness.LOW)

        gpsd.connect()

    def __enter__(self):
        return self

    def __exit__(self, etyp, ev, etb):
        self.exit()

    def exit(self):
        self.disp.control(display=0, cursor=0, blink=0)
        self.stopped = True

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

    def render_datetime(self):
        return datetime.datetime.now().strftime('%c')

    def render(self):
        self.disp.clear()
        self.disp.setpos(0, 0)
        self.disp.write(self.render_datetime())

        self.disp.setpos(1,0)
        self.disp.write(self.render_pos())

        self.disp.update()

    def loop_forever(self):
        last_state_change = monotonic()
        last_shift = monotonic()
        while not self.stopped:
            if monotonic() - last_shift > self.SCROLL_INTERVAL:
                last_shift = monotonic()
                self.disp.shift_display(Direction.LEFT)

            self.render()
            sleep(self.UPDATE_RATE)

if __name__ == '__main__':
    main = Main()

    try:
        with main:
            def sigterm_handler(signum, stackframe):
                main.exit()
            signal.signal(signal.SIGTERM, sigterm_handler)
    
            main.loop_forever()
    except KeyboardInterrupt:
        pass

