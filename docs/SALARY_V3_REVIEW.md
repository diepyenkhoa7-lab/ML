# Vòng train nhãn rõ kỳ tháng ngày 18/10/2026

Đã train thật hai vòng, tổng **24 cấu hình Ridge/Random Forest**. V3.1 dùng 87 tin gần đây và thử thêm 127 tin năm 2022–2024 với trọng số 0,5. Không dùng nhãn giả định tháng. Các nhãn có câu hoặc trường ghi rõ kỳ tháng nhưng vẫn là **silver**, chưa phải nhãn gold do con người duyệt.

**Chưa triển khai checkpoint mới.** Web giữ Ridge v2 và Gemma adapter đã chọn. Model v3/v3.1 không đạt gate; bộ nạp model từ chối checkpoint được đánh dấu không đủ điều kiện nghiệm thu.

| Vòng | Train gần đây / bổ sung cũ | Validation | MAE / RMSE validation, triệu VND | Khoảng lệch nhóm ITviec |
|---|---:|---:|---:|---:|
| v3 `v3_b5ae152b9dd5` | 55 / 60 | 18 | 6,249 / 10,236 | 29,98% |
| v3.1 `v31_b089fdf458a5` | 87 / 127 | 28 | 4,847 / 6,707 | 31,09% |
| v2 đang phục vụ, trên cùng panel thị trường | — | — | — | 21,09% |

Hai vòng có validation khác nhau: không diễn giải chênh lệch hai dòng thành mức cải thiện trên cùng tập. Cả hai chọn RF bằng MAE validation, RMSE phá hòa; từng vòng khóa selection và hash trọng số trước khi mở dữ liệu kiểm tra mới. V3.1 chọn RF 300 cây, `min_samples_leaf=5`, nhánh thêm dữ liệu cũ, tổng 214 nhãn train.

## Điều đã sửa trong dữ liệu

- Dùng số tiền trong câu lương tháng thay vì mặc nhiên coi khung phân loại đầu bài là nhãn: có trường hợp header `20–30 triệu`, nội dung `21–27 triệu/tháng`.
- Loại “up to”, khoảng hở, ngoại tệ, explicit net, lương mâu thuẫn, PLC/CNC và giáo viên. Không tự đổi tiền hoặc suy kỳ lương từ thưởng tháng 13.
- V3.1 bổ sung dạng header rõ `20000000 - 30000000 VND MONTH` mà parser v3 yêu cầu dấu `/` đã bỏ sót. Giữ v3 nguyên vẹn để truy vết.
- Seniority rõ trong tiêu đề được ưu tiên trước chức danh chung “Nhân viên”; tiêu đề nhiều cấp bậc được để Unknown. Không dùng seniority để bịa số năm kinh nghiệm.
- Chỉ fit preprocessing trên train. Chia validation theo công ty; loại công ty của valid/test v1/v2 khỏi toàn bộ dữ liệu phát triển mới.

## Nguồn mới và kiểm tra độc lập

Đã đọc 45 `JobPosting` công khai từ CareerLink/TopDev và 44 từ JobOKO. Bộ thu thập kiểm tra robots, giới hạn số trang/tốc độ, dừng khi HTTP 403/429 hoặc gặp trang challenge, kể cả HTTP 200. Audit lượt CareerLink đầu phát hiện 42 trang challenge không chứa JobPosting; không có nhãn nào từ các trang này được dùng. Không vượt CAPTCHA hoặc đăng nhập để lấy lương ẩn.

Chỉ nhận `currency=VND`, `unitText=MONTH`, hai cận số hợp lệ. Không lấy “thương lượng”, không biến mức “từ”/“đến” thành nhãn điểm; loại metadata kinh nghiệm mâu thuẫn nội dung. Để so với v2 công bằng hơn, loại mọi công ty từng xuất hiện trong dữ liệu v1/v2 và dữ liệu phát triển mới; v3.1 còn loại công ty của mẫu v3 đã mở.

Sau lọc, v3 còn **1 mẫu**, v3.1 còn **3 mẫu / 3 công ty**. Đây là kiểm tra thăm dò, **không phải benchmark đủ tin cậy**. Trên 3 mẫu v3.1, RF MAE 7,331 triệu so với v2 9,715 triệu; không suy rộng kết quả này, không báo CI khi dưới 10 công ty. Gate tối thiểu 20 mẫu/10 công ty không đạt. Test v1/v2 không được dùng lại để điều chỉnh tham số.

[Stack Overflow 2026 chính thức](https://github.com/StackExchange/Survey/tree/6c646551e86ffcafca0ac04f1dfb17a2558ec23d/packages/archive/2026) đã tải đủ CSV 122.407.316 byte, SHA-256 khớp Git LFS. Có 30.903 phản hồi, 68 ở Việt Nam, 61 chọn VND, 32 điền compensation; chỉ 13 phản hồi có số tiền VND/năm trong ngưỡng sanity rộng và có kinh nghiệm. Câu hỏi là **total annual gross compensation gồm lương, thưởng, perks**, không phải lương cơ bản tháng. Không trộn vào nhãn chào tuyển hoặc tạo mô hình thu nhập riêng từ 13 mẫu.

## Vì sao thị trường vẫn chưa khớp

So v2 và candidate trên **cùng panel profile train v2 được đóng băng**, cùng 13 nhóm vai trò/kinh nghiệm có ít nhất 5 profile, với [ITviec 2025–2026](https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam). V3.1 lệch 31,09%, kém v2 21,09%. File `market_panel_comparison.csv` giữ từng nhóm, không chỉ số tổng.

Đây là độ lệch trung vị nhóm, không phải MAE thu nhập cá nhân. Lương chào tuyển có công bố và khảo sát thu nhập khác quần thể, kỹ năng, công ty và gross/net. Nhóm có dữ liệu rõ kỳ tháng còn nhỏ và nhiều tin lương thấp; thêm dữ liệu cũ có thể mang sai lệch thời gian. Bỏ giả định kỳ tháng giúp nhãn có bằng chứng hơn nhưng không tự tạo đại diện thị trường. Không nhân dự đoán lên cho “đẹp”, không dùng trung vị báo cáo làm hàng nghìn người giả. ITviec là mục tiêu đối chiếu đã biết, không phải test độc lập của vòng mới.

## Nhãn cần duyệt tiếp và Gemma

`data/annotation/v3.1.0/salary_review_queue.jsonl` chứa **214 dòng chỉ thuộc train**, có dữ liệu gốc, đề xuất và dẫn chứng; `gold=null`, `review_status=pending`. Đây là gói annotation, không có định dạng `messages` để chạy SFT nhầm. Người duyệt cần xác nhận vai trò, kỹ năng, kinh nghiệm, hai cận tiền, kỳ lương và gross/net; trường thiếu bằng chứng phải giữ null hoặc loại. Tini không có URL từng tin nên không tự bịa URL/ngày đăng.

Cần bổ sung nhãn thu nhập cá nhân có định nghĩa khoản thu rõ ràng nếu muốn dự đoán thu nhập thị trường, cùng dữ liệu mới độc lập theo công ty/thời điểm. Mục tiêu thực tế cho lượt sau: khoảng 100–200 mẫu được duyệt, có vùng/role/experience đa dạng; tối thiểu 20 mẫu/10 công ty độc lập là gate kỹ thuật, chưa bảo đảm đủ độ tin cậy thống kê. Chưa có đủ nhãn gold mới để fine-tune Gemma. Adapter hiện tại vẫn trích tin trên web; train bộ hồi quy lương không cập nhật trọng số Gemma.

## Lệnh train và suy luận

```bash
# Chỉ suy luận bằng model đang được nghiệm thu; không train
make app
make app-test

# Các lệnh dưới TRAIN THẬT CPU, không đổi model web tự động
make salary-v3-train
make salary-v31-train

# Thu thập công khai / chuẩn bị dữ liệu; không train
make salary-v3-collect
make salary-v31-prepare

# TRAIN Gemma là lệnh riêng, chỉ dùng sau khi duyệt nhãn/protocol mới
# make gemma-adapter
```

Các artifact của hai vòng đã tồn tại; prepare/train từ chối ghi đè để không tối ưu theo test đã mở. Muốn thử tiếp cần version protocol/split/experiment mới. Source gọn chứa model candidate, split, metrics và log; raw lớn/HTML và JSON-LD có mô tả đầy đủ giữ local. Manifest ghi URL/hash để kiểm tra nguồn, không mặc định rằng public metadata có giấy phép open dataset.

Kết quả máy đọc: `outputs/metrics/salary_v3_b5ae152b9dd5/`, `outputs/metrics/salary_v31_b089fdf458a5/`. Log: `outputs/training_logs/salary_v3_20261018/`, `outputs/training_logs/salary_v31_20261018/`.
