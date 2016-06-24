#!/usr/bin/python3

import socket
import json
import requests
from mote import Mote
import binascii
from time import sleep
import datetime
import credentials

from sense_hat import SenseHat

sense = SenseHat()
def color_matrix():
    sense.clear([255,5,5])
    sleep(0.5)
    sense.clear([0,0,0])

Mote_DevAddr = 0x014C605E
mote_devaddr = '01:4C:60:5E'

DatasourceID = 'e84cf38c68254d58979306a7fccd20c0'
StreamID = 'b9e841f17c564566829212a16e5797b3'

host = 'https://api.orange.com:443'
headers = {
        'User-Agent': 'python',
        'Content-Type': 'application/json',
        'X-ISS-Key': credentials.XISSKey,
        'X-OAPI-Key': credentials.XOAPIKey
}

url = '/datavenue/v1/datasources/'+ DatasourceID + '/streams/'+ StreamID
endpoint = host + url

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

print('Get stream infos:')
r = requests.get(endpoint, headers=headers)
print(r.status_code)
print(r.text)

url = '/datavenue/v1/datasources/'+ DatasourceID + '/streams/'+ StreamID + '/values'
endpoint = host + url

mote = Mote( )
mote.ActivateAbp( Mote_DevAddr, 
                    credentials.LoRa_nwkSKey,
                    credentials.LoRa_appSKey )

fcnt_prev = -1

while True:
    #print('Get stream values:')
    try:
        r = requests.get(endpoint, headers=headers)
    except requests.exceptions.Timeout:
        print('ERROR: Timeout')
        print(r.status_code)
        sleep(30)
        continue
    except requests.exceptions.TooManyRedirects:
        print('ERROR: Too Many Redirects')
        print(r.status_code)
        sleep(30)
        continue
    except requests.exceptions.RequestException as e:
        print('ERROR' + str(e))
        print(r.status_code)
        sleep(30)
        continue

    parsed_json = json.loads(r.text)
    num_frames = len(parsed_json)
    print('got ' + str(num_frames) + ' frames')

    # Display the whole content
    for frame in parsed_json:
        datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
        time = frame['at']
        port = frame['metadata']['port']
        fcnt = frame['metadata']['fcnt']
        enc_payload = bytes.fromhex(frame['value'])
        payload = mote.EncryptPayload(port, enc_payload, Mote_DevAddr, 0, fcnt)
        #payload_str = ''.join('{:02X}'.format( x ) for x in payload)
        #print(str(port) + '\t' + time + '\t' + str(frame['metadata']['fcnt']) + '\t' + frame['value'] + '\t' + payload_str)

    # Only send the last packet to UDP (if not already sent)
    fcnt = parsed_json[0]['metadata']['fcnt']
    if fcnt != fcnt_prev:
        color_matrix()
        print("Last:")
        time = parsed_json[0]['at']
        port = parsed_json[0]['metadata']['port']
        rssi = parsed_json[0]['metadata']['rssi']
        snr = parsed_json[0]['metadata']['snr']
        sf = parsed_json[0]['metadata']['sf_used']
        enc_payload = bytes.fromhex(parsed_json[0]['value'])
        payload = mote.EncryptPayload(port, enc_payload, Mote_DevAddr, 0, fcnt)
        payload_str = ''.join('{:02X}'.format( x ) for x in payload)
        print(str(port) + '\t' + time + '\t' + str(parsed_json[0]['metadata']['fcnt']) + '\t' + parsed_json[0]['value'] + '\t' + payload_str)

        json_send = {
            'mote': mote_devaddr,
            'at': time,
            'rssi': rssi,
            'snr': snr,
            'datr': sf,
            'fcnt': fcnt,
            'data': payload_str
        }
        print(json.dumps(json_send))
        sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
        sock.sendto(bytes(json.dumps(json_send), 'UTF-8'), (UDP_IP, UDP_PORT))
        fcnt_prev = fcnt

    # wait a moment before fetching new packets
    sleep(30)
