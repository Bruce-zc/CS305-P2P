import threading
import time

from PClient import PClient
from SimpleTracker import SimpleTracker

tracker_address = ("127.0.0.1", 44474)
tarfile = "../test_files/bg.png"


'''
SpeedTest_1.py:

Feature:
    15 clients register and 1 client download
File: 
    fid  bg.png  6074KB
Process: 
    15 clients register fid
    A download fid
'''


if __name__ == '__main__':
    # A,B join the network

    provider = []
    fid = ''
    for i in range(15):
        p = PClient(tracker_address, upload_rate=100000, download_rate=100000)
        fid = p.register(tarfile)
        provider.append(p)

    E = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    file = ''
    def download_files(file, client):
        file = client.download(fid)


    # E join the network and download this file
    t1 = threading.Thread(target=download_files,args=(file, E))



    time_start = time.time_ns()
    t1.start()
    t1.join()
    time1 = (time.time_ns() - time_start) * 1e-9


    for p in provider:
        p.close()


    # F join the network and download the file from E
    F = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    time_start = time.time_ns()
    data2 = F.download(fid)
    time2 = (time.time_ns() - time_start) * 1e-9
    # print(data2)

    f = open(file=tarfile, mode='rb', )
    data = f.read()
    print('File Size', len(data))
    if data == data2 :
        print("Simple Test1 Passed!")
    else:

        raise RuntimeError
    if file == data2:
        print("Simple Test2 Passed!")
    else:
        raise RuntimeError

    E.close()
    F.close()


    print('Time for multi-source:', time1)
    print('Time for single-source:', time2)