from PClient import PClient

tracker_address = ("127.0.0.1", 44494)


'''
SimpleTest_1.py:

Feature:
    4 clients, download 2 files
File:
    fid1  xl.xlsx    14KB
    fid2  alice.txt  149KB
Process: 
    A register fid1
    B register fid2
    B download fid1
    C download fid1
    A cancel fid1
    B cancel fid1
    A download fid2
    A close
    D download fid1
    C download fid2
    D download fid2
    B close
    C close
    D close
'''


if __name__ == '__main__':
    # A,B join the network
    A = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    B = PClient(tracker_address, upload_rate=100000, download_rate=100000)
    C = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    fid1 = A.register("../test_files/xl.xlsx")
    fid2 = B.register("../test_files/alice.txt")

    data11 = B.download(fid1)
    data12 = C.download(fid1)

    A.cancel(fid1)
    B.cancel(fid1)

    data21 = A.download(fid2)

    A.close()

    D = PClient(tracker_address, upload_rate=100000, download_rate=100000)

    data13 = D.download(fid1)

    data22 = C.download(fid2)
    data23 = D.download(fid2)

    f = open(file="../test_files/xl.xlsx", mode='rb', )
    data1 = f.read()
    f = open(file="../test_files/alice.txt", mode='rb', )
    data2 = f.read()
    if data11 == data12 == data13 == data1 and data21 == data22 == data23 == data2:
        print("Simple Test Passed!")
    else:
        raise RuntimeError

    B.close()
    C.close()
    D.close()