"""Trace source rows through normalization, deduplication and EDA eligibility."""

import io
import os
import zipfile
from pathlib import Path

import streamlit as st

from career_market import MarketError, MarketService

st.set_page_config(page_title="Chất lượng dữ liệu", layout="wide")
st.title("Chất lượng dữ liệu và snapshot")
raw_dir = os.environ.get("CAREER_MARKET_RAW_DIR")
service = MarketService(raw_dir=Path(raw_dir) if raw_dir else None)
try:
    snapshot = service.snapshot()
except MarketError as error:
    st.error(str(error))
    st.stop()
report = snapshot["report"]
summary = report["summary"]
columns = st.columns(4)
for column, (label, key) in zip(
    columns,
    [
        ("Dòng thô", "raw_rows"),
        ("Tin EDA", "eda_postings"),
        ("Dòng trùng", "duplicates"),
        ("Nhãn lương", "salary_targets"),
    ],
):
    column.metric(label, summary[key])
st.info(
    "ML bị chặn: gate nhãn lương chưa được giải quyết. Snapshot nhãn rỗng vẫn giữ schema; không huấn luyện khi mở trang."
)
st.caption(
    "Raw = trùng + ID lỗi + ngoài nghề + nghề cần review + EDA. Review theo trường có thể chồng lắp EDA; không cộng review vào tổng raw. Nhóm giống nội dung dùng để rà soát, không tự coi URL khác là một tin."
)
st.json(summary)
partition = st.selectbox("Tập đối chiếu", ["rows", "eda", "review", "duplicates", "targets"])
selected = report[partition]
visible = [
    {
        key: row[key]
        for key in [
            "row_id",
            "posting_id",
            "title_raw",
            "role",
            "partition",
            "locations",
            "work_modes",
            "salary_reason",
            "review_reasons",
        ]
    }
    for row in selected
]
st.dataframe(visible, hide_index=True)
if not selected:
    st.info("Tập này hiện không có bản ghi; file CSV xuất vẫn có đầy đủ tên cột.")
st.subheader("Nguồn và phiên bản snapshot")
st.json(snapshot["manifest"])
archive = io.BytesIO()
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zipped:
    for name, content in snapshot["files"].items():
        zipped.writestr(name, content)
st.download_button(
    "Tải snapshot CSV và manifest", archive.getvalue(), "eda-snapshot.zip", "application/zip"
)
