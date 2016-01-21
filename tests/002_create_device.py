#!/usr/bin/python
#-*- coding: utf-8 -*-create_device.py

### configuration ######################################
DEVICE_NAME= 'Test-PLCBUS-device'
##################################################
DEVICE_NAME_PLCBUS = "Test-plcbus"
ADDRESS = 'B1'

from domogik.tests.common.testdevice import TestDevice
from domogik.common.utils import get_sanitized_hostname

plugin = 'plcbus'

def create_device():
    ### create the device, and if ok, get its id in device_id
    client_id  = "plugin-{0}.{1}".format(plugin, get_sanitized_hostname())
    print "Creating the PLCBUS  device..."
    td = TestDevice()
    params = td.get_params(client_id, "plcbus.switch")
        # fill in the params
    params["name"] = DEVICE_NAME
    params["reference"] = "reference"
    params["description"] = "description"

    for idx, val in enumerate(params['xpl']):
        params['xpl'][idx]['value'] = ADDRESS

    # go and create
    td.create_device(params)
    print "Device PLCBUS {0} configured".format(DEVICE_NAME_PLCBUS)

if __name__ == "__main__":
    create_device()



