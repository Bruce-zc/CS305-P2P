import _thread
import time
from socketserver import BaseRequestHandler, ThreadingUDPServer
from Proxy import Proxy
from queue import Queue, SimpleQueue
import re


class Tracker:
    def __init__(self, upload_rate=10000, download_rate=10000, port=None, tit4tat=False):
        self.proxy = Proxy(upload_rate, download_rate, port)
        self.files = {}
        self.downloading = {}
        self.query = {}
        self.frm = ""
        self.download_ports = {}
        self.choked_ports = {}
        self.tit4tat = tit4tat

    def __send__(self, data: bytes, dst: (str, int)):
        """
        Do not modify this function!!!
        You must send all your packet by this function!!!
        :param data: The data to be send0
        :param dst: The address of the destination
        """
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

    def response(self, data: str, address: (str, int)):
        self.__send__(data.encode(), address)

    def handle_query(self):
        while True:
            time.sleep(0.15)
            if not self.query:
                time.sleep(1)
                continue

            fid_list = []
            for fid in self.query:
                fid_list.append(fid)

            for fid in fid_list:
                if not self.files.__contains__(fid):
                    continue
                if not self.files[fid]:
                    continue
                elif self.query[fid].qsize() == 0:
                    time.sleep(1)
                    continue

                available_port = []
                print(self.files)
                for (client, state) in self.files[fid]:
                    if state:
                        available_port.append(client)

                if len(available_port) > 0:
                    frm = self.query[fid].get()
                    print(f'Dealing query from {frm}')
                    if fid not in self.downloading:
                        self.downloading[fid] = []
                    self.downloading[fid].append(frm)

                    if self.tit4tat:
                        if self.choked_ports.__contains__(frm):
                            for port in self.choked_ports[frm]:
                                if available_port.__contains__(port):
                                    available_port.remove(port)

                    self.response("PORT INFO" + fid + "--" + "[%s]" % ("|".join(available_port)), frm)

                    if not self.download_ports.__contains__(fid):
                        self.download_ports[fid] = {}

                    if not self.download_ports[fid].__contains__(frm):
                        self.download_ports[fid][frm] = []

                    # self.download_ports[fid][frm] = available_port

                    while not self.download_ports[fid][frm]:
                        time.sleep(0.1)
                        print('Waiting')

                    for index in range(len(self.download_ports[fid][frm])):
                        port = self.download_ports[fid][frm][index]
                        client = '(\"%s\", %d)' % port

                        index_o = self.files[fid].index((client, True))
                        self.files[fid][index_o] = (client, False)

                    print(f'After port selecting {self.files}\r\n')
                else:
                    time.sleep(1)

        # while self.query.qsize() > 0:
        #     if not self.downloading.__contains__(fid) or not self.downloading[fid]:
        #         (fid, frm) = self.query.get()
        #         # Add the client to the "downloading" list
        #         if fid not in self.downloading:
        #             self.downloading[fid] = []
        #         self.downloading[fid].append(frm)
        #
        #         # Reply to the PClient
        #
        #         if not self.files.__contains__(fid):
        #             print('No one own this file')
        #             continue
        #         else:
        #             result = []
        #             for (c, state) in self.files[fid]:
        #                 if state:
        #                     result.append(c)
        #             self.response("PORT INFO" + fid + "--" + "[%s]" % ("|".join(result)), frm)
        #     else:
        #         _thread.start_new_thread(self.start, ())
        #         time.sleep(1)

    def start(self):
        _thread.start_new_thread(self.handle_query, ())
        while True:
            msg, frm = self.__recv__()
            msg, client = msg.decode(), '(\"%s\", %d)' % frm
            print(f"Received message from {client}")

            if msg.startswith("REGISTER:"):
                # Client can use this to REGISTER a file and record it on the tracker
                fid = msg[9:]
                print(f"Registering fid {fid}")

                # Modify the information stored
                if fid not in self.files:
                    self.files[fid] = []
                self.files[fid].append((client, True))

                # Remove the client from downloading and broadcast the latest available ports
                if fid in self.downloading:
                    print('Exist:', self.download_ports)
                    if self.download_ports.__contains__(fid):
                        if self.download_ports[fid].__contains__(frm):
                            for port in self.download_ports[fid][frm]:
                                port = '(\"%s\", %d)' % port
                                print('search', port)
                                print('exist', self.files[fid])
                                if (port, False) in self.files[fid]:
                                    index = self.files[fid].index((port, False))
                                    self.files[fid][index] = (port, True)
                    self.download_ports[fid][frm] = []

                    if frm in self.downloading[fid]:
                        self.downloading[fid].remove(frm)
                    result = []
                    print('Broadcast the updated available ports')

                    for (clients1, state) in self.files[fid]:
                        if state:
                            result.append(clients1)

                        # update = "PORT UPDATE" + "[%s]" % ("|".join(result))
                        # self.response(update, ('127.0.0.1', int(clients1.split(', ')[1].split(')')[0])))

                    for clients2 in self.downloading[fid]:

                        if self.tit4tat:
                            if self.choked_ports.__contains__(clients2):
                                for port in self.choked_ports[clients2]:
                                    if result.__contains__(port):
                                        result.remove(port)
                                        print(clients2, "is not able to download from", port)

                        update = "PORT UPDATE" + fid + "--" + "[%s]" % ("|".join(result))
                        print(f"Update to {clients2}: {update}")
                        self.response(update, clients2)
                        # todo
                        pass

                # Reply to the PClient
                self.response("REGISTER SUCCESS", frm)
                print(f'Current dictionary: {self.files}\r\n')

            elif msg.startswith("QUERY:"):
                # Client can use this to check who has the specific file with the given fid
                fid = msg[6:]
                print(f"Querying fid {fid}")

                if not self.query.__contains__(fid):
                    self.query[fid] = SimpleQueue()
                self.query[fid].put(frm)

                # while self.query.qsize() > 0:
                #     if not self.downloading.__contains__(fid) or not self.downloading[fid]:
                #         (fid, frm) = self.query.get()
                #         # Add the client to the "downloading" list
                #         if fid not in self.downloading:
                #             self.downloading[fid] = []
                #         self.downloading[fid].append(frm)
                #
                #         # Reply to the PClient
                #
                #         if not self.files.__contains__(fid):
                #             print('No one own this file')
                #             continue
                #         else:
                #             result = []
                #             for (c, state) in self.files[fid]:
                #                 if state:
                #                     result.append(c)
                #             self.response("PORT INFO" + fid + "--" + "[%s]" % ("|".join(result)), frm)
                #     else:
                #         _thread.start_new_thread(self.start, ())
                #         time.sleep(1)

                # print('Downloading', self.downloading)

            elif msg.startswith("CANCEL:"):
                # Client can use this file to cancel the share of a file
                fid = msg[7:]
                print(f"Canceling fid {fid}")

                # Modify the information stored
                if (client, True) in self.files[fid]:
                    self.files[fid].remove((client, True))

                if (client, False) in self.files[fid]:
                    self.files[fid].remove((client, False))

                if not self.files[fid]:
                    del self.files[fid]

                self.response("CANCEL SUCCESS", frm)

                # Remove the client from downloading and broadcast the latest available ports
                if fid in self.downloading:
                    result = []
                    print('Broadcast the updated available ports')

                    if not self.files.__contains__(fid):
                        print('No one own this file')
                        continue
                    else:
                        for (clients1, state) in self.files[fid]:
                            if state:
                                result.append(clients1)

                        for frm in self.download_ports[fid]:
                            if client in self.download_ports[fid][frm]:
                                self.download_ports[fid][frm].remove(client)

                        for port in self.download_ports[fid][frm]:
                            client = '(\"%s\", %d)' % port
                            result.append(client)

                        for clients2 in self.downloading[fid]:

                            if self.tit4tat:
                                if self.choked_ports.__contains__(clients2):
                                    print('aaa')
                                    for port in self.choked_ports[clients2]:
                                        if result.__contains__(port):
                                            result.remove(port)
                                            print(clients2, "is not able to download from", port)

                            update = "PORT UPDATE" + fid + "--" + "[%s]" % ("|".join(result))
                            print(f"Update to {clients2}: {update}")
                            self.response(update, clients2)
                            # todo
                            pass

                # Reply to the PClient

                print(f'Current dictionary: {self.files}\r\n')

            elif msg.startswith("CLOSE:"):
                # Client can use this file to close
                print(f"Closing")

                self.response("CLOSE SUCCESS", frm)

                # Modify the information stored
                for fid in self.files:
                    if (client, True) in self.files[fid] or (client, False) in self.files[fid]:
                        if (client, True) in self.files[fid]:
                            self.files[fid].remove((client, True))
                        if (client, False) in self.files[fid]:
                            self.files[fid].remove((client, False))
                        # Remove the client from downloading and broadcast the latest available ports

                        if fid in self.downloading:
                            result = []
                            print('Broadcast the updated available ports')

                            if not self.files.__contains__(fid):
                                print('No one own this file')
                                continue
                            else:
                                for (clients1, state) in self.files[fid]:
                                    if state:
                                        result.append(clients1)

                                for frm in self.download_ports[fid]:
                                    if client in self.download_ports[fid][frm]:
                                        self.download_ports[fid][frm].remove(client)
                                for port in self.download_ports[fid][frm]:
                                    client = '(\"%s\", %d)' % port
                                    result.append(client)
                                for clients2 in self.downloading[fid]:

                                    if self.tit4tat:
                                        if self.choked_ports.__contains__(clients2):
                                            print('aaa')
                                            for port in self.choked_ports[clients2]:
                                                if result.__contains__(port):
                                                    result.remove(port)
                                                    print(clients2, "is not able to download from", port)

                                    update = "PORT UPDATE" + fid + "--" + "[%s]" % ("|".join(result))
                                    print(f"Update to {clients2}: {update}")
                                    self.response(update, clients2)

                files_tmp = {}
                for fid in self.files:
                    if self.files[fid]:
                        files_tmp[fid] = self.files[fid]
                self.files = files_tmp

                # Reply to the PClient

                print(f'Current dictionary: {self.files}\r\n')
            elif msg.startswith("OCCUPIED:"):
                info = msg.split("OCCUPIED:")[1]
                rcv_fid = info.split("*")[0]
                ports = info.split("*")[1]
                download_ports = re.findall(r"\d\d\d\d\d?", re.sub('\'(\w{32})\':', '', ports))

                ports = []
                for i in range(len(download_ports)):
                    port = ("127.0.0.1", int(download_ports[i]))
                    ports.append(port)

                self.download_ports[rcv_fid][frm] = ports
                print('DP:', self.download_ports)
            elif msg.startswith("CHOKE PORT:"):
                port = msg.split("CHOKE PORT:")[1]
                choked_port = re.findall(r"\d\d\d\d\d?", re.sub('\'(\w{32})\':', '', port))
                choked_port = ("127.0.0.1", int(choked_port[0]))
                if not self.choked_ports.__contains__(choked_port):
                    self.choked_ports[choked_port] = []
                self.choked_ports[choked_port].append(frm)
                print('Choked Ports:', self.choked_ports)
                if self.tit4tat:
                    choke_fid = []

                    for fid in self.downloading:
                        if self.downloading[fid].__contains__(choked_port):
                            choke_fid.append(fid)

                    for fid in choke_fid:
                        result = []

                        for client in self.download_ports[fid][choked_port]:
                            client = '(\"%s\", %d)' % client
                            result.append(client)

                        print("Before choking:", result)

                        for port in self.choked_ports[choked_port]:
                            port = '(\"%s\", %d)' % port
                            if result.__contains__(port):
                                result.remove(port)
                                print(choked_port, "is not able to download from", port)

                        update = "PORT UPDATE" + fid + "--" + "[%s]" % ("|".join(result))
                        print(f"Update to {choked_port}: {update}")
                        self.response(update, choked_port)
            elif msg.startswith("UNCHOKE PORT:"):
                port = msg.split("UNCHOKE PORT:")[1]
                unchoked_port = re.findall(r"\d\d\d\d\d?", re.sub('\'(\w{32})\':', '', port))
                unchoked_port = ("127.0.0.1", int(unchoked_port[0]))
                self.choked_ports[unchoked_port].remove(frm)
                if len(self.choked_ports[unchoked_port]) == 0:
                    self.choked_ports.__delitem__(unchoked_port)
                print('Unchoked Ports:', self.choked_ports)
                if self.tit4tat:
                    unchoke_fid = []

                    for fid in self.downloading:
                        if self.downloading[fid].__contains__(unchoked_port):
                            unchoke_fid.append(fid)

                    for fid in unchoke_fid:
                        result = []

                        for client in self.download_ports[fid][unchoked_port]:
                            client = '(\"%s\", %d)' % client
                            result.append(client)

                        unchoke_client = '(\"%s\", %d)' % frm
                        result.append(unchoke_client)
                        update = "PORT UPDATE" + fid + "--" + "[%s]" % ("|".join(result))
                        print(f"Update to {unchoked_port}: {update}")
                        self.response(update, unchoked_port)


if __name__ == '__main__':
    # Original port: 10086, but something wrong with that port
    tracker = Tracker(port=10086)

    # Tit-for-tat
    tracker.tit4tat = True

    tracker.start()
