#
# / _____)             _              | |
#( (____  _____ ____ _| |_ _____  ____| |__
# \____ \| ___ |    (_   _) ___ |/ ___)  _ \
# _____) ) ____| | | || |_| ____( (___| | | |
#(______/|_____)_|_|_| \__)_____)\____)_| |_|
#    (C)2016 Semtech
#
#Description: Implements a mote object
#
# REMARK: Search for author acknowledgment and check license
#
#License: Revised BSD License, see LICENSE.TXT file include in the project
#
#Maintainer: Miguel Luis
#
from Cryptodome.Hash import CMAC
from Cryptodome.Cipher import AES
from math import ceil
from utilities import Map

JsonData = Map( Time = "", Timestamp = 0, Modulation = "",
                Datarate = "", Frequency = 0.0, Coderate = "", Snr = 0.0,
                Rssi = 0, Data64 = "", Data = "" )

class Mote( object ):
    def __init__( self ):
        self.activated = False
        self.appNonce = []
        self.devNonce = []
        self.upLinkCounter = 0
        self.Frames = []
        #self.LastFrame = Map( Time = "", Timestamp = 0, Modulation = "",
        #                       Datarate = "", Frequency = 0.0, Coderate = "", Snr = 0.0
        #                       Rssi = 0, Data64 = "", Data = ""

    def ActivateAbp( self, devAddr = 0, nwkSKey = "0", appSKey = "0" ):
        self.devAddr = devAddr
        self.appSKey = '{0:>32s}'.format( str( appSKey ) )
        self.nwkSKey  = '{0:>32s}'.format( str( nwkSKey ) )
        self.upLinkCounter = 0

    def ActivateOtaa( self, devEui = "0", appKey = "0" ):
        self.devEui  = devEui
        self.appKey  = '{0:>32s}'.format( str( appKey ) )
        self.appSKey = '{0:>32s}'.format( str( "0" ) )
        self.nwkSKey  = '{0:>32s}'.format(str( "0" ) )
        self.upLinkCounter = 0

    def EncryptPayload( self, port, payload, address, dir, sequence ):
        if( port != 0 ):
            key = bytes.fromhex( self.appSKey )
        else:
            key = bytes.fromhex( self.nwkSKey )

        aBlock = bytearray( [0x01,0x00,0x00,0x00,0x00] )

        aBlock.append( dir )

        aBlock.extend( [( address ) & 0xFF, ( address >> 8 ) & 0xFF, ( address >> 16 ) & 0xFF, ( address >> 24 ) & 0xFF] )
        aBlock.extend( [( sequence ) & 0xFF, ( sequence >> 8 ) & 0xFF, ( sequence >> 16 ) & 0xFF, ( sequence >> 24 ) & 0xFF] )
        aBlock.extend( [0, 0] )
        idx = 0
        output = bytearray()
        blocks = ceil( float( len( payload ) ) / 16.0 )
        # decrypt bytes using procedure described in LoRaWAM spec section 4.3.3.1
        for i in range( 1, blocks + 1 ):
            aBlock[15] = i

            cipher = AES.new( key, AES.MODE_ECB )
            sBlock = cipher.encrypt( bytes( aBlock ) )

            for i in sBlock:
                if idx >= len( payload ):
                    break
                output.append( i ^ payload[idx] )
                idx = idx + 1
        return output

    def ComputMic( self, frame, address, dir, sequence ):
        key = bytes.fromhex( self.nwkSKey )

        b0Block = bytearray( [0x49, 0x00, 0x00, 0x00, 0x00]);

        b0Block.append( dir )

        b0Block.extend( [( address ) & 0xFF, ( address >> 8 ) & 0xFF, ( address >> 16 ) & 0xFF, ( address >> 24 ) & 0xFF] )
        b0Block.extend( [( sequence ) & 0xFF, ( sequence >> 8 ) & 0xFF, ( sequence >> 16 ) & 0xFF, ( sequence >> 24 ) & 0xFF] )
        b0Block.extend( [0, len( frame ) & 0xFF] )
        cmac = CMAC.new( key,ciphermod=AES )
        cmac.update( bytes( b0Block + frame ) )
        mic = ( cmac.digest()[3] << 24 ) | ( cmac.digest()[2] << 16 ) | ( cmac.digest()[1] << 8 ) | ( cmac.digest()[0] << 0 )
        return mic

    def CheckSequence( self, frame ):
        upLinkCounter = self.upLinkCounter

        sequence = frame["FCnt"]
        
        sequencePrev = upLinkCounter & 0xFFFF
        sequenceDiff = sequence - sequencePrev

        isMicOk = False
        if( sequenceDiff < ( 1 << 15 ) ):
            upLinkCounter = upLinkCounter + sequenceDiff
            mic = self.ComputMic( frame["Data"][0:len( frame["Data"] ) - 4], frame["DevAddr"], 0 if frame["Direction"] == "UP" else 1, upLinkCounter )
            if( frame["MIC"] == mic ):
                isMicOk = True
            else:
                # check for sequence roll-over
                upLinkCounterTmp = upLinkCounter + 0x10000 + ( sequenceDiff & 0xFFFF )
                mic = self.ComputMic( frame["Data"][0:len( frame["Data"] ) - 4], frame["DevAddr"], 0 if frame["Direction"] == "UP" else 1, upLinkCounterTmp )
                if( frame["MIC"] == mic ):
                    isMicOk = True;
                    upLinkCounter = upLinkCounterTmp;
        return isMicOk, upLinkCounter
