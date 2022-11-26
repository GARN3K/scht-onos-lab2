from __future__ import annotations
from dataclasses import dataclass
from math import inf
from queue import PriorityQueue
#host1, host2, delay, bandwith, isoccupied;


@dataclass
class Edge:
    city: str 
    delay: float
    bandwith: int

HOSTS = {
    "Berlin": [
        Edge("Hamburg", 1, 100),
        Edge("Munich", 3.6, 100),
        # Edge("Cologne", 3.4, 100),
        # Edge("Frankfurt", 3, 100),
        # Edge("Stuttgart", 3.6, 100),
        # Edge("Dusseldorf", 3.4, 100),
        # Edge("Leipzig", 1.1, 100),
        # Edge("Dortmund", 3, 100),
        # Edge("Essen", 3.2, 100)
    ],
    "Hamburg": [
        Edge("Berlin", 1, 100),
        Edge("Munich", 1, 100)
    ],
    "Munich": [
        Edge("Hamburg", 1, 100),
        Edge("Berlin", 3.6, 100),
    ]
}
class Node:
    def __init__(self, current: str, hosts, graph: dict[str, Node], distance: float = inf) -> None:
        self.__graph = graph
        self.__graph[current] = self
        self.city = current
        self.__edges = hosts[current]
        self.__visited = False 
        self.__distance = distance
        self.__parent = None

    @property
    def neighbours(self) -> iter[tuple[Node, float, int]]:
        for edge in self.__edges:
            edge_node: Node = self.__graph[edge.city]
            if not edge_node.__visited:
                yield edge_node, edge.delay, edge.bandwith
        self.__visited = True

    def set_distance(self, distance: float, node: str | None = None) -> None:
        if distance <= self.__distance:
            self.__distance = distance
            self.__parent = node

    @property
    def distance(self) -> float:
        return self.__distance

    @property
    def path(self) -> str:
        # path = '['
        path = []
        node = self.city
        while node:
            node_o = self.__graph[node]
            path.append(node_o.city)
            # path += node_o.city + ', '
            node = node_o.__parent
        # return path[:-2] + ']'
        return path

    # @property
    # def parent(self) -> str:
    #     return self.

    def __lt__(self, other: Node) -> bool:
        return self.__distance < other.__distance

    def __le__(self, other: Node) -> bool:
        return self.__distance <= other.__distance


def construct_graph(hosts: dict[str, Edge]) -> list[Node]:
    graph = {}
    graph = [Node(current, hosts, graph) for current in hosts]
    graph[0].set_distance(0)
    return graph


def find_shortest_path(graph: PriorityQueue[Node]) -> None:
    while not graph.empty():
        node = graph.get()
        for neighbour, delay, bandwith in node.neighbours:
            neighbour.set_distance(node.distance + delay, node.city)


def main() -> None:
    queue = PriorityQueue()
    nodes = construct_graph(HOSTS)
    for node in nodes:
        queue.put(node)
    find_shortest_path(queue)
    for node in nodes:
        print(node.city, node.distance, node.path)


if __name__ == '__main__':
    main()

