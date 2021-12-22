from Proxy import *

import hashlib
from threading import Thread
import time
from queue import SimpleQueue


class PClient:
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        self.fid_file_dict = {}
        self.tracker_msg = SimpleQueue()
        self.clients_msg = SimpleQueue()
        self.activate = True
        Thread(target=self.__listen__).start()
        """
        Start your additional code below!
        """

    def __str__(self):
        return str(self.proxy.port)

    def __listen__(self):
        while self.activate:
            try:
                msg, frm = self.__recv__(sleep_time)
            except TimeoutError:
                time.sleep(sleep_time)
                continue
            msg = msg.decode()
            if frm == self.tracker:
                self.tracker_msg.put(msg)
            else:
                self.clients_msg.put(msg)

    def __send__(self, data: bytes, dst: (str, int)):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send
        :param dst: The address of the destination
        """
        self.proxy.sendto(data, dst)

    def __recv__(self, timeout=None) -> (bytes, (str, int)):
        """
        Do not modify this function!!!
        You must receive all data from this function!!!
        :param timeout: if its value has been set, it can raise a TimeoutError;
                        else it will keep waiting until receive a packet from others
        :return: a tuple x with packet data in x[0] and the source address(ip, port) in x[1]
        """
        return self.proxy.recvfrom(timeout)

    def getRespond(self, tp, **kwargs):
        if tp == 0:
            hasRespond = False
            while not hasRespond:
                if self.tracker_msg.empty():
                    continue
                else:
                    while 1:
                        msg = self.tracker_msg.get()
                        if not msg.startswith('fid'):
                            pass
                        else:
                            res_fid = msg[3:35]
                            if res_fid == kwargs['fid']:
                                hasRespond = True
                                break
                            else:
                                pass
                        self.tracker_msg.put(msg)


    def register(self, file_path: str):
        """
        Share a file in P2P network
        :param file_path: The path to be shared, such as "./alice.txt"
        :return: fid, which is a unique identification of the shared file and can be used by other PClients to
                 download this file, such as a hash code of it
        """
        file = open(file_path, 'rb')
        _hash = hashlib.md5()
        for line in file:
            _hash.update(line)
        fid = str(_hash.hexdigest())
        self.fid_file_dict[fid] = file_path
        msg = '100' + fid
        msg = msg.encode()
        self.__send__(msg, self.tracker)

        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        msg = '101' + fid
        msg = msg.encode()
        self.__send__(msg, self.tracker)
        hasRespond = False
        while not hasRespond:
            if self.tracker_msg.empty():
                continue
            else:
                while 1:
                    msg = self.tracker_msg.get()
                    if not msg.startswith('fid'):
                        pass
                    else:
                        res_fid = msg[3:35]
                        if res_fid == fid:
                            hasRespond = True
                            break
                        else:
                            pass
                    self.tracker_msg.put(msg)
        addresses = msg[35:]
        print(addresses)
        return None

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """

        pass

        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        self.activate = False
        self.proxy.close()


if __name__ == '__main__':
    pass
