# Kiểm tra bàn giao — model đã chốt

Quyết định mới nhất của người dùng: dùng `outputs/qwen_20261023T082631`, không train thêm. Model này đã học2epoch, chọn epoch1 bằng validation. Trial bổ sung đã hủy, không được tính là một model hoàn tất.

| Yêu cầu | Bằng chứng đã kiểm tra |
|---|---|
| TensorFlow/Keras, backbone và môi trường cố định | requirements-lock-tf-macos-arm64.txt, configs/qwen_source.json; CPU thật |
| Dữ liệu có nguồn, audit, checksum; tách đơn vị và nhóm | data/tensorflow_v1/manifest.json, README.md, train/valid/test CSV và JSONL, international_audit.csv, vn_audit.csv; tests chống leakage/group/unit đạt |
| LLM đã học và lưu/nạp được | llm.json, lineage completed, qwen.lora.h5, salary_head.keras, fresh_process_reload.json:2 probe khớp ở tiến trình mới |
| Checkpoint có optimizer/cursor | smoke auto_lr_low_smoke có cập nhật LoRA thật, khôi phục iteration2/cursor16, nạp lại đạt; không dùng điểm smoke chấm chất lượng |
| Hai mô hình, MAE/RMSE/R² theo thị trường/nhóm | LLM và TensorFlow linear baseline; metric validation/test, comparison.csv; test không dùng để tune |
| Chất lượng ngôn ngữ | language_valid.json:32 mẫu; language_test.json:85 mẫu; JSON schema, accuracy từng trường, Skill F1; nhãn silver |
| CSV/JSON/XLSX → dự đoán → bảng/biểu đồ | outputs/auto_dev/demo: mỗi định dạng6 dòng,4 hợp lệ/2 lỗi, dự đoán khớp; đơn vị và model_version đầy đủ |
| Văn bản → LLM trích xuất → dự đoán | demo/text_predictions.json:2 thị trường; mô tả tổng hợp từ train không có lương, không coi là benchmark |
| Tư vấn tối đa3 kỹ năng có bằng chứng | advice.json: LLM chọn kỹ năng và giải thích tiếng Việt; support>=10; Việt Nam thiếu nhóm phù hợp báo insufficient_data |
| Biểu đồ Matplotlib/Seaborn | outputs/eda và model/figures: kỹ năng, thu nhập theo kỹ năng, kinh nghiệm, vai trò, khu vực; phân biệt thu nhập quan sát/dự đoán và khảo sát/nhu cầu tuyển dụng |
| Đầu vào rỗng/thiếu trường/quá dài | edge_cases/acceptance.json: CSV/JSON/XLSX rỗng trả0 dòng, hồ sơ thiếu trường trả lỗi từng dòng; demo từ chối mô tả quá dài |
| Năm notebook kernel sạch | notebooks/01…05, toàn bộ code có execution_count, không output lỗi; training mặc định tắt |
| Kiểm thử phần mềm |32 unittest đạt; Ruff và git diff --check đạt; fixture không là metric AI |
| Phân tích sai số và giới hạn | AUTONOMOUS_RESULTS.md; largest_errors.csv có20 dòng; nhóm vai trò/kinh nghiệm, dữ liệu Việt Nam ít, baseline test đã mở trước |
| Manifest artifact | outputs/auto_dev/handoff.json:20 artifact đã đối chiếu SHA256/kích thước; gói bàn giao riêng có manifest cho trọng số/log/biểu đồ |

Đã xem trực tiếp biểu đồ thu nhập theo kỹ năng quốc tế và kinh nghiệm–thu nhập dự đoán Việt Nam. Các đầu ra demo ít mẫu ghi đúng số mẫu; không dùng chúng suy diễn thị trường. Model quốc tế chỉ nhỉnh hơn baseline, model Việt Nam kém hơn baseline; giữ nguyên kết quả.

Chạy demo từ thư mục dự án sau khi cài môi trường và nạp đúng base/adapter:

```sh
.venv-tf/bin/python -m career_ai analyze --run outputs/qwen_20261023T082631 --input data/profiles_demo.json
.venv-tf/bin/python -m career_ai advise --run outputs/qwen_20261023T082631 --input data/profiles_demo.json
```

Thay file đầu vào bằng CSV/XLSX/JSON cùng schema. `analyze` ghi predictions.csv/json và figures; `advise` ghi advice.json. Không chạy lại prepare/train để dùng demo.

Gói bàn giao: outputs/delivery/qwen_salary_demo_20261025.zip;97 file, có trọng số đã học và manifest SHA256. Nạp model từ chính gói đã kiểm ở tiến trình mới. Backbone tải riêng theo manifest. Source dùng để tạo gói tại commit e8b6c18; các commit sau chỉ ghi nhận bàn giao.
