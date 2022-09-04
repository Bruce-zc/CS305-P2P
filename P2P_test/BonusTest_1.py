import threading
import time
from threading import Thread

from PClient import PClient
from Proxy_bonus import Proxy_bonus

tracker_address = ("127.0.0.1", 10086)
tarfile = "../test_files/bg.png"

if __name__ == '__main__':

    bad_proxy = Proxy_bonus(upload_rate=60000, download_rate=200000, change_rate=True)

    P_normal = PClient(tracker_address, upload_rate=40000, download_rate=100000)
    P_bad = PClient(tracker_address, proxy=bad_proxy)
    P1 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    P2 = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    P1.tit4tat = True
    P2.tit4tat = True
    P_bad.tit4tat = True
    P_normal.tit4tat = True

    print("P1:",P1.proxy.port)
    print("P2:",P2.proxy.port)
    print("P_bad:",P_bad.proxy.port)
    print("P_normal:",P_normal.proxy.port)

    fid1 = P_normal.register("../test_files/bg.png")
    P_bad.register("../test_files/bg.png")
    fid2 = P1.register("../test_files/ag.png")
    P2.register("../test_files/ag.png")

    files = {}

    def download(node, index, fid):
        files[index] = node.download(fid)

    t1 = threading.Thread(target=download, args=(P1, 1, fid1))
    t2 = threading.Thread(target=download, args=(P_bad, 2, fid2))

    threads = [t1, t2]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # files[1] = P1.download(fid1)
    # files[2] = P_bad.download(fid2)

    data = open(tarfile, "rb").read()

    if data != files[1] or data != files[2]:
        raise Exception("Downloaded file is different with the original one")
    else:
        print('Bonus get!')

    P1.close()
    P2.close()
    P_bad.close()
    P_normal.close()
