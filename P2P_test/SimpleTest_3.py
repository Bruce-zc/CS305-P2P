from PClient import PClient
from SimpleTracker import SimpleTracker

tracker_address = ("127.0.0.1", 44494)


'''
SimpleTest_3.py:

Feature:
    small file transmission
File:
    fid1 dot.png 1KB
Process: 
    A register fid1
    B download fid1 (from A)
    A close
    C download fid1 (from B)
    B close
    C close
'''


if __name__ == '__main__':
    # A,B join the network
    A = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    # A register a file and B download it
    fid = A.register("../test_files/dot.png")

    data1 = B.download(fid)

    # A cancel the register of the file
    A.close()

    # C join the network and download the file from B
    C = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    data2 = C.download(fid)

    f = open(file="../test_files/dot.png", mode='rb', )
    data = f.read()
    if data1 == data2 and data1 == data:
        print("Simple Test 3 Passed!")
    else:
        raise RuntimeError

    B.close()
    C.close()
