# T08: Bổ sung framework, cơ sở dữ liệu và cloud

Trạng thái: đã được người dùng duyệt và đăng [GitHub Issue](https://github.com/theihoz/ML/issues/22) ngày 28/10/2026. Tính năng: F02. Chưa triển khai; chỉ lấy việc khi mọi blocker đã hoàn tất.

## What to build

Người dùng lọc/xuất các kỹ năng framework, database và cloud đã thống nhất alias, đồng thời xem bằng chứng nguồn.

## Công việc

- [ ] Mở rộng danh mục kỹ năng theo dữ liệu mới đã quan sát.
- [ ] Gom đúng alias, phân biệt khái niệm liên quan nhưng không tương đương.
- [ ] Bổ sung bảng bằng chứng, export và kiểm tra false positive.

## Acceptance criteria

- [ ] Alias như ReactJS/React.js được xử lý theo cùng khái niệm đã xác minh.
- [ ] Không mặc nhiên coi .NET và C# là một kỹ năng hoặc suy cloud từ từ viết tắt mơ hồ.
- [ ] Các kỹ năng có raw/đoạn nguồn và chỉ được đếm một lần mỗi tin.

## Blocked by

- T07 — Bóc tách ngôn ngữ lập trình có bằng chứng

## Cách chứng minh hoàn thành

Demo hành vi đầu vào → xử lý → giao diện/file xuất, đối chiếu kết quả thực và chạy kiểm tra liên quan. Mock hoặc kế hoạch chưa chạy không phải bằng chứng hoàn thành.

