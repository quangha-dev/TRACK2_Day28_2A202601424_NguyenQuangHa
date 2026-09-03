# Sự cố và khôi phục

Lần chạy ngày 03/09/2026 được ghi bằng integration test trên Kafka, Airflow, Spark/Delta, Feast và Qdrant thật. Hồ sơ gốc nằm trong `evidence/j4-*.json`; log `logs/integration-non-gpu.txt` có lệnh, thời gian và kết quả.

## Phụ thuộc phục vụ bị dừng

Trước thử nghiệm, API trả HTTP 200 và trạng thái `degraded` vì chưa có vLLM. Test dừng Feast, kiểm tra probe báo lỗi nhưng API vẫn giữ HTTP 200; sau khi khởi động lại, probe Feast phải phục hồi. Khi dừng Qdrant, thành phần bắt buộc, test xác nhận HTTP 503 và `not_ready`. Các context manager luôn gọi start trong `finally`.

Sau khôi phục, API trả HTTP 200 và `degraded`, trùng trạng thái nền. Chưa thể suy ra hệ thống có câu trả lời LLM từ phép kiểm tra readiness này. Bằng chứng: [trạng thái và kết quả test](evidence/j4-dependency-recovery.json).

## Bản tin hỏng trong Kafka

Dự đoán trước khi thử: JSON hỏng phải đi vào DLQ kèm tọa độ Kafka và nguyên nhân; bản tin hợp lệ cùng lô vẫn phải được ghi Delta. J4 chủ động gửi một JSON bị cắt cùng phản hồi của entity `it-j4-14adf37c`.

DAG `it-bd9b5c92` kết thúc `success`. Số dead letter tăng từ 0 lên 1; bản tin hợp lệ có đúng 1 dòng ở Delta. Envelope lưu topic, partition, offset, key và lỗi validation để điều tra. Đây là bằng chứng đọc lại dữ liệu, không chỉ trạng thái DAG.

Để kiểm tra thao tác replay, test đưa một event hợp lệ đã đọc từ Kafka vào DLQ với lý do thử nghiệm. Lệnh replay phát lại 1 event và bỏ qua 1 payload không hợp lệ. Run `it-5b526898` thành công; khóa `fb:it-j4-replay-ddecc3a2:3851e21afa21521407904e03cb7471fd` còn đúng 1 dòng trong Delta. [Bản tin hỏng và dòng tốt](evidence/j4-poison-batch.json), [replay và dòng sau khôi phục](evidence/j4-dlq-replay.json).

Không dùng reset, xóa volume hoặc dựng lại database để tạo kết quả khôi phục. Phép thử chứng minh các event được chọn không bị mất/trùng; chưa phải diễn tập phục hồi sau mất máy hoặc mất toàn bộ vùng lưu trữ.

## Lỗi phát hiện khi dựng hệ thống

Lần J1 đầu tiên báo DAG success nhưng chưa có bảng Delta: consumer hết ba lần poll rỗng trước khi được Kafka gán partition. Sửa mã để chờ assignment có timeout, sau đó chỉ dừng khi số poll rỗng liên tiếp đạt ngưỡng. Ba regression test mới kiểm tra việc chờ assignment, reset bộ đếm idle và lỗi timeout. J1 chạy lại đạt 12 test và J2 đạt 9 test; test gốc không bị sửa.
