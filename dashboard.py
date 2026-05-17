import os
import pandas as pd
import streamlit as st

CSV_FILE = "inspection_results.csv"

st.set_page_config(page_title="SPARKS Dashboard", layout="wide")

st.title("S.P.A.R.K.S Tray Inspection Dashboard")

if not os.path.exists(CSV_FILE):
    st.error("inspection_results.csv not found.")
    st.stop()

df = pd.read_csv(CSV_FILE)

if df.empty:
    st.warning("No inspection data yet.")
    st.stop()

# Tray summary
tray_summary = df.groupby("tray_id").agg(
    total_dies=("die_id", "count"),
    good_count=("prediction", lambda x: (x == "GOOD").sum()),
    defect_count=("prediction", lambda x: (x == "DEFECT").sum()),
    average_score=("die_score", "mean")
).reset_index()

def risk_level(score):
    if score >= 80:
        return "LOW RISK"
    elif score >= 60:
        return "MEDIUM RISK"
    else:
        return "HIGH RISK"

tray_summary["risk_level"] = tray_summary["average_score"].apply(risk_level)

st.subheader("Tray Overview")

cols = st.columns(3)

for i, row in tray_summary.iterrows():
    with cols[i % 3]:
        st.metric(
            label=f"Tray {row['tray_id']}",
            value=f"{row['average_score']:.1f}%",
            delta=row["risk_level"]
        )
        st.write(f"Total Dies: {row['total_dies']}")
        st.write(f"Good: {row['good_count']} | Defect: {row['defect_count']}")

st.divider()

selected_tray = st.selectbox(
    "Select tray to view details",
    tray_summary["tray_id"].tolist()
)

tray_df = df[df["tray_id"] == selected_tray]

st.subheader(f"Details for Tray {selected_tray}")

col1, col2, col3, col4 = st.columns(4)

avg_score = tray_df["die_score"].mean()
good_count = (tray_df["prediction"] == "GOOD").sum()
defect_count = (tray_df["prediction"] == "DEFECT").sum()

col1.metric("Average Score", f"{avg_score:.1f}%")
col2.metric("Good Dies", good_count)
col3.metric("Defect Dies", defect_count)
col4.metric("Risk Level", risk_level(avg_score))

st.dataframe(tray_df, use_container_width=True)

st.subheader("Die Images")

for _, row in tray_df.iterrows():
    image_path = os.path.join("captures", row["image_name"])

    with st.expander(f"{row['die_id']} - {row['prediction']} - Score {row['die_score']}"):
        st.write(f"Confidence: {row['confidence']}")
        st.write(f"Timestamp: {row['timestamp']}")

        if os.path.exists(image_path):
            st.image(image_path, caption=row["image_name"], width=400)
        else:
            st.warning(f"Image not found: {image_path}")