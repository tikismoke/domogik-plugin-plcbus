#!/usr/bin/python
#-*- coding: utf-8 -*-

from domogik.tests.common.helpers import configure, delete_configuration
from domogik.common.utils import get_sanitized_hostname

plugin =  "plcbus"

host_id = get_sanitized_hostname()
delete_configuration("plugin", plugin, host_id)

configure("plugin", plugin, host_id, "device", "/dev/plcbus")
configure("plugin", plugin, host_id, "usercode", "D1")
configure("plugin", plugin, host_id, "probe-list", "A")
configure("plugin", plugin, host_id, "usercode", "D1")
configure("plugin", plugin, host_id, "probe-interval", 60)
configure("plugin", plugin, host_id, "configured", True)
