from time import sleep
import datetime
import gps
from vfd import VFD, Brightness

def main():
    RS = 4
    E = 27
    DB7 = 19
    DB6 = 13
    DB5 = 6
    DB4 = 5

    with VFD(RS, E, DB7, DB6, DB5, DB4) as disp:
        disp.control(display=1, cursor=0, blink=0)
        disp.brightness(Brightness.LOW)

        while True:
            disp.home()
            dt = datetime.datetime.now().strftime('%c')
            disp.write(dt)

            sleep(0.01)

if __name__ == '__main__':
    main()

