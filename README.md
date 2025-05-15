# Intra-Domain Routing Algorithms Implementation

## Project Overview

This project implements two fundamental intra-domain routing algorithms used within autonomous systems (AS) in computer networks:

1. **Distance Vector (DV) Routing Algorithm**
2. **Link State (LS) Routing Algorithm**

Both algorithms are designed to find the shortest (lowest-cost) paths through a network and handle dynamic network changes such as link failures and additions.

## Implementation Details

### Distance Vector Router

The Distance Vector implementation follows the Bellman-Ford algorithm and includes:

- **Distance Vector Table**: Maintains the cost to reach each destination
- **Forwarding Table**: Maps destination addresses to output ports
- **Neighbor Information**: Tracks direct neighbors and their costs
- **Count-to-Infinity Prevention**: Uses a maximum distance value (16) to prevent routing loops

Key features:
- Periodic broadcasting of distance vectors
- Dynamic updates when topology changes
- Efficient handling of link failures and additions
- Proper handling of the count-to-infinity problem

### Link State Router

The Link State implementation uses Dijkstra's algorithm and includes:

- **Link State Database**: Stores the network topology information
- **Sequence Numbers**: Prevents processing of outdated information
- **Forwarding Table**: Maps destination addresses to output ports
- **Flooding Mechanism**: Reliably propagates link state updates

Key features:
- Sequence number-based update mechanism
- Complete network topology maintenance
- Efficient shortest path calculation using Dijkstra's algorithm
- Proper handling of link state packet flooding

## Data Structures

### Distance Vector Router
- `distance_vector`: Maps destination addresses to costs
- `forwarding_table`: Maps destination addresses to output ports
- `neighbors`: Maps ports to (neighbor_address, link_cost) tuples
- `neighbor_dv`: Stores neighbors' distance vectors

### Link State Router
- `link_state_db`: Maps router addresses to (sequence_number, link_state) tuples
- `forwarding_table`: Maps destination addresses to output ports
- `neighbors`: Maps ports to (neighbor_address, link_cost) tuples
- `forwarded_packets`: Tracks already forwarded packets to prevent loops

## Algorithm Implementation

### Distance Vector Algorithm
1. Each router initializes its distance vector with 0 cost to itself and infinity to all other destinations
2. When a router receives a distance vector from a neighbor:
   - It updates its local copy of the neighbor's distance vector
   - Recalculates its own distance vector using the Bellman-Ford equation
   - Updates its forwarding table
   - If changes occurred, broadcasts its updated distance vector to all neighbors
3. Periodically broadcasts its distance vector to all neighbors

### Link State Algorithm
1. Each router maintains a database of link states for all routers in the network
2. When a router detects a change in its links:
   - It increments its sequence number
   - Updates its link state
   - Floods the new link state to all neighbors
3. When a router receives a link state update:
   - If the sequence number is higher than the stored one, it updates its database
   - Recalculates shortest paths using Dijkstra's algorithm
   - Updates its forwarding table
   - Forwards the update to other neighbors
4. Periodically broadcasts its link state to all neighbors

## Testing

Both implementations have been tested with various network topologies:
- Small networks with 2 routers and 3 clients
- Complex networks with multiple routers and clients
- Networks with link failures and additions

The implementations successfully find the shortest paths in all test cases and handle dynamic network changes correctly.

## Running the Simulation

To run the simulation with a graphical interface:
```bash
python visualize_network.py <network_json_file> {DV,LS}
```

To run the simulation without the graphical interface:
```bash
python network.py <network_json_file> {DV,LS}
```

Example:
```bash
python network.py 01_small_net.json DV
```

## Conclusion

This project demonstrates the implementation of two fundamental routing algorithms used in computer networks. Both implementations correctly find the shortest paths through the network and handle dynamic network changes, providing a solid foundation for understanding how routing works in real-world networks.
