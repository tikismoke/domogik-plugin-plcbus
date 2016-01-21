#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

PLCBUS client

Implements
==========

- plcbusManager.__init__(self)
- plcbusManager.plcbus_cmnd_cb(self, message)
- plcbusManager.plcbus_send_ack(self, message)

@author: Francois PINET <domopyx@gmail.com>
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplconnector import Listener, XplTimer
from domogik_packages.plugin_plcbus.lib.plcbus import PLCBUSAPI
import threading
import time
import re


class PlcBusManager(XplPlugin):
    ''' Manage PLCBus technology, send and receive order/state
    '''

    def __init__(self):
        '''
	    Manages the plcbus domogik plugin
	    '''
        # Load config
        XplPlugin.__init__(self, name='plcbus')

        ### get the devices list
        # for this plugin, if no devices are created we won't be able to use devices.
        # but.... if we stop the plugin right now, we won't be able to detect existing device and send events about them
        # so we don't stop the plugin if no devices are created
        self.devices = self.get_device_list(quit_if_no_device=False)

        # register helpers
        self.register_helper('scan', 'test help', 'scan')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        if not self.check_configured():
            return

        ### get all config keys
        plcbus_device = str(self.get_config('device'))
        self._usercode = self.get_config('usercode')
        self._probe_inter = int(self.get_config('probe-interval'))
        self._probe_list = self.get_config('probe-list')

        # Init Plcbus
        self.manager  = PLCBUSAPI(self.log, plcbus_device, self._command_cb, self._message_cb)
        self.add_stop_cb(self.manager.stop)

    	# Create the xpl listeners
        Listener(self._plcbus_cmnd_cb, self.myxpl, {'xpltype': 'xpl-cmnd', 'schema': 'plcbus.basic'})

        if self._probe_inter == 0:
            self.log.warning(
                "The probe interval has been set to 0. This is not correct. The plugin will use a probe interval of 5 seconds")
            self._probe_inter = 5
        self._probe_status = {}
        self._probe_thr = XplTimer(self._probe_inter, self._send_probe, self.myxpl)
        self._probe_thr.start()
        self.register_timer(self._probe_thr)
        self.ready()

    def _send_probe(self):
        print("send_probe(self)")
        """ Send probe message 

        """
        for h in self._probe_list:
            print("send get_all_id")
            self.manager.send("GET_ALL_ID_PULSE", h, self._usercode, 0, 0)
            time.sleep(1)
            print("send get_all_on_id")
            self.manager.send("GET_ALL_ON_ID_PULSE", h, self._usercode, 0, 0)
            time.sleep(1)

    def _plcbus_cmnd_cb(self, message):
        print("plcbus_cmnd_cb(self, message):")
        '''
        General callback for all command messages
        '''
        cmd = None
        dev = None
        user = '00'
        level = 0
        rate = 0
        print("xpl message receive %s" % message)
        if 'command' in message.data:
            cmd = message.data['command']
        if 'device' in message.data:
            dev = message.data['device'].upper()
        if 'address' in message.data:
            dev = message.data['address'].upper()
        if 'usercode' in message.data:
            user = message.data['usercode']
        else:
            user = self._usercode
        if 'level' in message.data:
            level = message.data['level']
	    if level == "1":
		cmd = "ON"
	    else:
	        cmd = "OFF"
        if 'data1' in message.data:
            level = message.data['data1']
        if 'data2' in message.data:
            rate = message.data['data2']
#        self.log.debug("%s received : device = %s, user code = %s, level = " \
#                       "%s, rate = %s" % (cmd.upper(), dev, user, level, rate))
        self.log.debug("%s received : device = %s, user code = %s, level = " \
                       "%s, rate = %s" % (cmd, dev, user, level, rate))
        if cmd == 'GET_ALL_ON_ID_PULSE':
            self.manager.get_all_on_id(user, dev)
        else:
#            self.manager.send(cmd.upper(), dev, user, level, rate)
            self.manager.send(cmd, dev, user, level, rate)
        if cmd == 'PRESET_DIM' and level == 0:
            print("cmd : %s " % cmd)
            print("level : %s " % level)
            self.manager.send("OFF", dev, user)

        if cmd == 'PRESET_DIM' and level != 0:
            print('WORKAROUD : on fait suivre le DIM d un ON pour garder les widgets switch allumes')
            print("DEBUG cmd : %s " % cmd)
            print("DEBUG level : %s " % level)
            self.manager.send("ON", dev, user)

    def _command_cb(self, f):
        ''' Called by the plcbus library when a command has been sent.
        If the commands need an ack, this callback will be called only after the ACK has been received
        @param : plcbus frame as an array
        '''
        if f["d_command"] == "GET_ALL_ID_PULSE":
            print("elif fd_command =GET ALL  PULSE ")
            #           data = int("%s%s" % (f["d_data1"], f["d_data2"]))
            #	    Workaround with autodetection problem force data to 511
            #	    to consider discover of device with value from 0 to 9
            #	    Could also be set to 4095 to force from 0 to F
            data = 511
            house = f["d_home_unit"][0]
            for i in range(0, 16):
                unit = data >> i & 1
                code = "%s%s" % (house, i + 1)
                if unit and not code in self._probe_status:
                    self._probe_status[code] = ""
                    self.log.info("New device discovered : %s" % code)
                elif (not unit) and code in self._probe_status:
                    del self._probe_status[code]
        elif f["d_command"] == "GET_ALL_ON_ID_PULSE":
            print("elif fd_command =GET ALL ON ID PULSE ")
            data = "%s%s" % (bin(f["d_data1"])[2:].zfill(8), bin(f["d_data2"])[2:].zfill(8))
            print("f : %s" % f)
            print("data : %s" % data)
            house = f["d_home_unit"][0]
            item = 16
            for c in data:
                unit = int(c)
                code = "%s%s" % (house, item)
                print("Etat : %s " % code, unit)
                if code in self._probe_status and (self._probe_status[code] != str(unit)):
                    print('DEBUG in rentre dans le IF detection GET_ALL_ON')
                    self._probe_status[code] = str(unit)
                    if unit == 1:
                        command = 1
                    else:
                        command = 0
                    self.log.info("New status for device : %s is now %s " % (code, command))
                    mess = XplMessage()
                    mess.set_type('xpl-trig')
                    mess.set_schema('plcbus.basic')
                    mess.add_data({"address": code, "level": command})
                    self.myxpl.send(mess)
                    print("message XPL : %s" % mess)
                item = item - 1
        else:
            print("else")
            if f["d_command"] == "ON":
                command = 1
            else:
                command = 0
            mess = XplMessage()
            mess.set_type('xpl-trig')
            mess.set_schema('plcbus.basic')
            mess.add_data({"usercode": f["d_user_code"], "address": f["d_home_unit"],
                           "level": command, "data1": f["d_data1"], "data2": f["d_data2"]})
            self.myxpl.send(mess)
            print("message XPL : %s" % mess)

    def _message_cb(self, message):
        print("Message : %s " % message)


if __name__ == "__main__":
    PlcBusManager()
