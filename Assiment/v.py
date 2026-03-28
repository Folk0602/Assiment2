import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import time
import random

from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg

st.set_page_config(layout="wide")

# =====================
# LOAD IMAGE
# =====================
house_img = mpimg.imread("house.jpg")
car_img = mpimg.imread("car.jpg")

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

    pos = nx.spring_layout(G, seed=42)

    st.session_state.G = G
    st.session_state.pos = pos

G = st.session_state.G
pos = st.session_state.pos

# =====================
# UPDATE LAYOUT (ไม่ขยับ)
# =====================
def update_layout(new_node=None):
    global pos

    if new_node:
        pos[new_node] = (
            random.uniform(-1, 1),
            random.uniform(-1, 1)
        )

    pos = nx.spring_layout(G, pos=pos, fixed=pos.keys())
    st.session_state.pos = pos

# =====================
# DRAW GRAPH (ใช้รูป)
# =====================
def draw_graph(path=None, packet_positions=None):
    fig, ax = plt.subplots()

    # edge
    nx.draw_networkx_edges(G, pos, ax=ax)
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G, 'weight'),
        font_size=7,
        ax=ax
    )

    # 🏠 node
    for node, (x, y) in pos.items():
        imagebox = OffsetImage(house_img, zoom=0.08)
        ab = AnnotationBbox(imagebox, (x, y), frameon=False)
        ax.add_artist(ab)

        ax.text(x, y - 0.1, node, fontsize=7, ha='center')

    # 🔴 path
    if path:
        edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(
            G, pos,
            edgelist=edges,
            edge_color='red',
            width=2,
            ax=ax
        )

    # 🚗 packet
    if packet_positions:
        for (x, y) in packet_positions:
            imagebox = OffsetImage(car_img, zoom=0.05)
            ab = AnnotationBbox(imagebox, (x, y), frameon=False)
            ax.add_artist(ab)

    ax.set_title("Smart Traffic Simulation", fontsize=10)
    ax.axis('off')

    return fig

# =====================
# ANIMATION
# =====================
def animate(path, num_packets):
    placeholder = st.empty()

    original_weights = {}
    traffic = {}

    for i in range(len(path)-1):
        u, v = path[i], path[i+1]
        original_weights[(u, v)] = G[u][v]['weight']
        traffic[(u, v)] = 0

    packets = []
    for i in range(num_packets):
        packets.append({
            "edge_index": 0,
            "t": 0.0,
            "speed": random.uniform(0.005, 0.01),
            "delay": i * 8
        })

    step = 0
    running = True

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

            if p["t"] == 0:
                traffic[(u, v)] += 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]

            x1, y1 = pos[u]
            x2, y2 = pos[v]

            p["t"] += p["speed"]

            x = x1 + (x2 - x1) * p["t"]
            y = y1 + (y2 - y1) * p["t"]

            packet_positions.append((x, y))

            if p["t"] >= 1:
                traffic[(u, v)] -= 1
                G[u][v]['weight'] = original_weights[(u, v)] + traffic[(u, v)]
                p["edge_index"] += 1
                p["t"] = 0

        fig = draw_graph(path, packet_positions)
        placeholder.pyplot(fig)

        time.sleep(0.01)
        step += 1

# =====================
# UI
# =====================
st.title("🚦 Smart Traffic Simulation")

col1, col2 = st.columns(2)

# CRUD
with col1:
    st.subheader("Manage Graph")

    node = st.text_input("Add Node")
    if st.button("Add Node"):
        if node:
            G.add_node(node)
            update_layout(node)
            st.success("Node added")

    del_node = st.text_input("Delete Node")
    if st.button("Delete Node"):
        if del_node in G.nodes:
            G.remove_node(del_node)
            pos.pop(del_node, None)
            update_layout()
            st.success("Node removed")
        else:
            st.error("Node not found")

    u = st.text_input("From")
    v = st.text_input("To")
    w = st.number_input("Weight", value=1)

    if st.button("Add Edge"):
        if u and v:
            G.add_edge(u, v, weight=w)
            update_layout()
            st.success("Edge added")

# Simulation
with col2:
    st.subheader("Simulation")

    start = st.text_input("Start Node")
    end = st.text_input("End Node")
    packets = st.number_input("Packets", min_value=1, value=5)

    if st.button("Run Simulation"):
        try:
            path = nx.shortest_path(G, start, end, weight='weight')
            st.write("Path:", " -> ".join(path))
            animate(path, packets)
        except:
            st.error("Path not found")

# Show graph
st.subheader("Graph View")
st.pyplot(draw_graph())