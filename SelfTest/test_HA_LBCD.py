import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 10086)


if __name__ == '__main__':
    # A,B,C,D,E join the network
    A = PClient(tracker_address, upload_rate=200000, download_rate=200000)
    B = PClient(tracker_address, upload_rate=600000, download_rate=600000)
    C = PClient(tracker_address, upload_rate=500000, download_rate=500000)
    D = PClient(tracker_address, upload_rate=800000, download_rate=800000)

    clients = [B, C, D]
    # A register a file and B download it
    fid = A.register("../test_files/bg.png")
    threads = []
    files = {}

    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)

    time_start = time.time_ns()
    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(client, i)))
    # start download in parallel
    for t in threads:
        t.start()
    # wait for finish
    for t in threads:
        t.join()
    # check the downloaded files
    with open("../test_files/bg.png", "rb") as bg:
        bs = bg.read()
        for i in files:
            if files[i] != bs:
                raise Exception("Downloaded file is different with the original one")

    # B, C, D, E has completed the download of file
    threads.clear()


    A.close()
    B.close()
    C.close()
    D.close()
