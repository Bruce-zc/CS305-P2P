# -*- coding: UTF-8 -*-
import queue
import threading
from queue import Queue, SimpleQueue
from threading import Thread

from Proxy import Proxy
import hashlib
import re
import _thread
import time
#from tqdm import tqdm, trange


class PClient():

    def __init__(self, tracker_addr: (str, int), proxy=None, port=None, upload_rate=0, download_rate=0):
        if proxy:
            self.proxy = proxy
        else:
            self.proxy = Proxy(upload_rate, download_rate, port)  # Do not modify this line!
        self.tracker = tracker_addr
        """
        Start your additional code below!
        """
        self.localFiles = {}
        self.msg_rcv = SimpleQueue()
        self.data_queue = {}
        self.frm = ""
        self.display = False
        self.port_update = {}
        self.rcv_index = []
        self.error_state = False
        self.choke_state = False
        self.pkt_info = {}
        self.file_port = {}

        self.rtt_info = {}
        self.downloading_port = {}

        self.tit4tat = False
        self.choked_port = []

        _thread.start_new_thread(self.receive, ())

    def msg_clear(self):
        self.msg_rcv = SimpleQueue()
        self.frm = ""

    # Displaying all the received messages
    def display_msg(self):
        self.display = True

    def __send__(self, data: bytes, dst: (str, int)):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send
        :param dst: The address of the destination
        """
        # print('sending:',data)
        self.proxy.sendto(data, dst)

    def __recv__(self, timeout=None) -> (bytes, (str, int)):
        """
        Do not modify this function!!!
        You must receive all data from this function!!!
        :param timeout: if its value has been set, it can raise a TimeoutError;
                        else it will keep waiting until receive a packet from others
        :return: a tuple x with packet data in x[0] and the source address(ip, port) in x[1]
        """
        return self.proxy.recvfrom(timeout)

    def register(self, file_path: str):
        """
        Share a file in P2P network
        :param file_path: The path to be shared, such as "./alice.txt"
        :return: fid, which is a unique identification of the shared file and can be used by other PClients to
                 download this file, such as a hash code of it
        """
        fid = None
        """
        Start your code below!
        """

        print(f"Registering file with path {file_path}")

        # Extract file name from path
        file_name = file_path.split('/')[-1]
        print(f'File Name: {file_name}')

        # md5 hash encoding
        m = hashlib.md5()
        m.update(file_name.encode('utf-8'))
        fid = m.hexdigest()
        print(f'ID (md5): {fid}')

        # Create message and send to tracker, until receiving 'success' message
        msg = "REGISTER:" + fid
        self.__send__(msg.encode(), self.tracker)
        if self.msg_rcv.get() == 'REGISTER SUCCESS':
            print("REGISTER success!\r\n")

        # Clear the msg stored
        self.msg_clear()

        # Read the data with file path
        f = open(file=file_path, mode='rb', )
        data = f.read()

        # Store local data for following sharing
        self.localFiles[fid] = data

        """
        End of your code
        """
        return fid

    def download(self, fid) -> bytes:
        """
        Download a file from P2P network using its unique identification
        :param fid: the unique identification of the expected file, should be the same type of the return value of share()
        :return: the whole received file in bytes
        """
        data = None
        """
        Start your code below!
        """
        # Create message and send to tracker, until receiving not null message
        choked_ports_download = []
        self.msg_clear()
        self.data_queue[fid] = SimpleQueue()
        print(f"Querying file with fid {fid}")
        msg = "QUERY:" + fid
        self.__send__(msg.encode(), self.tracker)
        while not self.file_port.__contains__(fid):
            time.sleep(0.1)
        msg = self.file_port[fid]

        print(f'{msg} have the required file!')

        # Find the port that have the required file
        def get_ports(msg):
            download_ports = re.findall(r"\d\d\d\d\d?", re.sub('\'(\w{32})\':', '', msg))
            print('Available Port:', download_ports)

            # download_address = ("127.0.0.1", int(download_ports[-1]))

            addr = {}

            for i in range(len(download_ports)):
                addr[i] = ("127.0.0.1", int(download_ports[i]))
#            print(addr[0])
            return addr

        addr = get_ports(msg)

        # Clear the msg stored
        self.msg_clear()

        # Create message and send to PClient that have the file to obtain the file information
        msg = "QUERYING INFO\r\n" + fid
        self.__send__(msg.encode(), addr[0])

        # Get the information of the upcoming packets
        while not self.pkt_info.__contains__(fid):
            # msg = self.msg_rcv.get()
            time.sleep(0.1)
        msg = self.pkt_info[fid]
        total_num = 0
        data_len = 0

        if self.display:
            print(str(self.proxy.port) + "File Info:" + msg)

        # Get the file info
        if str(msg).count('||') != 0:
            total_num = int(str(msg).split('||')[0])
            data_len = str(msg).split('||')[1]

        new_addr = {}
        data = {}
        part = 0

        total_part = total_num // 100 + 1

        while part < total_part:

            if int(part * total_num / total_part) == int((part + 1) * total_num / total_part):
                part += 1
                continue

            transmit_pkts = range(int(part * total_num / total_part), int((part + 1) * total_num / total_part))
            #print(transmit_pkts)

            # Retrieve the desired data from different peers

            ## Codes to retrieve data from other client
            if new_addr:
                port_num = len(new_addr)
                print('New Available Ports:', new_addr)
                addr = new_addr
            else:
                port_num = len(addr)
            begin = 0
            if not self.tit4tat:
                print('Port Number:', port_num)
                print('Total Number:', total_num)

            if self.tit4tat:
                for p in choked_ports_download:
                    if not self.choked_port.__contains__(p):
                        print("Re-selecting")
                        choked_ports_download.remove(p)
                        #print(p,'okkkkk')
                        #print(addr)
                        #addr[len(addr)] = p
                        #print(addr)

                if self.choke_state:
                    if len(self.downloading_port[fid]) == 1:
                        # TODO： 找tracker要地址 如果只有那一个那就继续下，清空他的rtt信息，
                        #  如果不是就从别的地方下
                        msg = "QUERY:" + fid
                        self.file_port.__delitem__(fid)
                        self.__send__(msg.encode(), self.tracker)
                        while not self.file_port.__contains__(fid):
                            time.sleep(0.1)
                        msg = self.file_port[fid]
                        addr = get_ports(msg)
                        if len(addr) == 1 and addr.__contains__(choked_ports_download[0]):
                            self.rtt_info.__delitem__(addr[0])
                            self.rtt_measure(addr)
                            self.choked_port.remove(choked_ports_download[0])
                            choked_ports_download.remove(choked_ports_download[0])
                        else:
                            for choke in self.choked_port:
                                if addr.__contains__(choke):
                                    addr.__delitem__(choke)
                                    #self.choked_port.remove(choke)
                                    #choked_ports_download.remove(choke)
                    else:
                        print('BEFORE', addr)
                        tmp = []
                        for index in addr:
                            tmp.append(index)

                        for address in tmp:
                            if self.choked_port.__contains__(addr[address]):
                                addr.__delitem__(address)

                                #self.choked_port.remove(addr[address])
                                #choked_ports_download.remove(addr[address])
                        print('AFTER',addr)

                    self.choke_state = False

            best_match = addr

            # Choose the port that match the download_rate best
            def choose_port(addr):
                larger = 0
                diff = 1e9
                download_rate = self.proxy.download_rate
                best_match = {}
                port_num = len(addr)

                for num in range(port_num):
                    self.rtt_measure(addr)
                    time.sleep(0.3)

                for num in range(port_num):
                    # modified
                    if self.rtt_info.__contains__(addr[num]):
                        if self.rtt_info[addr[num]].__contains__(1):
                            if self.rtt_info[addr[num]][1] >= download_rate:
                                larger += 1
                                diff1 = self.rtt_info[addr[num]][1] - download_rate
                                if diff1 < diff:
                                    diff = diff1
                                    best_match[0] = addr[num]

                if larger == 0:
                    rate_sum = 0
                    n = 0
                    for num in range(port_num):
                        if rate_sum >= download_rate:
                            break
                        if self.rtt_info.__contains__(addr[num]):
                            if self.rtt_info[addr[num]].__contains__(1):
                                rate_sum += self.rtt_info[addr[num]][1]
                                best_match[n] = addr[num]
                                n += 1

                print(self.proxy.port,'chose ports:', best_match)
                return best_match

            best_match = choose_port(addr)
            port_num = len(best_match)
            self.downloading_port[fid] = best_match

            occupied_port = []
            for p in best_match:
                occupied_port.append(str(best_match[p]))

            to_tracker = 'OCCUPIED:' + fid + '*' + '|'.join(occupied_port)
            self.__send__(to_tracker.encode(), self.tracker)
            #

            threads = []
            data_index = ''

            # Send msgs to different ports querying files using threads
            for num in range(port_num):
                data_index = ''
                end = int(len(transmit_pkts) * (num + 1) / port_num)
                if not self.tit4tat:
                    print(begin, '-----', end)
                    print(end)
                for i in range(begin, end):
                    data_index += str(transmit_pkts[i])
                    if i != end - 1:
                        data_index += ' '

                begin = end

                t = threading.Thread(target=self.retrieve_msg, args=(best_match[num], fid, data_index))
                threads.append(t)

            for t in threads:
                t.start()

            for t in threads:
                t.join()


            # Receive downloading packets
            packet_num = 0

            # Receiving the data packets from the queue
            if not self.tit4tat:
                print('Receiving packets:')
            # time.sleep(0.6)
            time_start = time.time_ns()

            # The method to process the data stored in the queue
            def data_process():
                try:
                    rcv_data = self.data_queue[fid].get(timeout=10)
                except Exception:
                    self.error_state = True
                    return

                try:
                    rcv_data = rcv_data.encode()
                    rcv_fid = rcv_data[0:32].decode()
                    if rcv_fid == fid:
                        rcvpkt_num = int(rcv_data[32:52], 2)
                        data[rcvpkt_num] = rcv_data[52:]
                    else:
                        print("Wrong!")
                        # self.msg_rcv.put(rcv_data.decode())
                    # print("Receiving pkt number:", int(rcvpkt_num))
                    # print(rcv_data[20:])
                except:
                    rcv_fid = rcv_data[0:32].decode()
                    rcvpkt_num = int(rcv_data[32:52], 2)
                    # print("Receiving pkt number:", int(rcvpkt_num))
                    if rcv_fid == fid:
                        data[rcvpkt_num] = rcv_data[52:]
                    else:
                        print("Wrong!")
                        # self.msg_rcv.put(rcv_data)

            rcv_pkt = 0
            print('Downloading...')
            for num in range(len(transmit_pkts)):

                # TODO: tit-for-tat
                if self.tit4tat:
                    for port in self.downloading_port[fid]:
                        if self.choked_port.__contains__(self.downloading_port[fid][port]):
                            self.choke_state = True
                            choked_ports_download.append(self.downloading_port[fid][port])

                if self.choke_state:
                    break

                if self.port_update.__contains__(fid):
                    # print("port:" + self.port_update[fid])
                    if self.port_update[fid] == '[]':
                        print('No port update')
                        self.error_state = True
                    else:
                        print('Port Update:', self.port_update[fid])
                        new_addr = get_ports(self.port_update[fid])
                    # print('New addresses:', new_addr)
                    self.port_update.__delitem__(fid)
                t = threading.Thread(target=data_process, args=())
                t.start()
                t.join()
                if self.error_state:
                    self.error_state = False
                    break
                rcv_pkt += 1

            #print(len(data), transmit_pkts[-1] + 1)

            # while not self.msg_rcv.empty():
            #     data_process()

            if len(data) < transmit_pkts[-1] + 1:
                if not self.tit4tat:
                    print(f'Expect {transmit_pkts[-1] + 1} pkts, but only {len(data)} are received.')
                continue

            time_process = (time.time_ns() - time_start) * 1e-9
            if not self.tit4tat:
                print('Process time:', time_process)
            print(fid, ':', part + 1, '/', total_part)

            part += 1

        data_whole = b''
        time_start = time.time_ns()

        # Assemble the trunks of data stored in the array
        for num in range(len(data)):
            data_whole += data[num]
            # print(num,':',data[num])
        data = data_whole
        time_assemble = (time.time_ns() - time_start) * 1e-9
        if not self.tit4tat:
            print('Assemble time:', time_assemble)

        # Check the received file
        if data_len == str(len(data)):
            print('Total Size:', str(len(data)))
            print(str(self.proxy.port) + 'Download Completed!\r\n')

            # Store local data for following sharing
            self.localFiles[fid] = data
            # print(rcv_index)

            # Create message and send to tracker, until receiving 'success' message
            msg = "REGISTER:" + fid
            self.__send__(msg.encode(), self.tracker)
            while self.msg_rcv.qsize() == 0:
                time.sleep(0.1)
            if self.msg_rcv.get() == 'REGISTER SUCCESS':
                print("Ready to share!\r\n")

            self.rcv_index = []
        else:
            print("Repeat!")
            data = self.download(fid)
            pass

        return data

    def retrieve_msg(self, download_address, fid, data_index):
        # Obtain the desired packet index
        data_index = str(data_index)
        # start_index = int(data_index.split('---')[0])
        # end_index = int(data_index.split('---')[1])
        # total_num = end_index - start_index

        # Create message and send to PClient that have the file
        print(f"Querying {download_address}, fid {fid}")
        msg = "QUERYING FILE\r\n" + fid + "\r\n" + data_index

        # print('-------')
        # print('Transmitting Query:', msg)
        # print('-------')

        self.__send__(msg.encode(), download_address)

    def cancel(self, fid):
        """
        Stop sharing a specific file, others should be unable to get this file from this client any more
        :param fid: the unique identification of the file to be canceled register on the Tracker
        :return: You can design as your need
        """

        # Create message and send to tracker, until receiving 'success' message
        print(f"Canceling file with fid {fid}")
        msg = "CANCEL:" + fid
        self.__send__(msg.encode(), self.tracker)
        while self.msg_rcv.qsize() == 0:
            time.sleep(0.1)
        if self.msg_rcv.get() == 'CANCEL SUCCESS':
            print("CANCEL success!\r\n")

        # Clear the msg stored
        self.msg_clear()

        # Clear the record of local data
        self.localFiles[fid] = []

        """
        End of your code
        """

    def close(self):
        """
        Completely stop the client, this client will be unable to share or download files any more
        :return: You can design as your need
        """

        # Create message and send to tracker, until receiving 'success' message
        print(f"Closing client")
        msg = "CLOSE:"
        self.__send__(msg.encode(), self.tracker)
        _thread.start_new_thread(self.receive, ())
        msg = self.msg_rcv.get()
        if msg == "CLOSE SUCCESS":
            print("CLOSE success!\r\n")

        time.sleep(1)

        # Clear the msg stored
        self.msg_clear()

        """
        End of your code
        """
        self.proxy.close()

    # Receiving all messages from this method and store to self.msg_rcv and self.frm
    def receive(self):
        cnt = 0
        while True:
            # time.sleep(1)
            last_frm = self.frm
            msg_rcv, frm = self.__recv__()

            cnt += 1
            if cnt == 30:
                cnt = 0
                for p in self.downloading_port:
                    self.rtt_measure(self.downloading_port[p])
                for p in self.choked_port:
                    self.rtt_measure({0:p})

            if frm != last_frm:
                if not self.tit4tat:
                    print(f'Message received: from {frm}')

            if self.display:
                print('-------')
                print('RECEIVING:', msg_rcv)
                print('-------')

            # Check whether the received message is other type of data or string
            try:
                msg_rcv = msg_rcv.decode()
                if msg_rcv.endswith("SUCCESS"):
                    print(msg_rcv)
                    self.msg_rcv.put(msg_rcv)
                    self.frm = frm
                    continue
                elif msg_rcv.startswith("QUERY RATE"):
                    self.frm = frm
                    #print("Here is my upload rate:" + str(self.proxy.upload_rate))
                    pkt = ("REPLY RATE" + str(self.proxy.upload_rate) + '|' + str(self.proxy.download_rate) + '|')
                    while len(pkt) != 30:
                        pkt = pkt + '-'

                    tmp_buf = self.proxy.send_queue
                    self.proxy.send_queue.empty()
                    self.__send__(pkt.encode(), frm)
                    self.proxy.send_queue = tmp_buf

                    continue
                elif msg_rcv.startswith("REPLY RATE"):
                    self.frm = frm
                    time_rcv = time.time_ns()
                    rtt = (time_rcv - self.rtt_info[frm][3]) * 1e-9
                    info = msg_rcv.split("REPLY RATE")[1]
                    up = info.split('|')[0]
                    down = info.split('|')[1]

                    if not self.rtt_info[frm].__contains__(0):
                        self.rtt_info[frm][0] = []

                    record = True
                    choke = False
                    if len(self.rtt_info[frm][0]) != 0:
                        average_rtt = 0
                        rtt_num = len(self.rtt_info[frm][0])
                        for rtt in self.rtt_info[frm][0]:
                            average_rtt += rtt
                        average_rtt = average_rtt / rtt_num
                        if not self.tit4tat:
                            print('Average RTT', frm, ':', average_rtt)

                        if rtt > 2 * average_rtt:
                            record = False
                            choke = True

                    if rtt != 0:
                        if not self.tit4tat:
                            print('RTT of ' + str(frm[1]) + ':' + str(rtt))
                    else:
                        if not self.tit4tat:
                            print('Bad RTT!')
                        record = False

                    if self.rtt_info[frm].__contains__(1):
                        if float(up) <= 0.6 * self.rtt_info[frm][1]:
                            choke = True
                            record = False

                    if self.choked_port.__contains__(frm):
                        if float(up) >= 2 * self.rtt_info[frm][1]:
                            print("Re-select:", frm)
                            self.choked_port.remove(frm)
                            unchock_msg = "UNCHOKE PORT:" + str(frm)
                            tmp_buf = self.proxy.send_queue
                            self.proxy.send_queue.empty()
                            self.__send__(unchock_msg.encode(), self.tracker)
                            self.proxy.send_queue = tmp_buf
                            print(frm, "is not choked now!")

                    if record:
                        self.rtt_info[frm][0].append(rtt)
                    self.rtt_info[frm][1] = float(up)
                    self.rtt_info[frm][2] = int(down)

                    if choke:
                        print(len(self.choked_port))
                        self.choked_port.append(frm)
                        print(frm,"need be choked! for now. By",self.proxy.port)
                        chock_msg = "CHOKE PORT:" + str(frm)

                        tmp_buf = self.proxy.send_queue
                        self.proxy.send_queue.empty()
                        self.__send__(chock_msg.encode(),self.tracker)
                        self.proxy.send_queue = tmp_buf
                    continue
                elif msg_rcv.startswith("PORT UPDATE"):
                    # Try to rearrange the download port
                    ports = msg_rcv.split("PORT UPDATE")[1]
                    rcv_fid = ports.split('--')[0]
                    rcv_ports = ports.split('--')[1]
                    self.port_update[rcv_fid] = rcv_ports
                    continue
                elif msg_rcv.startswith("PKT INFO"):
                    info = msg_rcv.split("PKT INFO")[1]
                    rcv_fid = info.split('--')[0]
                    rcv_info = info.split('--')[1]
                    self.pkt_info[rcv_fid] = rcv_info
                    continue
                elif msg_rcv.startswith("PORT INFO"):
                    info = msg_rcv.split("PORT INFO")[1]
                    rcv_fid = info.split('--')[0]
                    rcv_port = info.split('--')[1]
                    self.file_port[rcv_fid] = rcv_port
                    continue
                else:

                    # Extract fid from message
                    fid = msg_rcv.split('\r\n')[1]

                    # Load the data, prepare to share
                    data = self.localFiles[fid]

                    # Divide into packets and transmit
                    packet_size = 8192
                    packets = [data[i * packet_size: (i + 1) * packet_size]
                               for i in range(len(data) // packet_size + 1)]

                    # If receiving message that desired to download the file
                    if msg_rcv.startswith("QUERYING INFO"):
                        # Generate and send the packets information
                        pkt_num = str(len(packets))
                        pkt_len = str(len(data))
                        pkt_info = 'PKT INFO' + fid + '--' + pkt_num + '||' + pkt_len

                        if self.display:
                            print(str(self.proxy.port) + "Sending info" + pkt_info)

                        self.__send__(pkt_info.encode(), frm)
                        continue
                    if msg_rcv.startswith("QUERYING FILE"):
                        t = threading.Thread(target=self.send, args=(msg_rcv, packets, frm, fid))
                        t.start()
                        t.join()
                        continue
                    else:
                        print(msg_rcv)
                        try:
                            rcv_fid = msg_rcv[0:32]
                            print('bbb' + rcv_fid)
                            self.data_queue[rcv_fid].put(msg_rcv)
                        except:
                            self.msg_rcv.put(msg_rcv)
                            self.frm = frm
            except:
                try:
                    msg_rcv.decode()
                    rcv_fid = msg_rcv[0:32].decode()
                    if len(rcv_fid) == 32:
                        self.data_queue[rcv_fid].put(msg_rcv)
                    else:
                        self.msg_rcv.put(msg_rcv)
                    self.frm = frm
                except:
                    rcv_fid = msg_rcv[0:32]
                    if len(rcv_fid) == 32:
                        try:
                            self.data_queue[rcv_fid.decode()].put(msg_rcv)
                        except:
                            self.data_queue[rcv_fid].put(msg_rcv)
                    else:
                        self.msg_rcv.put(msg_rcv)
                    self.frm = frm

    def rtt_measure(self, addr):

        pkt = "QUERY RATE"
        pkt = pkt.encode()
        for n in range(len(addr)):
            if not self.rtt_info.__contains__(addr[n]):
                self.rtt_info[addr[n]] = {}
            self.rtt_info[addr[n]][3] = time.time_ns()
            self.__send__(pkt, addr[n])

    # The method to send corresponding packets
    def send(self, msg_rcv, packets, frm, fid):

        data_index = msg_rcv.split('\r\n')[-1].split(' ')
        if data_index == '':
            return
        total_num = len(data_index)
        if not self.localFiles.__contains__(fid):
            return

        if len(packets) == 1 and len(packets) < total_num:
            return
        if not self.tit4tat:
            print(f'Packets: {len(packets)}')

        # send_num = 0
        if not self.tit4tat:
            print(f"Total packets to be transmitted: {total_num}")
        for i in data_index:

            # Add the binary sequence number to the first byte of the packet
            def Dec2Bin(dec):
                result = ''
                if dec:
                    result = Dec2Bin(dec // 2)
                    return result + str(dec % 2)
                else:
                    return result

            def len20(dec):
                b = Dec2Bin(dec)
                if len(b) < 20:
                    for i in range(0, 20 - len(b)):
                        b = "0" + b
                return b

            if i != '':
                binary_index = len20(int(i))
                # if self.display:
                #     print("Sending",fid,binary_index)
                self.__send__(fid.encode() + (str(binary_index)).encode() + packets[int(i)], frm)


if __name__ == '__main__':
    pass
