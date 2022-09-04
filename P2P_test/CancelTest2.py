import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 10086)

if __name__ == '__main__':
    A = PClient(tracker_address, upload_rate=200000, download_rate=50000)
    B = PClient(tracker_address, upload_rate=200000, download_rate=50000)
    fid = A.register("../test_files/alice.txt")
    # A.cancel(fid)
    # fid = B.register("../test_files/alice.txt")

    threads = []
    files = {}


    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)


    time_start = time.time_ns()
    C = PClient(tracker_address, upload_rate=50000, download_rate=100000)
    D = PClient(tracker_address, upload_rate=100000, download_rate=60000)

    # F, G join the network
    clients = [B, C, D]
    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(client, i)))
    for t in threads:
        t.start()

    time.sleep(0.1)
    B.close()
    # # A.close()
    # print("A cancel")

    # for t in threads:
    #     t.join()

    time.sleep(10)

    if files == {}:
        raise Exception("No files")
    else:
        with open("../test_files/alice.txt", "rb") as bg:
            bs = bg.read()
            for i in files:
                if files[i] != bs:
                    print(2)
                    # raise Exception("Downloaded file is different with the original one")
        print("SUCCESS")

    A.close()
    # B.close()
    C.close()
    D.close()
    print((time.time_ns() - time_start) * 1e-9)
