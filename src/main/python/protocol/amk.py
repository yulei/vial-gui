import struct

from keycodes.keycodes import Keycode
from protocol.base_protocol import BaseProtocol
from protocol.constants import CMD_VIA_MACRO_GET_COUNT, CMD_VIA_MACRO_GET_BUFFER_SIZE, CMD_VIA_MACRO_GET_BUFFER, \
    CMD_VIA_MACRO_SET_BUFFER, BUFFER_FETCH_CHUNK, VIAL_PROTOCOL_ADVANCED_MACROS
from unlocker import Unlocker
from util import chunks

AMK_PROTOCOL_PREFIX = 0xFD
AMK_PROTOCOL_OK = 0xAA

AMK_PROTOCOL_GET_VERSION = 0
AMK_PROTOCOL_GET_APC = 1
AMK_PROTOCOL_SET_APC = 2
AMK_PROTOCOL_GET_RT = 3
AMK_PROTOCOL_SET_RT = 4
AMK_PROTOCOL_GET_DKS = 5
AMK_PROTOCOL_SET_DKS = 6

class ProtocolAmk(BaseProtocol):

    def amk_protocol_version(self):
        """ Get the version of AMK protocol """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_VERSION), retries=20)
        print("AMK protocol:", data[2])
        return data[2]

    def reload_apc(self):
        """ Reload APC information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_APC, row, col),
                                retries=20)
            val = data[3]*256+data[4]
            self.amk_apc[(row, col)] = val
            print("AMK protocol: APC={}, row={}, col={}".format(val, row, col))

    def reload_rt(self):
        """ Reload RT information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RT, row, col),
                                retries=20)
            val = data[3]*256+data[4]
            self.amk_rt[(row, col)] = val
            print("AMK protocol: RT={}, row={}, col={}".format(val, row, col))

    def reload_dks(self):
        print("DKS loading: todo")
