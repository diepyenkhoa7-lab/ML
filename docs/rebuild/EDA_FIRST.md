# Đợt triển khai EDA trước

Người dùng duyệt ngày 28/10/2026: triển khai EDA trước, giữ ML bị chặn. Mã nguồn mới đặt trong job_market, package Python độc lập; không import hoặc đọc dataset/artifact của hệ thống cũ.

## Nguồn mới dùng trong đợt này

| Nguồn | Phiên bản | File mới đã kiểm tra | Phạm vi chấp nhận |
| --- | --- | --- | --- |
| lucaznguyenofficial/vietnamese-job-posting-vietnamese-version | Kaggle v2, CC0 theo metadata | 2.056 dòng, có job_id/job_url/JD/ngày thông báo | Nhập, làm sạch, EDA theo tin đã lọc và khử trùng; kỳ lương chưa xác nhận |
| baocgb/vietnam-it-jobs-raw-data-from-topcv-2026 | Kaggle v1, CC BY 4.0 theo metadata | 1.550 dòng, có URL/ngày/kinh nghiệm/lương; thiếu JD | Nhập, làm sạch, EDA; kỹ năng chỉ trích từ tiêu đề có chứng cứ, kỳ lương chưa xác nhận |

Nguồn chính chủ: [metadata 2023](https://www.kaggle.com/api/v1/datasets/view/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version), [metadata 2026](https://www.kaggle.com/api/v1/datasets/view/baocgb/vietnam-it-jobs-raw-data-from-topcv-2026). Dataset 2023 có nguồn CareerBuilder, 2026 có nguồn TopCV theo bên phát hành; không coi hai lần thu thập từ hai nền tảng là chuỗi thời gian cùng phạm vi.

ZIP tải mới v2 năm 2023 có SHA-256 ffaf1a9a06848036e25ed9d87836e6f5a4918237aa34d312298fdf9e24b59307. ZIP v1 năm 2026 có SHA-256 29651eb3e85d4d5b0fb8e45f968e01585c51de95f038cb850dc72607352f0426. Raw bất biến, giữ attribution và revision; lúc import phải đối chiếu checksum, schema và số dòng thực.

## Hợp đồng của đợt EDA

- Dùng source ID và job ID/URL chuẩn để nhận diện tin; bỏ tham số tracking, giữ URL gốc để đối chiếu. Dòng thô khác tin duy nhất, khác tin thuộc bảy nhóm nghề, khác dòng đủ nhãn.
- Kỹ năng có bằng chứng và phân biệt nguồn chứng cứ là tiêu đề hay JD/yêu cầu. Thiếu JD hiển thị rõ; không điền JD hoặc kỹ năng bằng model.
- Giữ raw–clean, trạng thái và lý do cho vai trò, địa điểm, Remote, kỹ năng, kinh nghiệm và lương. Nhiều địa điểm không làm tăng tổng tin.
- Tiền tệ và kỳ lương là hai trường riêng. Giữ khoảng tiền để review khi thiếu kỳ; salary_target_vnd_month chỉ có giá trị khi chứng cứ xác nhận VND/tháng hoặc kỳ được chuyển đổi minh bạch. Không tự điền MONTH theo thói quen tuyển dụng.
- Tách bản ghi EDA và target. Nếu không có target đủ chứng cứ, báo n=0 và trạng thái ML bị chặn; không train, điền metric hoặc hiển thị dự đoán giả.
- Biểu đồ tuyển dụng theo nguồn/kỳ được gắn phạm vi. Nếu chưa đủ cơ sở so sánh năm thì cho bảng độ phủ dữ liệu và giải thích, không vẽ xu hướng tổng thị trường.
- Fixture tổng hợp nhỏ chỉ kiểm tra logic tại seam đã duyệt. Fixture không đi vào dataset nộp bài, huấn luyện hoặc số liệu thị trường.

## Triển khai và kiểm tra

Giữ integration branch dev/job-market-ml-from-scratch. Mỗi ticket có implementer worktree riêng dựa trên đầu branch; TDD từng lát cắt, merger đưa vào integration rồi mới mở frontier tiếp. Điểm kiểm thử đã duyệt: giao diện nghiệp vụ chung được CLI/Streamlit sử dụng, smoke UI và CLI. Khi có bug cụ thể, tạo command tái hiện đỏ trước khi chẩn đoán/sửa.

Triage hiện không có issue ngoài bộ kế hoạch đang mở. Các ticket do to-tickets tạo đã được duyệt, nên không đưa chúng qua triage lại. Các thay đổi có sẵn trong AGENTS và docs/agents cũng như docs/research/spec-method-review.md thuộc người dùng, không nằm trong đợt code này.
