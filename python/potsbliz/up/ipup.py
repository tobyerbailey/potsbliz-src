# POTSBLIZ - Plain Old Telephone Service Beyond Local IP Stack
# (C)2015  - Norbert Huffschmid - GNU GPL V3 

# IPUP - IP User Part

import sys
from subprocess import Popen, PIPE
from threading import Thread
from potsbliz.logger import Logger
from potsbliz.up.userpart import UserPart


class Ipup(UserPart):
    
    def __init__(self, identity, proxy, password, port=5060):
        
        with Logger('Ipup::__init__') as log:
            super(Ipup, self).__init__('net.longexposure.potsbliz.ipup.port' + str(port)) # call base class constructor
            self._identity = identity
            self._proxy = proxy
            self._password = password
            self._port = port
            
        
    def __enter__(self):
        with Logger('Ipup::__enter__'):

            # write linphonec config file
            config_file = '/var/tmp/.linphonerc-' + self._identity
            with open(config_file, 'w') as file:
                file.write("[sip]\n")
                file.write("sip_port=%d\n" % self._port)

            self._linphonec = Popen(['/usr/bin/linphonec', '-c' , config_file],
                                    stdout=PIPE, stdin=PIPE)        

            self._worker_thread = Thread(target=self._linphone_worker)
            self._worker_thread.start()
            
            return self

    
    def __exit__(self, type, value, traceback):
        with Logger('Ipup::__exit__'):
            self._linphonec.stdin.write("quit\n")
            self._worker_thread.join()

    
    def MakeCall(self, called_number):
        with Logger('Ipup::MakeCall'):
            sip_provider = self._identity.split('@')[1]
            destination = 'sip:' + called_number + '@' + sip_provider
            self._linphonec.stdin.write('call ' + destination + '\n')
            return True
        
        
    def AnswerCall(self):
        with Logger('Ipup::AnswerCall'):
            self._linphonec.stdin.write('answer\n')
        
        
    def SendDtmf(self, digit):
        with Logger('Ipup::SendDtmf'):
            self._linphonec.stdin.write(digit + '\n')
        
        
    def TerminateCall(self):
        with Logger('Ipup::TerminateCall'):
            self._linphonec.stdin.write('terminate\n')


    def _linphone_worker(self):        
        with Logger('Ipup::_linphone_worker') as log:

            register_command = "register %s %s %s\n" % (self._identity, self._proxy, self._password)
            self._linphonec.stdin.write(register_command)
            self._linphonec.stdin.flush()
            
            while self._linphonec.poll() is None:
                
                message = self._linphonec.stdout.readline()
                log.debug('Linphonec: ' + message)

                if (message.find('Receiving new incoming call') >= 0):
                    self.IncomingCall()
                    
                if (message.find('Call terminated.') >= 0):
                    self.Release()

                if (message.endswith('busy.\n')):
                    self.Busy()

                if (message.startswith('linphonec> Registration')):
                    if (message.endswith('successful.\n')):
                        self.register()
                    else:
                        self.unregister()
                        log.error('Registration at remote sip server failed')


if __name__ == '__main__':
    with Logger('Ipup::__main__') as log:
        
        log.info('IP userpart for POTSBLIZ started ...')

        if (len(sys.argv) != 5):
            raise ValueError('4 arguments expected, %d received' % (len(sys.argv) - 1))

        with Ipup(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])) as userpart:
            userpart.run()
        
        log.info('IP userpart for POTSBLIZ terminated')
