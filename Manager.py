from queue import PriorityQueue

import pandas as pd
import Dijkstra

class Manager:
    def __init__(self) -> None:
        loaded_data = pd.read_excel("dane.ods", engine="odf")
        self.HOSTS = {}
        for index, row in loaded_data.iterrows():
            if (row[0] in self.HOSTS):
                self.HOSTS[row[0]].append(Dijkstra.Edge(row[1], row[2], 100))
            else:
                self.HOSTS[row[0]] = ([Dijkstra.Edge(row[1], row[2], 100)])

    def data_input(self):
        self.hostB = input("Podaj Hosta Pierwotnego\n")
        self.hostA = input("Podaj Hosta Docelowego\n")
        self.bandwith = input("Podaj wielkosc strumienia danych\n")

    def sort_dict(self, dictionary, hostA) -> dict:
        dictionary_temp1 = {hostA:dictionary[hostA]}
        dictionary_temp2 = {k:v for k, v in dictionary.items() if k!=hostA}
        dictionary_final = {**dictionary_temp1, **dictionary_temp2}
        return dictionary_final

    def shortest_path(self, hosts, hostB):
        queue = PriorityQueue()
        nodes = Dijkstra.construct_graph(hosts)
        for node in nodes:
            queue.put(node)
        Dijkstra.find_shortest_path(queue)
        for node in nodes:
            if(node.city == hostB):
                path = node.path
                distance = node.distance
        print(path,distance)

    def get_hosts(self) -> dict:
        return self.HOSTS

    def get_hostA(self) -> str:
        return self.hostA

    def get_hostB(self) -> str:
        return self.hostB

def main() -> None:
    start = Manager()
    try:
        while True:
            start.data_input()
            sorted_dict = start.sort_dict(start.get_hosts(), start.get_hostA())
            start.shortest_path(sorted_dict, start.get_hostB())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()