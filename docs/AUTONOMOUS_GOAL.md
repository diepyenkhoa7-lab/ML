# Goal tự động TensorFlow — hợp đồng thực thi

Đã kích hoạt goal trong chat và heartbeat `t-ng-ho-n-thi-n-ml-tensorflow` mỗi30 phút. Đây là goal phát triển model + demo CLI/notebook, chưa làm web. Chỉ máy local, không cloud/chi phí, một train tại một thời điểm.

## Trạng thái và tiếp quản

Nguồn chính sách: `configs/auto_goal.json`. Registry đang chạy: `outputs/auto_dev/state.json`. Mỗi lần heartbeat đọc cả hai, kiểm tra PID thật bằng command, log/checkpoint và dung lượng, sau đó chạy:

```
.venv-tf/bin/python -m career_auto.coordinator
```

Lệnh này chỉ đưa ra một bước điều phối, có khóa chống gọi trùng; job dài được tách phiên và ghi exit record. Khi job xong có thể gọi lại để đi tiếp, không cần chờ đủ30 phút. Chỉ thông báo mốc quan trọng/lỗi/cần xử lý; im lặng lúc chờ bình thường.

Vòng gốc `outputs/qwen_20261023T082631` vẫn train nguyên code/dữ liệu. Controller legacy PID18836 đã SIGSTOP có chủ đích, **model PID19191 không dừng**, để ngăn tự mở test. Không SIGCONT controller tùy tiện. Sau khi model hoàn tất và lineage completed, coordinator kết thúc controller này và tiếp quản. Tiến trình cha legacy có thể báo failed vì handoff có chủ đích; phân biệt với lỗi model.

Không sửa `career_ai/*.py` hoặc dữ liệu trong lúc vòng gốc đang train. Module mới ở `career_auto` được chuẩn bị riêng. Khi vòng gốc kết thúc mới cài mặc định CLI `evaluate --split valid`; hiện dùng module `career_auto.evaluation` đã có mặc định validation. Không sửa training/checkpoint source khi experiment mới đang chạy; kiểm checksum identity trước resume.

## Thí nghiệm và lựa chọn

Giữ nguyên raw/nhãn/split/đơn vị/seed42. Tối đa3 cấu hình bổ sung: rank8/lr2e-5; rank8/lr1e-4; rank16 với learning rate có validation tốt nhất trong vòng gốc và các vòng trước. Mỗi cấu hình có smoke20 mẫu, kiểm resume optimizer + lưu/nạp trong tiến trình mới trước khi train full tối đa2epoch, context1024, microbatch1, tích lũy8. Smoke không là metric chất lượng chung và không làm tăng quota cấu hình.

Các vòng mới có checkpoint atomic LoRA/head/optimizer slot/iteration/con trỏ epoch-phase-index, giữ hai bản hoàn chỉnh; không chép backbone6,88GB vào mỗi checkpoint. Resume phải khớp config, code, dataset và phiên bản thư viện. Checkpoint cũ chỉ adapter/head, không được gọi là resume đầy đủ. Các vòng mới tích lũy8 cả nhánh ngôn ngữ; vòng legacy giữ nguyên hành vi đã chạy, không diễn giải so sánh như ablation chỉ riêng learning rate.

Chọn điểm nhỏ nhất: market-mean logMAE +0,1×validation answer CE. Đồng thời báo MAE/RMSE/R² theo thị trường/vai trò/kinh nghiệm, JSON schema/field accuracy/Skill F1 trên32 mẫu validation đầu cố định; lỗi quá context tính là lỗi trong đánh giá generation, không âm thầm bỏ. CE dùng tối đa32 mẫu cùng chính sách legacy. Nhãn silver chưa là human gold.

Nếu2 cấu hình liên tiếp không giảm ít nhất1% so với best trước đó thì dừng thử tiếp. Vẫn giữ điểm tốt nhất thực tế khi cải thiện dưới1%, nhưng không reset patience. Chỉ authorize test sau khi chốt selected_run, không chọn/tune theo test. Baseline test đã mở trước, phải nêu rõ điều này; không gọi nguồn/split này là benchmark mới độc lập.

## Lỗi và kiểm chứng

Mỗi bước tối đa2 retry. Job còn PID đúng hoặc model con còn sống thì không tạo job khác. Retry train dùng checkpoint khi có; khởi tạo hỏng chưa có checkpoint được lưu nguyên vào failed-init trước khi thử lại. Khi hết retry hoặc gặp trạng thái không thể tiếp tục an toàn: needs_attention, lưu log và báo người dùng. Không tự đổi nguồn dữ liệu hay mượn GPU.

Đã kiểm16 hợp đồng phần mềm, bao gồm serializer optimizer thật nhưng không thực hiện cập nhật model trong bài test đó. Fixture trọng số chỉ kiểm serialization; không là bằng chứng AI. Cấu hình Qwen mới vẫn phải qua smoke thực tế và check_saved_run trước full.

Sau khi chọn: test ứng viên cuối, so sánh baseline, demo ba định dạng và lỗi từng dòng/quá dài, tư vấn từ evidence, chạy5 notebook kernel sạch, tests. Coordinator kết thúc ở ready_for_handoff; agent còn phải đọc kết quả, phân tích nhóm sai số lớn, kiểm notebook/demo thật, cập nhật tài liệu, commit/push source gọn và đối chiếu remote. Chỉ sau toàn bộ bằng chứng đạt mới complete goal; nếu LLM thua baseline thì giữ nguyên kết quả và giải thích. Không được complete khi bước bắt buộc còn chạy.

Khi cần sửa lỗi, ghi giả thuyết, sửa và kiểm thử đúng phạm vi; không tự vượt ngân sách thí nghiệm/retry. Khi bàn giao xong, dừng heartbeat phát triển để không tiếp tục train ngoài goal.
