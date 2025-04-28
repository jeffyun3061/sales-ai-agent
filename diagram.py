import plotly.graph_objects as go
import pandas as pd

df = pd.read_csv("fake_lead_data_full (1).csv")

def score_bin(score):
    if score >= 0.9:
        return "90점 이상"
    elif score >= 0.8:
        return "80~89점"
    elif score >= 0.7:
        return "70~79점"
    else:
        return "70점 미만"
    
df["score_bin"] = df["relevance_score"].apply(score_bin)

# 노드 리스트 구성
all_nodes = list(df["score_bin"].unique()) + list(df["company"])
node_map = {name: idx for idx, name in enumerate(all_nodes)}

# 링크 구성
sources = df["score_bin"].map(node_map)
targets = df["company"].map(node_map)
values = [1] * len(df)

# Sankey 그리기
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=all_nodes
    ),
    link=dict(
        source=sources,
        target=targets,
        value=values
    )
)])

fig.update_layout(title_text="리드 추천 생키 다이어그램 (점수 → 회사)", font_size=10)
fig.show()