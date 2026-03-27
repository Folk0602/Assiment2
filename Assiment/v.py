import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import time
import random

st.set_page_config(layout="wide")

# =====================
# INIT
# =====================
if "G" not in st.session_state:
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
    st.session_state.G = G
    st.session_state.pos = nx.spring_layout(G, seed=42)

G = st.session_state.G
pos = st.session_state.pos

# =====================
# DRAW
# =====================
def draw_graph(path=None, packet_positions=None):
    fig, ax = plt.subplots()

    nx.draw(G, pos,
            with_labels=True,
            node_color='skyblue',
            node_size=200,
            ax=ax)

    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G, 'weight'),
        ax=ax
    )

    # highlight path
    if path:
        edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='red', width=3, ax=ax)

    # draw packets
    if packet_positions:
        for i, (x, y) in enumerate(packet_positions):
            ax.scatter(x, y, s=250, color='yellow', edgecolors='black')
            ax.text(x, y, str(i), fontsize=8)

    return fig

# =====================
# ANIMATION (SMOOTH)
# =====================
def animate(path, num_packets):
    placeholder = st.empty()

    original_weights = {}
    traffic = {}

    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        original_weights[(u, v)] = G[u][v]['weight']
        traffic[(u, v)] = 0

    # 🔥 packet ลื่น
    packets = []
    for i in range(num_packets):
        packets.append({
            "edge_index": 0,
            "t": 0.0,
            "speed": random.uniform(0.005, 0.01),  # smooth
            "delay": i * 8
        })

    step = 0
    running = True
    start_time = time.time()

    while running:
        running = False
        packet_positions = []

        for p in packets:

            if step < p["delay"]:
                continue

            if p["edge_index"] >= len(path)-1:
                continue

            running = True

            u = path[p["edge_index"]]
            v = path[p["edge_index"]+1]

            # เข้า edge
            if p["t"] == 0:
                traffic[(u, v)] += 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]

            x1, y1 = pos[u]
            x2, y2 = pos[v]

            # 🔥 smooth movement
            p["t"] += p["speed"]

            x = x1 + (x2 - x1) * p["t"]
            y = y1 + (y2 - y1) * p["t"]

            packet_positions.append((x, y))

            # ออกจาก edge
            if p["t"] >= 1:
                traffic[(u, v)] -= 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]
                p["edge_index"] += 1
                p["t"] = 0

        fig = draw_graph(path, packet_positions)
        placeholder.pyplot(fig)

        # 🔥 ลื่นขึ้น
        time.sleep(0.01)
        step += 1

    end_time = time.time()
    return end_time - start_time

# =====================
# UI
# =====================
st.title("🚦 Graph Traffic Simulation (Smooth Version)")

col1, col2 = st.columns(2)

# CRUD
with col1:
    st.subheader("➕ Manage Graph")

    node = st.text_input("Add Node")
    if st.button("Add Node"):
        if node:
            G.add_node(node)
            st.session_state.pos = nx.spring_layout(G, seed=42)
            st.success("Node added")

    del_node = st.text_input("Delete Node")
    if st.button("Delete Node"):
        if del_node in G.nodes:
            G.remove_node(del_node)
            st.session_state.pos = nx.spring_layout(G, seed=42)
            st.success("Node removed")
        else:
            st.error("Node not found")

    u = st.text_input("From")
    v = st.text_input("To")
    w = st.number_input("Weight", value=1)

    if st.button("Add Edge"):
        if u and v:
            G.add_edge(u, v, weight=w)
            st.success("Edge added")

# Simulation
with col2:
    st.subheader("🚀 Simulation")

    start = st.text_input("Start Node")
    end = st.text_input("End Node")
    packets = st.number_input("Packets", min_value=1, value=5)

    if st.button("Run Simulation"):
        try:
            path = nx.shortest_path(G, start, end, weight='weight')
            st.write("Path:", " -> ".join(path))

            t = animate(path, packets)

            st.success(f"Simulation Time: {t:.2f} sec")

        except:
            st.error("Path not found")

# Show graph
st.subheader("📊 Graph View")
st.pyplot(draw_graph())