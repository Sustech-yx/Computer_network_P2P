from PClient import PClient
import threading

tracker_address = ("127.0.0.1", 10086)

if __name__ == '__main__':
    # A,B join the network
    A = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    print(A, B)

    # A register a file and B download it
    fid = A.register("../test_files/alice.txt")
    data1 = B.download(fid)
    # A cancel the register of the file
    A.close()

    # C join the network and download the file from B
    C = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    data2 = C.download(fid)

    if data1 == data2:
        print("Success!")
        print(threading.enumerate())
    else:
        raise RuntimeError

    B.close()
    C.close()
