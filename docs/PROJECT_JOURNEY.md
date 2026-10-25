# Nhật ký làm lại dự án TensorFlow

## 2026-10-23 — Đã thực hiện

Người dùng tự dọn source cũ và yêu cầu tiếp tục triển khai kiến trúc đã chốt. Giữ thư mục dữ liệu gốc và môi trường; không phục hồi giao diện hoặc Gemma. Bản thay đổi trước khi dọn đã lưu ở `/private/tmp/ml-before-tf-20261023/`; lịch sử Git cũ vẫn tồn tại.

Đã viết pipeline Python `career_ai`: chuẩn hóa, chia nhóm, đầu hồi quy trong Qwen3, baseline tuyến tính TensorFlow, loss có trọng số thị trường, trích xuất JSON, thống kê tư vấn và xuất biểu đồ. Một backbone Qwen dùng chung cho hai loại target; trường thị trường xác định đơn vị và thang log. Baseline là mô hình đối chứng, không thay thế LLM trong kiến trúc.

Rà soát nhãn từ raw thay vì kế thừa nhãn kỳ tháng suy đoán. Gom cùng công ty và nội dung tin đăng trùng thành nhóm trước khi tạo biến thể JSONL. Đóng băng bảng và nhãn bằng checksum. Tập chốt: train10.417 (155 VN), validation2.405 (37 VN), test3.206 (49 VN). Nhãn Việt Nam ít; nhãn trích xuất vẫn là silver. Chưa có cơ sở nói sai số được cải thiện.

Đã có 7 kiểm thử hợp đồng dữ liệu đạt: không trùng nhóm, không rò salary vào prompt, đúng đơn vị, JSONL theo split và metric hỗ trợ nhóm nhỏ. Kiểm tra tĩnh source đạt. Bằng chứng: `tests/test_contracts.py`, `data/tensorflow_v1/manifest.json`, `outputs/prepare.log`. Năm notebook được chuẩn bị; trạng thái thực thi từng notebook thể hiện ngay trong file.

## Đang thực hiện

Cài TensorFlow2.20/TensorFlow Text2.20.1/KerasHub0.32 trong `.venv-tf`; tải preset Qwen phiên bản cố định. Trọng số chính thức nặng6.883.417.048 byte. Mạng chậm là trở ngại thực tế; có công cụ tải chia phần và kiểm SHA256, không coi metadata đã tải là đủ trọng số.

Chưa xác nhận nạp pretrained, cập nhật LoRA trên pretrained hoặc độ chính xác mới. Công cụ kiểm tra Qwen nhỏ khởi tạo ngẫu nhiên chỉ xác minh API, không là kết quả đề tài. Metric phải lấy từ experiment thật; không dùng thành công của sửa kiến trúc làm bằng chứng tăng độ chính xác.

## Các bước sẽ chạy sau khi đủ điều kiện

Kiểm tra import/thiết bị và LoRA nhỏ → train/evaluate baseline → kiểm tra pretrained Qwen, smoke LoRA trên cả hai thị trường, save/reload → train đầy đủ tối đa2epoch → đánh giá test riêng đơn vị và phần trích xuất → demo tệp và biểu đồ. Mỗi bước có log riêng và dừng khi thất bại; không bỏ qua lỗi để công bố hoàn tất.

## 2026-10-23 — Mốc lưu source và khởi chạy điều phối

Đã push source gọn lên `origin/dev/tensorflow-rebuild`, commit triển khai `d5db9e9`. Lịch sử local trước rebuild giữ ở `dev/tensorflow-rebuild-history-20261023`; bản khôi phục thay đổi chưa commit cũng được chép sang `data/archive/pre_tensorflow_20261023/` để không phụ thuộc riêng thư mục tạm.

Đã khởi chạy bộ cài môi trường, tải trọng số theo phiên bản và bộ điều phối training thật. Trạng thái tại thời điểm ghi là **waiting_for_environment**, chưa bắt đầu cập nhật trọng số. `outputs/latest_pipeline.json` là bằng chứng hiện hành, `.cache/tf_environment_status.json` là trạng thái bộ cài. Không coi khởi chạy bộ điều phối là đã train thành công. Output notebook cũ từ lần chuẩn bị dữ liệu trước được xóa để tránh nhầm với kết quả snapshot chốt; sẽ chạy lại bằng kernel TensorFlow sạch.

## 2026-10-23 — Kiểm thử thực tế và bắt đầu fine-tune đầy đủ

Phát hiện tiến trình trước không còn sống dù status còn ghi running. Không xác định được nguyên nhân kết thúc từ log, vì vậy đánh dấu interrupted; không tiếp tục gọi đó là đang training. Thử launchd bị kẹt khi mở môi trường Python, đã dỡ tác vụ này. Sau đó chuyển sang worker tách phiên, kiểm tra PID/tiến trình thực tế và lưu trạng thái worker riêng. Không tạo tác vụ tự khởi động khi đăng nhập.

Tái sử dụng14 wheel đã tải hoàn chỉnh sau kiểm CRC, tải tiếp các phần trọng số. Đã tải đủ6.883.417.048 byte, SHA256 khớp manifest. TensorFlow2.20/Keras3.15.1/KerasHub0.32 đã import và cập nhật LoRA trên Qwen nhỏ thành công. Metal1.2.0 lỗi nạp thư viện `_pywrap_tensorflow_internal.so`; đã gỡ plugin, kiểm tra lại CPU và khóa môi trường. Không gọi CPU là GPU/Metal.

Baseline đầu train được nhưng dự đoán ngoài miền số cho phép. Chẩn đoán trên validation cho thấy chuẩn hóa one-hot hiếm khuếch đại các đặc trưng phân loại. Sửa chỉ chuẩn hóa kinh nghiệm, giữ one-hot0/1; thêm kiểm thử hồi quy lỗi và train experiment mới. Test evaluation trước đã được gọi nhưng dừng do miền dự đoán, chưa sinh metric; không chọn hyperparameter theo test.

Baseline mới `outputs/baseline_20261023T082631`: quốc tế MAE30.577,77USD/năm, RMSE58.495,02USD/năm, R²0,4219 (3.157 mẫu); Việt Nam MAE5.497.220,55VND/tháng, RMSE7.287.465,53VND/tháng, R²0,4258 (49 mẫu). Đây là mức đối chứng thực tế, chưa phải kết quả LLM. Lưu/nạp ở tiến trình mới cho hai thị trường khớp. CLI thực tế đọc CSV/XLSX/JSON:4 dòng hợp lệ,1 dòng lỗi riêng; xuất dự đoán và biểu đồ thành công.

Phát hiện lỗi hậu xử lý sinh văn bản: cắt số ký tự của prompt làm mất phần đầu JSON do cách tokenizer xử lý token đặc biệt. Đổi sang `strip_prompt=True` của Keras và thêm test. Kiểm tra lại pretrained bằng câu tiếng Việt trả đúng JSON với Backend Developer,3 năm,Python/SQL. Một mẫu này chỉ là kiểm tương thích, không là điểm chất lượng chung.

Smoke Qwen LoRA20 mẫu hoàn tất, có2 language update và32 mẫu validation language; lưu adapter/head và so sánh dự đoán trong tiến trình mới đạt. Không dùng smoke để chấm test full. Vòng đầy đủ trên10.417 dòng train, tối đa2epoch đã bắt đầu trên CPU lúc15:31. Các log loss hiện hữu; chưa có metric LLM full, chưa thể kết luận vượt baseline.

Đã chạy5 notebook bằng kernel TensorFlow sạch; cờ train trong notebook giữ tường minh. Có12 kiểm thử hợp đồng đạt trong môi trường mới. Bằng chứng tổng hợp có thể commit: `docs/RUNTIME_EVIDENCE.json`; trạng thái sống hiện hành: `outputs/background_status.json`, `outputs/latest_pipeline.json`, `scripts/status.py`.

## 2026-10-23 — Kích hoạt goal tự động có giới hạn

Người dùng duyệt goal model+CLI/notebook, tối đa3 cấu hình thêm, mỗi cấu hình2epoch, heartbeat mỗi30 phút. Goal và heartbeat native trong chat đã được tạo; không tạo cron thay thế hay dùng cloud. Chính sách/registry được lưu riêng.

Giữ model train PID19191 chạy nguyên source; SIGSTOP riêng controller18836 để nó không tự mở test trước khi chọn theo validation. Đã xác minh controller ở trạng tháiT và model vẫn dùng CPU, log tiếp tục tăng. Handoff chỉ thực hiện sau lineage completed, không dừng model để sửa code.

Đã chuẩn bị package `career_auto` riêng: khóa chống điều phối trùng, job tách phiên có exit record, quota/retry/patience, lựa chọn validation, gate test ứng viên cuối, checkpoint atomic LoRA/head/optimizer/cursor và chặn resume khi khác config/source/data/phiên bản. CLI legacy chỉ đổi mặc định evaluate khi vòng cũ đã kết thúc; module evaluate mới mặc định validation ngay từ đầu.

16 kiểm thử hợp đồng đạt, gồm round-trip optimizer thật nhưng không training trong test, kiểm checksum hỏng/config khác, patience không reset bởi cải thiện nhỏ, test gate và thử patch CLI trên bản sao tạm. Đây chưa chứng minh vòng Qwen mới resume đúng trên mọi phase: mỗi cấu hình phải qua smoke và kiểm restore optimizer thật trước full. Chưa mở cấu hình bổ sung khi vòng gốc còn chạy; chưa có metric LLM full mới. Log kiểm thử: `outputs/auto_dev/contract_tests.log`.

## 2026-10-23 — Siết kiểm tra resume và chuẩn bị bàn giao tự động

Đã bổ sung bước smoke dừng có chủ đích giữa epoch sau2 optimizer update, nạp lại đúng cursor và lưu resume event. Lý do: chỉ nạp checkpoint sau epoch cuối không chứng minh có thể tiếp tục phần train còn lại. Gate full yêu cầu bằng chứng resume giữa epoch, LoRA thay đổi và lưu/nạp trong tiến trình mới. Đây là cơ chế đã viết và kiểm hợp đồng; smoke pretrained cho cấu hình mới vẫn chờ vòng gốc kết thúc.

Đánh giá ngôn ngữ có độ khớp riêng từng trường và số nhãn khác null; generation lỗi được tính thất bại, không làm tăng điểm do bỏ mẫu. Đã chuẩn bị báo cáo lỗi lớn theo thị trường và notebook chỉ hiển thị model được chọn. Notebook không tự mở thí nghiệm khi goal còn hoạt động. Báo cáo cuối bị chặn trước khi test, demo, notebook và kiểm thử hoàn tất.

23 kiểm thử phần mềm đạt; kiểm chuẩn bị notebook chạy trên bản sao tạm, không thay notebook đang dùng hoặc cập nhật trọng số. Vòng gốc PID19191 vẫn sử dụng CPU và log đã tới step1350 epoch1 lúc kiểm tra; controller18836 giữ trạng tháiT có chủ đích. Raw, split và source `career_ai` của vòng gốc không thay đổi; chưa có kết quả LLM full để công bố cải thiện.

Rà soát bổ sung phát hiện đường chọn vòng gốc cần gate lưu/nạp ở cấp ứng viên cuối, dù đã có smoke trước đó. Đã thêm `final_reload` trước test cho mọi ứng viên; báo cáo chỉ sinh khi có `fresh_process_reload.json` đạt. Manifest bàn giao sẽ ghi checksum adapter/head, metadata, metric, môi trường và notebook để đối chiếu đúng phiên bản. 24 kiểm thử phần mềm đạt, gồm thứ tự reload trước test. Vòng gốc vẫn chạy và chưa dùng cấu hình bổ sung tại mốc này.

## 2026-10-23 — Rà soát thống kê và biểu đồ

Phát hiện biểu đồ cũ loại các dòng có cùng vai trò/vùng/kinh nghiệm/kỹ năng, dù có thể là những người hoặc tin khác nhau với mức thu nhập khác nhau. Điều này làm thay đổi mẫu và trung vị ngoài bước làm sạch có kiểm toán. Đã viết bản biểu đồ mới giữ từng quan sát và thêm cờ low_support; chỉ xếp hạng thu nhập khi kỹ năng có ít nhất10 mẫu. Biểu đồ từ kết quả suy luận được ghi rõ predicted income và kỹ năng trong hồ sơ, không trình bày thành nhu cầu tuyển dụng thực đo.

Hai kiểm thử riêng đạt: hai quan sát cùng đặc trưng nhưng thu nhập20/30triệu phải cho n=2 và trung vị25triệu; cài chuyển tiếp CLI chỉ tác động bản sao và không ghi đè bản backup khi gọi lại. Đã xuất thật10 PNG/4 CSV từ train10.417 dòng (10.262 quốc tế,155 Việt Nam), xem `outputs/chart_review_train/` và `outputs/auto_dev/chart_real_data.log`; đã kiểm tra trực quan biểu đồ thu nhập theo kỹ năng quốc tế. Đây là kiểm thống kê/EDA, không là cải thiện model hay kết quả AI giả lập. Bản sửa chỉ được nối vào CLI sau vòng gốc; checksum source experiment đang chạy vẫn khớp. README đã chỉ rõ registry goal thay cho trạng thái pipeline legacy.

## 2026-10-24 — Tiếp tục sau khi người dùng tạm dừng

Ngày23/10 lúc17:57 (giờ Việt Nam), người dùng yêu cầu tạm dừng: goal và heartbeat chuyển paused, riêng model PID19191 nhận SIGSTOP để giữ optimizer/trạng thái thực trong RAM. Controller legacy18836 vẫn dừng có chủ đích như trước. Không kết thúc experiment hay coi partial adapter/head là checkpoint có optimizer.

Ngày24/10 lúc06:14, người dùng yêu cầu tiếp tục. Đã xác minh PID/command đúng, tiến trình còn ở trạng tháiT và mọi checksum source trong lineage của vòng gốc vẫn khớp; sau đó gửi SIGCONT riêng model19191. Log thực tăng từ step2750 sang2760 epoch1, CPU hoạt động trở lại. Đây là tiếp tục tiến trình còn sống trong RAM, không phải nạp lại partial trên đĩa hoặc mở thêm cấu hình. Registry lưu `pause_history` với thời điểm tạm dừng/tiếp tục; quota cấu hình bổ sung vẫn0/3.

Heartbeat30 phút đã bật lại; goal được xác minh active sau khi người dùng tiếp tục trong ứng dụng. Dữ liệu/nhãn/split và cấu hình vòng đang chạy được giữ nguyên. Bằng chứng: `outputs/auto_dev/state.json`, `outputs/qwen_20261023T082631/lineage.json`, `outputs/pipeline_20261023T082631/train_qwen_full.log`. Chưa có metric LLM full; các vòng tiếp theo vẫn chờ vòng gốc kết thúc.

## 2026-10-24 — Epoch1 hoàn tất, vòng gốc sang epoch2

Khoảng17:46 (giờ Việt Nam), vòng gốc đã ghi `llm_history.json`, adapter/head và reload probe cho epoch1; log sau đó xác nhận epoch2 bắt đầu. Validation sau language replay cho MAE log trung bình theo thị trường0,4305962306, answer cross-entropy0,1411506637 trên32 mẫu phù hợp context, selection score0,4447112970. Giá trị này đúng công thức đã chốt, chưa là MAE theo USD/năm hoặc VND/tháng và không chứng minh chất lượng generation JSON hay model vượt baseline.

Đã ghi checksum/kích thước artifact epoch1 và mốc quan sát vào `docs/RUNTIME_EVIDENCE.json`; chúng là trọng số trung gian của vòng full, chưa được công bố là checkpoint có optimizer hoặc full-model reload đã kiểm. Vòng hiện tại vẫn tiếp tục epoch2, `lineage` còn running; chưa mở test hay dùng cấu hình bổ sung. Phần JSON/validation của trainer gốc không in log từng bước, vì vậy giai đoạn im log trước đó được giám sát qua PID/CPU/bộ nhớ và artifact, không tự restart. Không sửa nóng source đang train.

## 2026-10-24 — Rà soát biên gián đoạn của trainer cho vòng sau

Phát hiện và tái hiện cửa sổ lỗi khi checkpoint cuối epoch đã lưu nhưng history chưa kịp xuất: resume nhận cursor đã đủ epoch, bỏ qua vòng lặp và công bố completed mà thiếu `llm_history.json`, khiến bước lựa chọn model sau đó thất bại. Test `tests/test_training_resume.py` dùng Qwen giả, checkpoint cursor hoàn tất và không chạy gradient update; trước sửa tái hiện FileNotFoundError, sau sửa history được xuất lại từ cursor. Bằng chứng: `outputs/auto_dev/terminal_resume_regression_before.log` và `outputs/auto_dev/contract_tests.log`.

Đồng thời sửa điều kiện chụp trọng số trước cập nhật theo optimizer iteration0, để resume từ checkpoint ban đầu vẫn kiểm LoRA thực sự thay đổi. Nhánh này được rà soát mã; kiểm trên pretrained thực tế vẫn chờ smoke của vòng mới, chưa công bố đã kiểm cold-resume Qwen. Tổng27 kiểm thử phần mềm đạt. Các sửa chỉ nằm trong module `career_auto` dành cho experiment chưa mở; checksum source `career_ai` của vòng gốc vẫn khớp. Không dùng kết quả mock để nói chất lượng model được cải thiện.

## 2026-10-25 — Lưu/nạp trọng số và kiểm chứng demo văn bản

Đã thêm check_reference: nạp trọng số vòng gốc trong tiến trình mới trước validation/chọn model. Đường suy luận hiện nạp pretrained Qwen rồi qwen.lora.h5 và salary_head.keras đã học (career_ai/models.py, loaded_llm); chưa coi checkpoint epoch 1 là model cuối. Demo bổ sung hai mô tả tổng hợp từ đặc trưng train, không chứa lương, chạy trích xuất rồi dự đoán. Báo cáo yêu cầu demo này đạt. Trainer gốc chưa bị thay code/dữ liệu.

29 unittest đạt, Ruff đạt; log outputs/auto_dev/contract_tests.log. Test demo dùng CLI giả chỉ kiểm hợp đồng và bảo toàn bảng đầu ra, chưa chứng minh chất lượng Qwen. Lưu/nạp và demo thật còn chờ model cuối.

## 2026-10-25 — Sửa khoảng im log cuối epoch

Theo yêu cầu sửa log của người dùng, bổ sung career_auto/training.py: log chuyển pha học số/JSON, mẫu bị bỏ vì context, validation lương mỗi100 dòng và ngôn ngữ mỗi4 dòng, validation score và lưu checkpoint tốt nhất. Có timestamp, số xử lý/tổng, flush terminal và progress.json. Không thay career_ai/models.py đã nạp trong PID19191, không restart hay can thiệp bộ nhớ. Vì vậy log legacy hiện tại chưa được thay đổi. Test mới dùng model/giá trị giả chỉ kiểm thông báo đúng pha, tổng và mẫu ngôn ngữ bị bỏ; không đo chất lượng AI.

## 2026-10-25 20:13 — Hoàn tất train gốc và nạp lại trọng số thật

Lineage vòng outputs/qwen_20261023T082631 completed lúc 13:13:07Z; 10.417 dòng mỗi epoch, 2 epoch và 648 language updates theo metadata. Điểm validation chọn model: epoch 1 = 0,4447112970, epoch 2 = 0,4553996349; chọn epoch 1. Đây là market-mean logMAE + 0,1×answer CE, không phải sai số USD/VND.

Đã kết thúc controller legacy dừng có chủ đích sau khi trainer kết thúc; bộ điều phối mới tiếp quản. CLI evaluate mặc định validation và bản biểu đồ mới được cài sau train, không sửa source vòng đang chạy. Baseline validation hoàn tất: quốc tế n=2368 MAE=31556,44 USD/năm, RMSE=64839,90, R²=0,34975; Việt Nam n=37 MAE=6337482,63 VND/tháng, RMSE=8217053,96, R²=0,29356.

Fresh-process check đã nạp backbone đúng phiên bản + qwen.lora.h5 + salary_head.keras; khớp dự đoán 2 hồ sơ trước lưu với rtol=1e-5 (fresh_process_reload.json passed). Đây là bằng chứng lưu/nạp, chưa phải chất lượng tổng quát. Đang đánh giá validation đầy đủ Qwen; chưa mở test và chưa chạy cấu hình bổ sung. Hash/metadata/history/bằng chứng tại docs/RUNTIME_EVIDENCE.json, full_training_completion.

Kiểm thử sau handoff phát hiện bài test migration biểu đồ phụ thuộc source legacy trong checkout nên lỗi khi checkout đã chuyển sang delegate. Đã đổi sang fixture legacy độc lập để vẫn kiểm backup và idempotence, giữ kiểm checkout không bị test sửa. Đây là sửa tính tái lập của test, không là cải thiện độ chính xác.

## 2026-10-25 — Validation đầy đủ model vòng gốc

Job validate_reference kết thúc exit 0. Quốc tế n=2368: MAE=31508,37 USD/năm, RMSE=64012,33, R²=0,36624. Việt Nam n=37: MAE=7696924,67 VND/tháng, RMSE=9080539,59, R²=0,13729. So với baseline validation đã ghi ở trên, quốc tế gần tương đương, Việt Nam kém hơn; không tuyên bố LLM tốt hơn toàn bộ.

32 mẫu ngôn ngữ validation: JSON schema 1,0; role accuracy 0,8125; experience accuracy 1,0; Skill F1=0,64661654; không lỗi schema. Nhãn silver chưa được gọi human gold. Chi tiết và hash tại docs/RUNTIME_EVIDENCE.json/reference_validation_completion; không dùng test để chọn.

Đã reserve cấu hình bổ sung thứ nhất rank8/lr2e-5 và khởi động smoke outputs/auto_lr_low_smoke, chưa gọi full training đạt. Smoke phải chủ động dừng sau2 optimizer update, resume từ cursor giữa epoch và qua kiểm tra nạp model ở tiến trình mới. Một train local tại một thời điểm.

## 2026-10-25 21:20 — Smoke Qwen thật đạt, bắt đầu cấu hình bổ sung thứ nhất

Smoke outputs/auto_lr_low_smoke đã chứng minh actual_lora_changed=true; chủ động dừng ở optimizer iteration2/cursor epoch0 numeric next_index16; khôi phục optimizer238 variables và đúng cursor, học tiếp rồi lineage completed. scripts/check_saved_run.py chạy tiến trình mới khớp2 probe; smoke_acceptance.json đạt cả4 cổng. Đây là kiểm chứng cập nhật/resume/lưu-nạp thật, không dùng metric smoke để tuyên bố chất lượng tổng quát.

Đã bắt đầu full outputs/auto_lr_low: rank8/lr2e-5,2epoch, từ pretrained cùng phiên bản, tập10.417 dòng; một train local. Quan sát bước21 epoch1 và optimizer2, checkpoint ban đầu đã lưu, actual_lora_changed=true. Log có timestamp/phase/examples/total và sẽ cập nhật validation/lưu best. Bằng chứng thực tế tại docs/RUNTIME_EVIDENCE.json/first_additional_smoke_acceptance. Chưa mở test, chưa chọn ứng viên cuối.

## 2026-10-25 — Người dùng chốt model vòng gốc, dừng thử thêm

Người dùng yêu cầu giảm thời gian xuống1epoch, bỏ rank8/lr1e-4 và rank16, sau đó chốt dùng model vòng trước outputs/qwen_20261023T082631 với các metric validation đã công bố. Đã hủy trial auto_lr_low, không dùng checkpoint dở dang của trial này làm ứng viên. Quyết định này thay giới hạn thử nghiệm trước; chỉ tiếp tục bàn giao model đã chọn, không mở train nữa.

Trước quyết định chốt model có thử chuyển giới hạn epoch qua checkpoint giữ nguyên mảng trọng số/optimizer, lưu bản gốc và migration manifest; tiến trình resume bị chặn bởi kiểm identity lineage trước khi học tiếp. Không coi resume đó thành công. Trial được hủy theo quyết định người dùng, log/migration vẫn giữ trong outputs; không retry hoặc làm yếu guard. Trọng số model vòng gốc không bị sửa.

Đã đặt selected_run và search_closed, cập nhật heartbeat không train thêm; khởi động final_reload trước final_test. Kết quả test chỉ dùng báo cáo, không điều chỉnh model nữa.

Đã xác nhận final_reload exit0, chuyển final_test cho đúng model đã chốt. 31 unittest đạt (outputs/auto_dev/contract_tests_selected_model.log), gồm kiểm search_closed không mở thử nghiệm dù còn quota và config train tuân thủ max_epochs. Ruff đạt. Heartbeat đã cập nhật chỉ hoàn thiện bàn giao, không train thêm.
