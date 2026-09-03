# Kết quả đo tải

Đo GET `/ready` qua Envoy ngày 03/09/2026 (UTC), mỗi cấu hình 200 request sau 5 request warm-up. Đây là phép đo readiness và giới hạn tốc độ của gateway. vLLM thật được nối sau phép đo, nhưng benchmark `/api/v1/ask` không được chạy lại khi chốt bài.

| Workers | HTTP 200 | HTTP 429 | Lỗi | RPS tổng | RPS thành công | P50 / P95 / P99 thành công (ms) |
|---|---:|---:|---:|---:|---:|---|
| 8 | 35 | 165 | 82.5% | 69.16 | 12.10 | 420.08 / 1731.98 / 1755.06 |
| 16 | 12 | 188 | 94.0% | 306.14 | 18.37 | 525.34 / 644.55 / 644.55 |

Nút thắt quan sát được là token bucket của Envoy. Phần lớn request bị từ chối sớm bằng 429, nên RPS tổng cao và P50 của tất cả request thấp không chứng minh API nhanh. Đặc biệt cấu hình 16 workers chỉ có 12 mẫu thành công; percentile của nhóm này chưa đủ để suy rộng thành SLO.

Hai lần đo là burst ngắn, chạy trên cùng máy với các dịch vụ lab. Trạng thái token bucket lúc bắt đầu và tải nền ảnh hưởng kết quả; chưa thể kết luận tăng gấp đôi workers làm hệ thống xử lý nhanh hơn. Để đánh giá năng lực phục vụ cần thêm phép đo kéo dài, kiểm soát tốc độ gửi và đo riêng `/ask` với vLLM thật.

Công cụ ghi HTTP status thật, lỗi mạng dưới mã 0, percentile của mọi request và percentile riêng cho request thành công. Số liệu gốc: [8 workers](load-8.json), [16 workers](load-16.json); log chứa lệnh và thời gian trong thư mục `logs/`.

```powershell
uv run python load-tests/run_profile.py --requests 200 --workers 8 --warmup 5 --output submission/load-8.json
uv run python load-tests/run_profile.py --requests 200 --workers 16 --warmup 5 --output submission/load-16.json
```

Khi có vLLM, chạy lại với `--endpoint /api/v1/ask`, giữ model/prompt/collection cố định và ghi rõ lượt làm nóng. Không dùng con số đánh giá do fixture J3 cung cấp làm benchmark thực nghiệm.
