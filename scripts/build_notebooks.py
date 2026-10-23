from pathlib import Path

import nbformat as n

root = Path(__file__).resolve().parents[1]
sections = [
    (
        "01_data_eda",
        "Dữ liệu và EDA",
        (
            "from career_ai.data import load\n"
            "from career_ai.charts import charts\n"
            "train=load('train')\n"
            "display(train.groupby('market').salary.agg(['count','median']))\n"
            "charts(train, ROOT/'outputs/eda')"
        ),
    ),
    (
        "02_baseline",
        "Hồi quy tuyến tính TensorFlow",
        (
            "from career_ai.models import baseline_train\n"
            "RUN_TRAINING=False\n"
            "if RUN_TRAINING:\n"
            "    run=ROOT/'outputs/baseline_notebook'\n"
            "    run.mkdir(exist_ok=False)\n"
            "    baseline_train(run)\n"
            "else:\n"
            "    print('Training thật: python -m career_ai train-baseline. Bật"
            " RUN_TRAINING để train từ notebook.')"
        ),
    ),
    (
        "03_qwen_finetune",
        "Qwen3 LoRA và đầu hồi quy",
        (
            "RUN_TRAINING=False\n"
            "if RUN_TRAINING:\n"
            "    from career_ai.models import llm_train\n"
            "    run=ROOT/'outputs/qwen_notebook'\n"
            "    run.mkdir(exist_ok=False)\n"
            "    llm_train(run, epochs=2)\n"
            "else:\n"
            "    print('Lệnh train thật: python -m career_ai train-llm --epoch"
            "s 2')"
        ),
    ),
    (
        "04_evaluation",
        "Đánh giá tách đơn vị",
        (
            "import json\n"
            "paths=list((ROOT/'outputs').glob('*/*metrics.json'))\n"
            "for path in paths:\n"
            "    print(path.relative_to(ROOT))\n"
            "    display(json.loads(path.read_text()))\n"
            "if not paths: print('Chưa có metric training; không dùng số liệu "
            "giả lập.')"
        ),
    ),
    (
        "05_demo",
        "Demo CSV và tư vấn",
        (
            "from career_ai.data import load\n"
            "profiles=load('train').groupby('market').head(2).drop(columns=['s"
            "alary','group'])\n"
            "profiles.to_json(ROOT/'data/profiles_demo.json',orient='records',"
            "force_ascii=False,indent=2)\n"
            "display(profiles)\n"
            "print('python -m career_ai analyze --run outputs/RUN --input data"
            "/profiles_demo.json --model llm')"
        ),
    ),
]
for name, title, code in sections:
    book = n.v4.new_notebook(
        cells=[
            n.v4.new_markdown_cell(
                "# " + title + "\nTrain và suy luận là hai thao tác riêng. "
                "Dữ liệu mẫu lấy từ train, không phải holdout mới."
            ),
            n.v4.new_code_cell(
                "from pathlib import Path\n"
                "import sys\n"
                "ROOT=Path.cwd() if (Path.cwd()/'career_ai').exists() else Path.cw"
                "d().parent\n"
                "sys.path.insert(0,str(ROOT))"
            ),
            n.v4.new_code_cell(code),
        ],
        metadata={
            "kernelspec": {
                "display_name": "Python TensorFlow",
                "language": "python",
                "name": "career-ai-tf",
            }
        },
    )
    n.write(book, root / "notebooks" / f"{name}.ipynb")
