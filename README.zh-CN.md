# jcheng-benchmark

JCHENG Robotics 生态的离线、只读基准测试工具。它声明基准套件，读取由能力仓或系统仓导出的录制 JSONL 数据集，计算预先注册的指标并生成带来源标注的报告。它不加入 DDS、不打开设备、不读取传感器、不发送运动命令。

> 状态：**实验性**，截至 2026-11-26。版本 0.1.0。仓库不附带任何基准数据集或结果；工具只用合成数据自测，因此不作出精度、时延或硬件方面的结论。
> 本文为英文主文档的中文对照；如有歧义，以 [README.md](README.md) 为准。

## 范围与边界

| 项 | 本仓库 |
|---|---|
| 层 | BENCH — 不在运行时依赖图中（见 [`.github` `docs/repo-taxonomy.md`](https://github.com/JCHENG-Robotics/.github/blob/main/docs/repo-taxonomy.md)） |
| 输入 | 套件 YAML 声明、录制 JSONL 数据集、命令行来源字段 |
| 输出 | JSON 基准报告与 Markdown 渲染 |
| 硬件访问 | `none`（`capability.yaml`） |
| 拥有设备 | 无 |
| 运动权限 | `none`；`control_path: none` |
| 禁止 | 加入 DDS/ROS、打开设备、发送运动命令、修改测量数据、把合成结果表述为硬件结果 |

本仓库**不是**运行时能力。没有产品仓导入它，它不在 `ecosystem.lock.yaml` 中，也没有通往机器人的路径。它是测量工具：文件进，报告出。

## 为什么存在

过去基准数字由各仓自行产生，样本格式、聚合规则和来源说明各不相同，导致横向比较脆弱，合成运行也容易滑向硬件结论。

本仓库固定三件事：

1. **先声明套件，再采集数据。** 指标、最小样本数和门限先写清楚，然后才采集数据。
2. **数据用哈希标识，不复制进仓。** 每份报告记录数据集 SHA-256、套件 SHA-256、操作者、主机和时间；大体积录制留在仓外。
3. **结果按层级和数据来源标注。** 合成或 mock 运行永远不是硬件结果，基准通过也永远不是安全认证。

完整规则见 [docs/BENCHMARK_PROTOCOL.md](docs/BENCHMARK_PROTOCOL.md)。

## 测量内容

| 指标类型 | 每个样本的输入 | 输出 |
|---|---|---|
| `position_error` | `measured_m` 与 `reference_m`，均为米制 `[x, y, z]` | 逐样本欧氏误差（毫米），再计算 mean/p50/p95/max/min |
| `scalar` | 一个有限数值字段，例如 `latency_ms` | 按声明单位计算 mean/p50/p95/max/min |
| `success_rate` | 一个布尔字段，默认 `success` | 真值计数除以样本数 |

百分位采用最近秩定义，不依赖插值库。任何一行格式错误都会中止运行，不会静默丢弃。

## 仓库结构

```text
jcheng-benchmark/
├── capability.yaml          # 准入清单：BENCH 层、无硬件访问
├── benchmarks/
│   ├── README.md            # 套件目录与编写说明
│   └── suites/              # 预先注册的套件声明（模板）
├── docs/
│   ├── ARCHITECTURE.md      # 信任边界与组件
│   ├── BENCHMARK_PROTOCOL.md# 预注册、层级、格式、结果规则
│   └── EVIDENCE.md          # 报告存储与不可变性
├── evidence/                # 处理真实数据集后的报告
├── src/jcheng_benchmark/    # 无 ROS 依赖的 runner、模型、统计、CLI
├── scripts/check_repo_gate.sh
└── tests/                   # 单元、CLI、报告与边界测试
```

## 依赖

- Python 3.10 或更新版本（本机 3.12；CI 覆盖 3.10 与 3.12）。
- 运行时依赖 `PyYAML` 6.x；测试依赖 `pytest` 7.4+。
- 不需要 ROS 发行版、DDS 中间件、相机、串口、CAN 或 GPIO 设备，也不需要机器人访问权限。

## 快速开始

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[test]'

# 查看并校验随仓发布的声明。
jcheng-benchmark list --dir benchmarks/suites
jcheng-benchmark validate --spec benchmarks/suites/template-position-accuracy.yaml

# 用仓内合成夹具运行工具自测。
# 这是自测，不是基准结果。
jcheng-benchmark run \
  --spec tests/fixtures/synthetic/suite.yaml \
  --data tests/fixtures/synthetic/samples.jsonl \
  --operator self-test \
  --json /tmp/benchmark-report.json \
  --markdown /tmp/benchmark-report.md

# 等价于 CI 的检查。
python3 -m pytest -q
bash scripts/check_repo_gate.sh
```

所有声明的门限通过时退出码为 `0`；门限失败为 `1`；结果不确定或输入非法为 `2`。退出码 `0` 表示“在声明的数据来源下通过了声明的门限”，不表示“已通过硬件验证”。

## 验证状态

| 结论 | 状态 | 证据 |
|---|---|---|
| 套件、样本与门限校验会拒绝非法输入 | 部分验证（合成） | `tests/test_runner.py`、`tests/test_cli.py` |
| 位置、标量与成功率指标会计算声明的聚合值 | 部分验证（合成） | `tests/test_stats.py`、`tests/test_runner.py` |
| 报告记录层级、数据来源、操作者、主机和两个 SHA-256 | 部分验证（合成） | `tests/test_reports.py`、gate 中的合成自测 |
| 已运行过录制数据回放套件 | 未验证 | 仓内没有数据集；M2 尚未开始 |
| 已运行过硬件基准 | 未验证 | 设计上无硬件访问 |

完整报告：[ACCEPTANCE.md](ACCEPTANCE.md)。状态词汇遵循组织[文档标准](https://github.com/JCHENG-Robotics/.github/blob/main/docs/documentation-standard.md)。

## 基准层级

| 层级 | 环境 | 允许的数据来源 |
|---|---|---|
| L0 | 契约/静态 | 不适用 |
| L1 | 单元 | `synthetic` 或 `mock` |
| L2 | Mock 集成 | `synthetic` 或 `mock` |
| L3 | Mock 端到端 | `synthetic` 或 `mock` |
| L4 | 回放 | `recorded`（或直接硬件录制的 `hardware`） |
| L5 | 硬件 | `hardware` |

加载器会拒绝“L4 + 合成/mock 数据”和“L5 + 非 hardware 数据”。

## 相关仓库

- [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) — 契约来源；本仓库不定义跨仓契约。
- [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) — 固定点、跨视角与时延录制的来源。
- [`jcheng-mobile`](https://github.com/JCHENG-Robotics/jcheng-mobile) — 激光里程计、SLAM 与 Nav2 录制的来源。
- [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) — Mock 端到端与安全路径录制的来源。
- [`jcheng-ops`](https://github.com/JCHENG-Robotics/jcheng-ops) — 运维；不是基准消费者。
- [`.github`](https://github.com/JCHENG-Robotics/.github) — 生态路线图、变更日志、验收与分类。

## 许可

**待定。** 本仓库没有 `LICENSE` 文件；第三方与版权审查尚未关闭。详见 [LICENSE-REVIEW.md](LICENSE-REVIEW.md)。运行时依赖为 PyYAML（MIT），测试依赖为 pytest（MIT）。
