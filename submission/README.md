# Bài nộp — Modern AI Platform Integration Lab

**Nguyễn Quang Hà — 2A202601424 · Track 2, Day 28 · Bài cá nhân**

Repo nộp: [quangha-dev/TRACK2_Day28_2A202601424_NguyenQuangHa](https://github.com/quangha-dev/TRACK2_Day28_2A202601424_NguyenQuangHa), nhánh `main`.

## Cách áp dụng hướng dẫn repo

**Đánh giá hướng dẫn:** Hướng dẫn quá khó hiểu: trong codelab yêu cầu tạo nhánh trên repo gốc, nhưng trên Discord lại yêu cầu fork repo.

## Kết quả đã xác nhận

| Phần | Kết quả thực tế |
| --- | --- |
| Unit/starter/repository tests | 95 passed |
| J1 golden path | 12 passed, 3 deselected |
| J2 idempotent replay | 9 passed |
| Integration không GPU/LangSmith | 56 passed, 16 deselected |
| Integration matrix | 245 checks passed |
| Ruff, portability, manifests | exit code 0 |
| Load `/ready`, 200 request | Đã chạy ở 8 và 16 workers; 429 được phân tích riêng |
| vLLM thật | v0.28.0, Qwen/Qwen2.5-0.5B-Instruct, 349 metric `vllm:` |

Test gốc không bị sửa. J1 và J2 được chạy lại sau khi sửa consumer đợi Kafka partition assignment; bằng chứng cho thấy Delta replay không tăng số hàng. J3 ghi promotion/rollback alias champion. J4 ghi sự cố tùy chọn, bắt buộc, DLQ và khôi phục. IP09 có hai đầu ra nên bộ nộp gồm **11 JSON cho 10 integration point**.

vLLM đã được xác minh bằng `/version`, `/v1/models`, `/metrics`, log runtime và hash trọng số. Theo quyết định chốt bài ngay, GPU integration/inference không được chạy lại sau khi server sẵn sàng; vì vậy các assertion completion và serving trace vẫn được ghi là chưa xác nhận. LangSmith và triển khai Kubernetes live cũng chưa xác nhận do thiếu credential/context. Kiểm tra manifest/GitOps tĩnh đã đạt.

## File chính

- `ANSWERS.md`: báo cáo kỹ thuật, vai trò và reflection.
- `docs/architecture-ownership.md`: sơ đồ, IP01–IP10 và trách nhiệm từng vùng.
- `submission/evidence/`: 11 file evidence IP và các hành trình J1–J4.
- `submission/logs/`: log test/lint/validation/runtime đã dùng làm căn cứ.
- `submission/failure-recovery-record.md`: sự cố, dấu hiệu, nguyên nhân và khôi phục.
- `submission/load-profile-analysis.md`: phân tích đo tải.
- `submission/gitops-validation-and-rollback.md`: phạm vi K8s/GitOps và rollback.
- `submission/vllm-local.md`: lựa chọn model và bằng chứng vLLM thật.
- `submission/manifest.json`: hash và trạng thái file trong bundle.

Không đưa `.venv/`, `.lab28/`, `.git/`, cache, database, token, URL tạm hoặc model weights vào Git/ZIP. Bundle nộp là `Day28_NguyenQuangHa.zip` ở thư mục gốc.
