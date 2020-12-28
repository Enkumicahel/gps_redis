#!/usr/bin/env python3

import socket
import threading
import binascii
import logging
import requests

# logging.basicConfig()
logging.basicConfig(level=logging.DEBUG, filename='gps-coords.log', \
    filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

port = 8080
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', port))


def decodethis(data, imei):
    codec = int(data[16:18], 16)
    #print('\nHexlified data: ', data[:])
    if (codec == 8):
        length = int(data[8:16], 16)
        record = int(data[18:20], 16)
        timestamp = int(data[20:36], 16)
        priority = int(data[36:38], 16)
        lon = int(data[38:46], 16)
        lat = int(data[46:54], 16)
        alt = int(data[54:58], 16)
        angle = int(data[58:62], 16)
        sats = int(data[62:64], 16)  # maybe
        speed = int(data[64:68], 16)

        try:
            requests.get('http://197.156.65.169:8004/add_item?lng={}&lat={}&imei={}&speed={}&angle={}'.format(lon, lat, imei, speed, angle,))
        except Exception as e:
            logging.info(e)

        logging.info("Record: " + str(record) + ", Timestamp: " +
                     str(timestamp) + ", Lat,Lon: " + str(lat) + ", " +
                     str(lon) + ", Altitude: " + str(alt) + ", Sats: " +
                     str(sats) + ", Speed: " + str(speed) + ", Length: " +
                     str(length) + "\n")
        return "0000" + str(record).zfill(4)


def handle_client(conn, addr):
    logging.info("[NEW CONNECTION] {} connected.".format(addr))
    connected = True
    imei = conn.recv(1024)
    try:
        #print(int(binascii.hexlify(imei[:2]), 16), len(imei[2:]))
        if int(binascii.hexlify(imei[:2]), 16) == len(imei[2:]):
            message = '\x01'
            message = message.encode('utf-8')
            conn.send(message)
            logging.info('IMEI: {}'.format(imei[2:]))
            while connected:
                try:
                    data = conn.recv(1024)
                    recieved = binascii.hexlify(data)
                    if recieved:
                        record = decodethis(recieved, str(imei[2:], 'utf-8')).encode('utf-8')
                        conn.send(record)
                    else:
                        conn.close()
                except socket.error:
                    logging.error("Error Occured.")
                    conn.close() # new added
                    break
            else:
                conn.close() # newly added
        else:
            pass
            #conn.close()
    except:
        logging.error("Maybe it's not our device")

    conn.close()


def start():
    s.listen(1)
    print(" Server is listening ...")

    while True:
        conn, addr = s.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        # logging.error("[ACTIVE CONNECTIONS] {}".format(threading.activeCount() - 1))


print("[STARTING] server is starting...")

start()

