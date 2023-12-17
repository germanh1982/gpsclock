from time import sleep
import datetime
import gpsd
from vfd import VFD, Brightness
from batt_gauge import MAX17040

class Main:
    UPDATE_RATE = 0.01

    def __init__(self):
        RS = 4
        E = 27
        DB7 = 19
        DB6 = 13
        DB5 = 6
        DB4 = 5

        self.batt = MAX17040(1)

        self.disp = VFD(RS, E, DB7, DB6, DB5, DB4, rows=2, cols=24)
        self.disp.initialize()
        self.disp.control(display=1, cursor=0, blink=0)
        self.disp.brightness(Brightness.LOW)

        gpsd.connect()

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
        self.disp.clearbuf()
        self.disp.setpos(0, 0)
        self.disp.write(self.render_datetime())

        self.disp.setpos(1,0)
        self.disp.write(self.render_batt())

        self.disp.update()

    def loop_forever(self):
        while True:
            self.render()
            sleep(self.UPDATE_RATE)

if __name__ == '__main__':
    try:
        with Main() as main:
            main.loop_forever()
    except KeyboardInterrupt:
        pass

