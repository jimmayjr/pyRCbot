#!/usr/bin/env python2
## @package pyRCbot
# Documentation for the pyRCbot package
#

# Standard library modules
import argparse
import ConfigParser as cp
import multiprocessing as mp
import os
import socket
import ssl
import sys
import time

# Custom modules
import pyRClogging

# Definitions
VERSIONNUM = '0.1'
VERSION = 'pyRCbot v%s' % VERSIONNUM
DESCRIPTION = 'pyRCbot A python based multi-server IRC bot.'
EPILOG = 'See pyRCbot documentation for more help.'
DEFAULTLOGPATH = '/var/log/pyRCbot.log'
DEFAULTLOGLEVEL = pyRClogging.INFO

## Core bot code.
#
# The Bot class serves as a single entity that can connect to multiple IRC 
# servers. All bot logic and connections are handled by this class. A Bot 
# object can be spawned as a separate process if running the bot from a 
# terminal This allows for stdin to direct commands to the bot without having 
# to send commands across an IRC channel or direct message - useful 
# when the bot is not connected to any servers and/or channels.
class Bot(mp.Process):
    
    ## Bot constructor.
    #
    # @param self Bot Object pointer.
    # @param cfgPath Configuration file path [string].
    # @param dMode In daemon mode? [bool].
    # @param logQueue Logging queue [mp.Queue].
    def __init__(self,cfgPath,dMode,logQueue,bPipeConn):
        if not dMode:
            mp.Process.__init__(self)
            self.bPipeConn = bPipeConn
        self.cfgPath = cfgPath
        self.dMode = dMode
        self.logQueue = logQueue
        self.logName = 'pyRCBot'
        
        # Dict of servers
        self.serverDict = dict()
        
        # Dict of config data
        self.botCFG = dict()
    
    ## Configuration file loader
    #
    # This method loads a configuration file specified as an argument
    # to the program or from the default location. If running in terminal
    # mode, a configuration file is not necessary.
    def loadConfig(self,cfgPath):
        # Create parser
        cfg = cp.SafeConfigParser(allow_no_value=False)
        # Return parsed object
        parsed = cfg.read(cfgPath)
        # Check if file parsed successfully and process info
        if parsed[0] == os.path.basename(cfgPath):
            for cfgSect in cfg.sections():
                # Process Bot configuration
                if cfgSect == 'cfg':
                    # Set logPath to cfg file value or default
                    # Check if option exists
                    if cfg.has_option('cfg','logPath'):
                        # Set to value in cfg file
                        self.botCFG['logPath'] = os.path.abspath(cfg.get('cfg','logPath'))
                    else:
                        self.botCFG['logPath'] = DEFAULTLOGPATH
                    # Set logLevel to cfg file value or default
                    # Check if option exists
                    if cfg.has_option('cfg','logLevel'):
                        # Check if value defined in option exists
                        if hasattr(pyRClogging,cfg.get('cfg','logLevel')):
                            # Set to valu in cfg file
                            self.botCFG['logLevel'] = pyRClogging.__dict__[cfg.get('cfg','logLevel')]
                        else:
                            # NOTIFY INVALID logLevel IN CFG SECTION, USING DEFAULT INSTEAD
                            self.botCFG['logLevel'] = DEFAULTLOGLEVEL
                    else:
                        # NOTIFY logLevel MISSING FROM CFG SECTION, USING DEFAULT
                        self.botCFG['logLevel'] = DEFAULTLOGLEVEL
                # Process Server information
                else:
                    # Failed to parse flag
                    sFail = False
                    # Dict for storing parsed server data
                    tServDict = dict()
                    # Required server info
                    reqOpts = ['address','port','user']
                    for opt in reqOpts:
                        if cfg.has_option(cfgSect,opt):
                            if cfg.get(cfgSect,opt) is '':
                                # NOTIFY of INVALID BLANK opt
                                sFail = True
                            else:
                                tServDict[opt] = cfg.get(cfgSect,opt)
                        else:
                            # NOTIFY OF MISSING opt
                            sFail = True
                            
                    # Optional server info
                    optionalOpts = ['serverPW','nick','nickPW','realName',
                                    'channels','channelsPW']
                    for opt in optionalOpts:
                        if cfg.has_option(cfgSect,opt):
                            if opt is 'channels' or opt is 'channelsPW':
                                tServDict[opt] = cfg.get(cfgSect,opt).split(',')
                            else:
                                tServDict[opt] = cfg.get(cfgSect,opt)
                        else:
                            if opt is 'nick':
                                # If nick missing, set to user
                                # NOTIFY OF MISSING NICK, USING USER FOR NICK
                                tServDict[opt] = tServDict['user']
                            elif opt is 'channels':
                                # NOTIFY OF MISSING opt
                                # Set opt to blank
                                tServDict[opt] = ['']
                            elif opt is 'channelsPW':
                                pass
                            else:
                                # NOTIFY OF MISSING opt
                                # Set opt to blank
                                tServDict[opt] = ''
                    if len(tServDict['channels']) is len(tServDict['channelsPW']):
                        chanList = tServDict['channels']
                        chanPWList = tServDict['channelsPW']
                        tServDict['channels'] = dict()
                        for chanIndex in xrange(0,len(chanList)):
                            if len(chanList[chanIndex].split('#')) is 2:
                                tServDict['channels'][chanList[chanIndex]] = dict({'PW':chanPWList[chanIndex]})
                            else:
                                # NOTIFY of invalid channel name and skip
                                pass
                        del tServDict['channelsPW']
                    else:
                        # Don't connect to any channels
                        tServDict['channels'] = dict()
                        del tServDict['channelsPW']
                        # NOTIFY OF mismatching number of chanels to channel passwords
                    print(tServDict)
                    print(sFail)
                        
            print(cfg.sections())
            print(self.botCFG)
        else:
            # Notify of failure to parse config file
            pass
        
    ## Multiprocessing run method for Bot object process in terminal mode 
    # and/or main loop for Bot object.
    #
    # This method starts the core bot functions.
    def run(self):
        rootLogger = pyRClogging.RootLog(logQueue)
        rootLogger.start()
        self.logger = pyRClogging.ProcLog(logQueue)
        #self.logger.putLog(self.logName,pyRClogging.INFO,
        
        
        
    ## Server connection.
    #
    # The Server class holds all information related to a connection to an IRC
    # server. It also holds methods for (re)connecting to and communicating
    # with an IRC server.
    class Server(mp.Process):
    
        ## Server constructor.
        #
        # @param self Server Object pointer.
        # @param name Server name [string].
        # @param address Server address [address or ip string].
        # @param port Server port [int].
        # @param ssl Use ssl connection? [bool].
        # @param serverPW Server password [string].
        # @param user Username to use on server [string].
        # @param nick Nick to use on server [string].
        # @param nickPW Nickserv password for Nick [string].
        # @param channels List of channels to automatically connect to
        # [tuple (#channel [string],channelPW [string])].
        # @param sPipeConn Pipe for communicating with Bot process.
        # @param logQueue Logging queue [mp.Queue].
        def __init__(self,
                     name,
                     address,
                     port,
                     ssl,
                     serverPW,
                     user,
                     nick,
                     nickPW,
                     channels,
                     pipeConn,
                     logQueue):
            mp.Process.__init__(self)
            self.daemon = True
            self.name = name
            self.address = address
            self.port = port
            self.ssl = ssl
            self.serverPW = serverPW
            self.nick = nick
            self.nickPW = nickPW
            self.channels = channels
            self.sPipeConn = sPipeConn
            self.logQueue = logQueue
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        ## Attempt to make tcp/ssl connection to server.
        def connect(self):
            try:
                self.sock.connect((address,port))
                if ssl:
                    self.sock = ssl.wrap_socket(self.sock)
            except Exception,e:
                print(e)
        
        ## Multiprocessing run method for Server object process.
        #
        # This method calls the connect method and then loops over the 
        # socket and pipe communication functions as necessary.
        def run(self):
            pass
        

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
                        description=DESCRIPTION,
                        epilog=EPILOG,
                        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-d',
                        action='store_true',
                        default=False,
                        help='run bot in daemon mode',
                        dest='daemonFlag')
    parser.add_argument('-v','--version',
                        action='version',
                        version=VERSION)
    parser.add_argument('-c',
                        action='store',
                        default=None,
                        nargs=1,
                        help='path to configuration file',
                        required=False,
                        metavar='cfgFilePath',
                        dest='cfgPath')
    parser.add_argument('--debug',
                        action='store_true',
                        default=False,
                        help='enable debug features immediately',
                        dest='debugFlag')
    args = parser.parse_args()
    print(args)
    
    # Create logging queue
    logQueue = mp.Queue()
    
    # TESTING
    #testRootLog = pyRClogging.RootLog(logQueue)
    #testRootLog.start()
    #testLog = pyRClogging.ProcLog(logQueue)
    #testLog.putLog('pyRCbot',10,'test1')
    #testLog.putLog('pyRCbot.Freenode',20,'test2')
    #testLog.putLog('pyRCbot.Terminal',30,'test3')
    #logQueue.put_nowait(None)
    #testRootLog.join()
    #print('Yay')
    
    bot = Bot('main.cfg',True,logQueue,None)
    bot.loadConfig('main.cfg')
    
    
    
                        
    # Main loop
    
if __name__ == '__main__':
    main()
