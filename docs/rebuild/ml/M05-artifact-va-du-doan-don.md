# M05 — Artifact và dự đoán một hồ sơ

## Problem Statement

Model có thể chạy trong tiến trình train nhưng thiếu encoder, sai schema hoặc không hỗ trợ hồ sơ người dùng khi demo.

## Solution

Nạp bộ artifact hoàn chỉnh đã kiểm tra và dùng cùng service cho form/CLI; trả ước tính hoặc trạng thái rõ thay vì luôn trả số.

## User Stories

1. Là người demo, tôi muốn reload ở tiến trình mới, để biết artifact có đủ thành phần.
2. Là người dùng, tôi muốn nhập vai trò/kinh nghiệm/skills/địa điểm/Remote, để ước tính lương chào tuyển trong phạm vi dữ liệu.
3. Là người dùng, tôi muốn thấy lý do từ chối/cảnh báo, đơn vị và phiên bản, để hiểu giới hạn kết quả.

## Implementation Decisions

- Artifact gồm preprocessing/model, feature schema, alias/catalog/policy, đơn vị/basis, snapshot/split/run ID, hash và báo cáo đánh giá. Kiểm tương thích trước suy luận; không tìm model cũ để fallback.
- Một pipeline chuẩn hóa cho hồ sơ đơn và file, phân biệt missing/0/range/bound, canonical/unknown/OOV. Hình thức Remote phải là bằng chứng làm việc, không chỉ từ “remote” thuộc lĩnh vực kỹ thuật.
- Các trạng thái có mã/lý do gồm model_unavailable, invalid_input, unsupported_profile, prediction_error và ok; ngưỡng support/warning do #4 chốt. Không đồng nhất row preview hợp lệ với hồ sơ được model hỗ trợ.
- Output ok có lương hữu hạn/dương, VND/tháng, basis, model/run/snapshot và cảnh báo. Lương là ước tính lương chào tuyển, không phải thu nhập thực nhận hoặc lời cam kết.
- Lỗi hash/schema/model thiếu hoặc output sai không kích hoạt train, download model ngoài hoặc ghi đè artifact. Chỉ promote ứng viên đã đạt release policy; không dùng quy tắc “file mới nhất” thay lựa chọn đã kiểm tra.

## Testing Decisions

Dùng artifact tự train từ nhãn thật sau gate; fresh-process và CLI/UI cho cùng kết quả trong dung sai ghi rõ. Kiểm artifact sai/thiếu, role chưa có trong train, kỹ năng/địa điểm OOV, tuổi kinh nghiệm bất hợp lý, hồ sơ thiếu và output không hợp lệ. Hash trước/sau inference giữ nguyên.

## Out of Scope

Train trong dashboard, nạp model từ upload, fallback về công thức lương hoặc model cũ.

## Further Notes

F05, T17/T20; phụ thuộc M03/M04 và #4. Không yêu cầu seam mới ngoài service/CLI/UI đã duyệt.
