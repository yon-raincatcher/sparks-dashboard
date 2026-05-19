from collections import Counter

import pandas as pd
import streamlit as st

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSAHlcV81kCPWHfzpBRJNvpwkmvT5yNQ53fIwtFkv0tx99ki7odtlDLDzZXhiWd2nuPPmboVuV-7s8I/pub?output=csv"

REQUIRED_COLUMNS = [
    "tray_id",
    "die_id",
    "image_name",
    "prediction",
    "defect_type",
    "defect_count",
    "confidence",
    "die_score",
    "timestamp"
]

st.set_page_config(page_title="SPARKS Dashboard", layout="wide")

st.title("S.P.A.R.K.S Intelligent Inspection Dashboard")
# Read Google Sheets CSV
df = pd.read_csv(SHEET_CSV_URL)

if df.empty:
    st.warning("No inspection data yet.")
    st.stop()

missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]

if missing_columns:
    st.error(f"CSV format error. Missing columns: {missing_columns}")
    st.stop()

df["die_score"] = pd.to_numeric(df["die_score"], errors="coerce").fillna(0)
df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0)
df["defect_count"] = pd.to_numeric(df["defect_count"], errors="coerce").fillna(0)

def risk_level(score):
    if score >= 80:
        return "LOW RISK"
    elif score >= 60:
        return "MEDIUM RISK"
    else:
        return "HIGH RISK"

# Tray overview
tray_summary = df.groupby("tray_id").agg(
    total_dies=("die_id", "count"),
    good_count=("prediction", lambda x: (x == "GOOD").sum()),
    defect_count=("prediction", lambda x: (x == "DEFECT").sum()),
    average_score=("die_score", "mean")
).reset_index()

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
total_dies = len(tray_df)

col1.metric("Average Score", f"{avg_score:.1f}%")
col2.metric("Total Dies", total_dies)
col3.metric("Good Dies", good_count)
col4.metric("Defect Dies", defect_count)

st.metric("Risk Level", risk_level(avg_score))

st.subheader("Defect Breakdown")

all_defects = []

for defect_item in tray_df["defect_type"]:
    if pd.notna(defect_item) and str(defect_item).lower() != "none":
        all_defects.extend(str(defect_item).split(";"))

if all_defects:
    defect_counter = Counter(all_defects)
    defect_df = pd.DataFrame({
        "defect_type": list(defect_counter.keys()),
        "count": list(defect_counter.values())
    })
    st.bar_chart(defect_df.set_index("defect_type"))
else:
    st.info("No defects detected for this tray.")

st.subheader("Die Data")

st.dataframe(
    tray_df[REQUIRED_COLUMNS],
    width="stretch"
)

st.info("Note: Online dashboard displays inspection data from Google Sheets. YOLO images are stored locally unless uploaded to cloud storage.")
