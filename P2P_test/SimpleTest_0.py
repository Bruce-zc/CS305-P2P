import threading
import time

from PClient import PClient

tracker_address = ("127.0.0.1", 44494)


'''
SimpleTest_0.py:

Feature:
    2 clients download file mutually
File:
    fid1  bg.png     6074KB
    fid2  pic1.jpg   71KB
    fid3  alice.txt  149KB
Process: 
    A register fid1
    A register fid2
    B register fid3
    A download fid3, B download fid2, 
        C download fid1 at the same time
    A close
    B close
    C close
'''


if __name__ == '__main__':

    P1 = PClient(tracker_address, upload_rate=200000, download_rate=200000)

    fid1 = P1.register("../test_files/bg.png")
    fid2 = P1.register("../test_files/pic1.jpg")

    P2 = PClient(tracker_address, upload_rate=200000, download_rate=200000)

    fid3 = P2.register("../test_files/alice.txt")

    P3 = PClient(tracker_address, upload_rate=200000, download_rate=200000)

    files = {0: ''}


    def download(node, index, fid):
        files[index] = node.download(fid)


    t1 = threading.Thread(target=download, args=(P1, 3, fid3))
    t2 = threading.Thread(target=download, args=(P2, 2, fid2))
    t3 = threading.Thread(target=download, args=(P3, 1, fid1))

    threads = [t1, t2, t3]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    f1 = open(file="../test_files/bg.png", mode='rb', ).read()
    f2 = open(file="../test_files/pic1.jpg", mode='rb', ).read()
    f3 = open(file="../test_files/alice.txt", mode='rb', ).read()

    if files[1] != f1 or files[2] != f2 or files[3] != f3:
        raise Exception
    else:
        print("Complex Test 2 Passed!")

    P1.close()
    P2.close()
    P3.close()
