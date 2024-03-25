import struct

from keycodes.keycodes import Keycode

from protocol.base_protocol import BaseProtocol

AMK_VERSION = "0.3.0"

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
AMK_PROTOCOL_GET_NKRO = 13
AMK_PROTOCOL_SET_NKRO = 14
AMK_PROTOCOL_GET_POLE = 15
AMK_PROTOCOL_SET_POLE = 16
AMK_PROTOCOL_GET_RT_SENS = 17
AMK_PROTOCOL_SET_RT_SENS = 18
AMK_PROTOCOL_GET_TOP_SENS = 19
AMK_PROTOCOL_SET_TOP_SENS = 20
AMK_PROTOCOL_GET_BTM_SENS = 21
AMK_PROTOCOL_SET_BTM_SENS = 22
AMK_PROTOCOL_GET_APC_SENS = 23
AMK_PROTOCOL_SET_APC_SENS = 24
AMK_PROTOCOL_GET_NOISE_SENS = 25
AMK_PROTOCOL_SET_NOISE_SENS = 26

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

    def update_inner_key(self, index, key):
        if index >= DKS_KEY_MAX:
            return

        if not Keycode.is_basic(key):
            return

        if not Keycode.is_mask(self.keys[index]):
            return

        kc = Keycode.find_outer_keycode(self.keys[index])
        if kc is None:
            return
        
        keycode = kc.qmk_id.replace("(kc)", "({})".format(key))
        self.keys[index] = keycode
        self.dirty = True

        #print("DKS keys: index={}, code={}".format(index, keycode))

    def add_key(self, index, key):
        if index < DKS_KEY_MAX:
            if self.keys[index] != key:
                self.keys[index] = key
                self.dirty = True
            return True
        else:
            #print("DKS failed to add key: index ={}, key={}".format(index, key))
            return False
    
    def del_key(self, index):
        if self.keys[index] != "KC_NO":
            self.keys[index] = "KC_NO"
            self.dirty = True

    def add_event(self, event, key, down):
        if event >= DKS_EVENT_MAX:
            #print("DKS failed to set event: index={}, key={}, down={}".format(event, key, down))
            return False

        evts = self.down_events if down else self.up_events
        if evts[event][key] == 0:
            evts[event][key] = 1
            self.dirty = True
        return True

    def del_event(self, event, key, down):
        if event >= DKS_EVENT_MAX:
            #print("DKS failed to clear event: index={}, key={}, down={}".format(event, key, down))
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
    
    def save(self):
        dks = {}
        dks["down"] = self.down_events
        dks["up"] = self.up_events
        dks["codes"] = self.keys
        return dks

    def load(self, dks):
        for i in range(len(self.down_events)):
            for j in range(len(self.down_events[i])):
                self.down_events[i][j] = dks["down"][i][j]

        for i in range(len(self.up_events)):
            for j in range(len(self.up_events[i])):
                self.down_events[i][j] = dks["up"][i][j]

        for i in range(len(self.keys)):
            self.keys[i] = dks["codes"][i]

    def is_same(self, dks):
        for i in range(len(self.down_events)):
            for j in range(len(self.down_events[i])):
                if self.down_events[i][j] != dks["down"][i][j]:
                    return False

        for i in range(len(self.up_events)):
            for j in range(len(self.up_events[i])):
                if self.down_events[i][j] != dks["up"][i][j]:
                    return False

        for i in range(len(self.keys)):
            if self.keys[i] != dks["codes"][i]:
                return False

        return True

    def parse(self, data):
        #print("Parse DKS")
        for i in range(4):
            #print("Event:{:b}".format(data[i]))
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
            #print("Keys", self.keys[i])


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
        return
        #print("Dump DKSKey")
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
        #print("AMK protocol:", data[2])
        return data[2]

    def reload_apc(self):
        """ Reload APC information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_APC, row, col),
                                retries=20)
            val = struct.unpack(">H", data[3:5])
            self.amk_apc[(row, col)] = val[0]
            #print("AMK protocol: APC={}, row={}, col={}".format(val, row, col))

    def reload_rt(self):
        """ Reload RT information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RT, row, col),
                                retries=20)
            val = struct.unpack(">H", data[3:5])[0]
            cont = True if val & 0x8000 > 0 else False
            down = (val & 0x0FC0) >> 6
            up = val & 0x003F
            rt = {"cont": cont, "down": down, "up": up}

            self.amk_rt[(row, col)] = rt
            #print("AMK protocol: RT={}, row={}, col={}".format(val, row, col))

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
            #print("AMK protocol: DKS={}, row={}, col={}".format(dks.pack_dks(), row, col))
    
    def reload_poll_rate(self):
        """ Reload Poll Rate information from keyboard """
        # poll rate
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_POLL_RATE))
        self.amk_poll_rate = data[3]
        #print("AMK protocol: poll rate={}, result={}".format(self.amk_poll_rate, data[2]))

    def reload_debounce(self):
        """ Reload Debounce information from keyboard """
        # down debounce
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_DOWN_DEBOUNCE))
        self.amk_down_debounce = data[3]
        #print("AMK protocol: down debounce ={}, result={}".format(self.amk_down_debounce, data[2]))
        # up debounce
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_UP_DEBOUNCE))
        self.amk_up_debounce = data[3]
        #print("AMK protocol: up debounce ={}, result={}".format(self.amk_up_debounce, data[2]))
    
    def reload_nkro(self):
        """ Reload NKRO information from keyboard """
        #nkro  
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_NKRO))
        self.amk_nkro = True if data[3] > 0 else False
        #print("AMK protocol: NKRO={}, result={}".format(self.amk_nkro, data[2]))

    def reload_pole(self):
        """ Reload Magnetic pole information from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_POLE))
        self.amk_pole = True if data[3] > 0 else False

    def reload_rt_sensitivity(self):
        """ Reload RT sensitivity setting from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RT_SENS))
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_rt_sens = data[3]
        #print("AMK protocol: RT sensitivity={}, result={}".format(self.amk_rt_sens, data[2]))

    def reload_top_sensitivity(self):
        """ Reload TOP sensitivity setting from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_TOP_SENS))
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_top_sens = data[3]
        #print("AMK protocol: TOP sensitivity={}, result={}".format(self.amk_top_sens, data[2]))

    def reload_bottom_sensitivity(self):
        """ Reload BOTTOM sensitivity setting from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_BTM_SENS))
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_btm_sens = data[3]
        #print("AMK protocol: BOTTOM sensitivity={}, result={}".format(self.amk_btm_sens, data[2]))

    def reload_apc_sensitivity(self):
        """ Reload APC sensitivity setting from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_APC_SENS))
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_apc_sens = data[3]
        #print("AMK protocol: APC sensitivity={}, result={}".format(self.amk_apc_sens, data[2]))

    def reload_noise_sensitivity(self):
        """ Reload NOISE sensitivity setting from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_NOISE_SENS))
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_noise_sens = data[3]
        #print("AMK protocol: NOISE sensitivity={}, result={}".format(self.amk_noise_sens, data[2]))

    def apply_dks(self, row, col, dks=None):
        if dks is not None:
            if self.amk_dks[(row, col)].is_same(dks):
                return
            self.amk_dks[(row,col)].load(dks)

        #self.amk_dks[(row,col)].dump()
        data = struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_DKS, row, col) + self.amk_dks[(row,col)].pack_dks()
        data = self.usb_send(self.dev, data, retries=20)

    def apply_apc(self, row, col, val):
        if self.amk_apc[(row,col)] == val:
            return

        #print("Update APC at({},{}), old({}), new({})".format(row, col, self.amk_apc[(row,col)], val))
        self.amk_apc[(row,col)] = val
        data = struct.pack(">BBBBH", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_APC, row, col, val)
        data = self.usb_send(self.dev, data, retries=20)

    def apply_rt(self, row, col, val):
        if self.amk_rt[(row,col)]["cont"] == val["cont"] and \
            self.amk_rt[(row,col)]["down"] == val["down"] and \
            self.amk_rt[(row,col)]["up"] == val["up"]:
            return

        #print("Update RT at({},{}), old({}), new({})".format(row, col, self.amk_rt[(row,col)], val))

        self.amk_rt[(row,col)]["cont"] = val["cont"] 
        self.amk_rt[(row,col)]["down"] = val["down"] 
        self.amk_rt[(row,col)]["up"] = val["up"] 
        rt = 0x8000 if val["cont"] else 0
        rt = rt + ((val["down"] & 0x3F) << 6)
        rt = rt + (val["up"] & 0x3F)
        data = struct.pack(">BBBBH", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_RT, row, col, rt)

        data = self.usb_send(self.dev, data, retries=20)

    def apply_poll_rate(self, val):
        if self.amk_poll_rate == val:
            return

        print("Update poll rate: old({}), new({})".format(self.amk_poll_rate, val))
        self.amk_poll_rate = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_POLL_RATE, val), retries=20)

    def apply_debounce(self, val, down):
        if down:
            if self.amk_down_debounce == val:
                return 

            #print("Update down debounce: old({}), new({})".format(self.amk_down_debounce, val))
            self.amk_down_debounce = val
        else:
            if self.amk_up_debounce == val:
                return

            #print("Update up debounce: old({}), new({})".format(self.amk_up_debounce, val))
            self.amk_up_debounce = val

        cmd = AMK_PROTOCOL_SET_DOWN_DEBOUNCE if down else AMK_PROTOCOL_SET_UP_DEBOUNCE
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, cmd, val), retries=20)
    
    def apply_nkro(self, val):
        if self.amk_nkro == val:
            return

        #print("Update NKRO : old({}), new({})".format(self.amk_nkro, val))
        self.amk_nkro = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_NKRO, val), retries=20)

    def apply_pole(self, val):
        if self.amk_pole == val:
            return

        #print("Update POLE: old({}), new({})".format(self.amk_pole, val))
        self.amk_pole = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_POLE, val), retries=20)

    def apply_rt_sensitivity(self, val):
        if self.amk_rt_sens == val:
            return

        self.amk_rt_sens = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_RT_SENS, val), retries=20)
        #print("update RT sensitivity: ", val)

    def apply_top_sensitivity(self, val):
        if self.amk_top_sens == val:
            return

        self.amk_top_sens = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_TOP_SENS, val), retries=20)
        #print("update TOP sensitivity: ", val)

    def apply_btm_sensitivity(self, val):
        if self.amk_btm_sens == val:
            return

        self.amk_btm_sens = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_BTM_SENS, val), retries=20)
        #print("update BOTTOM sensitivity: ", val)

    def apply_apc_sensitivity(self, val):
        if self.amk_apc_sens == val:
            return

        self.amk_apc_sens = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_APC_SENS, val), retries=20)
        #print("update APC sensitivity: ", val)

    def apply_noise_sensitivity(self, val):
        if self.amk_noise_sens == val:
            return

        self.amk_noise_sens = val
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_NOISE_SENS, val), retries=20)
        #print("update NOISE sensitivity: ", val)
