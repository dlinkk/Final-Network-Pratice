from router import Router
from packet import Packet
import json
import heapq

class LSrouter(Router):

    def __init__(self, addr, heartbeat_time):
        Router.__init__(self, addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0
        self.link_state_db = {}
        self.sequence_number = 0
        self.link_state_db[self.addr] = (self.sequence_number, {})
        self.forwarding_table = {}
        self.neighbors = {}
        self.forwarded_packets = set()

    def handle_packet(self, port, packet):
        if packet.is_traceroute:
            if packet.dst_addr in self.forwarding_table:
                out_port = self.forwarding_table[packet.dst_addr]
                self.send(out_port, packet)
        else:
            try:
                ls_info = json.loads(packet.content)
                src_addr = ls_info['src_addr']
                sequence_number = ls_info['sequence_number']
                link_state = ls_info['link_state']
                is_new_or_updated = False
                if src_addr not in self.link_state_db:
                    is_new_or_updated = True
                else:
                    current_seq, _ = self.link_state_db[src_addr]
                    if sequence_number > current_seq:
                        is_new_or_updated = True
                if is_new_or_updated:
                    self.link_state_db[src_addr] = (sequence_number, link_state)
                    self.update_forwarding_table()
                    packet_id = (src_addr, sequence_number)
                    if packet_id not in self.forwarded_packets:
                        self.forwarded_packets.add(packet_id)
                        for neighbor_port in self.neighbors:
                            if neighbor_port != port:
                                self.send(neighbor_port, packet)
            except Exception:
                pass

    def handle_new_link(self, port, endpoint, cost):
        self.neighbors[port] = (endpoint, cost)
        self.update_own_link_state()
        self.update_forwarding_table()
        self.broadcast_link_state()

    def handle_remove_link(self, port):
        if port in self.neighbors:
            del self.neighbors[port]
            self.update_own_link_state()
            self.update_forwarding_table()
            self.broadcast_link_state()

    def handle_time(self, time_ms):
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            self.broadcast_link_state()

    def update_own_link_state(self):
        new_link_state = {}
        for _, (neighbor, cost) in self.neighbors.items():
            new_link_state[neighbor] = cost
        self.sequence_number += 1
        self.link_state_db[self.addr] = (self.sequence_number, new_link_state)

    def update_forwarding_table(self):
        new_forwarding_table = {}
        if not self.link_state_db:
            self.forwarding_table = new_forwarding_table
            return
        graph = {}
        for router, (_, link_state) in self.link_state_db.items():
            if router not in graph:
                graph[router] = {}
            for neighbor, cost in link_state.items():
                if neighbor not in graph:
                    graph[neighbor] = {}
                graph[router][neighbor] = cost
        distances, predecessors = self.dijkstra(graph, self.addr)
        for dest in distances:
            if dest != self.addr:
                next_hop = dest
                while predecessors.get(next_hop) is not None and predecessors[next_hop] != self.addr:
                    next_hop = predecessors[next_hop]
                if next_hop is not None and predecessors.get(next_hop) == self.addr:
                    for port, (neighbor, _) in self.neighbors.items():
                        if neighbor == next_hop:
                            new_forwarding_table[dest] = port
                            break
        self.forwarding_table = new_forwarding_table

    def dijkstra(self, graph, source):
        distances = {}
        predecessors = {}
        for node in graph:
            distances[node] = float('infinity')
            predecessors[node] = None
        distances[source] = 0
        pq = [(0, source)]
        visited = set()
        while pq:
            current_distance, current_node = heapq.heappop(pq)
            if current_node in visited:
                continue
            visited.add(current_node)
            if current_node not in graph:
                continue
            for neighbor, weight in graph[current_node].items():
                distance = current_distance + weight
                if distance < distances.get(neighbor, float('infinity')):
                    distances[neighbor] = distance
                    predecessors[neighbor] = current_node
                    heapq.heappush(pq, (distance, neighbor))
        return distances, predecessors

    def broadcast_link_state(self):
        _, link_state = self.link_state_db[self.addr]
        ls_content = {
            'src_addr': self.addr,
            'sequence_number': self.sequence_number,
            'link_state': link_state
        }
        content_str = json.dumps(ls_content)
        for port, (neighbor, _) in self.neighbors.items():
            packet = Packet(Packet.ROUTING, self.addr, neighbor, content_str)
            self.send(port, packet)

    def __repr__(self):
        output = f"LSrouter(addr={self.addr}, seq={self.sequence_number})\n"
        output += "Link State:\n"
        _, link_state = self.link_state_db.get(self.addr, (0, {}))
        for neighbor, cost in link_state.items():
            output += f"  {neighbor}: {cost}\n"
        output += "Forwarding Table:\n"
        for dest, port in self.forwarding_table.items():
            output += f"  {dest} -> Port {port}\n"
        return output