import struct

from keycodes.keycodes import Keycode

from protocol.base_protocol import BaseProtocol

AMK_PROTOCOL_PREFIX = 0xFD
AMK_PROTOCOL_OK = 0xAA

AMK_PROTOCOL_GET_VERSION = 0
AMK_PROTOCOL_GET_APC = 1
AMK_PROTOCOL_SET_APC = 2
AMK_PROTOCOL_GET_RT = 3
AMK_PROTOCOL_SET_RT = 4
AMK_PROTOCOL_GET_DKS = 5
AMK_PROTOCOL_SET_DKS = 6
AMK_PROTOCOL_GET_POLL_RATE = 7
AMK_PROTOCOL_SET_POLL_RATE = 8
AMK_PROTOCOL_GET_DOWN_DEBOUNCE = 9
AMK_PROTOCOL_SET_DOWN_DEBOUNCE = 10
AMK_PROTOCOL_GET_UP_DEBOUNCE = 11
AMK_PROTOCOL_SET_UP_DEBOUNCE = 12

DKS_EVENT_0 = 0
DKS_EVENT_1 = 1
DKS_EVENT_2 = 2
DKS_EVENT_3 = 3

DKS_EVENT_MAX = 4
DKS_KEY_MAX = 4

class DksKey:
    def __init__(self):
        self.down_events = ([0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0])
        self.up_events = ([0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0])
        self.keys = ["KC_NO","KC_NO","KC_NO","KC_NO"]
        self.dirty = False

    def is_dirty(self):
        return self.dirty
    
    def is_valid(self):
        for k in self.keys:
            if k != "KC_NO":
                return True
        for t in self.down_events:
            for e in t:
                if e != 0:
                    return True
        for t in self.up_events:
            for e in t:
                if e != 0:
                    return True
        return False
    
    def set_dirty(self, dirty):
        self.dirty = dirty

    def add_key(self, index, key):
        if index < DKS_KEY_MAX:
            if self.keys[index] != key:
                self.keys[index] = key
                self.dirty = True
            return True
        else:
            print("DKS failed to add key: index ={}, key={}".format(index, key))
            return False
    
    def del_key(self, index):
        if self.keys[index] != "KC_NO":
            self.keys[index] = "KC_NO"
            self.dirty = True

    def add_event(self, event, key, down):
        if event >= DKS_EVENT_MAX:
            print("DKS failed to set event: index={}, key={}, down={}".format(event, key, down))
            return False

        evts = self.down_events if down else self.up_events
        if evts[event][key] == 0:
            evts[event][key] = 1
            self.dirty = True
        return True

    def del_event(self, event, key, down):
        if event >= DKS_EVENT_MAX:
            print("DKS failed to clear event: index={}, key={}, down={}".format(event, key, down))
            return False

        evts = self.down_events if down else self.up_events
        if evts[event][key] == 1:
            evts[event][key] = 0
            self.dirty = True
        return True

    def pack_dks(self):
        evts = [0,0,0,0]
        for i in range(DKS_EVENT_MAX):
            for j in range(4):
                if self.down_events[i][j] > 0:
                    evts[i] |= 1 << j
                if self.up_events[i][j] > 0:
                    evts[i] |= 1 << (j+4)
        
        keys = [0,0,0,0]
        for i in range(len(self.keys)):
            keys[i] = Keycode.resolve(self.keys[i])
        
        data = struct.pack(">BBBBHHHH", 
                        evts[0], evts[1], evts[2], evts[3],
                        keys[0], keys[1], keys[2], keys[3])
        return data
    
    def parse(self, data):
        print("Parse DKS")
        for i in range(4):
            print("Event:{:b}".format(data[i]))
            for j in range(4):
                if data[i] & (1<<j) > 0:
                    self.down_events[i][j] = 1
                else:
                    self.down_events[i][j] = 0

                if data[i] & (1<<(j+4)) > 0:
                    self.up_events[i][j] = 1
                else:
                    self.up_events[i][j] = 0

        keys = struct.unpack(">HHHH", data[4:13])
        for i in range(4):
            self.keys[i] = Keycode.serialize(keys[i])
            print("Keys", self.keys[i])


    def clear(self):
        for i in range(len(self.keys)):
            self.keys[i] = "KC_NO"

        for i in range(DKS_EVENT_MAX):
            for j in range(4):
                self.down_events[i][j] = 0
                self.up_events[i][j] = 0

        self.dirty = True
    
    def get_key(self, index):
        if index < len(self.keys):
            return self.keys[index]

        return 0
    
    def is_event_on(self, event, index, down):
        if event < DKS_EVENT_MAX:
            if down:
                if index < 4:
                    return self.down_events[event][index] > 0
            else:
                if index < 4:
                    return self.up_events[event][index] > 0

        return False

    def dump(self):
        print("Dump DKSKey")
        for i in range(4):
            print("Key({}) is {}".format(i, self.keys[i]))

        for i in range(DKS_EVENT_MAX):
            for j in range(4):
                print("Event({}), Down({}) is {:b}".format(i, j, self.down_events[i][j]))
                print("Event({}), Up({}) is {:b}".format(i, j, self.up_events[i][j]))

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
            val = struct.unpack(">H", data[3:5])
            self.amk_apc[(row, col)] = val[0]
            print("AMK protocol: APC={}, row={}, col={}".format(val, row, col))

    def reload_rt(self):
        """ Reload RT information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RT, row, col),
                                retries=20)
            val = struct.unpack(">H", data[3:5])
            self.amk_rt[(row, col)] = val[0]
            print("AMK protocol: RT={}, row={}, col={}".format(val, row, col))

    def reload_dks(self):
        """ Reload DKS information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_DKS, row, col),
                                retries=20)
            dks_data = data[3:15]
            dks = DksKey()
            dks.parse(dks_data)
            self.amk_dks[(row, col)] = dks 
            print("AMK protocol: DKS={}, row={}, col={}".format(dks.pack_dks(), row, col))
    
    def reload_poll_rate(self):
        """ Reload Poll Rate information from keyboard """
        # poll rate
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_POLL_RATE))
        self.amk_poll_rate = data[3]
        print("AMK protocol: poll rate={}, result={}".format(self.amk_poll_rate, data[2]))

    def reload_debounce(self):
        """ Reload Debounce information from keyboard """
        # down debounce
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_DOWN_DEBOUNCE))
        self.amk_down_debounce = data[3]
        print("AMK protocol: down debounce ={}, result={}".format(self.amk_down_debounce, data[2]))
        # up debounce
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_UP_DEBOUNCE))
        self.amk_up_debounce = data[3]
        print("AMK protocol: up debounce ={}, result={}".format(self.amk_up_debounce, data[2]))

        
        
