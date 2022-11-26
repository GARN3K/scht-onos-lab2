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
    "Berlin": "10.0.0.1",
    "Hamburg": "10.0.0.7",
    "Koln": "10.0.0.2",
    "Frankfurt": "10.0.0.6",
    "Stuttgart": "10.0.0.10",
    "Dusseldorf": "10.0.0.4",
    "Leipzig": "10.0.0.8",
    "Dortmund": "10.0.0.3",
    "Essen": "10.0.0.5",
    "Munich": "10.0.0.9",
}


class Manager:
    def __init__(self) -> None:
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
        print('Wybierz opcje: \n 1) Dodaj nowe polaczenie \n 2) Usun poprzednie polaczenia')
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
        dictionary_temp2 = {k: v for k, v in dictionary.items() if k != hostA}
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

    def get_path(self) -> []:
        return self.path

    def get_hosts(self) -> dict:
        return self.HOSTS

    def get_hostD(self) -> str:
        return self.hostD

    def get_hostS(self) -> str:
        return self.hostS

#Funckja znajdujaca porty na linku
    def get_ports(self, hostS, hostD) -> []:
        r = requests.get(onosUrl + "links", auth=HTTPBasicAuth("onos", "rocks"))
        for item in r.json()['links']:
            if item['src']['device'] == devices[hostS] and item['dst']['device'] == devices[hostD]:
                self.PORTS['src'] = hostS
                self.PORTS['src_port'] = item['src']['port']
                self.PORTS['dst'] = hostD
                self.PORTS['dst_port'] = item['dst']['port']
        return self.PORTS

#Funkcja tworzaca flowy dla danej sciezki
    def create_flow(self, path):
        if (len(path) < 2):
            AssertionError()
        elif (len(path) == 2):
            Manager.addFlow(self, devices[self.PORTS['src']], "1", self.PORTS['src_port'], IPs[self.PORTS['dst']])
            Manager.addFlow(self, devices[self.PORTS['src']], self.PORTS['src_port'], "1", IPs[self.PORTS['src']])

            Manager.addFlow(self, devices[self.PORTS['dst']], "1", self.PORTS['dst_port'], IPs[self.PORTS['src']])
            Manager.addFlow(self, devices[self.PORTS['dst']], self.PORTS['dst_port'], "1", IPs[self.PORTS['dst']])

    def getTemplate(self) -> json:
        with open("flow.json") as file:
            return json.load(file)

#Funkcja dodajaca flowy do onosa
    def addFlow(self, deviceId: str, inputPort: str, outputPort: str, ipDest: str):
        template = Manager.getTemplate(self)

        template["deviceId"] = deviceId
        template["treatment"]["instructions"][0]["port"] = outputPort
        template["selector"]["criteria"][0]["port"] = inputPort
        template["selector"]["criteria"][2]["ip"] = ipDest+"/32"

        r = requests.post(onosUrl + "flows/" + deviceId, json=template, auth=HTTPBasicAuth("onos", "rocks"))

#Funkcja usuwajaca flowy z onosa
    def deleteFlows(self):
        r = requests.delete(onosUrl + "flows/application/org.onosproject.rest", auth=HTTPBasicAuth("onos", "rocks"))
        self.PORTS = {}
        self.PATH = {}
        self.HOSTS = {}
        Manager.load_data(self)

def main() -> None:

    start = Manager()
    try:
        while True:
            if(start.data_input()):
                sorted_dict = start.sort_dict(start.get_hosts(), start.get_hostD())
                start.shortest_path(sorted_dict, start.get_hostS())
                start.get_ports(start.get_hostS(), start.get_hostD())
                start.create_flow(start.path)
    except KeyboardInterrupt:
        pass
    except AssertionError:
        print('Podales te dwa same hosty')
    except NameError:
        print('Podales zla nazwe miasta')
    except KeyError:
        print('Podales zla nazwe miasta')

if __name__ == '__main__':
    main()
