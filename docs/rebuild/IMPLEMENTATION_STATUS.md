# Trạng thái triển khai EDA trước

Ngày 29/10/2026. Integration branch: `dev/job-market-ml-from-scratch`. Mốc spec/EDA-first: `b7466be04e6fe49c420482d81a3943ac2619358c`.

## Phạm vi đang làm

Người dùng chọn EDA trước; source gate cho EDA đã chốt. Gate [nhãn lương đủ kỳ/tiền tệ](https://github.com/theihoz/ML/issues/42) tiếp tục chặn ML. Mã mới ở job_market, không import hoặc đọc code/dataset/model cũ.

TDD dùng seam đã được duyệt: giao diện nghiệp vụ chung được CLI và Streamlit gọi, smoke UI/CLI. Mỗi ticket có worktree/branch riêng, test đỏ → implementation tối thiểu → test xanh, merger đưa vào integration và kiểm tra lại trước khi đóng ticket.

## Công việc

| Mã | Trạng thái | Bằng chứng |
| --- | --- | --- |
| [T01](https://github.com/theihoz/ML/issues/15) | Hoàn tất | Merge 0691444; Ruff và 17 tests qua; issue đã đóng |
| [T02](https://github.com/theihoz/ML/issues/16) | Đang thực hiện | Worktree dev/impl-t02-20261029 |
| [T03](https://github.com/theihoz/ML/issues/17) | Đang thực hiện | Worktree dev/impl-t03-20261029 |
| [T04](https://github.com/theihoz/ML/issues/18) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T05](https://github.com/theihoz/ML/issues/19) | Đang thực hiện | Worktree dev/impl-t05-20261029 |
| [T06](https://github.com/theihoz/ML/issues/20) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T07](https://github.com/theihoz/ML/issues/21) | Đang thực hiện | Worktree dev/impl-t07-20261029 |
| [T08](https://github.com/theihoz/ML/issues/22) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T09](https://github.com/theihoz/ML/issues/23) | Đang thực hiện | Worktree dev/impl-t09-20261029 |
| [T10](https://github.com/theihoz/ML/issues/24) | Đang thực hiện | Worktree dev/impl-t10-20261029 |
| [T11](https://github.com/theihoz/ML/issues/25) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T12](https://github.com/theihoz/ML/issues/26) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T13](https://github.com/theihoz/ML/issues/27) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T14](https://github.com/theihoz/ML/issues/28) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T15](https://github.com/theihoz/ML/issues/29) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T16](https://github.com/theihoz/ML/issues/30) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T17](https://github.com/theihoz/ML/issues/31) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T18](https://github.com/theihoz/ML/issues/32) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T19](https://github.com/theihoz/ML/issues/33) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T20](https://github.com/theihoz/ML/issues/34) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T21](https://github.com/theihoz/ML/issues/35) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T22](https://github.com/theihoz/ML/issues/36) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T23](https://github.com/theihoz/ML/issues/37) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T24](https://github.com/theihoz/ML/issues/38) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T25](https://github.com/theihoz/ML/issues/39) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T26](https://github.com/theihoz/ML/issues/40) | Chưa thực hiện | Chờ các blocker hoàn tất |
| [T27](https://github.com/theihoz/ML/issues/41) | Chưa thực hiện | Chờ các blocker hoàn tất |

## Triage và chẩn đoán

Kiểm tra live không có issue mở ngoài bộ kế hoạch/wayfinder. Không triage lại các ticket đã được to-tickets chuẩn bị. Chưa có bug người dùng báo; diagnosing-bugs áp dụng cho lỗi thực tế có command tái hiện đỏ và kiểm thử hồi quy tại đúng seam.

## Giới hạn hiện tại

Chưa có model/metric/dự đoán mới. Raw lương thiếu kỳ không thành target tháng. Các số liệu EDA sẽ ghi nguồn, n, thời gian và phạm vi; không coi hai nguồn khác nền tảng ở hai năm là xu hướng thị trường cùng phạm vi.

