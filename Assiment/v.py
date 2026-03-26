import tkinter as tk
from tkinter import messagebox
import networkx as nx
import matplotlib.pyplot as plt
import time
import random

plt.ion()

# =====================
# Graph
# =====================
G = nx.Graph()

G.add_weighted_edges_from([
    ("Bangkok", "Nakhon Nayok", 4),
    ("Bangkok", "Chachoengsao", 2),
    ("Bangkok", "Nakhon Pathom", 6),
    ("Nakhon Nayok", "Chachoengsao", 7),
    ("Nakhon Nayok", "Sing Buri", 5),
    ("Chachoengsao", "Saraburi", 8),
    ("Chachoengsao", "Lop Buri", 3),
    ("Saraburi", "Bangkok", 3),
    ("Sing Buri", "Nakhon Pathom", 2),
    ("Sing Buri", "Chonburi", 3),
    ("Lop Buri", "Nakhon Nayok", 7),
    ("Lop Buri", "Chai Nat", 4)
])

pos = nx.kamada_kawai_layout(G)

# =====================
# Draw Graph
# =====================
def draw_graph(highlight_path=None, packet_positions=None):
    plt.clf()

    nx.draw(G, pos,
            with_labels=True,
            node_color='skyblue',
            node_size=900)

    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G, 'weight')
    )

    if highlight_path:
        edges = list(zip(highlight_path, highlight_path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='red', width=3)

    if packet_positions:
        for p in packet_positions:
            plt.scatter(p[0], p[1], s=200)

    plt.title("Dynamic Traffic Simulation")
    plt.pause(0.01)

# =====================
# CRUD
# =====================
def add_node():
    node = entry_node.get()
    if node:
        G.add_node(node)
        update_layout()
        draw_graph()

def remove_node():
    node = entry_del_node.get()
    if node in G.nodes:
        G.remove_node(node)
        update_layout()
        draw_graph()
    else:
        messagebox.showerror("Error", "Node not found")

def add_edge():
    u = entry_u.get()
    v = entry_v.get()
    try:
        w = float(entry_w.get())
        G.add_edge(u, v, weight=w)
        draw_graph()
    except:
        messagebox.showerror("Error", "Invalid input")

def update_layout():
    global pos
    pos = nx.kamada_kawai_layout(G)

# =====================
# Multi Packet + Traffic
# =====================
def animate_multiple_packets(path, num_packets):
    start_time = time.time()
    total_distance = 0

    original_weights = {}
    traffic = {}

    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        original_weights[(u, v)] = G[u][v]['weight']
        traffic[(u, v)] = 0
        total_distance += G[u][v]['weight']

    # 🔥 สร้าง packet (เรียงลำดับ = สำคัญมาก ห้ามสลับ)
    packets = []
    for i in range(num_packets):
        packets.append({
            "index": 0,
            "progress": 0.0,
            "delay": i * 10,
            "speed": random.uniform(0.5, 1.5)
        })

    running = True
    step = 0

    while running:
        running = False
        packet_positions = []

        for i, p in enumerate(packets):

            if step < p["delay"]:
                continue

            if p["index"] >= len(path)-1:
                continue

            running = True

            u = path[p["index"]]
            v = path[p["index"]+1]

            # 🔥 ห้ามแซง: เช็คตัวหน้า
            if i > 0:
                front = packets[i-1]

                if front["index"] == p["index"]:
                    # ถ้าอยู่ edge เดียวกัน
                    if front["progress"] - p["progress"] < 5:
                        speed = 0  # 🚫 หยุด
                    else:
                        speed = p["speed"]
                else:
                    speed = p["speed"]
            else:
                speed = p["speed"]

            # เข้า edge → เพิ่ม traffic
            if p["progress"] == 0:
                traffic[(u, v)] += 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]

            x1, y1 = pos[u]
            x2, y2 = pos[v]

            p["progress"] += speed
            t = p["progress"] / 30

            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t

            packet_positions.append((x, y))

            # ออกจาก edge
            if p["progress"] >= 30:
                traffic[(u, v)] -= 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]

                p["index"] += 1
                p["progress"] = 0

        draw_graph(path, packet_positions)

        time.sleep(0.02)
        step += 1

    end_time = time.time()
    return end_time - start_time, total_distance

# =====================
# Find Path
# =====================
def find_path():
    start = entry_start.get()
    end = entry_end.get()

    try:
        num_packets = int(entry_packets.get())
        path = nx.shortest_path(G, start, end, weight='weight')

        travel_time, total_distance = animate_multiple_packets(path, num_packets)

        messagebox.showinfo(
            "Result",
            f"Path: {' -> '.join(path)}\n"
            f"Packets: {num_packets}\n"
            f"Distance: {total_distance}\n"
            f"Time: {travel_time:.2f} sec"
        )

    except:
        messagebox.showerror("Error", "Invalid input or path not found")

# =====================
# GUI
# =====================
root = tk.Tk()
root.title("Graph Manager (Dynamic Traffic Simulation)")

# Node
tk.Label(root, text="Add Node").grid(row=0, column=0)
entry_node = tk.Entry(root)
entry_node.grid(row=0, column=1)
tk.Button(root, text="Add", command=add_node).grid(row=0, column=2)

tk.Label(root, text="Delete Node").grid(row=1, column=0)
entry_del_node = tk.Entry(root)
entry_del_node.grid(row=1, column=1)
tk.Button(root, text="Delete", command=remove_node).grid(row=1, column=2)

# Edge
tk.Label(root, text="From").grid(row=2, column=0)
entry_u = tk.Entry(root)
entry_u.grid(row=2, column=1)

tk.Label(root, text="To").grid(row=3, column=0)
entry_v = tk.Entry(root)
entry_v.grid(row=3, column=1)

tk.Label(root, text="Weight").grid(row=4, column=0)
entry_w = tk.Entry(root)
entry_w.grid(row=4, column=1)

tk.Button(root, text="Add Edge", command=add_edge).grid(row=5, column=1)

# Path
tk.Label(root, text="Start").grid(row=6, column=0)
entry_start = tk.Entry(root)
entry_start.grid(row=6, column=1)

tk.Label(root, text="End").grid(row=7, column=0)
entry_end = tk.Entry(root)
entry_end.grid(row=7, column=1)

# Packet count
tk.Label(root, text="Packets").grid(row=8, column=0)
entry_packets = tk.Entry(root)
entry_packets.insert(0, "1")
entry_packets.grid(row=8, column=1)

# Buttons
tk.Button(root, text="Find Path (Animate)", command=find_path).grid(row=9, column=1)
tk.Button(root, text="Show Graph", command=lambda: draw_graph()).grid(row=10, column=1)

# Start
draw_graph()
root.mainloop()