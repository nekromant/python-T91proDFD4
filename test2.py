import pygatt
from binascii import hexlify
import logging
logging.basicConfig()
logging.getLogger('pygatt').setLevel(logging.DEBUG)
import time
import numpy as np

# The BGAPI backend will attemt to auto-discover the serial device name of the
# attached BGAPI-compatible USB adapter.


package = [0x11, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x11 ]


class t91packet(object):
    data = bytearray([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]);
    def __init__(self, band, tp):
        self.data[0] = tp
        self.band = band

    def set(self, pos, byte):
        self.data[pos] = byte

    def checksum(self):
        self.data[15] = 0;
        cs = 0
        for p in self.data:
            cs = cs + p;
            cs = cs & 0xff;
        self.data[15] = cs;
        self.data = self.data[0:16]

    def dump(self):
        print("sent packet data: %s" % hexlify(self.data))

    def send(self):
        self.checksum()
        self.dump();
        self.band.send_packet(self.data)

class t91band(object):
    CMD_ANTI_LOST_RATE = 80;
    CMD_BIND_SUCCESS = 16;
    CMD_BP_TIMING_MONITOR_CONFIRM = 14;
    CMD_BP_TIMING_MONITOR_DATA = 13;
    CMD_BP_TIMING_MONITOR_SWITCH = 12;
    CMD_CALIBRATION_RATE = 32;
    CMD_DISPLAY_CLOCK = 18;
    CMD_DISPLAY_STYLE = 42;
    CMD_FANWAN = 5;
    CMD_GET_ALARM_CLOCK = 36;
    CMD_GET_ANCS_ON_OFF = 97;
    CMD_GET_BAND_PRESSURE = 20;
    CMD_GET_DEVICE_ELECTRICITY_VALUE = 3;
    CMD_GET_DRINK_TIME = 40;
    CMD_GET_HEART_RATE = 21;
    CMD_GET_PERSONALIZATION_SETTING = 23;
    CMD_GET_SIT_LONG = 38;
    CMD_GET_SLEEP = 68;
    CMD_GET_SPORT = 19;
    CMD_GET_STEP_SOMEDAY_DETAIL = 67;
    CMD_GET_STEP_TODAY = 72;
    CMD_GET_STEP_TOTAL_SOMEDAY = 7;
    CMD_GET_TIME_SETTING = 10;
    CMD_HR_TIMING_MONITOR_CONFIRM = 14;
    CMD_HR_TIMING_MONITOR_DATA = 13;
    CMD_HR_TIMING_MONITOR_SWITCH = 22;
    CMD_INTELL = 9;
    CMD_MSG_GET_HW_AND_FW_VERSION = 147;
    CMD_MSG_NOTIFY = 114;
    CMD_MUTE = 6;
    CMD_ORIENTATION = 41;
    CMD_PHONE_NOTIFY = 17;
    CMD_PUSH_MSG = 114;
    CMD_QUERY_DATA_DISTRIBUTION = 70;
    CMD_RE_BOOT = 8;
    CMD_RE_STORE = -1;
    CMD_SET_ALARM_CLOCK = 35;
    CMD_SET_ANCS_ON_OFF = 96;
    CMD_SET_DEVICE_TIME = 1;
    CMD_SET_DRINK_TIME = 39;
    CMD_SET_PHONE_OS = 4;
    CMD_SET_SIT_LONG = 37;
    CMD_START_HEART_RATE = 105;
    CMD_STOP_HEART_RATE = 106;
    CMD_SWITCH_HEART_RATE = 22;
    CMD_TAKING_PICTURE = 2;
    CMD_TUNE_TIME_DIRECT = 115;
    CMD_TUNE_TIME_INVERSE = 116;

    def send_packet(self, data):
        print(data)
        self.device.char_write_handle(0x0011, data)

    def start_measuring(self, data):
        self.device.char_write_handle(0x0011, self.h2s("69:05:25:00:00:00:00:00:00:00:00:00:00:00:00:93"))


    def display_message(self, icon, message):
        packet = t91packet(self, self.CMD_MSG_NOTIFY);
        packet.data[1] = 0x2 #icon;
        packet.data[2] = 1 #(byte) total;
        packet.data[3] = 1 #(byte) index;
        packet.data[4:4] = bytes(message, encoding='ascii')

        self.send_packet(packet.data)


    def rq_version(self):
        packet = t91packet(self, self.CMD_MSG_GET_HW_AND_FW_VERSION);
        packet.send()

    def rq_find(self):
        packet = t91packet(self, self.CMD_ANTI_LOST_RATE);
        packet.data[1] = 85
        packet.data[2] = 170
        packet.send()

    def rq_orient(self):
        packet = t91packet(self, self.CMD_ORIENTATION)
        packet.send()

    def rq_pressure(self):
        packet = t91packet(self, self.CMD_GET_BAND_PRESSURE)
        packet.data[1]=0xff;
        packet.data[2]=0xff;
        packet.data[4]=2;
        packet.send()

    def start_hr(self, a, b):
        packet = t91packet(self, self.CMD_START_HEART_RATE)
        packet.data[1] = a;
        packet.data[2] = b;
        packet.send()

    def stop_hr(self):
        packet = t91packet(self, self.CMD_STOP_HEART_RATE)
        packet.send()

    def get_steps(self):
        packet = t91packet(self, self.CMD_GET_STEP_TODAY);
        packet.send()

    def enable_notifications(self):
        self.device.char_write_handle(0x000b,  self.h2s("01:00"))
        self.device.char_write_handle(0x000f,  self.h2s("01:00"))
        self.device.char_write_handle(0x00017, self.h2s("01:00"))
        self.device.char_write_handle(0x0001f, self.h2s("01:00"))
        self.device.char_write_handle(0x0002c, self.h2s("01:00"))

    def __init__(self, address):
        self.adapter = pygatt.GATTToolBackend()
        self.adapter.start()
        self.device = self.adapter.connect(address, address_type=pygatt.BLEAddressType.random)
        self.enable_notifications()

    def h2s(self, data):
        """Converts a string of hex numbers separated by a colon (:) to a
        string with the actual byte sequence. This is useful when sending
        commands to PyGattlib, because they can be expressed in the same way as
        wireshark dumps them; in example: ``03:1b:05``. ::

        >>> data = mibanda.h2s("68:65:6c:6c:6f")
        >>> print data
        hello
        """

        if isinstance(data, str):
            data = [int(x, 16) for x in data.split(":")]
            return bytearray(data)


    def notify(self, handle, value):
        """
        handle -- integer, characteristic read handle the data was received on
        value -- bytearray, the data returned in the notification
        """
        print("Received data: %s" % hexlify(value))



band = t91band('FD:4D:FE:86:A2:D3')
#band.display_message(3, "Checking ma")
#band.start_hr(6, 1); // realtime heart rate reporting

#band.rq_find()
#band.start_hr(5, 25); # check & report heart rate
#time.sleep(40);
#band.start_hr(3, 1); # check & report oxygen
band.rq_pressure(); # check & report oxygen
time.sleep(40);
#band.stop_hr()
