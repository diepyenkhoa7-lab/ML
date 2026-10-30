"""Make final notebooks show the selected model's real artifacts, then execute them."""

import subprocess
import sys

from .state import FOLDER, ROOT, read


def prepare():
    import nbformat

    state = read(FOLDER / "state.json")
    if not state.get("selected_run") or state.get("final_step", 0) < 4:
        raise ValueError("Selected model, test and demo must exist before final notebooks")
    setup = """from pathlib import Path
import json
import pandas as pd
state=json.loads((ROOT/'outputs/auto_dev/state.json').read_text())
selected=ROOT/state['selected_run']
"""
    cells = {
        "02_baseline.ipynb": setup
        + """policy=json.loads((ROOT/'configs/auto_goal.json').read_text())
baseline=ROOT/policy['baseline_run']
print('Baseline TensorFlow đã train; không tự huấn luyện lại khi chạy notebook.')
display(json.loads((baseline/'baseline_valid_metrics.json').read_text()))
display(json.loads((baseline/'baseline_test_metrics.json').read_text()))
""",
        "03_qwen_finetune.ipynb": setup
        + """metadata=json.loads((selected/'llm.json').read_text())
display(metadata)
display(pd.DataFrame(json.loads((selected/'llm_history.json').read_text())))
RUN_TRAINING=False
if RUN_TRAINING:
    if state['status'] != 'completed':
        raise RuntimeError('Goal vẫn hoạt động; không mở thêm thí nghiệm ngoài quota.')
    from datetime import datetime, timezone
    from career_auto.coordinator import training_processes
    from career_auto.training import train
    if training_processes():
        raise RuntimeError('Đang có tiến trình train khác.')
    config=dict(rank=metadata['rank'],learning_rate=metadata.get('learning_rate',5e-5),epochs=1)
    run=ROOT/'outputs'/('manual_notebook_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
    train(config,run)
""",
        "05_demo.ipynb": setup
        + """from IPython.display import Image, display
print('Kết quả demo thực tế; hồ sơ từ train, không là metric generalization.')
display(pd.DataFrame(json.loads((selected/'predictions.json').read_text())))
display(pd.DataFrame(json.loads((selected/'advice.json').read_text())))
for path in sorted((selected/'figures').glob('*.png')):
    display(Image(filename=str(path)))
print('Suy luận file mới, không train:')
print(f'python -m career_ai analyze --run {selected} --input FILE.csv')
""",
        "04_evaluation.ipynb": setup
        + """print('Chỉ hiển thị ứng viên cuối đã chọn bằng validation.')
names=['llm_valid_metrics.json','llm_test_metrics.json',
       'language_valid.json','language_test.json']
for name in names:
    print(name)
    values=json.loads((selected/name).read_text())
    display({k:v for k,v in values.items() if k != 'errors'})
display(pd.read_csv(ROOT/'outputs/auto_dev/comparison/comparison.csv'))
print('Nhãn ngôn ngữ silver, chưa là human gold. Baseline test từng được mở trước.')
""",
    }
    for name, code in cells.items():
        path = ROOT / "notebooks" / name
        book = nbformat.read(path, as_version=4)
        book.cells = book.cells[:2] + [nbformat.v4.new_code_cell(code)]
        book.metadata["selected_run"] = state["selected_run"]
        nbformat.write(book, path)


if __name__ == "__main__":
    prepare()
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/execute_notebooks.py")], cwd=ROOT, check=True
    )
