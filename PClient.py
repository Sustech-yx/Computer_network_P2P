import time
from Proxy import Proxy
import hashlib
from threading import Thread


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

        self.packet_size = 65000
        self.active = True
        self.tthread = Thread(target=self.transfer_thread)
        self.tthread.start()
        self.try_to_send = {}

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


    def transfer_thread(self):
        time.sleep(0.1)
        while self.active:
            try:
                msg, frm = self.__recv__(1)
            except Exception:
                continue
            if frm == ('127.0.0.1', 10086):
                continue
            try:
                fid = msg.decode()
            except Exception:
                continue
            # print(fid)
            fid1 = str(fid).split(' ')
            try:
                count = int(fid1[1])
            except Exception:
                continue
            # print(count)
            print("%s:%d ask %s for %s in" % (frm[0], frm[1], self.proxy.port, fid1[0]), count)
            try:
                msg = self.fid_addr_dict[fid1[0]]
            except Exception:
                continue
            if fid1[0] not in self.try_to_send:
                with open("%s" % msg, 'rb') as f:
                    data = f.read()
                packets = [data[i * self.packet_size: (i + 1) * self.packet_size]
                           for i in range(len(data) // self.packet_size + 1)]
                self.try_to_send[fid1[0]] = packets

            if count == 0:
                time.sleep(0.0001)
                self.proxy.sendto(msg.encode(), frm)
                time.sleep(0.0001)
                self.proxy.sendto(str(len(self.try_to_send[fid1[0]])).encode(), frm)

                # print("Total length of %s is %d bytes, %d packets" % (msg, len(data), len(packets)))
                # self.proxy.sendto(len(packets), frm)

                if fid1[0] in self.fid_addr_dict:
                    self.proxy.sendto(self.try_to_send[fid1[0]][count], frm)
                else:
                    continue
            else:
                try:
                    if fid1[0] in self.fid_addr_dict:
                        self.proxy.sendto(self.try_to_send[fid1[0]][count], frm)
                    else:
                        continue
                except Exception:
                    continue
                # print(self.try_to_send[fid1[0]])





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
        print(self.proxy.port, 'start')
        time.sleep(0.001)
        self.active = False
        fid = fid.decode()
        if fid.startswith('REGISTER:'):
            fid = fid[9:]
        time.sleep(0.0001)
        fid_ori = 'QUERY:' + str(fid)
        fid_ori = fid_ori.encode()
        # print(data_addr_1)
        count = 0
        stop = 1
        flag = False

        while count < stop:
            self.__send__(fid_ori, self.tracker)
            data_t = self.__recv__()
            data_addr = data_t[0].decode()
            if str(data_addr) == '[]':
                continue
            data_addr_1 = (str(data_addr[3:12]), int(data_addr[15:20]))
            fid1 = fid + ' ' + str(count)
            time.sleep(0.0001)
            self.__send__(fid1.encode(), data_addr_1)
            time.sleep(0.0001)
            # print(msg)
            if count == 0:
                data = b""
                msg, frm = self.__recv__()
                data += msg
                # print("%s receive %d" % (self.proxy.port, idx))

                self.fid_addr_dict[fid] = data.decode()
                data = b""
                msg, frm = self.__recv__()
                stop = int(msg.decode())
                msg, frm = self.__recv__()
                data += msg
                count += 1
            while count < stop:
                if flag:
                    flag = False
                    msg, frm = self.__recv__(5)
                try:
                    fid1 = fid + ' ' + str(count)
                    self.__send__(fid1.encode(), data_addr_1)
                    msg, frm = self.__recv__(5)
                except Exception:
                    # print('error')
                    flag = True
                    break
                data += msg
                count += 1

        self.active = True
        self.tthread = Thread(target=self.transfer_thread)
        self.tthread.start()

        time.sleep(0.0001)
        fid = 'REGISTER:' + str(fid_ori[6:].decode())
        fid = fid.encode()
        self.__send__(fid, self.tracker)
        time.sleep(0.0001)

        time.sleep(0.001)
        print('Finish')
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
        if fid.startswith('REGISTER:'):
            fid = fid[9:]
        del self.fid_addr_dict[fid]
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
        self.active = False
        self.proxy.close()


if __name__ == '__main__':
    pass
