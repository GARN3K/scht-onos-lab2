import json
from queue import PriorityQueue

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

import Dijkstra

#Url do onosa
onosUrl = "http://192.168.1.216:8181/onos/v1/"
#Slownik zawierajacy nazwy miast i id switchy w nich
devices = {
    "Berlin": "of:0000000000000001",
    "Hamburg": "of:0000000000000002",
    "Munich": "of:0000000000000003",
    "Koln": "of:0000000000000004",
    "Frankfurt": "of:0000000000000005",
    "Stuttgart": "of:0000000000000006",
    "Dusseldorf": "of:0000000000000007",
    "Leipzig": "of:0000000000000008",
    "Dortmund": "of:0000000000000009",
    "Essen": "of:000000000000000a",
}
#Slownik zawierajacy nazwy miast i ich adresy IP
IPs = {
    "of:0000000000000001": "10.0.0.1",
    "of:0000000000000002": "10.0.0.7",
    "of:0000000000000004": "10.0.0.2",
    "of:0000000000000005": "10.0.0.6",
    "of:0000000000000006": "10.0.0.10",
    "of:0000000000000007": "10.0.0.4",
    "of:0000000000000008": "10.0.0.8",
    "of:0000000000000009": "10.0.0.3",
    "of:000000000000000a": "10.0.0.5",
    "of:0000000000000003": "10.0.0.9",
}

class Manager:
    def __init__(self) -> None:
        self.HOSTS_temp = {}
        self.HOSTS = {}
        self.PORTS = {}
        self.path = []
        Manager.load_data(self)

#Funkcja wczytujaca dane z pliku .ods (taki excel mozesz to prosto przerobic na excela)
    def load_data(self):
        loaded_data = pd.read_excel("dane.ods", engine="odf")
        for index, row in loaded_data.iterrows():
            if (row[0] in self.HOSTS):
                self.HOSTS[row[0]].append(Dijkstra.Edge(row[1], row[2], 100))
            else:
                self.HOSTS[row[0]] = ([Dijkstra.Edge(row[1], row[2], 100)])

#Funkcja pozwalajaca uzytkownikowi czy chce dodac nowe polaczenie czy usunac stare
    def data_input(self) -> bool:
        print('Wybierz opcje: \n 1) Dodaj nowe polaczenie \n 2) Usun poprzednie przepływy')
        option = input()
        match option:
            case '1':
                self.hostS = input("Podaj Hosta Pierwotnego\n")
                self.hostD = input("Podaj Hosta Docelowego\n")
                self.bandwith = input("Podaj wielkosc strumienia danych\n")
                return True
            case '2':
                Manager.deleteFlows(self)
            case _:
                'Podales zly klucz'
                return False

#Funckja sortujaca slownik do znajdywania najkrotszej drogi
    def sort_dict(self, dictionary, hostA) -> dict:
        dictionary_temp1 = {hostA: dictionary[hostA]}
        dictionary_temp2    = {k: v for k, v in dictionary.items() if k != hostA}
        dictionary_final = {**dictionary_temp1, **dictionary_temp2}
        return dictionary_final

#Funkcja znajdujaca najkrtosza droge
    def shortest_path(self, hosts, hostB):
        queue = PriorityQueue()
        nodes = Dijkstra.construct_graph(hosts)
        for node in nodes:
            queue.put(node)
        Dijkstra.find_shortest_path(queue)
        for node in nodes:
            if (node.city == hostB):
                self.path = node.path
                distance = node.distance
        print(self.path, distance)

    def convert_path(self):
        path_temp = self.path
        self.path = []
        for i in range(len(path_temp)):
            for j in range(len(self.HOSTS[path_temp[i]])):
                if(i < len(path_temp) -1):
                    if(self.HOSTS[path_temp[i]][j].city == path_temp[i+1]):
                        self.HOSTS[path_temp[i]][j].bandwith -= int(self.bandwith)
                        for k in range(len(self.HOSTS[path_temp[i]])):
                            if(k == len(self.HOSTS[path_temp[i+1]])):
                                break
                            if self.HOSTS[path_temp[i+1]][k].city == path_temp[i]:
                                self.HOSTS[path_temp[i+1]][k].bandwith -= int(self.bandwith)

            self.path.append(devices[path_temp[i]])

    def get_path(self) -> list:
        return self.path

    def get_bandwith(self) -> str:
        return self.bandwith

    def get_hosts(self) -> dict:
        return self.HOSTS

    def get_hostD(self) -> str:
        return self.hostD

    def get_hostS(self) -> str:
        return self.hostS
    def get_host_temp(self) -> dict:
        return self.HOSTS_temp

#Funckja znajdujaca porty na linku
    def get_ports_of_device(self, deviceId: str):
        r = requests.get(onosUrl + "links", auth=HTTPBasicAuth("onos", "rocks"))
        links = r.json()["links"]
        for link in links:
            if link["src"]["device"] == deviceId:
                if deviceId not in self.PORTS:
                    self.PORTS[deviceId] = {}

                # output of that device and input of second device
                self.PORTS[deviceId][link["dst"]["device"]] = {"output": link["src"]["port"], "input": link["dst"]["port"]}

    #Funkcja tworzaca flowy dla danej sciezki
    def create_flow(self, Path:list):
        device1 = Path[0]
        device2 = Path[-1]

        ip1 = IPs[device1]
        ip2 = IPs[device2]

        route = Path[1:-1]

        Manager.get_ports_of_device(self, device1)
        Manager.get_ports_of_device(self, device2)

        if len(route) == 0:
            Manager.addFlow(self, device1, "1", self.PORTS[device1][device2]["output"], ip2)
            Manager.addFlow(self, device1, self.PORTS[device1][device2]["output"], "1", ip1)

            Manager.addFlow(self, device2, "1", self.PORTS[device2][device1]["output"], ip1)
            Manager.addFlow(self, device2, self.PORTS[device2][device1]["output"], "1", ip2)

        if len(route) > 0:
            ports = self.PORTS
            firstStop = route[0]
            lastStop = route[len(route) - 1]

            Manager.addFlow(self, device1, "1", ports[device1][firstStop]["output"], ip2)
            Manager.addFlow(self, device1, ports[device1][firstStop]["output"], "1", ip1)

            Manager.addFlow(self, device2, "1", ports[device2][lastStop]["output"], ip1)
            Manager.addFlow(self, device2, ports[device2][lastStop]["output"], "1", ip2)

            for device in route:
                Manager.get_ports_of_device(self, device)

            for i in range(len(route)):
                device = route[i]
                if device == firstStop and device == lastStop:
                    Manager.addFlow(self, device, ports[device1][device]["input"], ports[device][device2]["output"], ip2)
                    Manager.addFlow(self, device, ports[device2][device]["input"], ports[device][device1]["output"], ip1)
                    break

                if device == firstStop:
                    nextDevice = route[i + 1]
                    Manager.addFlow(self, device, ports[device1][device]["input"], ports[device][nextDevice]["output"], ip2)
                    Manager.addFlow(self, device, ports[nextDevice][device]["input"], ports[device][device1]["output"], ip1)
                if device == lastStop:
                    lastDevice = route[i - 1]
                    Manager.addFlow(self, device, ports[lastDevice][device]["input"], ports[device][device2]["output"], ip2)
                    Manager.addFlow(self, device, ports[device2][device]["input"], ports[device][lastDevice]["output"], ip1)

    def create_json_flow(self) -> json:
        with open("flow.json") as file:
            return json.load(file)

#Funkcja dodajaca flowy do onosa
    def addFlow(self, deviceId, inputPort, outputPort, ipDest):
        flow_file = Manager.create_json_flow(self)

        flow_file["deviceId"] = deviceId
        flow_file["treatment"]["instructions"][0]["port"] = outputPort
        flow_file["selector"]["criteria"][0]["port"] = inputPort
        flow_file["selector"]["criteria"][2]["ip"] = ipDest+"/32"

        r = requests.post(onosUrl + "flows/" + deviceId, json=flow_file, auth=HTTPBasicAuth("onos", "rocks"))

#Funkcja usuwajaca flowy z onosa
    def deleteFlows(self):
        r = requests.delete(onosUrl + "flows/application/org.onosproject.rest", auth=HTTPBasicAuth("onos", "rocks"))
        self.PORTS = {}
        self.PATH = {}
        self.HOSTS = {}
        Manager.load_data(self)

    def filter_data(self, bandwith):
        self.HOSTS_temp = self.HOSTS
        visits = {}
        for key, value in self.HOSTS.items():
            for i in range(len(value)):
                if (i == len(value)):
                    break
                if(value[i].bandwith < int(bandwith)):
                    if(key in visits):
                        number = visits[key]
                    else:
                        visits[key] = 0
                        number = 0
                    del self.HOSTS_temp[key][i-number]
                    visits[key] += 1





def main() -> None:

    start = Manager()
    try:
        while True:
            if(start.data_input()):
                start.filter_data(start.get_bandwith())
                sorted_dict = start.sort_dict(start.get_host_temp(), start.get_hostD())
                start.shortest_path(sorted_dict, start.get_hostS())
                start.convert_path()
                start.create_flow(start.path)
                start.filter_data(start.get_bandwith())
    except KeyboardInterrupt:
        pass
    except AssertionError:
        print('Podales te dwa same hosty')
    except NameError:
        print('Podales zla nazwe miasta 1')
    # except KeyError:
    #     print('Podales zla nazwe miasta 2')

if __name__ == '__main__':
    main()
