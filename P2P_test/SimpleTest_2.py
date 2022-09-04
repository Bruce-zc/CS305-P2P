import threading
import time

from PClient import PClient

tracker_address = ("127.0.0.1", 44494)


'''
SimpleTest_2.py:

Feature:
    parallel download 2 files
File:
    fid1  xl.xlsx    14KB
    fid2  pic1.jpg   71KB
Process: 
    A register fid1
    A register fid2
    B download fid1, fid2 
        at the same time (from A)
    A close
    B close
'''


if __name__ == '__main__':

    P1 = PClient(tracker_address, upload_rate=200000, download_rate=200000)

    fid1 = P1.register("../test_files/alice.txt")
    fid2 = P1.register("../test_files/pic1.jpg")

    P2 = PClient(tracker_address, upload_rate=200000, download_rate=200000)

    files = {0: ''}


    def download(node, index, fid):
        files[index] = node.download(fid)


    t1 = threading.Thread(target=download, args=(P2, 1, fid1))
    t2 = threading.Thread(target=download, args=(P2, 2, fid2))
    threads = [t1, t2]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    f1 = open(file="../test_files/alice.txt", mode='rb', ).read()
    f2 = open(file="../test_files/pic1.jpg", mode='rb', ).read()

    if files[1] != f1 or files[2] != f2:
        print(files[1] == f1 or files[2] == f2)
        raise Exception
    else:
        print("Parallel Download Test Passed!")

    P1.close()
    P2.close()
