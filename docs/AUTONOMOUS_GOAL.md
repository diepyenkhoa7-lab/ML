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

Giới hạn giám sát vòng gốc: `career_ai/models.py` chỉ in loss mỗi10 dòng và ghi partial/progress mỗi100 dòng trong phần hồi quy. Sau dòng cuối (log step10410 cho train10.417 dòng), trainer còn replay tối đa324 mẫu JSONL train, bỏ mẫu vượt context, rồi tính validation2.405 hồ sơ và tối đa32 mẫu language validation. Các phần này không có log từng bước hoặc partial mới. Vì vậy log/progress đứng ở cuối phần hồi quy chưa chứng minh tiến trình đã treo; kiểm PID/command, CPU/bộ nhớ, lỗi và artifact thực tế. CPU hoạt động chỉ chứng minh tiến trình còn tính toán, không tự chứng minh đã hoàn tất phase hoặc chất lượng model. `llm_history.json` chỉ xuất sau validation của epoch; `lineage completed` cùng `llm.json` mới cho phép handoff. Không tự restart vì khoảng im log này, không sửa nóng trainer để thêm print. Các experiment mới đã có progress theo phase và checkpoint optimizer riêng.

## Thí nghiệm và lựa chọn

Giữ nguyên raw/nhãn/split/đơn vị/seed42. Tối đa3 cấu hình bổ sung: rank8/lr2e-5; rank8/lr1e-4; rank16 với learning rate có validation tốt nhất trong vòng gốc và các vòng trước. Mỗi cấu hình có smoke20 mẫu, kiểm resume optimizer + lưu/nạp trong tiến trình mới trước khi train full tối đa2epoch, context1024, microbatch1, tích lũy8. Smoke không là metric chất lượng chung và không làm tăng quota cấu hình.

Các vòng mới có checkpoint atomic LoRA/head/optimizer slot/iteration/con trỏ epoch-phase-index, giữ hai bản hoàn chỉnh; không chép backbone6,88GB vào mỗi checkpoint. Resume phải khớp config, code, dataset và phiên bản thư viện. Checkpoint cũ chỉ adapter/head, không được gọi là resume đầy đủ. Các vòng mới tích lũy8 cả nhánh ngôn ngữ; vòng legacy giữ nguyên hành vi đã chạy, không diễn giải so sánh như ablation chỉ riêng learning rate.

Chọn điểm nhỏ nhất: market-mean logMAE +0,1×validation answer CE. Đồng thời báo MAE/RMSE/R² theo thị trường/vai trò/kinh nghiệm, JSON schema/field accuracy/Skill F1 trên32 mẫu validation đầu cố định; lỗi quá context tính là lỗi trong đánh giá generation, không âm thầm bỏ. CE dùng tối đa32 mẫu cùng chính sách legacy. Nhãn silver chưa là human gold.

Nếu2 cấu hình liên tiếp không giảm ít nhất1% so với best trước đó thì dừng thử tiếp. Vẫn giữ điểm tốt nhất thực tế khi cải thiện dưới1%, nhưng không reset patience. Chỉ authorize test sau khi chốt selected_run, không chọn/tune theo test. Baseline test đã mở trước, phải nêu rõ điều này; không gọi nguồn/split này là benchmark mới độc lập.

## Lỗi và kiểm chứng

Mỗi bước tối đa2 retry. Job còn PID đúng hoặc model con còn sống thì không tạo job khác. Retry train dùng checkpoint khi có; khởi tạo hỏng chưa có checkpoint được lưu nguyên vào failed-init trước khi thử lại. Khi hết retry hoặc gặp trạng thái không thể tiếp tục an toàn: needs_attention, lưu log và báo người dùng. Không tự đổi nguồn dữ liệu hay mượn GPU.

Đã kiểm29 hợp đồng phần mềm, bao gồm serializer optimizer thật nhưng không thực hiện cập nhật model trong bài test đó. Fixture trọng số chỉ kiểm serialization; không là bằng chứng AI. Cấu hình Qwen mới vẫn phải qua smoke thực tế và check_saved_run trước full.

Sau handoff, Qwen vòng gốc phải nạp lại trong tiến trình mới và khớp reload probe trước validation/chọn ứng viên. Suy luận dùng pretrained backbone cùng `qwen.lora.h5` đã học và `salary_head.keras` đã học, không chỉ dùng backbone gốc. Demo cuối có thêm hai mô tả tuyển dụng tổng hợp từ đặc trưng train, không chứa lương, để kiểm trích xuất rồi dự đoán cho hai thị trường. Lưu kết quả ở `outputs/auto_dev/demo/text_predictions.json`; đây là kiểm chứng luồng, không phải metric chất lượng. Báo cáo bàn giao yêu cầu demo văn bản đạt.

Smoke mới chủ động dừng sau2 cập nhật optimizer ở epoch0, numeric next_index16; bước sau phải nạp checkpoint và tiếp tục từ đúng vị trí này. Kiểm tra resume không chấp nhận chỉ nạp lại experiment đã xong epoch. `resume_events.json` lưu iteration/cursor thực tế; `smoke_acceptance.json` chỉ được tạo sau kiểm tra LoRA thay đổi, train hoàn tất và dự đoán khớp ở tiến trình mới. Các kiểm tra phần mềm hiện tại chỉ xác minh cơ chế; chưa tuyên bố smoke Qwen mới đã chạy.

Đã sửa cửa sổ lỗi sau checkpoint cuối epoch: khi cursor đã hoàn tất mọi epoch nhưng process chết trước lúc ghi history, resume phải tái xuất `llm_history.json` từ cursor trước khi công bố completed. Test hồi quy tái hiện lỗi trên trainer cũ rồi đạt sau sửa, dùng Qwen giả và không chạy gradient update; đây chỉ là hợp đồng vòng đời phần mềm. Với checkpoint ở optimizer step0, module mới vẫn chụp trọng số trước cập nhật để kiểm LoRA thay đổi; điều này chưa được gọi là bằng chứng cold-resume pretrained thực tế. Cả hai thay đổi chỉ ở `career_auto/training.py`, không sửa vòng gốc `career_ai` đang chạy.

Sau khi chọn: test ứng viên cuối, so sánh baseline, demo ba định dạng và lỗi từng dòng/quá dài, tư vấn từ evidence, chạy5 notebook kernel sạch, tests và tạo báo cáo. Notebook cuối chỉ đọc artifact của ứng viên đã chọn, không chọn run theo tên thư mục hoặc tự train lại. Báo cáo ghi MAE/RMSE/R², độ khớp riêng từng trường và mẫu hỗ trợ, các dòng/nhóm lỗi lớn; chỉ sinh sau khi demo và notebook thực thi thành công. Coordinator kết thúc ở ready_for_handoff; agent còn phải đọc kết quả, kiểm notebook/demo thật, cập nhật tài liệu, commit/push source gọn và đối chiếu remote. Chỉ sau toàn bộ bằng chứng đạt mới complete goal; nếu LLM thua baseline thì giữ nguyên kết quả và giải thích. Không được complete khi bước bắt buộc còn chạy.

Ứng viên cuối luôn qua `final_reload` trước `final_test`, kể cả khi được chọn từ vòng gốc. Báo cáo bàn giao ghi SHA256/kích thước adapter, đầu hồi quy, metadata/lineage, bằng chứng lưu/nạp, metric, manifest nguồn và môi trường cùng5 notebook đã chạy. Đây là manifest kiểm toàn vẹn artifact, không thay thế giấy phép/nguồn dữ liệu đã ghi riêng.

`career_auto.charts` được kiểm riêng bằng2 hợp đồng: không gộp các quan sát khác nhau chỉ vì cùng đặc trưng và cài chuyển tiếp CLI có giữ bản cũ. Đã xuất10 PNG và4 bảng từ toàn bộ tập train thật ở `outputs/chart_review_train/`; đây là EDA thu nhập quan sát, không là đánh giá dự đoán. CLI sẽ chuyển sang bản mới sau khi vòng gốc kết thúc; không đổi `career_ai` trong lúc train. Với file suy luận, biểu đồ ghi rõ thu nhập dự đoán và kỹ năng trong hồ sơ đầu vào; không gọi đó là nhu cầu tuyển dụng thực đo. Nhóm kỹ năng dưới10 mẫu không xếp hạng thu nhập.

Khi cần sửa lỗi, ghi giả thuyết, sửa và kiểm thử đúng phạm vi; không tự vượt ngân sách thí nghiệm/retry. Khi bàn giao xong, dừng heartbeat phát triển để không tiếp tục train ngoài goal.
