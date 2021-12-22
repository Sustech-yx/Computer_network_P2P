from Proxy import Proxy


class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None):
        self.proxy = Proxy(upload_rate, download_rate, port)
        self.files = {}

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

    def response(self, data: str, address: (str, int)):
        self.__send__(data.encode(), address)

    def start(self):
        """
        Start the Tracker and it will work forever
        :return: None
        """
        while 1:
            msg, frm = self.__recv__()
            msg, client = msg.decode(), "(\"%s\", %d)" % frm
            header = msg[0:3]
            if header[0] == '0':
                continue
            else:
                if header[1:3] == '00':  # register
                    fid = msg[3:]
                    if fid not in self.files:
                        self.files[fid] = []
                    self.files[fid].append(client)
                    self.response("regSuccess", frm)
                elif header[1:3] == '01':  # query
                    fid = msg[3:]
                    if fid not in self.files or len(self.files[fid]) == 0:
                        self.response("No peer", frm)
                    else:
                        result = []
                        for c in self.files[fid]:
                            result.append(c)
                        self.response('fid' + fid + "%s" % ("|".join(result)), frm)
                elif header[1:3] == '10':  # cancel
                    fid = msg[3:]
                    if client in self.files[fid]:
                        self.files[fid].remove(client)
                    self.response("canSuccess", frm)
                elif header[1:3] == '--':  # close
                    for fid, clients in self.files:
                        if client in clients:
                            self.files[fid].remove(client)
                    self.response("cloSuccess", frm)
        pass


if __name__ == '__main__':
    tracker = Tracker(port=10086)
    tracker.start()
