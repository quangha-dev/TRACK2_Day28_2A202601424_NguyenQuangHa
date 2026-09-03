# Báo cáo kỹ thuật — Track 2, Day 28

Học viên: **Nguyễn Quang Hà — 2A202601424**. Bài làm cá nhân trên repo fork `quangha-dev/TRACK2_Day28_2A202601424_NguyenQuangHa`, nhánh nộp `main`.

Codelab trên web hướng dẫn tạo nhánh trong repo private của tổ chức, trong khi thông báo cập nhật trên Discord yêu cầu học viên fork repo rồi làm bài. Bài này làm theo hướng dẫn Discord và nộp nhánh `main` của fork; giảng viên đã cho phép dùng fork hiện tại. Sự khác nhau chỉ nằm ở nơi lưu mã. Toàn bộ hợp đồng kỹ thuật, integration matrix và danh sách bằng chứng vẫn được giữ nguyên.

## Phần thực hiện

Bài lab nối luồng tiếp nhận dữ liệu, xử lý theo lô, dữ liệu phục vụ và giám sát. Các thành phần nền tảng được kế thừa từ scaffold; phần bài làm hoàn thiện bốn hàm trong `integration_tasks.py` và bổ sung công cụ thu bằng chứng, đo tải, đóng gói hồ sơ.

| Hàm | Cách xử lý |
|---|---|
| `event_headers` | Luôn mã hóa `idempotency-key` thành bytes; chỉ thêm `traceparent` khi có giá trị |
| `dedupe_latest` | Duyệt đầu vào một lần, giữ event lớn nhất theo `(occurred_at, event_id)` cho mỗi khóa, trả kết quả theo thứ tự khóa |
| `feast_online_request` | Dùng `FEATURE_REFS` làm nguồn tên feature, gửi `asker_id` dưới dạng danh sách và tắt full feature names |
| `readiness_status` | Lỗi bắt buộc tạo `not_ready`; chỉ lỗi tùy chọn tạo `degraded`; còn lại là `ready` |

Các cải tiến bổ sung gồm CI dành cho bài đã hoàn thiện trên fork, loại runtime khỏi Docker build context, đọc RAM trên Windows, ghi nguồn phiên bản vào release MLflow và xuất đầy đủ signature của release. Công cụ đo tải hỗ trợ cả GET `/ready` lẫn POST `/api/v1/ask`, phân biệt lỗi mạng với HTTP 429/503 và tách percentile của request thành công. Bổ sung retry hữu hạn cho seed khi Envoy trả 429 và sửa consumer chờ Kafka assignment trước khi kết luận lô rỗng. Các test gốc được giữ nguyên.

## Lựa chọn và đánh đổi

**Kafka làm vùng đệm.** API trả 202 khi đã tiếp nhận event; dữ liệu phục vụ được cập nhật sau khi pipeline xử lý. Cách này tách tốc độ tiếp nhận khỏi xử lý theo lô và cho phép đọc lại log còn trong retention. Đổi lại, một request được chấp nhận chưa có nghĩa Feast hoặc Qdrant đã cập nhật ngay.

**Khử trùng trước khi MERGE.** Với n event và k khóa, `dedupe_latest` cần O(n) để chọn bản mới nhất, O(k log k) để sắp xếp và O(k) bộ nhớ. Khóa ghép bảng Delta là `idempotency_key`; `event_id` dùng để nhận diện từng lần phát sinh và phá hòa khi timestamp bằng nhau. Việc chống trùng trong một lô được kiểm tra bằng unit test; hành vi ghi/đọc trên Delta được kiểm tra bằng J2. MERGE hiện chưa so thời gian với dòng đích, nên xử lý event cũ đến ở lô sau là một hướng cải tiến riêng.

**Tách đường dữ liệu.** Delta giữ lịch sử có phiên bản; Feast phục vụ feature theo `asker_id`; Qdrant phục vụ tìm tài liệu. Cách tách này giúp hợp đồng đọc rõ ràng nhưng cần theo dõi freshness và version để phát hiện cập nhật chậm. Các ngân sách độ trễ trong cấu hình là mục tiêu, không tự trở thành số đo đạt được.

**Readiness không thay cho liveness.** `/health` không gọi phụ thuộc ngoài. `/ready` phân loại phụ thuộc theo mức bắt buộc. Feast có thể suy giảm mà API vẫn nhận request. Với vLLM, mức bắt buộc của probe phụ thuộc `LAB28_VLLM_REQUIRE_REAL`; dù core có thể degraded khi thiếu vLLM, `/ask` vẫn cần inference thật và sẽ báo lỗi nếu endpoint không hoạt động. Envoy trong Compose kiểm tra upstream bằng `/health`, còn Kubernetes dùng `/ready` làm readiness probe.

**MLflow quản lý release.** Alias `champion` chọn bộ cấu hình prompt/retrieval đang phục vụ; đổi alias giúp promotion và rollback mà không sửa mã API. Release cần có version, run ID, nguồn dữ liệu, model ID và nguồn mã để đối chiếu. `lab28.source_sha256` nhận diện snapshot source; nếu có Git, release còn ghi commit và tình trạng working tree.

## Trách nhiệm trong bài cá nhân

| Vai trò | Phạm vi chịu trách nhiệm |
|---|---|
| Ingestion & Orchestration | Hợp đồng event, header Kafka, retry/commit, DLQ và DAG |
| Data & ML | Khử trùng, Delta version, Feast request/materialization và release MLflow |
| Serving & Retrieval | Qdrant point ID, kết quả tìm kiếm, vLLM identity và lỗi inference |
| Platform & Observability | Gateway, readiness, metrics, trace, cấu hình K8s/GitOps |
| Presenter | Tập hợp bằng chứng, giải thích sự cố, số đo và giới hạn của lần chạy |

Kết quả thực thi của từng phần được ghi trong `submission/README.md` và log đi kèm. Phần core đã được kiểm chứng bằng 95 test nhanh và 56 integration test không phụ thuộc GPU/LangSmith. vLLM 0.28.0 thật đã nạp Qwen/Qwen2.5-0.5B-Instruct trên RTX 3050; `/version`, `/v1/models` và 349 dòng metric mang tiền tố `vllm:` đã được đối chiếu. Theo quyết định chốt bài để nộp ngay, bộ GPU integration không được chạy lại, vì vậy báo cáo không nhận các assertion inference/serving trace này là đã đạt. LangSmith cũng được ghi UNVERIFIED vì không có credential và exporter phù hợp.

## Reflection

Phần khó nhất về kỹ thuật là giữ đúng ý nghĩa của từng định danh khi dữ liệu đi qua nhiều giao thức. `event_id`, `idempotency_key` và `trace_id` phục vụ ba mục đích khác nhau; nếu dùng lẫn, một kiểm thử nhỏ có thể đạt nhưng bằng chứng toàn luồng lại không khớp.

Lựa chọn đáng giữ lại là đưa logic khử trùng vào một hàm thuần. Có thể kiểm tra thứ tự, timestamp bằng nhau và dữ liệu replay mà không phải chờ dựng toàn nền tảng. Sau đó vẫn cần test live để xác nhận consumer commit và Delta MERGE làm đúng.

Nếu triển khai tiếp, ưu tiên xử lý dữ liệu đến muộn, sao lưu/khôi phục dữ liệu và quan sát freshness giữa Delta, Feast, Qdrant. Kafka một broker và lưu trữ local phù hợp bài thực hành nhưng chưa đủ dự phòng cho sản xuất. Với DLQ, chỉ phát lại sau khi sửa nguyên nhân, tránh vòng lặp cùng một payload lỗi.
