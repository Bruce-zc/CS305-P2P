import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 44494)

if __name__ == '__main__':
    A = PClient(tracker_address, upload_rate=200000, download_rate=50000)
    B = PClient(tracker_address, upload_rate=200000, download_rate=50000)
    fid = A.register("../test_files/alice.txt")
    fid = B.register("../test_files/alice.txt")

    threads = []
    files = {}


    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)


    time_start = time.time_ns()
    C = PClient(tracker_address, upload_rate=50000, download_rate=100000)
    D = PClient(tracker_address, upload_rate=100000, download_rate=60000)

    # F, G join the network
    clients = [C, D]
    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(client, i)))
    for t in threads:
        t.start()

    # # A exits
    # time.sleep(0.2)
    # A.cancel(fid)
    A.cancel(fid)

    # A.close()
    print("A cancel")

    for t in threads:
        t.join()

    if files == {}:
        raise Exception("No files")
    else:
        with open("../test_files/alice.txt", "rb") as bg:
            bs = bg.read()
            for i in files:
                # print("files: "+str(files[i]))
                if files[i] != bs:
                    # print("files: "+str(files[i]))
                    # print("----------------")
                    # print(bs)
                    # print(1)
                    raise Exception("Downloaded file is different with the original one")
        print("SUCCESS")

    A.close()
    B.close()
    C.close()
    D.close()
    print((time.time_ns() - time_start) * 1e-9)
