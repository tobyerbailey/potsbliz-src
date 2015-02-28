# BTUP - Bluetooth User Part
# (C) 2015 - Norbert Huffschmid

import dbus
import subprocess
import time
from threading import Thread
from potsbliz.logger import Logger
from potsbliz.userpart import UserPart


class Btup(UserPart):

    def __enter__(self):
        with Logger(__name__ + '.__enter__'):

            self._bus = dbus.SystemBus()
            
            # dbus-python offers signal handling, but the glib-mainloop stuff
            #   seems not very thread-safe and crashes quite often
            # => let's use dbus-monitor in seperate processes instead

            self._call_added_process = subprocess.Popen(['dbus-monitor', '--system',
                                                        "type='signal',sender='org.ofono',member='CallAdded'"],
                                                        stdout=subprocess.PIPE)

            self._call_removed_process = subprocess.Popen(['dbus-monitor', '--system',
                                                          "type='signal',sender='org.ofono',member='CallRemoved'"],
                                                          stdout=subprocess.PIPE)

            self._pulseaudio_process = subprocess.Popen(['/usr/local/bin/pulseaudio'])

            Thread(target=self._call_added_worker).start()
            Thread(target=self._call_removed_worker).start()


    def __exit__(self, type, value, traceback):
        with Logger(__name__ + '.__exit__'):
            self._call_added_process.terminate()
            self._call_removed_process.terminate()
            self._pulseaudio_process.terminate()


    def make_call(self, called_number):
        with Logger(__name__ + '.make_call') as log:

            ofono_manager = dbus.Interface(self._bus.get_object('org.ofono', '/'),
                                         'org.ofono.Manager')
            modems = ofono_manager.GetModems()
            modem_path = modems[0][0]
            log.debug("Connecting modem %s..." % modem_path)
            modem = dbus.Interface(self._bus.get_object('org.ofono', modem_path),
                                   'org.ofono.Modem')
            
            if (modem.GetProperties()['Powered'] == False):
                modem.SetProperty("Powered", dbus.Boolean(1), timeout = 120)
                time.sleep(1) # without delay call fails
            
            vcm = dbus.Interface(self._bus.get_object('org.ofono', modem_path),
                                 'org.ofono.VoiceCallManager')
            dial_path = vcm.Dial(called_number, "default")
            log.debug(dial_path)

        
    def answer_call(self):
        with Logger(__name__ + '.answer_call') as log:
            
            ofono_manager = dbus.Interface(self._bus.get_object('org.ofono', '/'),
                                           'org.ofono.Manager')
            modems = ofono_manager.GetModems()

            for path, properties in modems:
                log.debug("modem path: %s" % (path))
                if "org.ofono.VoiceCallManager" not in properties["Interfaces"]:
                    continue

                vcm = dbus.Interface(self._bus.get_object('org.ofono', path),
                                     'org.ofono.VoiceCallManager')
                calls = vcm.GetCalls()

                for path, properties in calls:
                    state = properties["State"]
                    log.debug("path: %s, state: %s" % (path, state))
                    if state != "incoming":
                        continue

                    call = dbus.Interface(self._bus.get_object('org.ofono', path),
                                          'org.ofono.VoiceCall')
                    call.Answer()


    def send_dtmf(self, digit):
        with Logger(__name__ + '.send_dtmf') as log:

            log.debug('Dbus: Get ofono manager')
            ofono_manager = dbus.Interface(self._bus.get_object('org.ofono', '/'),
                                           'org.ofono.Manager')
            log.debug('Dbus: Get modem path')
            modems = ofono_manager.GetModems()
            modem_path = modems[0][0]

            log.debug('Dbus: Get voicecall manager')
            vcm = dbus.Interface(self._bus.get_object('org.ofono', modem_path),
                                     'org.ofono.VoiceCallManager')
            log.debug('Dbus: Send tone ...')
            vcm.SendTones(str(digit))
            log.debug('Dbus: Tone sent.')


    def terminate_call(self):
        with Logger(__name__ + '.terminate_call'):
            
            ofono_manager = dbus.Interface(self._bus.get_object('org.ofono', '/'),
                                           'org.ofono.Manager')
            modems = ofono_manager.GetModems()
            modem_path = modems[0][0]

            vcm = dbus.Interface(self._bus.get_object('org.ofono', modem_path),
                                     'org.ofono.VoiceCallManager')
            vcm.HangupAll()


    def _call_added_worker(self):        
        with Logger(__name__ + '._call_added_worker'):
            while True:
                line = self._call_added_process.stdout.readline()
                if (line == ''):
                    break
                if ('\"incoming\"' in line):
                    self._pub.sendMessage(UserPart.TOPIC_INCOMING_CALL, sender=self)


    def _call_removed_worker(self):        
        with Logger(__name__ + '._call_removed_worker'):
            while True:
                line = self._call_removed_process.stdout.readline()
                if (line == ''):
                    break
                if ('CallRemoved' in line):
                    self._pub.sendMessage(UserPart.TOPIC_TERMINATE, sender=self)
