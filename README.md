# Data Mesh Learning Environment

一个完整的 Data Mesh MVP 学习环境，包含数据目录、联邦查询、数据编排和可视性。

## 快速开始

```bash
# 启动所有服务
./scripts/start.sh all

# 或分别启动
./scripts/start.sh stack1  # 数据平台核心
./scripts/start.sh stack2  # 可观测性和开发者门户

# 对于 Colima 用户 (macOS ARM)：需要启动端口转发
./scripts/port-forward.sh
```

## macOS ARM (Apple Silicon) 注意事项

如果你使用的是 Colima 而不是 Docker Desktop，需要手动设置端口转发才能从 localhost 访问服务：

```bash
# 启动端口转发
./scripts/port-forward.sh

# 停止端口转发
pkill -f 'ssh.*colima.*-L'
```

---

### Test Comment

This is a test comment for verifying the PR verification workflow.
