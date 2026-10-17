# ECC architecture audit — 18/10/2026



## Findings (trước sửa, theo mức độ)



### A01 · high · Worker Gemma thiếu hợp đồng gắn từng dòng

Triệu chứng/cơ chế: Thiếu/thừa/đảo kết quả vẫn được zip, có thể bỏ mất hoặc ghép nhầm trường.

Gốc lỗi: List JSON không có request identity, cardinality/index/hash; stderr bị bỏ khi lỗi. Lớp: 8 tool interpretation; confidence 1.0.

Bằng chứng sau sửa: `backend/app/services/gemma.py:37`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Typed batch v1, xác minh request_id/index/hash/số dòng, giữ raw và diagnostic; không repair.



### A02 · high · Snapshot đầu vào và provenance không gắn với lần chạy

Triệu chứng/cơ chế: Sửa dataset.json vẫn giữ input SHA cũ; chọn Gemma nhưng không chạy vẫn gán adapter.

Gốc lỗi: Không có checksum canonical snapshot; manifest đọc metadata trên đĩa khi export thay vì model đã nạp. Lớp: 12 persistence; confidence 1.0.

Bằng chứng sau sửa: `backend/app/services/store.py:121`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Hash snapshot có phiên bản; từ chối dữ liệu đổi/legacy khi submit. Ghi provenance loaded salary và worker thực sự đã chạy.



### A03 · high · Hàng đợi phân tích không giới hạn

Triệu chứng/cơ chế: POST lặp giữ các dataset/job trong hàng đợi không giới hạn dù chỉ một worker.

Gốc lỗi: ThreadPoolExecutor dùng SimpleQueue mà không có admission limit. Lớp: 7 tool execution; confidence 1.0.

Bằng chứng sau sửa: `backend/app/services/store.py:25`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Tối đa 2 job đang chạy/chờ, trả 429 + Retry-After; trả slot cả khi phân tích lỗi.



### A04 · medium · Một state JSON hỏng chặn khởi động

Triệu chứng/cơ chế: recover() ném JSONDecodeError trước khi server sẵn sàng.

Gốc lỗi: Tin persisted state mà không validate hoặc cô lập từng job. Lớp: 12 persistence; confidence 1.0.

Bằng chứng sau sửa: `backend/app/services/store.py:28`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Validate JobState/ID; giữ state.corrupt riêng và đánh dấu failed; completed hợp lệ còn nguyên.



### A05 · medium · Báo cáo kỹ năng được dùng như dữ kiện chưa kiểm chứng

Triệu chứng/cơ chế: CSV hệ số/số mẫu và train sửa tay có thể làm sai giải thích tư vấn.

Gốc lỗi: Chỉ checksum joblib, chưa checksum train; tin derived CSV thay vì fitted pipeline. Lớp: 4 distillation; confidence 1.0.

Bằng chứng sau sửa: `backend/app/services/salary.py:35`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Verify frozen manifest/train và nạp cùng bytes đã hash; tái tạo coefficients/support từ Ridge + train; enforce support >=5.



### A06 · medium · Giao diện giữ hoặc ghép phản hồi cũ

Triệu chứng/cơ chế: Hồ sơ đổi vẫn hiện lương cũ; response đến muộn có thể ghi đè trang mới.

Gốc lỗi: Không ràng buộc response với revision/profile/job đang hiển thị. Lớp: 10 platform rendering; confidence 1.0.

Bằng chứng sau sửa: `frontend/src/App.vue:30`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Xóa advice khi edit và revision-gate advice/poll/pagination; browser kiểm tra bằng giữ/release response thật.



### A07 · medium · Kiểm tra tiến trình không khóa GPU

Triệu chứng/cơ chế: Hai lệnh có thể cùng vượt qua pgrep trước khi nạp model.

Gốc lỗi: Time-of-check/time-of-use, không có mutual exclusion giữa managed commands. Lớp: 7 tool execution; confidence 0.99.

Bằng chứng sau sửa: `scripts/gpu_lock.py:11`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Khóa file nonblocking chung app worker/train/infer/evaluate generate; plan/scoring không chiếm GPU.



### A08 · medium · JSON/XLSX mơ hồ và schema LLM thiếu ràng buộc

Triệu chứng/cơ chế: JSON duplicate key bị ghi đè, NaN được nhận; pandas tự đổi tên cột Excel trùng.

Gốc lỗi: Parser mặc định và schema type-only không kiểm tra quan hệ trường. Lớp: 9 answer shaping; confidence 1.0.

Bằng chứng sau sửa: `backend/app/services/contracts.py:12`; trước sửa: Git `3eb9fe3` cùng file và `before.json`.

Đã sửa/kiểm chứng: Từ chối duplicate/nonfinite, check header Excel gốc; schema app strict và salary null coherence. Không sửa historical evaluator/test metrics.



## Chẩn đoán kiến trúc



- Lớp 1: Single shared SYSTEM + one user card; no extra prompt duplication observed.

- Lớp 2: No conversation history is sent to Gemma.

- Lớp 3: No long-term memory exists in the app.

- Lớp 4: Derived skill CSV was a pseudo-fact path; now recomputed from verified train + fitted Ridge.

- Lớp 5: No recall/re-summary layer.

- Lớp 6: Gemma optional explicit flag; description-only now requires Gemma in API too. Salary always uses fixed fitted model.

- Lớp 7: Real MLX subprocess with exit check, bounded queue and managed GPU lock.

- Lớp 8: Typed per-row batch contract prevents silent zip loss/misalignment.

- Lớp 9: Strict JSON and original raw output; no hidden coercion/JSON repair.

- Lớp 10: Profile/job/page response revisions fence stale UI.

- Lớp 11: No second LLM, repair prompt or silent retry observed. Row extraction errors are explicit.

- Lớp 12: Versioned input snapshots, quarantined corrupt jobs, actual loaded model/worker provenance.



## Thứ tự thực hiện



1. A01: Typed batch v1, xác minh request_id/index/hash/số dòng, giữ raw và diagnostic; không repair.

2. A02: Hash snapshot có phiên bản; từ chối dữ liệu đổi/legacy khi submit. Ghi provenance loaded salary và worker thực sự đã chạy.

3. A03: Tối đa 2 job đang chạy/chờ, trả 429 + Retry-After; trả slot cả khi phân tích lỗi.

4. A04: Validate JobState/ID; giữ state.corrupt riêng và đánh dấu failed; completed hợp lệ còn nguyên.

5. A05: Verify frozen manifest/train và nạp cùng bytes đã hash; tái tạo coefficients/support từ Ridge + train; enforce support >=5.

6. A06: Xóa advice khi edit và revision-gate advice/poll/pagination; browser kiểm tra bằng giữ/release response thật.

7. A07: Khóa file nonblocking chung app worker/train/infer/evaluate generate; plan/scoring không chiếm GPU.

8. A08: Từ chối duplicate/nonfinite, check header Excel gốc; schema app strict và salary null coherence. Không sửa historical evaluator/test metrics.



## Bằng chứng kiểm chứng và giới hạn



55 unit/integration tests đạt; Ruff 42 file, Prettier và build đạt. API CSV/XLSX/JSON và một mẫu Gemma GPU thật → RF đạt. Browser giữ response thật rồi trả ngược thứ tự để kiểm tra advice/pagination. Ảnh giao diện Gemma thật: `gemma_web.png`. Chỉ suy luận chức năng, không train hay chấm lại benchmark test.



Split/JSONL/checksum model đã chốt giữ nguyên. Không suy diễn rằng sửa wrapper làm giảm MAE. Các giới hạn:

- Local single-user demo, not a production security/load audit.

- Managed file lock does not cover direct external mlx_lm commands or legacy already-running processes.

- Input/worker checks establish structure and provenance, not semantic extraction accuracy.

- Historical salary MAE remains 6.656M VND/month on 28 silver test jobs; this audit did not retrain or reduce it.

- User requested a separate new-data training cycle after this audit; no new model quality claims here.
