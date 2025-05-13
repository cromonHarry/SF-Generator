# ap_model_visualization.py
import streamlit as st
import os
import networkx as nx
import json
import re
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import io
from PIL import Image
import pandas as pd

def load_ap_data_safe():
    """优先从session_state读取AP数据，如果没有则读取文件"""
    if 'bg_history' in st.session_state and st.session_state.bg_history:
        return st.session_state.bg_history
    else:
        try:
            with open("background_history.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"AP数据未找到。请先生成故事或上传background_history.json。\n\n错误详情：{e}")
            return None

def parse_ap_model_data(raw_content):
    result = {"objects": {}, "paths": {}}
    objects_match = re.search(r'### Objects([\s\S]*?)(?=### Paths|$)', raw_content)
    if objects_match:
        objects_text = objects_match.group(1)
        object_matches = re.finditer(r'\d+\.\s+\*\*(.*?)\*\*:\s+([\s\S]*?)(?=\d+\.\s+\*\*|$)', objects_text)
        for match in object_matches:
            name, description = match.groups()
            result["objects"][name.strip()] = description.strip()
    paths_match = re.search(r'### Paths([\s\S]*?)$', raw_content)
    if paths_match:
        paths_text = paths_match.group(1)
        path_matches = re.finditer(r'\d+\.\s+\*\*(.*?)\*\*:\s+([\s\S]*?)(?=\d+\.\s+\*\*|$)', paths_text)
        for match in path_matches:
            name, description = match.groups()
            result["paths"][name.strip()] = description.strip()
    return result

def create_ap_graph(stage):
    G = nx.DiGraph()
    objects = ["Technology and resource", "User experiences", "System", "Avant-garde social issues", "Social Issue", "Human's value"]
    for obj in objects:
        G.add_node(obj, generation=stage+1)
    if stage < 2:
        G.add_node("Next Technology", generation=stage+2)
    edges = [
        ("Technology and resource", "User experiences", {"label": "Products and Services", "dashed": False}),
        ("Technology and resource", "Avant-garde social issues", {"label": "Paradigm", "dashed": False}),
        ("User experiences", "System", {"label": "Business Ecosystem", "dashed": False}),
        ("User experiences", "Avant-garde social issues", {"label": "Art (Social Critique)", "dashed": True}),
        ("System", "Social Issue", {"label": "Media", "dashed": True}),
        ("Avant-garde social issues", "Human's value", {"label": "Culture art revitalization", "dashed": False}),
        ("Avant-garde social issues", "Social Issue", {"label": "Communization", "dashed": False}),
        ("Social Issue", "Human's value", {"label": "Communication", "dashed": False}),
    ]
    if stage < 2:
        edges.extend([
            ("Social Issue", "Next Technology", {"label": "Organization", "dashed": False}),
            ("System", "Next Technology", {"label": "Standardization", "dashed": True}),
        ])
    for source, target, attr in edges:
        G.add_edge(source, target, **attr)
    return G

def visualize_ap_graph(G, stage_data, stage, highlight_node=None):
    plt.figure(figsize=(14, 8))
    pos = {"Technology and resource": (0.2, 0.35), "User experiences": (0.4, 0.55),
           "Avant-garde social issues": (0.6, 0.35), "System": (0.6, 0.75),
           "Social Issue": (0.8, 0.55), "Human's value": (1.0, 0.35),
           "Next Technology": (1.0, 0.75)}
    node_colors = {"Avant-garde social issues": "lightcoral", "Human's value": "yellow",
                   "Social Issue": "lightyellow", "Technology and resource": "lightgreen",
                   "User experiences": "lightblue", "System": "skyblue", "Next Technology": "lightgreen"}
    for node in G.nodes():
        nx.draw_networkx_nodes(G, pos, nodelist=[node],
                               node_color=node_colors.get(node, "gray"), node_size=1500 if node == highlight_node else 1200,
                               alpha=1.0 if node == highlight_node else 0.8,
                               edgecolors='red' if node == highlight_node else 'black',
                               linewidths=3 if node == highlight_node else 1)
    nx.draw_networkx_edges(G, pos,
                           edgelist=[(u, v) for u, v, d in G.edges(data=True) if not d.get('dashed', False)],
                           width=1.5, arrows=True, arrowsize=25, connectionstyle='arc3,rad=0.1')
    nx.draw_networkx_edges(G, pos,
                           edgelist=[(u, v) for u, v, d in G.edges(data=True) if d.get('dashed', False)],
                           width=1.5, style='dashed', arrows=True, arrowsize=25, connectionstyle='arc3,rad=0.1')
    labels = {n: (f"Technology\n(Stage {G.nodes[n]['generation']})" if n == "Next Technology" else n) for n in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_weight='bold')
    edge_labels = {(u, v): d.get('label', '') for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=9, font_color='navy', rotate=False, label_pos=0.6)
    plt.legend(handles=[Line2D([0], [0], color='black', linewidth=1.5, label='No time difference'),
                        Line2D([0], [0], color='black', linewidth=1.5, linestyle='--', label='Past to future')],
               loc='upper left')
    plt.title(f"AP Model - Stage {stage+1}", fontsize=16, pad=20)
    plt.axis('off')
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf)
    plt.close()
    return img

def get_connections(node, G, path_descriptions):
    incoming, outgoing = [], []
    for u, v, data in G.in_edges(node, data=True):
        incoming.append({"from": u, "path": data.get("label", "Unknown"), "description": path_descriptions.get(data.get("label", ""), "No description"), "dashed": data.get("dashed", False)})
    for u, v, data in G.out_edges(node, data=True):
        outgoing.append({"to": v, "path": data.get("label", "Unknown"), "description": path_descriptions.get(data.get("label", ""), "No description"), "dashed": data.get("dashed", False)})
    return incoming, outgoing

def collapsible_visualization():
    st.title("🚀 Archaeological Prototyping Model Visualization")
    ap_data = load_ap_data_safe()
    if ap_data is None:
        st.stop()
    st.sidebar.header("Visualization Settings")
    stage = st.sidebar.radio("Select Evolution Stage:", ["Stage 1: Ferment", "Stage 2: Take-off", "Stage 3: Maturity"], index=0)
    stage_map = {"Stage 1: Ferment": 0, "Stage 2: Take-off": 1, "Stage 3: Maturity": 2}
    stage_index = stage_map[stage]
    current_stage_data = parse_ap_model_data(ap_data[stage_index]["background"])
    G = create_ap_graph(stage_index)
    selected_node = st.session_state.get('selected_node', None)
    if stage_index == 2 and selected_node == "Next Technology":
        st.session_state['selected_node'] = None
    col1, col2 = st.columns([3, 1])
    with col1:
        st.image(visualize_ap_graph(G, current_stage_data, stage_index, selected_node), use_container_width=True)
    with col2:
        for node in G.nodes():
            label = node if node != "Next Technology" else f"Technology (Stage {G.nodes[node]['generation']})"
            if st.button(label, key=f"btn_{node}", use_container_width=True):
                st.session_state['selected_node'] = node
                st.rerun()
    selected_node = st.session_state.get('selected_node', None)
    if selected_node:
        content = current_stage_data["objects"].get(selected_node, "No content")
        st.markdown(f"### {selected_node}")
        st.markdown(content)
        incoming, outgoing = get_connections(selected_node, G, current_stage_data["paths"])
        st.markdown("#### Incoming Connections")
        for conn in incoming:
            st.markdown(f"- From **{conn['from']}** via *{conn['path']}* → {conn['description']}")
        st.markdown("#### Outgoing Connections")
        for conn in outgoing:
            st.markdown(f"- To **{conn['to']}** via *{conn['path']}* → {conn['description']}")
