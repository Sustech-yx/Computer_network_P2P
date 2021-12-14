import time

from Proxy import Proxy
import hashlib


class PClient:
    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        """
        Start your additional code below!
        """
        self.fid_addr_dict = {}




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

    def register(self, file_path: str):
        """
        Share a file in P2P network
        :param file_path: The path to be shared, such as "./alice.txt"
        :return: fid, which is a unique identification of the shared file and can be used by other PClients to
                 download this file, such as a _hash code of it
        """
        fid = None
        """
        Start your code below!
        """
        time.sleep(0.0001)
        file = open(file_path, 'rb')
        _hash = hashlib.md5()
        for line in file:
            _hash.update(line)
        fid = str(_hash.hexdigest())
        self.fid_addr_dict[fid] = file_path
        fid = 'REGISTER:' + fid
        fid = fid.encode()
        self.__send__(fid, self.tracker)
        file.close()
        time.sleep(0.0001)
        """
        End of your code
        """
        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of register()
        :return: the whole received file in bytes
        """
        data = None
        """
        Start your code below!
        """
        fid = fid.decode()
        if fid.startswith('REGISTER:'):
            fid = fid[9:]
        time.sleep(0.0001)
        fid = 'QUERY:' + str(fid)
        fid = fid.encode()
        self.__send__(fid, self.tracker)
        fid = fid.decode()
        fid = fid[6:]
        data = self.__recv__()
        fid = 'REGISTER:' + str(fid)
        fid = fid.encode()
        self.__send__(fid, self.tracker)



        """
        End of your code
        """
        return data

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """
        time.sleep(0.0001)
        fid = fid.decode()
        self.fid_addr_dict.pop(fid)
        if fid.startswith('REGISTER:'):
            fid = fid[9:]
        time.sleep(0.0001)
        fid = 'CANCEL:' + str(fid)
        fid = fid.encode()
        self.__send__(fid, self.tracker)
        time.sleep(0.0001)

        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        time.sleep(0.0001)
        for i in self.fid_addr_dict:
            time.sleep(0.0001)
            time.sleep(0.0001)
            fid = i
            time.sleep(0.0001)
            fid = 'CANCEL:' + str(fid)
            fid = fid.encode()
            self.__send__(fid, self.tracker)
            time.sleep(0.0001)
            time.sleep(0.0001)
        self.fid_addr_dict.clear()
        """
        End of your code
        """
        self.proxy.close()


if __name__ == '__main__':
    pass
