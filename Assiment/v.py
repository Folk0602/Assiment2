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
def draw_graph(highlight_path=None, packet_positions=None):
    fig, ax = plt.subplots()

    nx.draw(G, pos,
            with_labels=True,
            node_color='skyblue',
            node_size=900,
            ax=ax)

    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G, 'weight'),
        ax=ax
    )

    if highlight_path:
        edges = list(zip(highlight_path, highlight_path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color='red', width=3, ax=ax)

    if packet_positions:
        for p in packet_positions:
            ax.scatter(p[0], p[1], s=200)

    return fig

# =====================
# ANIMATION
# =====================
def animate(path, num_packets):
    placeholder = st.empty()

    original_weights = {}
    traffic = {}
    total_distance = 0

    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        original_weights[(u, v)] = G[u][v]['weight']
        traffic[(u, v)] = 0
        total_distance += G[u][v]['weight']

    packets = []
    for i in range(num_packets):
        packets.append({
            "index": 0,
            "progress": 0.0,
            "delay": i * 10,
            "speed": random.uniform(0.5, 1.5)
        })

    step = 0
    running = True
    start_time = time.time()

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

            # 🚫 ห้ามแซง
            if i > 0:
                front = packets[i-1]
                if front["index"] == p["index"] and (front["progress"] - p["progress"] < 5):
                    speed = 0
                else:
                    speed = p["speed"]
            else:
                speed = p["speed"]

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

            if p["progress"] >= 30:
                traffic[(u, v)] -= 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]
                p["index"] += 1
                p["progress"] = 0

        fig = draw_graph(path, packet_positions)
        placeholder.pyplot(fig)

        time.sleep(0.03)
        step += 1

    end_time = time.time()
    return end_time - start_time, total_distance

# =====================
# UI
# =====================
st.title("🚦 Graph Traffic Simulation (Streamlit Version)")

col1, col2 = st.columns(2)

# ---------------------
# CRUD
# ---------------------
with col1:
    st.subheader("➕ Add Node / Edge")

    node = st.text_input("Node name")
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

# ---------------------
# PATH + ANIMATION
# ---------------------
with col2:
    st.subheader("🚀 Find Path")

    start = st.text_input("Start Node")
    end = st.text_input("End Node")
    packets = st.number_input("Packets", min_value=1, value=1)

    if st.button("Run Simulation"):
        try:
            path = nx.shortest_path(G, start, end, weight='weight')
            st.write("Path:", " -> ".join(path))

            travel_time, distance = animate(path, packets)

            st.success(f"Distance: {distance}")
            st.success(f"Time: {travel_time:.2f} sec")

        except:
            st.error("Path not found")

# ---------------------
# SHOW GRAPH
# ---------------------
st.subheader("📊 Graph View")
st.pyplot(draw_graph())