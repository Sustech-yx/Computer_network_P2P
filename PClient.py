from Proxy import *

import hashlib
from threading import Thread
import time
from queue import SimpleQueue
import re
import os
from copy import deepcopy as cp


class PClient:
    pkg_size = 65000

    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        self.fid_file_dict = {}
        self.download_buffer = {}
        # the key is the fid, and the value is a list of tuple, the first element of the
        # is the sequence number, and the second element of the tuple is data.
        self.download_progress = {}  # comment it for no usage
        self.download_addresses = {}
        self.download_flag = {}
        # the key is the fid, and the value is a dict of boolean which specify whether the
        # peer has complete them task
        self.port = self.proxy.port

        self.tracker_msg = SimpleQueue()
        self.clients_msg = SimpleQueue()
        self.sending_thread_id = []  # To prevent the repeated thread
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
                msg, frm = self.__recv__(10 * sleep_time)
            except TimeoutError:
                time.sleep(sleep_time)
                continue
            # msg = msg.decode()
            if frm == self.tracker:
                self.tracker_msg.put((msg, frm))
            else:
                self.clients_msg.put((msg, frm))
                header = msg[0:8].decode()
                if header == 'request0':
                    fid = msg[8:40].decode()
                    if (fid, frm) not in self.sending_thread_id:
                        if debug:
                            print(fid, self.fid_file_dict, frm)
                            pass
                        self.sending_thread_id.append((fid, frm))
                        thread = Thread(target=self.__send_pkg__, args=(fid, frm))
                        print(fid, frm)
                        thread.start()

    def __send_pkg__(self, fid: str, dst: (str, int)):
        file_path = self.fid_file_dict[fid][0]
        file_size = self.fid_file_dict[fid][1]
        respond_pkg = 'ack0' + fid + 'length:' + str(file_size)
        self.__send__(respond_pkg.encode(), dst)

        # send the file information to the peer who need this file ended.
        # then receive the specific task from the peer and give the corresponding fragment.

        with open(file_path, 'rb') as f:
            data = f.read()
        while 1:
            res = self.getRespond(5, pkg=respond_pkg, dst=dst, timeout=120, fid=fid, frm=dst)
            header = res[0:8].decode()

            if header == 'request1':
                # this means that the peer need package.
                index = int(res[52:].decode())
                data_frag = data[index * PClient.pkg_size:(index + 1) * PClient.pkg_size]
                index = str(index)
                while len(index) < 6:
                    index = '0' + index
                respond_pkg = ('ack1' + fid + 'package_cnt:' + str(index) + 'data:').encode() + data_frag
                self.__send__(respond_pkg, dst)
                pass
            elif header == 'request2':
                # this means that the peer need the file path of the file
                # and now the client do not need to send data. (It tasks have been completed).
                respond_pkg = 'ack2' + fid + file_path
                self.__send__(respond_pkg.encode(), dst)
                break
            else:  # strange branch, I do not know what will happen in this branch. Just print it.
                if debug:
                    # print(res)
                    pass
        self.sending_thread_id.remove((fid, dst))
        if debug:
            print(f'Task to {dst} has complete')

    def __recv_pkg__(self, fid: str, dst: (str, int), index: int, total_peer_cnt=1):
        request_pkg = 'request0' + fid
        # request for the information of the file
        self.__send__(request_pkg.encode(), dst)
        res = self._getRespond(2, fid=fid, frm=dst)
        while res is None:
            self.__send__(request_pkg.encode(), dst)
            time.sleep(sleep_time)
            res = self._getRespond(2, fid=fid, frm=dst)
        pkg_inform = cp(res).decode()
        pattern = re.compile(r'length:\d+')
        m = pattern.findall(pkg_inform)
        file_length = int(m[0][7:])
        package_cnt = file_length // PClient.pkg_size if file_length % PClient.pkg_size == 0 \
            else file_length // PClient.pkg_size + 1
        print(f'package count: {package_cnt}')
        task = []
        # arrange the task for each client who has the file. For example, there are 3 clients and the file is
        # separated into 17 packages:
        #       A  B  C  D  E
        # INDEX 0  1  2  3  4
        # --------------------
        #       0  1  2  3  4
        # TASKS 5  6  7  8  9
        #       10 11 12 13 14
        #       15 16 17
        for p in range(package_cnt):
            if (p + 1) % total_peer_cnt == index:
                task.append(p)
        for t in task:
            request_pkg = 'request1' + fid + 'package_cnt:' + str(t)
            self.__send__(request_pkg.encode(), dst)
            res = self.getRespond(3, pkg=request_pkg, dst=dst, timeout=120, fid=fid, cnt=t, frm=dst)

            self.processTask(fid, res)

        request_pkg = 'request2' + fid
        self.__send__(request_pkg.encode(), dst)
        res = self._getRespond(4, fid=fid, frm=dst)
        # got the file path of the file. That will lead to the file size of the file, of course.
        while res is None:
            self.__send__(request_pkg.encode(), dst)
            time.sleep(sleep_time)
            res = self._getRespond(4, fid=fid, frm=dst)
        res = res[4:]
        res = res[32:].decode()
        if fid not in self.fid_file_dict.keys():
            self.fid_file_dict[fid] = (res, os.path.getsize(res))
        if debug:
            print(f'Task from {dst} has complete')

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

    def getRespond(self, tp, pkg, dst, timeout=None, **kwargs):
        if timeout is None:
            res = self._getRespond(tp, **kwargs)
            while res is None:
                self.__send__(pkg.encode(), dst)
                time.sleep(sleep_time)
                res = self._getRespond(tp, **kwargs)
        else:
            start_time = time.time()
            res = self._getRespond(tp, **kwargs)
            while res is None:
                time.sleep(sleep_time)
                res = self._getRespond(tp, **kwargs)
                if time.time() - start_time > timeout:
                    raise TimeoutError
        return res

    def _getRespond(self, tp, **kwargs):  # tp is the type of the message for the client will listen
        msg = None
        if tp == 0:  # download
            hasRespond = False
            while not hasRespond:
                if self.tracker_msg.empty():
                    continue
                else:
                    while 1:
                        msg, frm = self.tracker_msg.get()
                        msg = msg.decode()
                        if not msg.startswith('fid'):
                            pass
                        else:
                            res_fid = msg[3:35]
                            if res_fid == kwargs['fid']:
                                hasRespond = True
                                break
                            else:
                                pass
                        self.tracker_msg.put(msg.encode(), frm)
        elif tp == 1:  # register
            if self.tracker_msg.empty():
                pass
            else:
                while 1:
                    msg, frm = self.tracker_msg.get()
                    msg = msg.decode()
                    if not msg.startswith('reg'):
                        pass
                    else:
                        temp = msg[3:]
                        if temp == 'Success':
                            break
                        else:
                            pass
                    self.tracker_msg.put(msg.encode(), frm)
        elif tp == 2:  # request 0
            if self.clients_msg.empty():
                pass
            else:
                while 1:
                    msg, frm = self.clients_msg.get()
                    header = msg[0:4].decode()
                    if not header == 'ack0' or frm != kwargs['frm']:
                        pass
                    else:
                        temp = msg[4:36].decode()
                        if temp == kwargs['fid']:
                            break
                        else:
                            pass
                    self.clients_msg.put((msg, frm))
        elif tp == 3:  # request1
            if self.clients_msg.empty():
                pass
            else:
                # if debug:
                #     print(self.clients_msg.qsize())
                while 1:
                    msg, frm = self.clients_msg.get()
                    header = msg[0:4].decode()

                    if header == 'ack0' and msg[4:36] == kwargs['fid'] and frm == kwargs['frm']:
                        return None
                    if not header == 'ack1' or frm != kwargs['frm']:
                        pass
                    else:
                        temp1 = msg[4:36].decode()
                        index = int(msg[48:54].decode())
                        if temp1 == kwargs['fid'] and kwargs['cnt'] == index:
                            break
                        else:
                            return None
                    self.clients_msg.put((msg, frm))
        elif tp == 4:  # request2
            if self.clients_msg.empty():
                pass
            else:
                while 1:
                    msg, frm = self.clients_msg.get()
                    header = msg[0:4].decode()
                    if (header == 'ack0' or header == 'ack1') \
                            and msg[4:36].decode() == kwargs['fid'] and frm == kwargs['frm']:
                        return None
                    if not header == 'ack2' or frm != kwargs['frm']:
                        pass
                    else:
                        temp = msg[4:36].decode()
                        if temp == kwargs['fid']:
                            break
                        else:
                            pass
                    self.clients_msg.put((msg, frm))
        elif tp == 5:  # respond for request 1 and 2
            if self.clients_msg.empty():
                pass
            else:
                while 1:
                    msg, frm = self.clients_msg.get()
                    header = msg[0:8].decode()
                    if header == 'request0' and frm == kwargs['frm']:
                        return None
                    if not (header == 'request2' or header == 'request1') or frm != kwargs['frm']:
                        pass
                    else:
                        temp = msg[8:40].decode()
                        if temp == kwargs['fid']:
                            break
                        else:
                            pass
                    self.clients_msg.put((msg, frm))
        elif tp == 6:  # close
            hasRespond = False
            while not hasRespond:
                if self.tracker_msg.empty():
                    continue
                else:
                    while 1:
                        msg, frm = self.tracker_msg.get()
                        msg = msg.decode()
                        if msg == 'cloSuccess':
                            hasRespond = True
                            break
                        else:
                            continue
        elif tp == 7:  # cancel
            hasRespond = False
            while not hasRespond:
                if self.tracker_msg.empty():
                    continue
                else:
                    while 1:
                        msg, frm = self.tracker_msg.get()
                        msg = msg.decode()
                        if msg == 'canSuccess':
                            hasRespond = True
                            break
                        else:
                            continue
        return msg

    def processTask(self, fid, result: str):
        result = result[4:]  # remove ack1
        result = result[32:]  # remove fid
        result = result[12:]  # remove 'package_cnt:'

        cnt = int(result[0:6])

        result = result[6:]  # remove the number
        data = result[5:]

        if debug:
            print(self.port, cnt)
        if self.download_buffer[fid] is None:
            self.download_buffer[fid] = []
        self.download_buffer[fid].append((cnt, data))

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
        self.fid_file_dict[fid] = (file_path, os.path.getsize(file_path))
        msg = '100' + fid
        msg = msg.encode()
        self.__send__(msg, self.tracker)
        res = self._getRespond(1)
        while res is None:
            self.__send__(msg, self.tracker)
            time.sleep(sleep_time)
            res = self._getRespond(1)
        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        self.download_progress[fid] = False
        msg = '101' + fid
        msg = msg.encode()
        self.__send__(msg, self.tracker)
        res = self._getRespond(0, fid=fid)
        temp = res[35:]
        temp = temp.split('|')
        addresses = []
        for address in temp:
            t = address.replace(' ', '').replace('(', '').replace(')', '').replace('"', '').split(',')
            addresses.append((str(t[0]), int(t[1])))
        del address
        # get all the addresses
        num_of_peer = len(addresses)
        self.download_buffer[fid] = []
        self.download_addresses[fid] = addresses
        dst = self.download_addresses[fid][0]
        request_pkg = 'request0' + fid
        # request for the information of the file
        self.__send__(request_pkg.encode(), dst)
        res = self._getRespond(2, fid=fid, frm=dst)
        while res is None:
            self.__send__(request_pkg.encode(), dst)
            time.sleep(sleep_time)
            res = self._getRespond(2, fid=fid, frm=dst)
        pkg_inform = cp(res).decode()
        pattern = re.compile(r'length:\d+')
        m = pattern.findall(pkg_inform)
        file_length = int(m[0][7:])
        package_cnt = file_length // PClient.pkg_size if file_length % PClient.pkg_size == 0 \
            else file_length // PClient.pkg_size + 1
        print(f'package count: {package_cnt}')
        # obtain the package size of the file
        self.download_progress[fid] = []
        for index in range(package_cnt):
            self.download_progress[fid].append(index)

        while 1:
            receive_threads = []
            for index, peer in enumerate(self.download_addresses[fid]):
                receive_threads.append(Thread(target=self.__recv_pkg__,
                                              kwargs={'fid': fid, 'dst': peer,
                                                      'index': self.download_progress[fid].pop()}))
                for thread in receive_threads:
                    thread.start()

            if len(self.download_progress[fid]) == 0:
                if len(list(set(self.download_buffer))) == package_cnt:
                    self.download_flag[fid] = True
                    break

        dst = self.download_addresses[fid][0]
        request_pkg = 'request2' + fid
        self.__send__(request_pkg.encode(), dst)
        res = self._getRespond(4, fid=fid, frm=dst)
        # got the file path of the file. That will lead to the file size of the file, of course.
        while res is None:
            self.__send__(request_pkg.encode(), dst)
            time.sleep(sleep_time)
            res = self._getRespond(4, fid=fid, frm=dst)
        res = res[4:]
        res = res[32:].decode()
        if fid not in self.fid_file_dict.keys():
            self.fid_file_dict[fid] = (res, os.path.getsize(res))

        data = b''
        self.download_buffer[fid] = list(set(self.download_buffer[fid]))
        self.download_buffer[fid] = sorted(self.download_buffer[fid], key=lambda x: x[0])

        for buffer in self.download_buffer[fid]:
            data += buffer[1]

        self.register(self.fid_file_dict[fid][0])

        del self.download_buffer[fid]
        del self.download_progress[fid]
        del self.download_flag[fid]
        del self.download_addresses[fid]

        if debug:
            print(f'Task from {dst} has complete')
        return data

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """
        cancel_pkg = '110' + fid
        cancel_pkg = cancel_pkg.encode()
        self.__send__(cancel_pkg, self.tracker)
        res = self._getRespond(7)
        while res is None:
            self.__send__(cancel_pkg, self.tracker)
            time.sleep(sleep_time)
            res = self._getRespond(7)
        print(res)

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """
        close_pkg = '1--'
        close_pkg = close_pkg.encode()
        self.__send__(close_pkg, self.tracker)
        res = self._getRespond(6)
        while res is None:
            self.__send__(close_pkg, self.tracker)
            time.sleep(sleep_time)
            res = self._getRespond(6)
        print(res)
        self.activate = False
        self.proxy.close()
        # clear the queue
        self.clients_msg = SimpleQueue()
        self.clients_msg = SimpleQueue()
        print('close complete')


if __name__ == '__main__':
    pass
