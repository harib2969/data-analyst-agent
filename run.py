import pandas as pd
import json
import networkx as nx
import base64, io
import matplotlib.pyplot as plt
from pathlib import Path

def analyze(payload):
    """
    Generic analyzer for multiple file formats:
    - CSV (tabular)
    - JSON (structured records)
    - GraphML (networks)
    - TXT (text)
    """

    file_path = detect_file(payload)
    if not file_path:
        return {"error": "No supported file found in payload"}

    suffix = Path(file_path).suffix.lower()
    result = {"file": file_path, "type": suffix}

    if suffix == ".csv":
        df = pd.read_csv(file_path)
        result.update(analyze_dataframe(df))

    elif suffix == ".json":
        with open(file_path, "r") as f:
            data = json.load(f)
        result.update(analyze_json(data))

    elif suffix == ".graphml":
        G = nx.read_graphml(file_path)
        result.update(analyze_graph(G))

    elif suffix == ".txt":
        with open(file_path, "r") as f:
            text = f.read()
        result.update(analyze_text(text))

    else:
        result["error"] = f"Unsupported file type: {suffix}"

    return result


def detect_file(payload):
    """Pick the first file-like value"""
    for v in payload.values():
        if isinstance(v, str) and Path(v).exists():
            return v
    return None


# ---------- Handlers ----------
def analyze_dataframe(df):
    result = {}
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    if numeric_cols:
        col = numeric_cols[0]
        result["total"] = float(df[col].sum())
        result["median"] = float(df[col].median())

        if len(numeric_cols) > 1:
            result["correlation"] = float(df[numeric_cols].corr().iloc[0, 1])

    if cat_cols:
        col = cat_cols[0]
        result["top_category"] = str(df[col].mode().iloc[0])
        result["bar_chart"] = make_bar_chart(df, col, numeric_cols[0] if numeric_cols else None)

    if numeric_cols:
        result["cumulative_chart"] = make_cumulative_chart(df, numeric_cols[0])

    return result


def analyze_json(data):
    result = {"records": len(data) if isinstance(data, list) else 1}
    if isinstance(data, list) and all(isinstance(d, dict) for d in data):
        df = pd.DataFrame(data)
        result.update(analyze_dataframe(df))
    return result


def analyze_graph(G):
    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "is_connected": nx.is_connected(G) if nx.is_connected(G.to_undirected()) else False,
    }


def analyze_text(text):
    words = text.split()
    return {
        "characters": len(text),
        "words": len(words),
        "lines": text.count("\n") + 1,
    }


# ---------- Chart helpers ----------
def make_bar_chart(df, cat_col, num_col=None):
    fig, ax = plt.subplots()
    if num_col:
        df.groupby(cat_col)[num_col].sum().plot(kind="bar", ax=ax, color="blue")
    else:
        df[cat_col].value_counts().plot(kind="bar", ax=ax, color="blue")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def make_cumulative_chart(df, num_col):
    fig, ax = plt.subplots()
    df[num_col].cumsum().plot(ax=ax, color="red")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
