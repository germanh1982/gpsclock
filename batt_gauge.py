import smbus

class MAX17040:
    def __init__(self, busnum, addr=0x36):
        self._bus = smbus.SMBus(busnum)
        self._addr = addr

    @property
    def charge(self):
        return int.from_bytes(self._bus.read_i2c_block_data(self._addr, 4, 2), 'big') / 256.0

    @property
    def voltage(self):
        return (int.from_bytes(self._bus.read_i2c_block_data(self._addr, 2, 2), 'big') >> 4) * 1e-3

