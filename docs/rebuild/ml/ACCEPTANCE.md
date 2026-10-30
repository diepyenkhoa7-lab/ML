# Tiêu chí nghiệm thu ML

Ngày đối chiếu: 29/10/2026. Đây là bằng chứng cần thu khi triển khai M01–M08, chưa phải kết quả kiểm thử đã đạt. Không thay trạng thái 27 ticket hoặc tự mở các gate đang chờ.

## Điều kiện bắt đầu

- #42: có nguồn nhãn mới được xác minh tiền tệ, kỳ trả lương, quyền sử dụng và thực thể tin. Sau kiểm duyệt 29/10, file riêng có hai nhãn được chấp nhận; pipeline chưa ghép bổ sung nên vẫn 0 target từ salary. Gate giữ chặn vì hai nhóm không đủ ba tập độc lập và policy còn mở.
- #4: chốt chính sách đánh giá và hỗ trợ trước fit/chọn model. Không xem phương án trong spec là quyết định đã duyệt.
- #5: chốt bằng chứng và xếp hạng trước nghiệm thu tư vấn.
- Các lỗi liên quan nhãn/định danh/nghề/Remote trong audit phải có regression test và snapshot được tạo lại. Không tái dùng checksum của snapshot cũ cho dữ liệu đã sửa.

## M01 — Nhãn và readiness

| ID | Tình huống qua service/CLI | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC01 | Khoảng `20 triệu - 30.000.000 VND/tháng` và cách viết đảo notation | Hai đầu 20/30 triệu, target 25 triệu; không nhân scale hai lần | Regression test và output chuẩn hóa |
| AC02 | `20.000.000đ/tháng`, thỏa thuận, một cận, thiếu tiền tệ/kỳ | Nhận ký hiệu đ sát số; chỉ nhãn đủ chứng cứ có target; giữ raw/reason của mọi loại | Bảng đối chiếu raw → nhãn |
| AC03 | Hai URL khác ID query; bản sao cùng tin bổ sung hoặc mâu thuẫn | Không gộp khác tin; giữ chứng cứ tương thích, đưa mâu thuẫn vào review; đổi thứ tự không đổi kết quả nghiệp vụ | Test định danh và reconciliation |
| AC04 | Snapshot 0 nhãn hoặc thiếu policy | Readiness không ready; train dừng trước fit, không có artifact/metric thành công | CLI exit status, reason, manifest trạng thái |

## M02 — Split và features

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC05 | Một tin nhiều địa điểm/kỹ năng và nhiều bản đăng lại | Một entity một quan sát; không có leakage group giao train/validation/test | Split manifest, số entity/group, kiểm giao nhóm |
| AC06 | Kỹ năng chỉ xuất hiện ở phần giữ lại; đổi dữ liệu test | Không đổi vocabulary/thống kê preprocessing đã fit; trường lương/JD nguyên văn không vào features | Feature schema và test chống leakage |
| AC07 | Chạy lại cùng snapshot/config/seed | Cùng phân hoạch và ID; hash khác bị phát hiện; không cắt nhóm để ép tỷ lệ | So manifest hai lần chạy |

## M03 — Huấn luyện

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC08 | Nhãn thật được chấp nhận, policy đã chốt | Hai model tự khởi tạo/fit trên cùng train và split; baseline không tính thay model thứ hai | Cấu hình run, log fit, hai artifact và hash |
| AC09 | Chọn model rồi đánh giá test | Validation MAE thấp hơn thắng, bằng nhau chọn Linear Regression; chỉ promote nếu MAE tốt hơn trung vị train trên cả validation/test; test không đạt giữ báo cáo, không chọn/chỉnh lại bằng test | Bảng lựa chọn, prediction từng split, baseline và release status |
| AC10 | Run lỗi hoặc bị ngắt giữa chừng | Không active run chưa đủ; artifact đang dùng nguyên vẹn | Trạng thái run và hash active trước/sau |

## M04 — Đánh giá và giải thích

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC11 | Tính lại MAE/RMSE từ prediction hai model | Khớp bảng báo cáo trong dung sai được ghi; VND/tháng và n đúng split | y_true/prediction, phép tính lại, cấu hình dung sai |
| AC12 | Nhóm rỗng, một mẫu hoặc prediction không hữu hạn | Metric nhóm rỗng ghi null/lý do; ít mẫu hiển thị n và trạng thái hỗ trợ; không âm thầm xóa output lỗi hoặc clip để đẹp điểm | Test metric tính tay và báo cáo lỗi |
| AC13 | Tin có HCM và HN; tải bảng/ảnh có bộ lọc | n tổng theo tin duy nhất; nhóm chồng lắp được giải thích; export có đơn vị, basis, split/run/snapshot, nguồn/revision, kỳ quan sát, n và bộ lọc | CSV/ảnh hoặc gói sidecar tự đủ ngữ cảnh |
| AC14 | Phân tích kỹ năng có giá trị theo model | Ghi phương pháp, tập dùng, n và giới hạn; tách importance, liên hệ lương và delta hồ sơ | Báo cáo kỹ năng tái lập, không tuyên bố nhân quả |

## M05 — Artifact và hồ sơ đơn

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC15 | Nạp artifact thật trong tiến trình mới qua CLI và form | Prediction nhất quán trong dung sai, đủ phiên bản/đơn vị/basis | Probe hồ sơ, output tiến trình mới, smoke UI |
| AC16 | Artifact thiếu/hỏng/sai schema; hồ sơ thiếu/âm/OOV | Trạng thái và reason đúng, prediction null khi không thể dự đoán; không fit/download/fallback | Kết quả lỗi và hash trước/sau suy luận |
| AC17 | Hồ sơ có alias HCM/HN, Remote và kinh nghiệm khoảng/cận | Chuẩn hóa chung với batch; giữ loại bằng chứng, không coi missing là 0 hoặc remote sensing là work mode | Test hồ sơ chuẩn hóa và support |

## M06 — Tư vấn kỹ năng

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC18 | Hồ sơ đã có kỹ năng qua alias | Không gợi ý lại; tối đa ba candidate đúng phạm vi train và policy | Candidate, n và lý do thứ tự |
| AC19 | Thử thêm từng kỹ năng | Các trường nền giữ nguyên; delta từ cùng artifact; nhu cầu/lương quan sát/delta trình bày riêng | Hồ sơ trước/sau và nguồn thống kê train |
| AC20 | Không đủ mẫu/candidate hoặc chưa có model | Trả insufficient_evidence hoặc trạng thái model tương ứng; không tạo lời khuyên giả | Test trường hợp thiếu hỗ trợ |

## M07 — CSV/XLSX

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC21 | Cùng hồ sơ ở form, CSV và XLSX, có dòng lỗi xen kẽ | Cùng kết quả hợp lệ; giữ mọi dòng đọc được, ordinal/raw/status/reason; không mất thứ tự | File đầu vào/đầu ra và đối chiếu form |
| AC22 | Nhiều sheet, sai mapping, file rỗng/hỏng/quá giới hạn | Chọn sheet rõ; lỗi file phân biệt lỗi dòng; không tự cắt dữ liệu hay báo hoàn tất một phần | Test parser và smoke UI |
| AC23 | Upload khi model không sẵn sàng | Không có con số lương; dataset/model/snapshot không đổi | Export trạng thái và hash trước/sau |

## M08 — Bàn giao

| ID | Tình huống | Kết quả bắt buộc | Bằng chứng lưu |
| --- | --- | --- | --- |
| AC24 | Cài gói vào môi trường mới | Đủ code mới, dataset thực được phép phân phối, attribution, label evidence, split/config/model/metric; checksum khớp | Manifest gói và log cài mới |
| AC25 | Demo đã chuẩn bị khi ngắt mạng | Chạy biểu đồ, so sánh hai model/ít nhất hai metric, form, tư vấn, CSV/XLSX và export | Kịch bản CLI/browser, output và ảnh UI thật |
| AC26 | Gate dữ liệu hoặc release policy chưa đạt | Bàn giao ghi chưa hoàn tất ML, không đánh dấu AC08–AC25 đạt chỉ nhờ fixture hoặc EDA chạy được | Checklist nghiệm thu có trạng thái và lý do |

## Quy tắc ghi nhận

Fixture chỉ khóa logic, không chứng minh chất lượng thị trường. Test fit/save/reload chờ nhãn thật được xác minh. Mỗi AC khi triển khai ghi commit, lệnh kiểm tra, kết quả và vị trí evidence; chưa chạy ghi chưa kiểm tra. Một báo cáo tests xanh không tự thay cho các AC cần dữ liệu thật, browser hoặc môi trường sạch.
