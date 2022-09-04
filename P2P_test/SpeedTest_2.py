import time
from threading import Thread
from PClient import PClient
from SimpleTracker import SimpleTracker

tracker_address = ("127.0.0.1", 44484)
tarfile = "../test_files/alice.txt"

if __name__ == '__main__':
    # A,B,C,D,E join the network
    A1 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    A2 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    A3 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    C = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    D = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    E = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    print(A1.proxy.port)
    #print(A2.proxy.port)

    clients = [B,C,D,E]
    threads = []
    files = {}

    # A register a file
    fid = A1.register(tarfile)
    A2.register(tarfile)
    A3.register(tarfile)

    def download(node, index):
        files[index] = node.download(fid)


    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(client, i)))

    time_start = time.time_ns()
    # start download in parallel
    t0 = time.time_ns()
    for t in threads:
        t.start()
        t1 = time.time_ns()
        #print('Thread',t,'Starts',(t1-t0)*1e-9)
        t0 = t1

    for t in threads:
        t.join()


    time1 = (time.time_ns() - time_start) * 1e-9

    B.close()
    C.close()
    D.close()
    E.close()
    #A3.close()
    #A2.close()

    # F join the network and download the file from E
    F = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    time_start = time.time_ns()
    data1 = F.download(fid)
    time2 = (time.time_ns() - time_start) * 1e-9
    # print(data2)

    print('Time for 4 client to download:',time1)
    print('Time for 1 client to download:',time2)

    f = open(file=tarfile, mode='rb', )
    data = f.read()
    print('File Size', len(data))
    if data == data1 and files[0] == files[1] and files[1] == files[2] and files[2] == files[3] and data == files[0]:
        print("Simple Test Passed!")
    else:

        raise RuntimeError

    F.close()
