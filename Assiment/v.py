import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
    pos = nx.spring_layout(G, seed=42)
    st.session_state.G = G
    st.session_state.pos = pos

G = st.session_state.G
pos = st.session_state.pos

# =====================
# UPDATE LAYOUT
# =====================
def update_layout(new_node=None):
    global pos
    if new_node:
        pos[new_node] = (random.uniform(-1, 1), random.uniform(-1, 1))
    fixed = list(pos.keys())
    pos = nx.spring_layout(G, pos=pos, fixed=fixed if fixed else None)
    st.session_state.pos = pos

# =====================
# DRAW GRAPH
# =====================
def draw_graph(path=None, packet_positions=None):
    fig, ax = plt.subplots(figsize=(8, 6))

    # วาด edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='gray', width=1.5)
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G, 'weight'),
        font_size=7,
        ax=ax
    )

    # วาด path สีแดง
    if path:
        edges = list(zip(path, path[1:]))
        nx.draw_networkx_edges(G, pos, edgelist=edges,
                               edge_color='red', width=3, ax=ax)

    # วาดโหนด (วงกลมสีฟ้า) + ไอคอนบ้าน (emoji ผ่าน text) + ชื่อข้างล่าง
    node_radius = 0.06
    for node, (x, y) in pos.items():
        # วงกลมพื้นหลัง
        circle = plt.Circle((x, y), node_radius, color="lightblue",
                             ec="steelblue", linewidth=1.5, zorder=3)
        ax.add_artist(circle)

        # ไอคอนบ้าน (unicode emoji)
        ax.text(x, y, "🏠", fontsize=10, ha='center', va='center',
                zorder=4)

        # ชื่อโหนด → อยู่ด้านล่าง (y - offset)
        ax.text(x, y - node_radius - 0.07, node,
                fontsize=7, ha='center', va='top',
                bbox=dict(facecolor='white', alpha=0.7,
                          edgecolor='none', pad=1),
                zorder=5)

    # วาดรถ (packet) ตามตำแหน่ง
    if packet_positions:
        for (x, y) in packet_positions:
            ax.text(x, y, "🚗", fontsize=12, ha='center', va='center',
                    zorder=6)

    ax.set_title("Smart Traffic Simulation", fontsize=12, fontweight='bold')
    ax.axis('off')

    # ปรับขอบให้ชื่อโหนดไม่ถูกตัด
    ax.set_xlim([min(x for x, y in pos.values()) - 0.25,
                 max(x for x, y in pos.values()) + 0.25])
    ax.set_ylim([min(y for x, y in pos.values()) - 0.25,
                 max(y for x, y in pos.values()) + 0.25])

    plt.tight_layout()
    return fig

# =====================
# ANIMATION
# =====================
def animate(path, num_packets):
    placeholder = st.empty()
    original_weights = {}
    traffic = {}

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        original_weights[(u, v)] = G[u][v]['weight']
        traffic[(u, v)] = 0

    packets = []
    for i in range(num_packets):
        packets.append({
            "edge_index": 0,
            "t": 0.0,
            "speed": random.uniform(0.03, 0.06),
            "delay": i * 8
        })

    step = 0
    running = True

    while running:
        running = False
        packet_positions = []

        for p in packets:
            if step < p["delay"]:
                running = True
                continue
            if p["edge_index"] >= len(path) - 1:
                continue

            running = True
            u = path[p["edge_index"]]
            v = path[p["edge_index"] + 1]

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
        plt.close(fig)
        time.sleep(0.05)
        step += 1

# =====================
# UI
# =====================
st.title("🚦 Smart Traffic Simulation")

col1, col2 = st.columns(2)

# CRUD
with col1:
    st.subheader("Manage Graph")

    node = st.text_input("Add Node", key="add_node_input")
    if st.button("Add Node"):
        if node and node not in G.nodes:
            G.add_node(node)
            update_layout(node)
            st.success(f"Node '{node}' added")
        elif node in G.nodes:
            st.warning("Node already exists")

    del_node = st.text_input("Delete Node", key="del_node_input")
    if st.button("Delete Node"):
        if del_node in G.nodes:
            G.remove_node(del_node)
            pos.pop(del_node, None)
            st.session_state.pos = pos
            st.success(f"Node '{del_node}' removed")
        else:
            st.error("Node not found")

    u = st.text_input("From", key="edge_from")
    v = st.text_input("To", key="edge_to")
    w = st.number_input("Weight", value=1, min_value=1)
    if st.button("Add Edge"):
        if u and v:
            G.add_edge(u, v, weight=w)
            update_layout()
            st.success(f"Edge {u} ↔ {v} (weight={w}) added")

# Simulation
with col2:
    st.subheader("Simulation")
    start = st.text_input("Start Node", key="start_node")
    end = st.text_input("End Node", key="end_node")
    packets = st.number_input("Packets", min_value=1, value=5)

    if st.button("Run Simulation"):
        if start not in G.nodes:
            st.error(f"Start node '{start}' not found")
        elif end not in G.nodes:
            st.error(f"End node '{end}' not found")
        else:
            try:
                path = nx.shortest_path(G, start, end, weight='weight')
                st.write("Path:", " → ".join(path))
                animate(path, int(packets))
            except nx.NetworkXNoPath:
                st.error("No path found between these nodes")
            except Exception as e:
                st.error(f"Error: {e}")

# Show graph
st.subheader("Graph View")
st.pyplot(draw_graph())