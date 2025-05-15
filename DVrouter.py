from router import Router
from packet import Packet
import json

class DVrouter(Router):

    def __init__(self, addr, heartbeat_time):
        Router.__init__(self, addr)
        self.heartbeat_time = heartbeat_time
        self.last_time = 0
        self.distance_vector = {addr: 0}
        self.forwarding_table = {}
        self.neighbors = {}
        self.neighbor_dv = {}
        self.INFINITY = 16

    def handle_packet(self, port, packet):
        if packet.is_traceroute:
            if packet.dst_addr in self.forwarding_table:
                out_port = self.forwarding_table[packet.dst_addr]
                self.send(out_port, packet)
        else:
            try:
                neighbor_addr = packet.src_addr
                received_dv = json.loads(packet.content)
                if (neighbor_addr not in self.neighbor_dv or
                    self.neighbor_dv[neighbor_addr] != received_dv):
                    self.neighbor_dv[neighbor_addr] = received_dv
                    neighbor_found = False
                    for p, (addr, _) in self.neighbors.items():
                        if addr == neighbor_addr:
                            neighbor_found = True
                            break
                    if not neighbor_found:
                        return
                    changed = self.update_distance_vector()
                    self.update_forwarding_table()
                    if changed:
                        self.broadcast_distance_vector()
            except Exception:
                pass

    def handle_new_link(self, port, endpoint, cost):
        self.neighbors[port] = (endpoint, cost)
        self.distance_vector[endpoint] = cost
        self.forwarding_table[endpoint] = port
        self.update_distance_vector()
        self.update_forwarding_table()
        self.broadcast_distance_vector()
        self.send_distance_vector(port)

    def handle_remove_link(self, port):
        if port in self.neighbors:
            endpoint, _ = self.neighbors[port]
            del self.neighbors[port]
            if endpoint in self.neighbor_dv:
                del self.neighbor_dv[endpoint]
            if endpoint in self.distance_vector:
                self.distance_vector[endpoint] = self.INFINITY
            if endpoint in self.forwarding_table and self.forwarding_table[endpoint] == port:
                del self.forwarding_table[endpoint]
            self.update_distance_vector()
            self.update_forwarding_table()
            self.broadcast_distance_vector()

    def handle_time(self, time_ms):
        if time_ms - self.last_time >= self.heartbeat_time:
            self.last_time = time_ms
            self.broadcast_distance_vector()

    def update_distance_vector(self):
        old_dv = self.distance_vector.copy()
        new_dv = {self.addr: 0}
        for port, (neighbor, cost) in self.neighbors.items():
            new_dv[neighbor] = cost
        all_destinations = set(old_dv.keys())
        for neighbor_dv in self.neighbor_dv.values():
            all_destinations.update(neighbor_dv.keys())
        for neighbor, neighbor_dv in self.neighbor_dv.items():
            neighbor_cost = float('inf')
            for port, (addr, cost) in self.neighbors.items():
                if addr == neighbor:
                    neighbor_cost = cost
                    break
            if neighbor_cost < float('inf'):
                for dest, dest_cost in neighbor_dv.items():
                    if dest == self.addr:
                        continue
                    total_cost = neighbor_cost + dest_cost
                    if total_cost >= self.INFINITY:
                        total_cost = self.INFINITY
                    if dest not in new_dv or total_cost < new_dv[dest]:
                        new_dv[dest] = total_cost
        for dest in all_destinations:
            if dest not in new_dv and dest != self.addr:
                new_dv[dest] = self.INFINITY
        self.distance_vector = new_dv
        return old_dv != new_dv

    def update_forwarding_table(self):
        new_forwarding_table = {}
        for dest in self.distance_vector:
            if dest == self.addr:
                continue
            best_cost = float('inf')
            best_port = None
            for port, (neighbor, cost) in self.neighbors.items():
                if neighbor == dest:
                    best_cost = cost
                    best_port = port
                    break
            for port, (neighbor, cost_to_neighbor) in self.neighbors.items():
                if neighbor in self.neighbor_dv and dest in self.neighbor_dv[neighbor]:
                    cost_from_neighbor = self.neighbor_dv[neighbor][dest]
                    total_cost = cost_to_neighbor + cost_from_neighbor
                    if total_cost < best_cost:
                        best_cost = total_cost
                        best_port = port
            if best_port is not None and best_cost < self.INFINITY:
                new_forwarding_table[dest] = best_port
        self.forwarding_table = new_forwarding_table

    def broadcast_distance_vector(self):
        for port in self.neighbors:
            self.send_distance_vector(port)

    def send_distance_vector(self, port):
        dv_content = json.dumps(self.distance_vector)
        packet = Packet(Packet.ROUTING, self.addr, self.neighbors[port][0], dv_content)
        self.send(port, packet)

    def __repr__(self):
        output = f"DVrouter(addr={self.addr})\n"
        output += "Distance Vector:\n"
        for dest, cost in self.distance_vector.items():
            output += f"  {dest}: {cost}\n"
        output += "Forwarding Table:\n"
        for dest, port in self.forwarding_table.items():
            output += f"  {dest} -> Port {port}\n"
        return output