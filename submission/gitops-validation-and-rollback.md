# Kubernetes và GitOps

Manifest có Deployment, Service, ServiceAccount, resource requests/limits, readiness/liveness/startup probe, HPA, PodDisruptionBudget, NetworkPolicy và Gateway API. Argo CD khai báo sync tự động và self-heal. Repo nguồn của Application đã được đổi sang fork của học viên.

```text
uv run python scripts/validate_manifests.py
```

Kết quả lệnh chỉ xác nhận các hợp đồng tĩnh của manifest. Máy hiện chưa có Kubernetes context để chạy phần triển khai, drift/self-heal và rollback; phần live này chưa được xác nhận.

Application đã ghim revision `b3c323daec70e6444b393c017b9d47e66c65a0f7`, là commit chứa mã và hồ sơ hoàn chỉnh trên fork. Khi triển khai thật, image cũng phải được build từ revision tương ứng. Việc đổi image/revision trong Git, sync và kiểm tra pod/gateway là rollback triển khai; chuyển alias champion trong MLflow là rollback release mô hình. Hai thao tác cần được giải thích riêng.

Kịch bản drift/rollback: lưu desired revision và image, sync Argo CD, kiểm tra health; tạo một drift có thể đảo ngược và quan sát self-heal; đưa desired state về phiên bản trước trong Git, sync rồi kiểm tra lại health và request qua gateway. Không ghi nhận kịch bản này là đã chạy nếu chưa có log hoặc ảnh tương ứng.
