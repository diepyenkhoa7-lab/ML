# F02: Chuẩn hóa dữ liệu và nhãn có chứng cứ

Trạng thái: đã triển khai chuẩn hóa và kiểm tra chất lượng trong đợt EDA, kiểm tra ngày 29/10/2026. [Spec tính năng trên GitHub](https://github.com/theihoz/ML/issues/8). Bằng chứng T03–T11 trong job_market/docs/tdd. Nhãn lương đủ điều kiện hiện n=0; các quyết định huấn luyện vẫn chờ gate riêng.

## Problem Statement

Các tên địa điểm/kỹ năng khác nhau, tin nhiều địa điểm và nhãn lương thiếu thông tin dễ làm lệch thống kê hoặc huấn luyện.

## Solution

Luồng chuẩn hóa có bảng đối chiếu raw–clean, trạng thái chất lượng, lý do cách ly và xuất bản sạch/review để người dùng kiểm tra.

## User Stories

1. Là người dùng dự án, tôi muốn gom HCM, Hồ Chí Minh và ho chi minh về HCM để thống kê thống nhất.
2. Là người dùng dự án, tôi muốn giữ đồng thời HCM và HN, tách Remote để không mất thông tin địa điểm.
3. Là người dùng dự án, tôi muốn phân nhóm nghề và kỹ năng với bằng chứng trích xuất để rà lại.
4. Là người dùng dự án, tôi muốn giữ hai đầu lương và dùng trung điểm khi đủ đơn vị, giữ tin thiếu lương cho EDA.

## Implementation Decisions

- Nhóm nghề: Backend, Frontend, Fullstack, Mobile, Data/ML, DevOps, QA Automation; vai trò mơ hồ cần trạng thái review.
- Alias gom theo cùng khái niệm; Java khác JavaScript, C khác C++, .NET và C# không mặc nhiên đồng nghĩa.
- Kinh nghiệm giữ khoảng/cận và trạng thái, thiếu khác 0; quy tắc biểu diễn số dùng huấn luyện được ghi rõ.
- Lương chỉ có một cận/thỏa thuận/thiếu đơn vị không thành target chính; VND/tháng tách ngoại tệ và gross/net chưa rõ.
- Một tin duy nhất có thể chứa nhiều địa điểm/kỹ năng; chuẩn hóa trước nhóm trùng/chia tập.

## Testing Decisions

- Fixture nhỏ kiểm tra alias, ranh giới từ, nhiều địa điểm, Remote, khoảng kinh nghiệm và lương thiếu.
- Các tổng thô/sạch/review/loại có thể đối chiếu bằng ID/lý do; chạy lại cho cùng kết quả.
- Bản sạch giữ được chuỗi raw, bằng chứng và nguồn cho từng target; không suy lương từ model khác.

## Out of Scope

Nhãn do pretrained/LLM sinh; chuẩn hóa địa chỉ không đủ bằng chứng bằng cách đoán.

## Further Notes

Yêu cầu III.1. Công việc T03–T11.

