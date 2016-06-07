#!/usr/bin/python3

import json
import requests
from mote import Mote
import binascii

XISSKey = '2662049a51094939ae38f1129d065a76'
XOAPIKey = 'RG4IAwwsTw8uJSNb9rlc4TnNoxUYDQ13'
DatasourceID = '203f7590d8a4402a88b2053c12740925'
StreamID = '6956102728674cfd8165b7ef720b2bb0'

host = 'https://api.orange.com:443'
headers = {
        'User-Agent': 'python',
        'Content-Type': 'application/json',
        'X-ISS-Key': XISSKey,
        'X-OAPI-Key': XOAPIKey
}

url = '/datavenue/v1/datasources/'+ DatasourceID + '/streams/'+ StreamID
endpoint = host + url

print('Get stream infos:')
r = requests.get(endpoint, headers=headers)
print(r.status_code)
print(r.text)

url = '/datavenue/v1/datasources/'+ DatasourceID + '/streams/'+ StreamID + '/values'
endpoint = host + url

print('Get stream values:')
r = requests.get(endpoint, headers=headers)
print(r.status_code)
print(r.text)

parsed_json = json.loads(r.text)
num_frames = len(parsed_json)
print('got ' + str(num_frames) + ' frames')

mote = Mote( )
mote.ActivateAbp( 0x00CC01AF, 
                  "2B7E151628AED2A6ABF7158809CF4F3C",
                  "2B7E151628AED2A6ABF7158809CF4F3C" )

for frame in parsed_json:
    time = frame['at']
    port = frame['metadata']['port']
    fcnt = frame['metadata']['fcnt']
    enc_payload = bytes.fromhex(frame['value'])
    payload = mote.EncryptPayload(port, enc_payload, 0x00CC01AF, 0, fcnt)
    payload_str = ''.join('{:02X}'.format( x ) for x in payload)
    #print(frame)
    print(str(port) + '\t' + time + '\t' + str(frame['metadata']['fcnt']) + '\t' + frame['value'] + '\t' + payload_str)
