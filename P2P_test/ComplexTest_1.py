import threading
import time

from PClient import PClient

'''
ComplexTest_1.py:

Feature:
    3 clients download 2 files from different sources at the same time
    One of the source will close
    One source cancel the file that only it owns for 10s
File: 
    fid1  ag.png  6074KB
    fid2  alice.txt  149KB
    fid3  bg.png  6074KB
    fid4  pic1.jpg  70KB
Process: 
    P1 register fid1
    P1 register fid2
    P2 register fid2
    P2 register fid3
    P3 register fid3
    P3 register fid4

    C1 download fid1 fid2 at the same time
    C2 download fid2 fid3 at the same time
    C3 download fid3 fid4 at the same time

    during F,G downloading:
        5s P3 cancel fid3
        15s P2 close
        45s P3 register fid 3
        
    all close
'''

tracker_address = ("127.0.0.1", 44484)

tarfile1 = "../test_files/ag.png"
tarfile2 = "../test_files/alice.txt"
tarfile3 = "../test_files/bg.png"
tarfile4 = "../test_files/pic1.jpg"

if __name__ == '__main__':

    P1 = PClient(tracker_address, upload_rate=200000, download_rate=100000)
    P2 = PClient(tracker_address, upload_rate=200000, download_rate=100000)
    P3 = PClient(tracker_address, upload_rate=200000, download_rate=100000)

    print('Port of P1:'+str(P1.proxy.port))
    print('Port of P2:'+str(P2.proxy.port))
    print('Port of P3:'+str(P3.proxy.port))

    fid1 = P1.register(tarfile1)
    fid2 = P1.register(tarfile2)

    P2.register(tarfile2)
    fid3 = P2.register(tarfile3)

    P3.register(tarfile3)
    fid4 = P3.register(tarfile4)



    C1 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    C2 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    C3 = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    files = {0: ''}


    def download(node, index, fid):
        files[index] = node.download(fid)


    t1 = threading.Thread(target=download, args=(C1, 1, fid1))
    t2 = threading.Thread(target=download, args=(C1, 2, fid2))
    t3 = threading.Thread(target=download, args=(C2, 3, fid2))
    t4 = threading.Thread(target=download, args=(C2, 4, fid3))
    t5 = threading.Thread(target=download, args=(C3, 5, fid3))
    t6 = threading.Thread(target=download, args=(C3, 6, fid4))

    threads = [t1, t2, t3, t4, t5, t6]

    for t in threads:
        t.start()

    time.sleep(5)
    P3.cancel(fid3)
    print("bg.png cancelled!")

    time.sleep(10)
    P2.close()
    print("P2 closed!")

    time.sleep(30)
    P3.register(tarfile3)
    print("bg.png registered!")

    for t in threads:
        t.join()

    f1 = open(file=tarfile1, mode='rb', ).read()
    f2 = open(file=tarfile2, mode='rb', ).read()
    f3 = open(file=tarfile3, mode='rb', ).read()
    f4 = open(file=tarfile4, mode='rb', ).read()

    if f1 == files[1]:
        pass
    else:
        print('Original Length:', len(f1))
        print('Received Length:', len(files[1]))
        print(f1 == files[1])
        raise RuntimeError

    if f2 == files[2] and f2 == files[3]:
        pass
    else:
        print('Original Length:', len(f2))
        print('Received Length:', len(files[2]), ',', len(files[3]))
        print(f2 == files[2], f2 == files[3])
        raise RuntimeError

    if f3 == files[4] and f3 == files[5]:
        pass
    else:
        print('Original Length:', len(f3))
        print('Received Length:', len(files[4]), ',', len(files[5]))
        print(f3 == files[4], f3 == files[5])
        raise RuntimeError

    if f4 == files[6]:
        pass
    else:
        print('Original Length:', len(f4))
        print('Received Length:', len(files[6]))
        print(f4 == files[6])
        raise RuntimeError

    P1.close()
    P3.close()
    C1.close()
    C2.close()
    C3.close()

    print("Complex Test 4 Pass!")
