# Kết quả kiểm duyệt ứng viên nhãn lương

Ngày 29/10/2026, trên dev/ml-development. Phạm vi gồm 26 trường hợp từ shortlist đã nghiên cứu: 4 tin trong raw 2023 được duyệt, 1 tin TopCV, 9 đối chứng VietJobs, 10 tin GitHub và 2 trang employer. Không xem số này là tổng nhãn hợp lệ của các dataset. Mã ứng dụng, raw/catalog, snapshot, tracker và model không đổi trong lượt kiểm duyệt.

## Kết quả

**2 accepted, 17 needs_review, 7 excluded. Training vẫn blocked.** Dataset kiểm duyệt trong job_market/datasets/labels/2026-10-29 có accepted_labels.csv, candidate_review.csv/json và manifest.json.

| Nhóm | Quyết định và bằng chứng |
| --- | --- |
| YODY Data Analyst, 35BB58E5 | accepted: 20–35 triệu VND/tháng, trung điểm 27,5 triệu. Data/ML từ title và nhiệm vụ dữ liệu. |
| YODY Data Engineer, 35BB58DC | accepted: 25–50 triệu VND/tháng, trung điểm 37,5 triệu. Data/ML từ title và nhiệm vụ ETL/data warehouse. |
| Jaxtina Senior Developer, 35BB4811 | needs_review: lương 25–45 triệu VND/tháng đủ chứng cứ, nhưng trách nhiệm Mobile và Backend cùng tồn tại; không ép thành một nghề. |
| VACS Nhân viên IT, 35BB74A6 | excluded: helpdesk/phần cứng/mạng ngoài bảy nghề; khoản bounded có điều khoản thương lượng cũng không được tự coi là nhãn chính xác. |
| TopCV 2000941 | needs_review: có tháng và khoảng 40–55 triệu, chưa có currency tường minh; không suy triệu thành VND. |
| VietJobs 9 đối chứng | 3 needs_review vì thiếu đơn vị/kỳ, notation hoặc range mâu thuẫn; 6 excluded vì phụ cấp, một cận, thu nhập công việc tương lai hoặc ngoài nghề. Thiếu URL/ID tin và ngày nguồn không được tự điền. |
| GitHub 10 + employer 2 | needs_review: giữ chứng cứ salary riêng với source admission. Có nhãn net, base salary và unknown, không gộp. Logic Lab cùng ID có hai range/phiên bản mâu thuẫn; giữ review thay vì chọn dòng đầu/cuối. |

## Quyết định được người dùng xác nhận

- ADR 0006: unknown gross/net thành nhóm riêng, không gộp với gross/net đã nêu rõ.
- ADR 0007: thu nhập tháng chào tuyển được chấp nhận thành phạm vi riêng, không tự coi là lương cơ bản. Hai tin YODY dùng phạm vi này, basis unknown; thưởng cuối năm tách riêng.

## Cách kiểm và truy vết

MarketService.preview xác minh SHA raw mới và schema trước khi đọc. Với YODY, hai đầu/currency từ salary được đối chiếu độc lập với hai đầu/period trong đoạn nguyên văn của job_requirements, cùng record và ID; cả hai khoảng khớp. Trung điểm tính từ hai đầu, không lấy salary_avg bên phát hành. Lưu nguyên raw salary, đoạn chứng cứ, phép bỏ HTML/unescape/chuẩn hóa whitespace và row hash. Mỗi ID xuất hiện đúng một lần, mỗi nhóm theo trường quan sát có một dòng trong nguồn 2023; hai nhóm khác nhau. Đây chưa là near-duplicate audit toàn thị trường.

Metadata [Kaggle chính chủ](https://www.kaggle.com/api/v1/datasets/view/lucaznguyenofficial/vietnamese-job-posting-vietnamese-version) đọc lại: revision 2, khai báo CC0; hash metadata 326fad5c445b55fb2409b66e5def2a5ed2ef98595350b7076df760d227dd7402. Nguồn raw có hash trong manifest, đã thuộc catalog EDA được duyệt. Không tuyên bố live page CareerBuilder được xác nhận lại: trang đó không truy cập được; chứng cứ là snapshot có hash.

External được kiểm riêng trong EXTERNAL_CANDIDATE_REVIEW-2026-10-29.md: pin GitHub revision, kiểm lại raw/row/description hash và offsets, phân biệt snapshot date với posting date, tra bản trùng/phiên bản và đọc các primary page truy cập được. Main đối chiếu lại các hash/offset, không sao chép role/skill do LLM của publisher gán. Phạm vi educational của GitHub được ghi nhận, không biến việc thiếu LICENSE thành kết luận cấm hoàn toàn; source admission và redistribution còn chưa giải quyết. Các trang chỉ đọc public, không liên hệ publisher hoặc vượt chặn.

## Điều kiện trước khi huấn luyện

Hai accepted cùng một công ty, một nghề, một ngày đăng 20/02/2023, thuộc hai nhóm tin quan sát. Hai nhóm không đủ ba tập train/validation/test độc lập và không rỗng. Không đặt ngưỡng mẫu tùy tiện hoặc fit để lách điều kiện này. Còn phải mở rộng số nhóm có nhãn, chốt phần còn lại của #4/#5 và triển khai nhập chứng cứ có kiểm soát.

File accepted_labels.csv là đầu ra kiểm duyệt riêng, canonical_imported=false; base pipeline eda-v5 vẫn 0 target từ salary. Gate #42 giữ mở, chưa có metric/model/dự đoán mới. Chấp nhận nhãn là bước tiến về bằng chứng, không phải nghiệm thu ML.

## Kiểm chứng đầu ra

Đã đọc lại JSON và cả hai CSV: đủ 26 review_id duy nhất, 2 accepted/17 needs_review/7 excluded; chỉ hai accepted có salary_target_vnd_month. Hash/byte count các file khớp manifest. Đối chiếu lại hai ID, URL, số record và row hash với raw đã pin; normalize riêng salary và đoạn kỳ tháng cho cùng hai đầu, currency VND và period MONTH có bằng chứng khác trường trong cùng tin. Trung điểm khớp 27.500.000 và 37.500.000. Bảng accepted giữ unknown basis và phạm vi advertised_monthly_income, không nhập canonical.

Kiểm tra base salary_report vẫn target_n=0; liên kết Markdown local và git diff --check qua. Không sửa code ứng dụng nên không chạy lại suite 246 tests chỉ để lặp số đếm. Không công bố metric ML hoặc hosted CI mới cho lượt dữ liệu/tài liệu này.
