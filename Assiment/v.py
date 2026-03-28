import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import time
import random
import os
import numpy as np

st.set_page_config(layout="wide")

# =====================
# LOAD IMAGE
# =====================
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
HOUSE_PATH = os.path.join(BASE_DIR, "house.jpg")
CAR_PATH   = os.path.join(BASE_DIR, "carr.jpg")

def load_jpg(path, size=64):
    """โหลด JPG (พื้นขาว) แปลงเป็น numpy array RGB"""
    from PIL import Image
    img = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    return np.array(img)

try:
    house_img = load_jpg(HOUSE_PATH, size=64)
    car_img   = load_jpg(CAR_PATH,   size=48)
    USE_IMG   = True
except Exception as e:
    st.warning(f"ไม่สามารถโหลดรูปได้: {e}")
    USE_IMG   = False

# =====================
# INIT
# =====================
if "G" not in st.session_state:
    G = nx.Graph()
    G.add_weighted_edges_from([
        ("Bangkok",      "Nakhon Nayok",   4),
        ("Bangkok",      "Chachoengsao",   2),
        ("Bangkok",      "Nakhon Pathom",  6),
        ("Nakhon Nayok", "Chachoengsao",   7),
        ("Nakhon Nayok", "Sing Buri",      5),
        ("Chachoengsao", "Saraburi",       8),
        ("Chachoengsao", "Lop Buri",       3),
        ("Saraburi",     "Bangkok",        3),
        ("Sing Buri",    "Nakhon Pathom",  2),
        ("Sing Buri",    "Chonburi",       3),
        ("Lop Buri",     "Nakhon Nayok",   7),
        ("Lop Buri",     "Chai Nat",       4),
    ])
    pos = nx.spring_layout(G, seed=42)
    st.session_state.G   = G
    st.session_state.pos = pos

G   = st.session_state.G
pos = st.session_state.pos

# =====================
# UPDATE LAYOUT
# =====================
def update_layout(new_node=None):
    global pos
    if new_node:
        pos[new_node] = (random.uniform(-1, 1), random.uniform(-1, 1))
    fixed = list(pos.keys())
    pos   = nx.spring_layout(G, pos=pos, fixed=fixed if fixed else None)
    st.session_state.pos = pos

# =====================
# DRAW GRAPH
# =====================
NODE_RADIUS = 0.06

def draw_graph(path=None, packet_positions=None):
    fig, ax = plt.subplots(figsize=(9, 6))

    # Edges
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="gray", width=1.5)
    nx.draw_networkx_edge_labels(
        G, pos,
        edge_labels=nx.get_edge_attributes(G, "weight"),
        font_size=7, ax=ax,
    )

    # Red path
    if path:
        nx.draw_networkx_edges(
            G, pos, edgelist=list(zip(path, path[1:])),
            edge_color="red", width=3, ax=ax,
        )

    # Nodes — วาดรูปบ้าน
    for node, (x, y) in pos.items():
        if USE_IMG:
            # zoom=0.55 → รูปขนาดพอดีโหนด
            ib = OffsetImage(house_img, zoom=0.55)
            ab = AnnotationBbox(
                ib, (x, y),
                frameon=True,                          # กรอบช่วยให้เห็นชัด
                bboxprops=dict(edgecolor="steelblue",
                               facecolor="lightblue",
                               linewidth=1.5,
                               boxstyle="round,pad=0.1"),
                zorder=4,
            )
            ax.add_artist(ab)
        else:
            circle = plt.Circle((x, y), NODE_RADIUS,
                                 color="lightblue", ec="steelblue",
                                 linewidth=1.5, zorder=3)
            ax.add_artist(circle)
            ax.text(x, y, "🏠", fontsize=10,
                    ha="center", va="center", zorder=4)

        # ชื่อโหนด ด้านล่าง
        ax.text(x, y - NODE_RADIUS - 0.10, node,
                fontsize=7, ha="center", va="top", zorder=5,
                bbox=dict(facecolor="white", alpha=0.8,
                          edgecolor="none", pad=1))

    # Packets — วาดรูปรถ
    if packet_positions:
        for (px, py) in packet_positions:
            if USE_IMG:
                ib2 = OffsetImage(car_img, zoom=0.40)
                ab2 = AnnotationBbox(
                    ib2, (px, py),
                    frameon=True,
                    bboxprops=dict(edgecolor="orange",
                                   facecolor="lightyellow",
                                   linewidth=1.2,
                                   boxstyle="round,pad=0.05"),
                    zorder=6,
                )
                ax.add_artist(ab2)
            else:
                ax.text(px, py, "🚗", fontsize=12,
                        ha="center", va="center", zorder=6)

    ax.set_title("Smart Traffic Simulation", fontsize=12, fontweight="bold")
    ax.axis("off")
    ax.set_xlim([min(x for x, y in pos.values()) - 0.35,
                 max(x for x, y in pos.values()) + 0.35])
    ax.set_ylim([min(y for x, y in pos.values()) - 0.35,
                 max(y for x, y in pos.values()) + 0.35])
    plt.tight_layout()
    return fig

# =====================
# ANIMATION
# =====================
def animate(path, num_packets):
    placeholder      = st.empty()
    original_weights = {}
    traffic          = {}

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        original_weights[(u, v)] = G[u][v]["weight"]
        traffic[(u, v)]          = 0

    packets = [
        {
            "edge_index": 0,
            "t":          0.0,
            "speed":      random.uniform(0.03, 0.06),
            "delay":      i * 8,
        }
        for i in range(num_packets)
    ]

    step    = 0
    running = True

    while running:
        running          = False
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
                G[u][v]["weight"] = original_weights[(u, v)] + traffic[(u, v)]

            x1, y1 = pos[u]
            x2, y2 = pos[v]
            p["t"] += p["speed"]
            packet_positions.append((
                x1 + (x2 - x1) * p["t"],
                y1 + (y2 - y1) * p["t"],
            ))

            if p["t"] >= 1:
                traffic[(u, v)] -= 1
                G[u][v]["weight"] = original_weights[(u, v)] + traffic[(u, v)]
                p["edge_index"] += 1
                p["t"] = 0

        fig = draw_graph(path, packet_positions)
        placeholder.pyplot(fig)
        plt.close(fig)
        time.sleep(0.05)
        step += 1

# =====================
# COMPUTE PATH INFO
# =====================
def get_path_info(G, path):
    total_dist = 0
    details    = []
    for u, v in zip(path, path[1:]):
        w = G[u][v]["weight"]
        total_dist += w
        details.append((u, v, w))
    dist_km    = total_dist * 10
    speed_kmh  = 80
    travel_min = (dist_km / speed_kmh) * 60
    return total_dist, dist_km, travel_min, details

# =====================
# UI
# =====================
st.title("🚦 Smart Traffic Simulation")

col1, col2 = st.columns(2)

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
    v = st.text_input("To",   key="edge_to")
    w = st.number_input("Weight", value=1, min_value=1)
    if st.button("Add Edge"):
        if u and v:
            G.add_edge(u, v, weight=w)
            update_layout()
            st.success(f"Edge {u} ↔ {v} (weight={w}) added")

with col2:
    st.subheader("Simulation")
    start   = st.text_input("Start Node", key="start_node")
    end     = st.text_input("End Node",   key="end_node")
    packets = st.number_input("Packets", min_value=1, value=5)

    if st.button("Run Simulation"):
        if start not in G.nodes:
            st.error(f"Start node '{start}' not found")
        elif end not in G.nodes:
            st.error(f"End node '{end}' not found")
        else:
            try:
                path = nx.shortest_path(G, start, end, weight="weight")
                total_w, dist_km, travel_min, seg = get_path_info(G, path)

                st.write("**เส้นทาง:**", " → ".join(path))

                m1, m2, m3 = st.columns(3)
                m1.metric("🛣️ ระยะทาง (น้ำหนักรวม)", f"{total_w} หน่วย")
                m2.metric("📏 ระยะทางโดยประมาณ", f"{dist_km:.0f} กม.")
                m3.metric("⏱️ เวลาเดินทางโดยประมาณ",
                          f"{int(travel_min)} นาที {int((travel_min % 1)*60)} วินาที")

                with st.expander("📋 รายละเอียดแต่ละช่วง"):
                    rows = [{"จาก": u, "ถึง": v, "น้ำหนัก": ww,
                             "ระยะทาง (กม.)": ww * 10,
                             "เวลา (นาที)": round(ww * 10 / 80 * 60, 1)}
                            for u, v, ww in seg]
                    st.table(rows)

                animate(path, int(packets))

            except nx.NetworkXNoPath:
                st.error("No path found between these nodes")
            except Exception as e:
                st.error(f"Error: {e}")

st.subheader("Graph View")
st.pyplot(draw_graph())