import time
from threading import Thread

from PClient import PClient

tracker_address = ("127.0.0.1", 10086)


if __name__ == '__main__':
    # A,B,C,D,E join the network
    A = PClient(tracker_address, upload_rate=200000, download_rate=50000)
    B = PClient(tracker_address, upload_rate=50000, download_rate=100000)
    C = PClient(tracker_address, upload_rate=100000, download_rate=50000)
    D = PClient(tracker_address, upload_rate=70000, download_rate=40000)
    E = PClient(tracker_address, upload_rate=200000, download_rate=700000)

    clients = [B, C, D, E]
    # A register a file and B download it
    fid = A.register("../test_files/alice.txt")
    fid1 = A.register("../test_files/snumber.txt")
    threads = []
    files = {}

    # function for download and save
    def download(node, index):
        files[index] = node.download(fid)

    def download1(node):
        file=node.download(fid1)
        with open("../test_files/snumber.txt", "rb") as bg:
            bs = bg.read()
            if bs!=file:
                print("error")

    time_start = time.time_ns()

    for i, client in enumerate(clients):
        threads.append(Thread(target=download, args=(client, i)))
    # start download in parallel
    threads.append(Thread(target=download1, args=(B,)))
    for t in threads:
        t.start()
    # wait for finish
    for t in threads:
        t.join()
    # check the downloaded files
    print(len(files))
    print("----------")
    with open("../test_files/alice.txt", "rb") as bg:
        bs = bg.read()
        for i in files:
            if files[i] != bs:
                raise Exception("Downloaded file is different with the original one")

    # B, C, D, E has completed the download of file
    threads.clear()

    # A exits
    # time.sleep(20)
    # A.cancel(fid)
    #
    # # A.close()
    # print("A cancel")
    #
    #
    # # B exits
    # time.sleep(10)
    # B.close()
    #
    # # D exits
    # time.sleep(30)
    # D.close()
    for t in threads:
        t.join()

    print(len(files))
    for i in files:
        if files[i] != bs:
            raise Exception("Downloaded file is different with the original one")
    print("SUCCESS")

    B.close()
    D.close()

    A.close()
    C.close()
    E.close()

    print((time.time_ns() - time_start) * 1e-9)
