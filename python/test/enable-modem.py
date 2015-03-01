#!/usr/bin/env python

import dbus
import sys

bus = dbus.SystemBus()

if len(sys.argv) == 2:
    path = sys.argv[1]
else:
    manager = dbus.Interface(bus.get_object('org.ofono', '/'),
            'org.ofono.Manager')
    modems = manager.GetModems()
    path = modems[0][0]

print("Connecting modem %s..." % path)
modem = dbus.Interface(bus.get_object('org.ofono', path),
                        'org.ofono.Modem')

modem.SetProperty("Powered", dbus.Boolean(1), timeout = 120)

