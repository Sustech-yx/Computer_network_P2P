from PClient import PClient
import threading
import difflib

d = difflib.Differ()
tracker_address = ("127.0.0.1", 10086)

if __name__ == '__main__':
    # A,B join the network
    A = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)
    B = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)
    print(A, B)

    # A register a file and B download it
    fid = A.register("../test_files/alice.txt")
    print('register complete')
    data1 = B.download(fid)

    data = b''
    with open('../test_files/alice.txt', 'rb') as f:
        line = f.readline()
        while line != b'':
            data += line
            line = f.readline()
    if data1 == data:
        print('download complete')
    else:
        data = data.decode()
        data1 = data1.decode()
        print(len(data1), len(data))
        print('something wrong happen!')
        # diff = d.compare(data1, data)
        # print(''.join(list(diff)))
        with open('../test_files/alice_comp.txt', 'w') as f:
            f.write(data1)
        print('please check the different!')
    # A cancel the register of the file

    A.close()

    # C join the network and download the file from B
    C = PClient(tracker_address, upload_rate=1000000, download_rate=1000000)

    data2 = C.download(fid)

    if data1 == data2:
        print("Success!")
        # print(threading.enumerate())
        # print(data1)
    else:
        raise RuntimeError

    B.close()
    C.close()
