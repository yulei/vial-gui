import struct

from keycodes.keycodes import Keycode

from protocol.base_protocol import BaseProtocol

AMK_VERSION = "0.8.1"

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
AMK_PROTOCOL_GET_MS_CONFIG = 15
AMK_PROTOCOL_SET_MS_CONFIG = 16
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
AMK_PROTOCOL_GET_RGB_STRIP_COUNT = 27
AMK_PROTOCOL_GET_RGB_STRIP_PARAM = 28
AMK_PROTOCOL_GET_RGB_STRIP_LED = 29
AMK_PROTOCOL_SET_RGB_STRIP_LED = 30
AMK_PROTOCOL_GET_RGB_STRIP_MODE = 31
AMK_PROTOCOL_SET_RGB_STRIP_MODE = 32
AMK_PROTOCOL_GET_RGB_INDICATOR_LED = 33
AMK_PROTOCOL_SET_RGB_INDICATOR_LED = 34
AMK_PROTOCOL_GET_FILE_SYSTEM_INFO = 35
AMK_PROTOCOL_GET_FILE_INFO = 36
AMK_PROTOCOL_OPEN_FILE = 37
AMK_PROTOCOL_WRITE_FILE = 38
AMK_PROTOCOL_READ_FILE = 39
AMK_PROTOCOL_CLOSE_FILE = 40
AMK_PROTOCOL_DELETE_FILE = 41
AMK_PROTOCOL_DISPLAY_CONTROL = 42
AMK_PROTOCOL_GET_RGB_MATRIX_INFO = 43
AMK_PROTOCOL_GET_RGB_MATRIX_ROW_INFO = 44
AMK_PROTOCOL_GET_RGB_MATRIX_MODE = 45
AMK_PROTOCOL_SET_RGB_MATRIX_MODE = 46
AMK_PROTOCOL_GET_RGB_MATRIX_LED = 47
AMK_PROTOCOL_SET_RGB_MATRIX_LED = 48
AMK_PROTOCOL_GET_SNAPTAP = 49
AMK_PROTOCOL_SET_SNAPTAP = 50
AMK_PROTOCOL_GET_SNAPTAP_COUNT = 51
AMK_PROTOCOL_GET_SNAPTAP_CONFIG = 52
AMK_PROTOCOL_SET_SNAPTAP_CONFIG = 53
AMK_PROTOCOL_SET_DATETIME = 54
AMK_PROTOCOL_GET_DATETIME = 55

RGB_LED_NUM_LOCK = 0
RGB_LED_CAPS_LOCK = 1
RGB_LED_SCROLL_LOCK = 2
RGB_LED_COMPOSE = 3
RGB_LED_KANA = 4

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

class RgbLed:
    def __init__(self, index, hue, sat, val, param):
        self.index = index
        self.hue = hue
        self.sat = sat
        self.val = val
        self.on = 0
        self.dynamic = 0
        self.blink = 0
        self.breath = 0
        self.speed = 0
        self.parse_param(param)

    def parse_param(self, param):
        self.on         = (param >> 0) & 0x01
        self.dynamic    = (param >> 1) & 0x01
        self.blink      = (param >> 2) & 0x01
        self.breath     = (param >> 3) & 0x01
        self.speed      = (param >> 4) & 0x0F

    def pack_param(self):
        param = 0
        if self.on > 0:
            param = param | (0x01 << 0)
            
        if self.dynamic > 0:
            param = param | (0x01 << 1)

        if self.blink > 0:
            param = param | (0x01 << 2)

        if self.breath > 0:
            param = param | (0x01 << 3)
    
        param = param | ((self.speed&0x0F) << 4)
        return param

    def pack(self):
        param = self.pack_param()

        data = struct.pack("BBBB", self.hue, self.sat, self.val, param)
        return data

    def set_hue(self, hue):
        self.hue = hue

    def get_hue(self):
        return self.hue

    def set_sat(self, sat):
        self.sat = sat

    def get_sat(self):
        return self.sat

    def set_val(self, val):
        self.val = val 

    def get_val(self):
        return self.val
    
    def set_on(self, on):
        self.on = on

    def get_on(self):
        return self.on

    def set_dynamic(self, dynamic):
        self.dynamic = dynamic 

    def get_dynamic(self):
        return self.dynamic

    def set_blink(self, blink):
        self.blink = blink 

    def get_blink(self):
        return self.blink

    def set_breath(self, breath):
        self.breath = breath

    def get_breath(self):
        return self.breath

    def set_speed(self, speed):
        self.speed = speed

    def get_speed(self):
        return self.speed

class RgbLedStrip:
    def __init__(self, index, config, start, count):
        self.index = index
        self.config = config 
        self.start = start
        self.count = count
        self.leds = [None] * count
        self.mode = 0

    def set_led(self, index, led):
        self.leds[index] = led
    
    def get_led(self, index):
        return self.leds[index]
    
    def set_index(self, index):
        self.index = index 

    def get_index(self):
        return self.index

    def set_config(self, config):
        self.config = config 

    def get_config(self):
        return self.config

    def set_start(self, start):
        self.start = start

    def get_start(self):
        return self.start

    def set_count(self, count):
        self.count = count 

    def get_count(self):
        return self.count
    
    def set_mode(self, mode):
        self.mode = mode
    
    def get_mode(self):
        return self.mode

class RgbIndicator:
    def __init__(self, index):
        self.led = None
        self.index = index
    
    def set_led(self, led):
        self.led = led
    
    def get_led(self):
        return self.led

    def set_index(self, index):
        self.led = index 
    
    def get_index(self):
        return self.index

class SnaptapKey:
    def __init__(self, index, first_row=0, first_col=0, second_row=0, second_col=0, mode=0):
        self.index = index
        self.first_row = first_row
        self.first_col = first_col
        self.second_row = second_row
        self.second_col = second_col
        self.mode = mode
    
    def get_first_row(self):
        return self.first_row

    def get_first_col(self):
        return self.first_col

    def get_second_row(self):
        return self.second_row

    def get_second_col(self):
        return self.second_col

    def get_mode(self):
        return self.mode
    
    def get_index(self):
        return self.index

class ProtocolAmk(BaseProtocol):

    def amk_protocol_version(self):
        """ Get the version of AMK protocol """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_VERSION), retries=20)
        #print("AMK protocol:", data[2])
        return data[2]

    def reload_apc(self, profile):
        """ Reload APC information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_APC, row, col, profile),
                                retries=20)
            val = struct.unpack(">H", data[3:5])
            if self.amk_apcrt_version == 1:
                self.amk_apc[profile][(row, col)] = val[0] * self.amk_apcrt_scale
            else:
                self.amk_apc[profile][(row, col)] = val[0]
            #print("AMK protocol: APC={}, row={}, col={}, profile={}".format(self.amk_apc[profile][(row,col)], row, col, profile))

    def reload_rt(self, profile):
        """ Reload RT information from keyboard """
        for row, col in self.rowcol.keys():
            data = self.usb_send(self.dev, 
                                struct.pack("BBBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RT, row, col, profile),
                                retries=20)
            val = struct.unpack(">H", data[3:5])[0]
            rt = {}
            if self.amk_apcrt_version == 1:
                cont = True if val & 0x8000 > 0 else False
                down = (val >> 6) & 0x3F
                up = val & 0x003F
                rt["cont"] = cont * self.amk_apcrt_scale
                rt["down"] = down * self.amk_apcrt_scale
                rt["up"] = up
            else:
                cont = True if val & 0x8000 > 0 else False
                down = (val >> 7) & 0x007F
                up = val & 0x007F
                rt["cont"] = cont
                rt["down"] = down
                rt["up"] = up

            self.amk_rt[profile][(row, col)] = rt
            #print("AMK protocol: RT={}, row={}, col={}, profile={}".format(self.amk_rt[profile][(row, col)], row, col, profile))

    def dump_apcrt(self):
        for i in range(self.amk_profile_count):
            for row, col in self.rowcol.keys():
                print("DUMP APCRT: apc={}, rt={}, row={}, col={}, profile={}".format(self.amk_apc[i][(row,col)],
                                                                                     self.amk_rt[i][(row,col)],
                                                                                     row,col,i))


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

    def reload_ms_config(self):
        """ Reload Magnetic Switch information from keyboard """
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_MS_CONFIG))
        self.amk_pole = True if (data[3] & 0x01) > 0 else False
        #self.amk_profile = (data[3] & 0x06) >> 1
        self.keyboard_profile = (data[3] & 0x06) >> 1
        self.amk_dks_disable = True if (data[3] & 0x08) > 0 else False

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
        if self.amk_apc[self.amk_profile][(row,col)] == val:
            return

        #print("Update APC at({},{}), old({}), new({})".format(row, col, self.amk_apc[(row,col)], val))
        self.amk_apc[self.amk_profile][(row,col)] = val
        if self.amk_apcrt_version == 1:
            val = val // self.amk_apcrt_scale

        data = struct.pack(">BBBBHB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_APC, row, col, val, self.amk_profile)
        data = self.usb_send(self.dev, data, retries=20)

    def apply_rt(self, row, col, val):
        if self.amk_rt[self.amk_profile][(row,col)]["cont"] == val["cont"] and \
            self.amk_rt[self.amk_profile][(row,col)]["down"] == val["down"] and \
            self.amk_rt[self.amk_profile][(row,col)]["up"] == val["up"]:
            return

        #print("Update RT at({},{}), old({}), new({})".format(row, col, self.amk_rt[(row,col)], val))

        self.amk_rt[self.amk_profile][(row,col)]["cont"] = val["cont"] 
        self.amk_rt[self.amk_profile][(row,col)]["down"] = val["down"] 
        self.amk_rt[self.amk_profile][(row,col)]["up"] = val["up"] 
        rt = 0x8000 if val["cont"] else 0
        if self.amk_apcrt_version == 1:
            rt = rt + (((val["down"]//self.amk_apcrt_scale) & 0x3F) << 6)
            rt = rt + ((val["up"]//self.amk_apcrt_scale) & 0x3F)
        else:
            rt = rt + ((val["down"] & 0x7F) << 7)
            rt = rt + (val["up"] & 0x7F)

        data = struct.pack(">BBBBHB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_RT, row, col, rt, self.amk_profile)

        data = self.usb_send(self.dev, data, retries=20)

    def apply_poll_rate(self, val):
        if self.amk_poll_rate == val:
            return

        #print("Update poll rate: old({}), new({})".format(self.amk_poll_rate, val))
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

    def compose_config(self):
        config = 1 if self.amk_pole else 0
        config = config + (self.keyboard_profile*2)
        config = config + (8 if self.amk_dks_disable else 0)
        #print("Config is:{}, keyboard_profile is:{} ".format(config, self.keyboard_profile))
        return config

    def apply_pole(self, val):
        if self.amk_pole == val:
            return

        #print("Update POLE: old({}), new({})".format(self.amk_pole, val))
        self.amk_pole = val
        config = self.compose_config()
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_MS_CONFIG, config), retries=20)

    def apply_profile(self, val):
        if self.keyboard_profile == val:
            return

        #print("Update PROFILE: old({}), new({})".format(self.keyboard_profile, val))
        self.keyboard_profile = val
        config = self.compose_config()
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_MS_CONFIG, config), retries=20)

    def apply_dks_disable(self, val):
        if self.amk_dks_disable == val:
            return

        #print("Update DKS DISABLE: old({}), new({})".format(self.amk_pole, val))
        self.amk_dks_disable = val
        config = self.compose_config()
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_MS_CONFIG, config), retries=20)

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

    def reload_rgb_strips(self):
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_STRIP_COUNT), retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_rgb_strip_count = data[3]
            for i in range(self.amk_rgb_strip_count):
                data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_STRIP_PARAM,i), retries=20)
                if data[2] == AMK_PROTOCOL_OK:
                    strip = RgbLedStrip(data[3], data[4], data[5], data[6])
                    self.amk_rgb_strips.append(strip)
                    #print("AMK protocol: get rgb strip: index={}, config={}, start={}, count={}".format(data[3], data[4], data[5], data[6]))
                    data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_STRIP_MODE,i), retries=20)
                    if data[2] == AMK_PROTOCOL_OK:
                        strip.set_mode(data[4])
                        #print("AMK protocol: get rgb strip mode: index={}, mode={}".format(data[3], data[4]))
                    #else:
                    #    print("AMK protocol: failed to get rgb strip mode:{}".format(i))


        #print("AMK protocol: rgb strip count ={}".format(self.amk_rgb_strip_count))

    def reload_rgb_strip_led(self, index):
        start = self.amk_rgb_strips[index].get_start()
        count = self.amk_rgb_strips[index].get_count()

        for i in range(count):
            data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_STRIP_LED,start+i), retries=20)
            if data[2] == AMK_PROTOCOL_OK:
                led = RgbLed(data[3], data[4], data[5], data[6], data[7])
                self.amk_rgb_strips[index].set_led(i, led)
                #print("AMK protocol: get rgb strip led: index={}, hue={},sat={},val={}, param={}".format(data[3], data[4], data[5], data[6],data[7]))


    def apply_rgb_strip_led(self, strip, index, led):
        self.amk_rgb_strips[strip].set_led(index, led)

        data = self.usb_send(self.dev,
                            struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_RGB_STRIP_LED, 
                                        self.amk_rgb_strips[strip].start+index) + led.pack(), 
                             retries=20)
        #print("AMK protocol: set rgb strip led: strip={}, index={}, led={}".format(strip, index, led.pack()))

    def apply_rgb_strip_mode(self, strip, mode):
        if self.amk_rgb_strips[strip].get_mode() == mode:
            return
        
        self.amk_rgb_strips[strip].set_mode(mode)
        data = self.usb_send(self.dev, struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_RGB_STRIP_MODE, strip, mode), retries=20)
        #print("AMK protocol: set rgb strip mode: index={}, mode={}".format(strip, mode))
    
    def reload_indicator(self, led):
        data = self.usb_send(self.dev, struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_INDICATOR_LED, led.get_index()), retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            indicator = RgbLed(data[3], data[4], data[5], data[6], data[7])
            led.set_led(indicator)
        else:
            print("Failed to get indicator at: ", led.get_index())

    def reload_rgb_indicators(self):
        if "indicator" in self.definition:
            if "num_lock" in self.definition["indicator"]:
                self.rgb_indicators["num_lock"] = RgbIndicator(self.definition["indicator"]["num_lock"]["index"])
                self.reload_indicator(self.rgb_indicators["num_lock"])
            if "caps_lock" in self.definition["indicator"]:
                self.rgb_indicators["caps_lock"] = RgbIndicator(self.definition["indicator"]["caps_lock"]["index"])
                self.reload_indicator(self.rgb_indicators["caps_lock"])
            if "scroll_lock" in self.definition["indicator"]:
                self.rgb_indicators["scroll_lock"] = RgbIndicator(self.definition["indicator"]["scroll_lock"]["index"])
                self.reload_indicator(self.rgb_indicators["scroll_lock"])
            if "compose" in self.definition["indicator"]:
                self.rgb_indicators["compose"] = RgbIndicator(self.definition["indicator"]["compose"]["index"])
                self.reload_indicator(self.rgb_indicators["compose"])
            if "kana" in self.definition["indicator"]:
                self.rgb_indicators["kana"] = RgbIndicator(self.definition["indicator"]["kana"]["index"])
                self.reload_indicator(self.rgb_indicators["kana"])

    def apply_rgb_indicator(self, led):
        data = self.usb_send(self.dev,
                            struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_SET_RGB_INDICATOR_LED, 
                                        led.get_index()) + led.get_led().pack(), 
                             retries=20)
    
    def reload_anim_file_list(self):
        data = self.usb_send(self.dev, 
                             struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_FILE_SYSTEM_INFO), 
                             retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            total_file, free_space, total_space = struct.unpack("<BII", data[3:12])
            self.animations["disk"] = {"total_file":total_file, "free_space":free_space, "total_space":total_space}
            self.animations["file"] = []
            #print("total file: {}, free space: {}, total space: {}".format(total_file, free_space, total_space))
            for i in range(total_file):
                data = self.usb_send(self.dev, 
                                    struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_FILE_INFO, i), 
                                    retries=20)
                if data[2] == AMK_PROTOCOL_OK:
                    index = 0
                    for d in range(13):
                        if data[3+d] == 0:
                            index = d
                            break
                    try:
                        name = data[3:3+index].decode("utf-8")
                    except:
                        name = data[3:3+index].decode("gbk")

                    size, = struct.unpack("<I", data[16:20])
                    self.animations["file"].append({"name":name.split("\0")[0], "size":size})
                else:
                    print("failed to get file at index: ", i)
        else:
            print("faild to refresh file list")

    def fastopen_anim_file(self, dev, name, read, index=0xFF):
        data = struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_OPEN_FILE, index, 1 if read else 0) + bytearray(name, "utf-8")
        data += b"\x00" * (64 - len(data))

        dev.write(4, data)
        data = dev.read(0x84, 64)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Open file at index:", data[3])
            return data[3]
        else:
            #print("Failed to open file: ", name)
            return 0xFF
    
    def fastwrite_anim_file(self, dev, index, data, offset):
        data = struct.pack("<BBBBI", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_WRITE_FILE, index, len(data), offset) + data
        dev.write(4, data)
        data = dev.read(0x84, 64)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Write file at index:{}, size:{}".format(index, len(data)))
            return True
        else:
            #print("Failed to write file: index=", index)
            return False
    
    def fastwrite_anim_file_vendor(self, dev, data):
        dev.write(4, data)
        return True

    def fastread_anim_file(self, dev, index, offset, size):
        data = struct.pack("<BBBBI", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_READ_FILE, index, size, offset)
        dev.write(4, data)
        data = dev.read(0x84, 64)
        if data[2] == AMK_PROTOCOL_OK:
            size = data[3]
            return data[8:8+size] 
        else:
            return None

    def fastclose_anim_file(self, dev, index):
        data = struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_CLOSE_FILE, index)
        dev.write(4, data)
        data = dev.read(0x84, 64)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Close file at index:", index)
            return True
        else:
            #print("Failed to close file: index=", index)
            return False

    def open_anim_file(self, name, read, index=0xFF):
        data = self.usb_send(self.dev, 
                            struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_OPEN_FILE, index, 1 if read else 0) + bytearray(name, "utf-8"),
                            retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Open file at index:", data[3])
            return data[3]
        else:
            #print("Failed to open file: ", name)
            return 0xFF

    def write_anim_file(self, index, data, offset):
        data = self.usb_send(self.dev, 
                            struct.pack("<BBBBI", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_WRITE_FILE, index, len(data), offset) + data,
                            retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Write file at index:{}, size:{}".format(index, len(data)))
            return True
        else:
            #print("Failed to write file: index=", index)
            return False
    
    def read_anim_file(self, index, offset, size):
        data = self.usb_send(self.dev, 
                            struct.pack("<BBBBI", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_READ_FILE, index, size, offset),
                            retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            size = data[3]
            return data[8:8+size] 
        else:
            return None

    def close_anim_file(self, index):
        data = self.usb_send(self.dev, 
                            struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_CLOSE_FILE, index),
                            retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Close file at index:", index)
            return True
        else:
            #print("Failed to close file: index=", index)
            return False

    def delete_anim_file(self, index):
        data = self.usb_send(self.dev, 
                            struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_DELETE_FILE, index),
                            retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            #print("Delete file at index:", index)
            return True
        else:
            #print("Failed to delete file: index=", index)
            return False

    def display_anim_file(self, play):
        data = self.usb_send(self.dev, 
                            struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_DISPLAY_CONTROL, play),
                            retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            return True
        else:
            return False

    def reload_amk_rgb_matrix(self):
        self.amk_rgb_matrix = {}
        data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_MATRIX_INFO), retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_rgb_matrix["start"] = data[3]
            self.amk_rgb_matrix["count"] = data[4]

            self.amk_rgb_matrix["mode"] = {}
            data = self.usb_send(self.dev, struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_MATRIX_MODE), retries=20)
            if data[2] == AMK_PROTOCOL_OK:
                self.amk_rgb_matrix["mode"]["current"] = data[3]
                self.amk_rgb_matrix["mode"]["custom"] = data[4]
                self.amk_rgb_matrix["mode"]["total"] = data[5]
                self.amk_rgb_matrix["mode"]["default"] = data[6]
                #print("RGB Matrix: current={}, custom={}, total={}, default={}".format(data[3], data[4], data[5], data[6]))

            self.amk_rgb_matrix["data"] = {}
            for i in range(self.rows):
                data = self.usb_send(self.dev, struct.pack("BBBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_RGB_MATRIX_ROW_INFO, 0, i), retries=20)
                if data[2] == AMK_PROTOCOL_OK:
                    for j in range(self.cols):
                        self.amk_rgb_matrix["data"][(i,j)] = data[4+j]

            start = self.amk_rgb_matrix["start"]
            count = self.amk_rgb_matrix["count"]
            self.amk_rgb_matrix["leds"] = {}
            for i in range(count):
                self.reload_rgb_matrix_led(i)
        
    def reload_rgb_matrix_led(self, index):
        start = self.amk_rgb_matrix["start"]
        data = self.usb_send(self.dev, 
                            struct.pack("BBB", 
                                        AMK_PROTOCOL_PREFIX, 
                                        AMK_PROTOCOL_GET_RGB_MATRIX_LED, 
                                        start+index), retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            led = RgbLed(data[3], data[4], data[5], data[6], data[7])
            self.amk_rgb_matrix["leds"][index] = led

    def apply_rgb_matrix_led(self, index, led):
        start = self.amk_rgb_matrix["start"]
        self.amk_rgb_matrix["leds"][index] = led
        data = self.usb_send(self.dev,
                            struct.pack("BBB", 
                                        AMK_PROTOCOL_PREFIX, 
                                        AMK_PROTOCOL_SET_RGB_MATRIX_LED, 
                                        start+index) + led.pack(), retries=20)
    
    def apply_rgb_matrix_mode(self, index, mode):
        data = self.usb_send(self.dev,
                            struct.pack("BBBB", 
                                        AMK_PROTOCOL_PREFIX, 
                                        AMK_PROTOCOL_SET_RGB_MATRIX_MODE, 
                                        index,
                                        mode), retries=20)
    
    def get_rgb_matrix_led_index(self, row, col):
        index = self.amk_rgb_matrix["data"].get((row, col)) - self.amk_rgb_matrix["start"]
        if index is None:
            #print("get led index at row: {}, col: {}".format(row, col))
            return None
        if index >= len(self.amk_rgb_matrix["leds"]):
            return None

        return index

    def get_rgb_matrix_led(self, row, col):
        index = self.get_rgb_matrix_led_index(row, col)
        if index is None:
            return None

        return self.amk_rgb_matrix["leds"][index]

    def reload_snaptap(self):
        data = self.usb_send(self.dev,
                            struct.pack("BB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_SNAPTAP_COUNT), retries=20)
        if data[2] == AMK_PROTOCOL_OK:
            self.amk_snaptap_count = data[3]
            self.amk_snaptap_keys = []
            for i in range(self.amk_snaptap_count):
                data = self.usb_send(self.dev,
                                    struct.pack("BBB", AMK_PROTOCOL_PREFIX, AMK_PROTOCOL_GET_SNAPTAP, i), retries=20)
                if data[2] == AMK_PROTOCOL_OK:
                    key = SnaptapKey(i, data[3], data[4], data[5], data[6], data[7])
                    self.amk_snaptap_keys.append(key)

    def apply_snaptap(self, index, key):
        cur = self.amk_snaptap_keys[index]
        if cur.get_first_row() != key["first_row"] or \
            cur.get_first_col() != key["first_col"] or \
            cur.get_second_row() != key["second_row"] or \
            cur.get_second_col() != key["second_col"] or \
            cur.get_mode() != key["mode"]:
            new_key = SnaptapKey(index, key["first_row"], key["first_col"], key["second_row"], key["second_col"], key["mode"]) 

            data = self.usb_send(self.dev,
                                struct.pack("BBBBBBBB", 
                                            AMK_PROTOCOL_PREFIX, 
                                            AMK_PROTOCOL_SET_SNAPTAP,
                                            index,
                                            new_key.get_first_row(),
                                            new_key.get_first_col(),
                                            new_key.get_second_row(),
                                            new_key.get_second_col(),
                                            new_key.get_mode()), retries=20)

            if data[2] == AMK_PROTOCOL_OK:
                self.amk_snaptap_keys[index] = new_key
            else:
                print("failed to set snaptap at ", index)

    def apply_datetime(self, year, month, day, weekday, hour, minute, second):
        data = self.usb_send(self.dev,
                             struct.pack(">BBHBBBBBB",
                                AMK_PROTOCOL_PREFIX,
                                AMK_PROTOCOL_SET_DATETIME,
                                year, month, day, weekday,
                                hour, minute, second), retries=20)
        if data[2] != AMK_PROTOCOL_OK:
            print("failed to sychronize datetime with keyboard")

