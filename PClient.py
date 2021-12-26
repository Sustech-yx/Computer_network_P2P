import time
import sys
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
            # try 和 except 是防止接听自己是出错
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
            # print("%s:%d ask %s for %s in" % (frm[0], frm[1], self.proxy.port, fid1[0]), count)
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
                # 发送第一个包，同时发送总长并保存packets
                time.sleep(0.0001)
                self.proxy.sendto(msg.encode(), frm)
                time.sleep(0.0001)
                self.proxy.sendto(str(len(self.try_to_send[fid1[0]])).encode(), frm)

                # print("Total length of %s is %d bytes, %d packets" % (msg, len(data), len(packets)))
                # self.proxy.sendto(len(packets), frm)

                count1 = str(count)
                while len(count1) < 6:
                    count1 = '0' + count1

                if fid1[0] in self.fid_addr_dict:
                    sd = self.try_to_send[fid1[0]][count] + count1.encode()
                    self.proxy.sendto(sd, frm)
                else:
                    continue
            else:
                # 正常传送
                try:
                    count1 = str(count)
                    while len(count1) < 6:
                        count1 = '0' + count1
                    if fid1[0] in self.fid_addr_dict:
                        sd = self.try_to_send[fid1[0]][count] + count1.encode()
                        self.proxy.sendto(sd, frm)
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
        flag = False # 防止换人传时的重复传输
        data = [None]
        ack = [0]
        q = [0]

        print(self.proxy.port, 'start transfer')
        while ack:
            start = time.time()
            # print(start)
            self.__send__(fid_ori, self.tracker)
            try:
                data_t = self.__recv__(2)
            except TimeoutError:
                print("tracker out")
                continue
            data_addr = data_t[0]
            if str(data_addr) == '[]' or len(str(data_addr)) > 300:
                # print('rubbish')
                continue
            index = 0
            data_addr = str(data_addr.decode())
            data_addr_1 = []
            # print(data_addr)
            while index + 20 < len(str(data_addr)):
                data_addr_1.append((str(data_addr[index + 3:index + 12]), int(data_addr[index + 15:index + 20])))
                index += 22
            # print(self.proxy.port, data_addr_1)
            while count == 0:
                fid1 = fid + ' ' + str(count)
                time.sleep(0.0001)
                self.__send__(fid1.encode(), data_addr_1[0])
                time.sleep(0.0001)
                # 乞求第一个包
                data1 = b""
                msg, frm = self.__recv__()
                data1 += msg
                # print("%s receive %d" % (self.proxy.port, idx))

                self.fid_addr_dict[fid] = data1.decode()
                # print(self.fid_addr_dict, self.proxy.port)
                msg, frm = self.__recv__()
                if len(msg) > 100:
                    continue
                stop = int(msg)
                count += 1
                ack = []
                q = []
                for i in range(count, stop):
                    ack.append(i)
                    q.append(i)
                    data.append(None)
                # print(q)
                msg, frm = self.__recv__()
                # msg = str(msg.decode())
                msg1 = msg[-6:]
                msg2 = msg[:-6]
                data[int(msg1)] = msg2
                for i in range(len(data_addr_1)):
                    if not q:
                        break
                    k = q.pop()
                    fid1 = fid + ' ' + str(k)
                    self.__send__(fid1.encode(), data_addr_1[i])
            else:
                for i in range(len(data_addr_1)):
                    if not q:
                        break
                    k = q.pop()
                    fid1 = fid + ' ' + str(k)
                    self.__send__(fid1.encode(), data_addr_1[i])
                    # print(fid1)
            while ack:
                # print(self.proxy.port, ack)
                if time.time() - start >= 70:
                    q.clear()
                    for i in range(len(ack)):
                        q.append(ack[i])
                    break
                try:
                    msg, frm = self.__recv__(5)
                    if frm == self.tracker:
                        continue
                    msg1 = msg[-6:]
                    msg2 = msg[:-6]
                    data[int(msg1)] = msg2
                    if int(msg1) in ack:
                        ack.remove(int(msg1))
                    if q:
                        k = q.pop()
                        fid1 = fid + ' ' + str(k)
                        self.__send__(fid1.encode(), frm)
                    print("\r", end="")
                    print(self.proxy.port, "Download progress: {}%: ".format(int((stop - (len(ack))) / stop * 100)),
                          "▋" * (int(((stop - (len(ack))) / stop * 100)) // 2), end="")
                    sys.stdout.flush()
                except TimeoutError:
                    # print('timeout')
                    q.clear()
                    # print(ack)
                    for i in range(len(ack)):
                        q.append(ack[i])
                    break
        data1 = b""
        for i in range(len(data)):
            data1 += data[i]
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

        return data1

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
        self.active = False
        time.sleep(0.0001)
        # print('close', self.fid_addr_dict, self.proxy.port)
        for i, _ in self.fid_addr_dict.items():
            fid = i
            # print(fid)
            fid = 'CANCEL:' + str(fid)
            # print(fid)
            fid = fid.encode()
            # print(fid)
            self.__send__(fid, self.tracker)
            time.sleep(0.1)
            self.__send__(fid, self.tracker)
            time.sleep(0.1)
            self.__send__(fid, self.tracker)
            time.sleep(0.1)
            self.__send__(fid, self.tracker)
        self.fid_addr_dict.clear()
        """
        End of your code
        """
        self.proxy.close()


if __name__ == '__main__':
    pass
