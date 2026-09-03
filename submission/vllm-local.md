# vLLM trên GPU local

Model chọn cho RTX 3050 Laptop 4 GB là **Qwen/Qwen2.5-0.5B-Instruct**, revision `7ae557604adf67be50417f59c2c2f167def9a775`. Model có 0,49 tỷ tham số và hỗ trợ tiếng Việt. Đây là lựa chọn nhẹ hơn cấu hình mặc định Qwen3-1.7B; ví dụ Kaggle dùng Qwen3-4B. Tài liệu và test của repo kiểm tra model ID khớp cấu hình, không bắt buộc một kích thước model duy nhất.

Nguồn: [model card của Qwen](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct), [hướng dẫn giảm bộ nhớ của vLLM](https://docs.vllm.ai/en/latest/configuration/conserving_memory/).

Môi trường cài riêng trên Ubuntu WSL2, Python 3.12 và vLLM 0.28.0. Script `scripts/start_vllm_small.sh` dùng trọng số local đã tải đúng revision, FP16, context 2048 token, tối đa một sequence, batch prefill 512 token và tắt CUDA graph. MLflow chạy một worker để giảm RAM của toàn bộ stack.

Trọng số `model.safetensors` có 988.097.824 byte và SHA-256 `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`, khớp metadata của snapshot đã ghim. vLLM khởi động thành công, báo phiên bản `0.28.0`, model ID `Qwen/Qwen2.5-0.5B-Instruct`; endpoint metrics có 349 dòng bắt đầu bằng `vllm:`. WSL không cung cấp UVA nên script dùng runner V1 được vLLM hỗ trợ và tắt FlashInfer sampler cần NVCC; server vẫn là vLLM thật và dùng FlashAttention 2 cho attention.

Các giá trị trên nằm trong `evidence/ip07-vllm-identity.json` và log runtime. Bộ GPU integration/inference không được chạy lại sau khi server sẵn sàng theo quyết định chốt bài ngay, nên báo cáo không coi serving trace hay completion là đã xác nhận.

Trọng số nằm trong `.lab28/vllm-model/`; môi trường Python GPU và cache nằm ngoài mã nguồn. Các thư mục này không thuộc gói nộp. `ports.local` chỉ giữ cấu hình chạy trên máy, được Git ignore.
