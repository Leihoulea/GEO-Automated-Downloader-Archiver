# GEO 自动化下载与归档器 版本审计报告

- 报告日期：2026-09-02
- 审计范围：源仓库 `D:\AAAresearch_paper`，分支 `codex/governance-recovery-20260812`
- 审计区间：`e02c2776`（2026-08-20 功能基线）至 `ab7363af`（2026-08-26 当前 HEAD）
- 审计方法：逐提交阅读 `git show` 代码差异，核对 blob SHA，比对测试函数清单，不依赖提交标题或正文（所有提交均无正文）。
- 审计人：opencode agent
- 审计状态：第一阶段取证完成，未经运行测试验证

## 一、取证方法说明

本报告的所有结论基于以下客观证据，而非提交消息：

1. `git ls-tree` 比对三个关键提交（`e02c2776`、`7fa67926`、`ab7363af`）各文件的 blob SHA。
2. `git show <commit>:<file>` 提取文件全文，用 `Select-String` 统计关键符号出现次数。
3. 逐提交阅读 `git show <commit> -- <path>` 的完整代码差异（共 15 个提交，差异文本已导出至临时文件）。
4. 比对基线与 HEAD 的测试函数清单（`def test_` 列表）。
5. 检查工作区未提交修改（`git diff`）。
6. 检查运行中进程（未发现 Python 下载/上传进程）。

关键事实：所有 16 个待审计提交的提交消息**均只有标题行，没有正文**。因此每个修复的具体内容只能从代码差异推断，不能依赖提交描述。

## 二、提交清单与时间线

按时间顺序列出 2026-08-20 至 2026-08-26 的全部相关提交：

| 序号 | 提交 SHA | 日期 | 标题 | 代码净变更* |
|----|---------|------|------|-----------|
| 1 | e02c2776 | 08-20 17:37 | Update downloader FY4B adaptive product batches | +45 -13 |
| 2 | b0ce5c1b | 08-22 23:39 | geo_ring_cloud: harden transfer lifecycle and dashboard status | +1285 -90 |
| 3 | a81e20b9 | 08-22 23:47 | geo_ring_cloud: preserve upload resume progress | +78 -8 |
| 4 | 890c0e1e | 08-22 23:53 | geo_ring_cloud: restore task centre selection | +20 -8 |
| 5 | 487139da | 08-23 00:31 | geo_ring_cloud: tolerate vanished upload process | +24 -6 |
| 6 | 0ebd1e8d | 08-24 01:29 | Update geo_ring_cloud data_transfer_dashboard recovery | +602 -123 |
| 7 | 559834ce | 08-24 01:30 | Update geo_ring_cloud runtime log hygiene | +1 -0 |
| 8 | f08ea0cd | 08-24 01:40 | Fix geo_ring_cloud Windows PID probing | +28 -22 |
| 9 | a7e70177 | 08-24 01:53 | Reconcile geo_ring_cloud completed downloads | +86 -7 |
| 10 | fbb5f7f6 | 08-24 11:23 | Fix geo_ring_cloud Windows job launch | +117 -20 |
| 11 | 3ed53b58 | 08-24 12:49 | Update geo_ring_cloud data_transfer_dashboard automation identity | +20 -8 |
| 12 | d5d85083 | 08-24 12:54 | Fix geo_ring_cloud uploader credential status | +27 -7 |
| 13 | b0c14b86 | 08-24 16:29 | Fix geo_ring_cloud automated_data_uploader SSH hangs | +89 -18 |
| 14 | fc58f258 | 08-24 19:47 | Harden geo_ring_cloud automated_data_uploader retries | +477 -11 |
| 15 | 8a115bdc | 08-25 13:07 | Fix geo_ring_cloud data_transfer_dashboard startup recovery | +146 -7 |
| 16 | 7fa67926 | 08-26 01:06 | Restore geo_ring_cloud data_transfer_dashboard pre-FY4B baseline | +219 -3372 |
| 17 | ab7363af | 08-26 01:38 | Fix geo_ring_cloud data_transfer_dashboard Windows job launch | +41 -22 |

\* 代码净变更指 `third_report/code/` 目录下文件的增删行数，不含工作区元数据文件。

注：559834ce 未列入计划的重点审计清单，但它位于审计区间内且仅修改 `.gitignore` 一行，已一并核实。

## 二B、8 月 20 日之前的版本谱系

e02c2776 基线并非在 8 月 20 日一天内构建，而是从 8 月 13 日到 8 月 20 日累积构建的。理解这段历史对于理解 7fa67926 回退的目标至关重要。

### 8 月 13 日 — 8 月 18 日（基线前置提交）

| 提交 | 日期 | 标题 | 说明 |
|------|------|------|------|
| 1c7a4012 | 08-13 | Add geo_ring_cloud batch_queue control plane | 批次队列控制面（空间门禁、自动启动下一批次） |
| c81b7d75 | 08-14 | Fix stage_00 download recovery and progress | 下载恢复与进度 |
| 169bfb8b | 08-14 | Fix stage_00 PowerShell launcher compatibility | PowerShell 启动器兼容性 |
| af6792f4 | 08-14 | Fix stage_00 control partial manifest gate | 部分 .part 文件清单门禁 |
| 18117a02 | 08-14 | Fix stage_00 retry stderr and completion state | 重试 stderr 和完成状态 |
| 6542ce57 | 08-16 | Update downloader adaptive space estimates | 自适应空间估计 |
| 3b4c141b | 08-16 | Update downloader dashboard controls | 仪表盘控制 |
| 08288a41 | 08-17 | Update downloader trend warmup | 趋势预热 |
| **92600fe1** | **08-17** | **Update downloader trend sampling** | **趋势采样 ← 7fa67926 回退 dashboard.py 到此版本（blob 289a5c8a）** |
| **cdc38d10** | **08-18** | **Add downloader FY4B local import upload** | **引入 FY4B 本地导入功能 ← 7fa67926 回退 auto_uploader.py 到此版本之前的版本（blob a659e076）** |

### 8 月 20 日当天（6 个提交，构建 e02c2776 基线）

| 提交 | 时间 | 标题 | 修改内容 |
|------|------|------|---------|
| 7d3fd460 | 01:26 | Update downloader FY4B archive mapping | FY4B AGRI L2 命名校验、归档映射（`FY4B/<变量>/<YYYYMMDD>/<HH>/<文件名>`）、预览按钮 |
| b6f47a11 | 01:33 | Update downloader FY4B preview panel | 预览面板 UI（+30 行 HTML） |
| e6e84555 | 11:17 | Update downloader FY4B automatic upload progress | auto_uploader 添加 progress_callback 和 preflight_status；dashboard 添加 `_fy4b_batch_label`（纯日期格式）和自动批次标识 |
| 7c746fec | 11:34 | Update downloader cleanup folder and quiet monitor | 清理文件夹、安静监控 |
| 09c88b7b | 14:13 | Fix downloader Windows console suppression | 在 auto_uploader、dashboard、monitor_dashboard 中添加 `hidden_startupinfo()`/`subprocess_startupinfo()`，隐藏 SSH/SFTP 子进程控制台窗口 |
| **e02c2776** | **17:37** | **Update downloader FY4B adaptive product batches** | **`_fy4b_batch_label` 从纯日期改为产品范围格式（`fy4b_20240401_20240401_clm`）← 计划定义的功能基线** |

### FY4B 功能的引入与演变

FY4B 官方应用本地导入功能并非 e02c2776 独有，而是在 cdc38d10（08-18）首次引入，然后在 8 月 20 日的多个提交中逐步完善：

1. **cdc38d10（08-18）**：引入 `_fy4b_source_files`、`start_fy4b_official_upload`。此时需要用户手填批次标识（`batch_label`），且 `_fy4b_source_files` 返回 `List[Tuple[Path, Path, int]]`（无产品/变量分类）。
2. **7d3fd460（08-20 01:26）**：添加 AGRI L2 官方命名校验、归档映射路径（`FY4B/<变量>/<YYYYMMDD>/<HH>/`）、预览按钮。`_fy4b_source_files` 改为返回 `List[Dict]`（含 product 字段）。
3. **e6e84555（08-20 11:17）**：添加 `_fy4b_batch_label`（纯日期格式 `20240401_20240401`），改为自动生成批次标识而非手填。auto_uploader 添加上传进度报告。
4. **e02c2776（08-20 17:37）**：`_fy4b_batch_label` 改为产品范围格式（`20240401_20240401_clm` 或 `20240601_20240630_clm-cth`），添加 `batch_product_scope` 字段。

### 7fa67926 回退的精确目标

7fa67926 是**混合回退**，不同文件回退到了不同的历史版本：

| 文件 | 回退后 blob | 对应时期 | 相对 e02c2776 |
|------|-----------|---------|-------------|
| geo_cloud_downloader.py | 4c78c3d1 | e02c2776 版本 | 同基线（回退 b0ce5c1b 的下载器改动） |
| geo_ring_cloud_transfer_batch.py | 46a48931 | e02c2776 版本 | 同基线（回退 b0ce5c1b 的传输改动） |
| geo_ring_cloud_auto_uploader.py | a659e076 | cdc38d10 之前（08-17 或更早） | **更早**（丢失 e6e84555 上传进度、09c88b7b 控制台隐藏） |
| geo_ring_cloud_transfer_dashboard.py | 289a5c8a | 92600fe1（08-17） | **更早**（丢失所有 FY4B 功能、控制台隐藏、清理文件夹） |

**回退原因（用户提供）**：b0ce5c1b 引入的下载器改动（`AdaptiveS3RangeController` 等）导致下载器 bug 太多，连正常下载都做不了。7fa67926 回退 `downloader.py` 到 e02c2776 状态是为了去掉这些有问题的改动，恢复正常下载。

**过度回退问题**：7fa67926 不仅回退了 `downloader.py`（合理），还将 `auto_uploader.py` 和 `dashboard.py` 回退到了比 e02c2776 更早的版本（过度）。这丢失了：
- e02c2776 基线的 FY4B 官方导入功能（cdc38d10 + 8 月 20 日 6 个提交）
- 09c88b7b 的控制台窗口隐藏（`hidden_startupinfo`/`subprocess_startupinfo`）
- e6e84555 的上传进度报告和自动批次标识
- 7c746fec 的清理文件夹和安静监控

## 三、版本谱系关键发现（最高优先级）

这是本次审计最重要的结论，直接影响候选版本的组成策略。

### 3.1 7fa67926 不是恢复到 e02c2776 基线

提交标题为"Restore ... pre-FY4B baseline"，字面含义是恢复到 FY4B 之前的基线。通过 blob SHA 比对确认，**7fa67926 确实将 `auto_uploader.py` 和 `dashboard.py` 回退到了 e02c2776 之前的状态**，而非 e02c2776 本身。

四个核心文件的 blob SHA 对比：

| 文件 | e02c2776（基线） | 7fa67926（回退） | ab7363af（HEAD） |
|------|-----------------|-----------------|-----------------|
| geo_cloud_downloader.py | 4c78c3d1 | 4c78c3d1（同基线） | 4c78c3d1（同基线） |
| geo_ring_cloud_auto_uploader.py | 628ef904 | a659e076（**更早**） | a659e076（同回退） |
| geo_ring_cloud_transfer_batch.py | 46a48931 | 46a48931（同基线） | 46a48931（同基线） |
| geo_ring_cloud_transfer_dashboard.py | a136ae8b | 289a5c8a（**更早**） | 255ce4d6（回退后再修） |

- `downloader.py` 和 `transfer_batch.py` 在三个提交中一致：7fa67926 回退了 b0ce5c1b 对这两个文件的改动，恢复到 e02c2776 状态。
- `auto_uploader.py`：e02c2776 是 `628ef904`，但 7fa67926 改为 `a659e076`。经 `git log --find-object` 追溯，`a659e076` 来自 `cdc38d10`（Add downloader FY4B local import upload）时期，比 e02c2776 更早。**7fa67926 丢失了 e02c2776 基线中的 auto_uploader 内容。**
- `dashboard.py`：三者各不相同。`289a5c8a` 来自 `92600fe1`/`cdc38d10` 时期，同样比 e02c2776 更早。HEAD 的 `255ce4d6` 是在回退版基础上叠加 ab7363af 的 Windows Job 修复。

### 3.2 HEAD 丢失了 e02c2776 基线的 FY4B 官方导入功能

通过统计关键符号出现次数验证：

- e02c2776 的 dashboard.py 中 `fy4b_batch_label|product_scope|batch_product_scope` 出现 **6 处**
- 7fa67926 和 HEAD 的 dashboard.py 中上述符号出现 **0 处**

e02c2776 基线包含完整的 FY4B 官方应用本地导入功能（`preview_fy4b_official_upload`、`start_fy4b_official_upload`、`_fy4b_source_files`、`_fy4b_batch_label` 等，约 325 行）。HEAD 的 dashboard.py 仅保留平台名称列表中的 `"FY4B"` 字符串，**所有 FY4B 导入逻辑均不存在**。

文件行数对比：e02c2776 dashboard.py 为 2765 行，HEAD dashboard.py 为 2440 行，相差约 325 行，与上述结论一致。

### 3.3 HEAD 丢失了 8a115bdc 的仪表盘启动恢复功能

8a115bdc 添加了 `recover_interrupted_uploads`、`start_startup_upload_recovery`、`startup_recovery_path`。HEAD 的 dashboard.py 中搜索 `recover_interrupted|startup_recovery|start_startup` 结果为 **0 处**。7fa67926 回退了 8a115bdc，且后续未恢复。

### 3.4 HEAD 丢失了 fbb5f7f6 的 Windows Job 回退重试功能

fbb5f7f6 添加了 `background_subprocess_creation_flag_attempts`、`is_windows_job_breakaway_denied`，实现 `CREATE_BREAKAWAY_FROM_JOB` 被拒绝后回退到 `inherit_dashboard_job` 的重试逻辑。HEAD 的 dashboard.py 中搜索这两个函数名结果为 **0 处**。

HEAD 的 ab7363af 虽然标题也叫"Windows job launch"，但它只是在回退版基础上重新引入 `background_subprocess_creation_flags()` 和 `hidden_startupinfo()` 两个函数，**没有**带回 fbb5f7f6 的回退重试机制。

### 3.5 HEAD 丢失了 fc58f258 的上传重试基础设施

fc58f258 添加了 `UploadFileFailure`、`is_retryable_upload_error`、`upload_manifest_item_with_retry`、`append_jsonl_durable`、`archive_failure_snapshot`，以及失败历史日志和快照存档。7fa67926 将 `auto_uploader.py` 回退到 `a659e076`，上述内容全部消失。

### 3.6 HEAD 丢失了 b0ce5c1b 的多项数据完整性增强

b0ce5c1b 是区间内最大的单提交（+1285 -90），被 7fa67926 大幅回退。被回退的功能包括：

- `AdaptiveS3RangeController`：S3 下载分块大小自适应控制
- `expected_local_missing.csv` 与 `completeness_audit`：下载完整性审计
- `build_auto_upload_manifest` 的 SHA-256 缓存复用：避免每次续传重新哈希全部文件
- `ledger_progress_for_files`：连续上传账本进度匹配
- `verify_manifest` 的多线程校验和进度记录
- `server_verify_workers`：服务器端并行 SHA-256 校验
- `current_process_created_epoch`：PID 复用防护
- `geo_ring_cloud_resume_uploader_task.py`：独立续传入口（新文件，被 7fa67926 删除）

### 3.7 HEAD 丢失了 0ebd1e8d 的仪表盘托管上传工作线程

0ebd1e8d 添加了 `_run_dashboard_upload_worker`、`_start_dashboard_upload_worker`、`_start_breakaway_upload_process`，将上传进程改为仪表盘托管线程（解决 Windows Job 30 分钟后杀死子进程问题），还添加了 `chunked_items`（远程预flight分批）、`geo_ring_cloud_dash.ps1`（仪表盘守护脚本）、`geo_ring_cloud_run_auto_uploader.ps1`（上传启动器）。7fa67926 删除了新增的 PS1 文件并回退了 dashboard.py。

### 3.8 测试数量对比

- e02c2776 基线：56 个测试函数
- HEAD（ab7363af）：52 个测试函数

HEAD 相对基线缺少以下 4 个测试：
- `test_fy4b_batch_label_includes_sorted_product_scope`
- `test_fy4b_official_import_creates_control_batch_without_copying_source`
- `test_fy4b_official_preview_rejects_ambiguous_nc_filename`
- `test_fy4b_cleanup_folder_opens_external_official_source`

HEAD 相对基线多出以下 4 个测试（来自后续修复，但对应的被测功能在 HEAD 中并不完整存在，见下节分析）：
- `test_dashboard_reports_restricted_unattended_key_mode`
- `test_download_launch_retries_without_breakaway_after_windows_access_denied`
- `test_download_status_reconciles_from_terminal_artifacts`
- `test_windows_pid_probe_never_calls_os_kill`

注意：`test_download_launch_retries_without_breakaway_after_windows_access_denied` 测试的是 fbb5f7f6 引入的 `background_subprocess_creation_flag_attempts` 回退重试功能，但该功能在 HEAD 中已被 7fa67926 回退。**该测试在 HEAD 上可能无法通过**，需在第二阶段实际运行验证。

### 3.9 工作区未提交修改

源仓库工作区有未提交修改，集中在 `paths.py` 和 `geo_ring_cloud_path_configuration.ps1`：将 `EXTERNAL_EPIC_L2_ROOT` 默认值从 `F:\DSCOVR_EPIC_L2_CLOUD_03_2024.03` 改为 `E:\GEO_Cloud_2024\DSCOVR_EPIC_L2_CLOUD_03_2024.03`。这是本地磁盘环境调整，不属于功能修复，迁移时不应纳入，应通过配置文件提供。

### 3.10 运行中进程

审计时未发现运行中的 `python` 或 `pythonw` 进程。有一个 PowerShell 进程（PID 32376，启动于 2026-09-01 23:09），但无证据表明它正在运行下载或上传脚本。

## 四、逐提交详细审计

以下按时间顺序逐个审计。每项包含：修改的模块、修复的具体问题、测试证据、是否依赖后续提交、是否适合纳入候选版本、未知风险。

### 4.1 e02c2776 — 8 月 20 日功能基线

- 日期：2026-08-20 17:37
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/test_geo_ring_cloud_transfer_batch.py`、操作指南
- 修复问题：FY4B 官方应用本地导入的批次命名从纯日期格式（`fy4b_20240401_20240401`）改为产品范围格式（`fy4b_20240401_20240401_clm` 或 `fy4b_20240601_20240630_clm-cth`）。从文件名的产品标识和 `NOM_YYYYMMDDHHMMSS` 提取变量集合、最早和最晚日期及小时集合自动生成控制批次名。相同来源再次提交会安全续传历史批次；不同来源覆盖同一日期和变量集合时会自动加上来源指纹以避免混淆。历史日期型控制批次不会被重命名。同时在 `fy4b_official_import_request.json` 中新增 `batch_product_scope` 字段。
- 测试证据：新增 `test_fy4b_batch_label_includes_sorted_product_scope`，验证 CTH/CLM/CTT 混合变量排序为 `clm-cth-ctt`。修改现有 FY4B 导入测试，断言批次名从 `fy4b_20240401_20240401` 变为 `fy4b_20240401_20240401_clm`。
- 是否依赖后续提交：否。此为基线，后续提交均基于此。
- 是否适合纳入候选版本：**是，作为基线整体纳入。** 这就是计划定义的"8 月 20 日功能基线"。
- 未知风险：该提交本身不修改 `auto_uploader.py`，但基线版的 `auto_uploader.py`（blob `628ef904`）缺少后续的 SSH 超时、重试、SHA-256 缓存等功能。候选版本需从后续提交选择性吸收这些增强。

### 4.2 b0ce5c1b — 上传生命周期与仪表盘状态

- 日期：2026-08-22 23:39
- 修改模块：`geo_cloud_downloader.py`、`geo_ring_cloud_auto_uploader.py`、`geo_ring_cloud_transfer_batch.py`、`geo_ring_cloud_transfer_dashboard.py`、`geo_ring_cloud_transfer_dashboard.html`、`geo_ring_cloud_transfer_batch.ps1`、`geo_ring_cloud_resume_uploader_task.py`（新增）、`tests/`、操作指南
- 修复问题：此为区间内最大的多功能提交，实际包含至少 8 项独立功能：
  1. **S3 自适应分块**（`AdaptiveS3RangeController`）：按源 bucket 维护独立的分块大小控制器，目标请求耗时 4-12 秒，超 16 秒则减半，连续 8 次稳定则翻倍（上限 64 MiB）。
  2. **下载完整性审计**：分离"远端不可用"（`missing_targets.csv`）和"本地缺失/损坏"（`expected_local_missing.csv`），新增 `completeness_audit` 字段（PASS/WARN），明确 `is_upload_gate=False`。
  3. **SHA-256 缓存复用**（`build_auto_upload_manifest`）：若已有完整自动上传清单且本地路径、大小、远程路径、校验和格式均匹配，则跳过全量重哈希。任何不匹配则回退到全量重哈希。
  4. **连续上传账本进度匹配**（`ledger_progress_for_files`）：按本地路径和大小匹配账本条目，保守计算已完成进度。
  5. **服务器端多线程 SHA-256 校验**（`verify_manifest` 的 `workers` 参数，1-4 路）：新增 `--progress` 进度记录和 `--workers` 参数，校验期间每 2 秒写入进度 JSON，支持吞吐量统计。
  6. **服务器校验进度同步**（`sync_verification_progress`）：上传端通过独立线程池运行远程校验命令，每 5 秒下载一次进度记录并更新本地状态。
  7. **PID 复用防护**（`current_process_created_epoch`）：记录进程创建时间，配合 `process_matches_status` 防止 PID 复用误判。
  8. **独立续传入口**（`geo_ring_cloud_resume_uploader_task.py`）：为 Windows 任务调度器提供短命令行入口，绕过 261 字符限制。
  9. **清单 SHA-256 来源标记**（`sha256_source` 字段）：区分 `signature_matched_ledger` 和 `computed_for_manifest`。
  10. **Conda 临时目录隔离**（`transfer_batch.ps1`）：每批次独立 `conda_tmp`，避免 Conda 包装器临时文件竞争。
  11. **下载完成释放槽位**：清单准备阶段状态改为 `finalizing`，释放仪表盘下载槽位。
  12. **仪表盘任务归档**：HTML 新增归档任务区域，分离已完成且本地数据已清理的任务。
- 测试证据：新增约 30 个测试，覆盖自适应分块、完整性审计、SHA-256 缓存复用、账本进度、多线程校验、PID 复用、归档显示等。
- 是否依赖后续提交：是。其 SHA-256 缓存和账本进度逻辑被 a81e20b9 的远程预flight进度保留所依赖；其 `current_process_created_epoch` 被 487139da 的进程消失容错所依赖。
- 是否适合纳入候选版本：**部分适合，但不应整体纳入。** 该提交混杂了多项功能，其中：
  - 适合纳入：SHA-256 缓存复用、完整性审计、账本进度匹配、Conda 临时目录隔离、任务归档。这些是数据完整性和可靠性增强。
  - **暂不纳入（用户确认有 bug）**：S3 自适应分块（`AdaptiveS3RangeController`）和下载完整性审计中的 `run_validate` 改动。用户确认这些下载器改动导致正常下载失败。候选版本应保留 e02c2776 基线的 `downloader.py`，不移植 b0ce5c1b 对 `downloader.py` 的改动。
  - 需谨慎评估：服务器端多线程校验（需确认服务器端 Python 环境支持）。
  - 独立续传入口（`geo_ring_cloud_resume_uploader_task.py`）：可作为便利工具纳入，但需去除硬编码的默认目标地址和密钥路径。
- 未知风险：
  1. **单提交过大**：1285 行变更混杂 12 项功能，无法单独撤销其中一项。计划要求"每项修复必须单独提交"，此提交严重违反该原则。
  2. **下载器改动有已知 bug**：用户确认 `AdaptiveS3RangeController` 等下载器改动导致正常下载失败。具体 bug 根因尚不清楚——可能是自适应分块在特定网络环境下（如中国教育网到 AWS S3）不断减半到 1 MiB 导致极慢，或分块边界处理有误。候选版本必须将 b0ce5c1b 的下载器改动（`geo_cloud_downloader.py`）与上传器改动（`auto_uploader.py`）分离，只移植后者。
  3. SHA-256 缓存复用的安全性依赖 `local_signature`（size + mtime_ns）匹配。若文件系统 mtime 精度不足或被外部工具修改，可能导致校验和复用错误。需测试验证。
  4. `geo_ring_cloud_resume_uploader_task.py` 硬编码 `DEFAULT_TARGET = "dhr@210.45.127.28"`、`DEFAULT_IDENTITY_FILE = Path.home() / ".ssh" / "id_ed25519_node05"`、`DEFAULT_SERVER_ROOT = "/data04/1/dhr/geo_ring_cloud_auto_upload"`。迁移时必须改为配置提供。

### 4.3 a81e20b9 — 上传断点续传进度

- 日期：2026-08-22 23:47
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：仪表盘重启上传时，若上次状态来自远程预flight（`progress_source` 为 `remote_preflight` 或 `previous_remote_preflight_pending_recheck`），则保留已完成的文件数和字节数作为显示基线，而非归零。写入新状态时携带 `file_count`、`total_size_bytes`、`completed_files`、`completed_size_bytes`、`percent`、`progress_source`。
- 测试证据：新增 `test_restart_upload_keeps_prior_remote_preflight_as_display_baseline`，模拟 10 文件中 7 个已完成的状态，断言重启后 `completed_files=7`、`progress_source=previous_remote_preflight_pending_recheck`。同时修改 `test_open_cleanup_folder_requires_approval_and_never_deletes`，补充 SSH 密钥和目标参数。
- 是否依赖后续提交：否。此修复独立于后续提交。
- 是否适合纳入候选版本：**是。** 进度保留是断点续传的核心体验，逻辑保守（仅保留远程已确认的进度作为显示基线，实际重传由远程预flight重新校验）。
- 未知风险：该修复作用于 `start_auto_upload` 的状态写入路径，依赖 b0ce5c1b 中 `auto_uploader.py` 的 `upload_batch` 读取 `progress_source` 并保留进度。若只移植此提交的 dashboard 改动而不移植 b0ce5c1b 的 uploader 改动，进度保留可能不完整。

### 4.4 890c0e1e — 任务中心批次选择

- 日期：2026-08-22 23:53
- 修改模块：`geo_ring_cloud_transfer_dashboard.html`、`tests/`
- 修复问题：当没有归档任务时，`renderTasks` 在清空归档列表后直接 `return`，跳过了 `bindTaskSelection()`，导致活跃任务的点击绑定失效，任务切换静默失败。修复为在 `return` 前调用 `bindTaskSelection()`。
- 测试证据：新增 HTML 内容断言，验证 `bindTaskSelection();\n        return;` 存在。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** 这是一个清晰的前端 bug 修复，改动最小，逻辑正确。
- 未知风险：测试仅断言 HTML 字符串存在，未验证点击行为。需在前端测试阶段补充交互测试。

### 4.5 487139da — 上传进程消失容错

- 日期：2026-08-23 00:31
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：`process_matches_status` 中，`pid_exists` 和 `Process(pid).create_time` 是两次独立系统调用，工作进程可能在两次调用之间退出。原代码未捕获 `NoSuchProcess`/`ZombieProcess` 异常，导致 HTTP 处理器崩溃。修复为捕获这两类异常并返回 `False`（视为已停止），其他异常返回 `True`（保守视为存活）。
- 测试证据：新增 `test_process_identity_treats_vanished_pid_as_stopped`，模拟 `NoSuchProcess` 异常，断言返回 `False`。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** 竞态条件容错是必要的健壮性修复。
- 未知风险：将未知异常视为"存活"（`return True`）可能在某些异常情况下误报进程存活。但相比误报已停止导致重复启动，这是更安全的选择。

### 4.6 0ebd1e8d — 仪表盘恢复

- 日期：2026-08-24 01:29
- 修改模块：`geo_ring_cloud_auto_uploader.py`、`geo_ring_cloud_transfer_dashboard.py`、`geo_ring_cloud_transfer_batch.ps1`、`geo_ring_cloud_dash.ps1`（新增）、`geo_ring_cloud_run_auto_uploader.ps1`（新增）、`geo_ring_cloud_notification_service.py`、`tests/`
- 修复问题：此为第二大提交（+602 -123），包含多项功能：
  1. **远程预flight分批**（`chunked_items`）：将远程路径列表按 128 个一批分批检查，每批更新进度，避免大批次单次 SSH 命令超时。
  2. **仪表盘托管上传工作线程**（`_run_dashboard_upload_worker`、`_start_dashboard_upload_worker`）：将上传进程从独立子进程改为仪表盘进程内的托管线程，解决 Windows Job 约 30 分钟后杀死子进程且退出码为 0 的问题。线程异常退出或无终态返回时写入 `FAIL` 状态。
  3. **脱离 Job 的上传启动**（`_start_breakaway_upload_process`）：保留独立子进程模式作为备选，通过 PowerShell 中间父进程实现脱离 Job。
  4. **仪表盘守护脚本**（`geo_ring_cloud_dash.ps1`）：`while($true)` 循环重启仪表盘 HTTP 进程，防止任务调度器以退出码 0 结束进程。
  5. **邮件监控间隔**：从 15 秒改为 30 分钟（`NOTIFICATION_MONITOR_INTERVAL_SECONDS`），匹配运维策略。
  6. **通知服务默认间隔**：`notification_service.py` 的 `--interval-seconds` 默认值从 15 改为 1800。
  7. **队列状态快照缓存**（`_queue_status_snapshot`）：`batch_queue_status` 使用非阻塞锁，若调度器正在刷新则返回上次一致快照，避免 HTTP 状态端点等待。
  8. **趋势写入容错**：`dashboard_trends` 写入趋势文件时捕获 `OSError`，避免文件共享冲突导致仪表盘无响应。
  9. **状态持久化**：`auto_upload_status` 和 `download_launcher_status` 在检测到停滞或失败时将协调结果写回 JSON，防止刷新后显示陈旧的 RUNNING 状态。
  10. **直传 Python 解释器**：`transfer_batch.ps1` 新增 `-PythonExe` 参数，避免 `conda run` 包装器的临时文件竞争和退出码延迟问题。
  11. **上传启动器**（`geo_ring_cloud_run_auto_uploader.ps1`）：脱离 Job 的 PowerShell 中间父进程。
- 测试证据：新增 `test_remote_preflight_is_bounded_into_small_batches`、`test_dashboard_upload_worker_marks_unreported_clean_return_as_failure`，修改现有测试适配托管线程模式。
- 是否依赖后续提交：是。`_start_dashboard_upload_worker` 被 a81e20b9 的测试所 patch。8a115bdc 的启动恢复在此基础上调用 `start_auto_upload`/`start_continuous_upload`。
- 是否适合纳入候选版本：**部分适合。**
  - 适合纳入：远程预flight分批、队列状态快照缓存、趋势写入容错、状态持久化、邮件间隔调整。这些是健壮性改进。
  - 需谨慎评估：仪表盘托管上传工作线程。这是解决 Windows Job 问题的核心方案，但将上传逻辑移入仪表盘进程意味着上传崩溃可能影响仪表盘。需测试验证线程异常隔离是否充分。
  - 不适合直接纳入：`geo_ring_cloud_dash.ps1` 硬编码 `--ssh-target "dhr@210.45.127.28"`、`--identity-file "...\.ssh\id_ed25519_node05"`、`--auto-upload-root "/data04/1/dhr/geo_ring_cloud_auto_upload"`。迁移时必须改为从配置读取。
- 未知风险：
  1. **单提交过大**：602 行变更混杂 11 项功能。
  2. 仪表盘托管线程模式下，`pid` 字段记录的是仪表盘进程自身的 PID（`os.getpid()`），而非独立子进程。这与 `process_matches_status` 的 PID 存活判断逻辑存在语义冲突——仪表盘进程当然存活，但这不代表上传工作线程仍在运行。需验证状态判断是否改为检查线程存活（`existing.is_alive()`）。
  3. `geo_ring_cloud_dash.ps1` 的 `while($true)` 无限重启循环可能导致仪表盘在配置错误时快速循环重启，需加入退避或最大重试次数。

### 4.7 559834ce — 运行时日志卫生

- 日期：2026-08-24 01:30
- 修改模块：`.gitignore`
- 修复问题：在 `.gitignore` 中新增一行（具体内容需查看，但仅 1 行变更）。
- 测试证据：无。
- 是否依赖后续提交：否。
- 是否适合纳入候选版本：**是，但需确认具体排除内容。** 迁移时应建立独立的 `.gitignore`。
- 未知风险：无。

### 4.8 f08ea0cd — Windows PID 判断

- 日期：2026-08-24 01:40
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：Windows 上 `os.kill(pid, 0)` 不是无害的存在探测——CPython 的 Windows 实现会将非控制台信号路由到 `TerminateProcess`，信号 0 会以退出码 0 终止目标进程。原代码先调用 `os.kill` 再在异常时回退到 `psutil.pid_exists`，为时已晚。修复为：Windows 上**直接使用** `psutil.pid_exists`，完全不调用 `os.kill`；POSIX 上保持 `os.kill(pid, 0)`。
- 测试证据：重命名测试为 `test_windows_pid_probe_never_calls_os_kill`，patch `os.name="nt"`，断言 `os.kill` **未被调用**，`psutil.pid_exists` 返回 `True`。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** 这是一个关键的安全修复——原代码会意外杀死进程（包括仪表盘自身）。P0 优先级。
- 未知风险：依赖 `psutil`。若 `psutil` 不可用则返回 `False`（视为已停止），可能导致进程被误判为已停止。需在启动入口检查 `psutil` 是否安装。

### 4.9 a7e70177 — 已完成下载协调

- 日期：2026-08-24 01:53
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：下载启动器可能在上传器正在读取同一清单时消失，但下载器已写完不可变传输清单和 `download_summary.json`。原代码仅看启动器状态，可能将已完成的批次显示为 FAIL。修复为：从 `download_summary.json` 和传输清单两个独立终态产物协调判断——若完整性审计为 PASS、本地缺失行为 0、已下载行数等于预期行数且大于 0、传输清单为 `READY_FOR_XFTP_UPLOAD`，则将状态改为 `COMPLETE`，并设置 `reconciliation_source`。同时 `download_phase` 在此情况下设为 `ready_for_xftp`。
- 测试证据：新增 `test_download_status_reconciles_from_terminal_artifacts`，模拟 FAIL 状态的启动器但 PASS 的下载摘要和就绪的传输清单，断言协调后状态为 `COMPLETE`、`reconciliation_source` 正确、`remote_unavailable_rows` 保留。
- 是否依赖后续提交：是。协调逻辑依赖 b0ce5c1b 在 `download_summary.json` 中引入的 `completeness_audit`、`expected_found_rows`、`expected_local_missing_rows`、`remote_unavailable_rows` 字段。若不纳入 b0ce5c1b 的下载器改动，此协调逻辑将无法工作。
- 是否适合纳入候选版本：**是，但必须与 b0ce5c1b 的下载完整性审计一并纳入。** P0 优先级。
- 未知风险：协调逻辑使用 `int(summary.get("expected_local_missing_rows", -1))`，默认值 -1 会导致 `== 0` 判断失败。这是保守设计（字段缺失时不协调），但需确认 b0ce5c1b 始终写入该字段。

### 4.10 fbb5f7f6 — Windows 后台任务启动

- 日期：2026-08-24 11:23
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：`CREATE_BREAKAWAY_FROM_JOB` 在仪表盘自身被 Windows Job 托管且未授予脱离权限时会以 WinError 5（访问拒绝）失败，导致所有下载无法启动。修复为引入 `background_subprocess_creation_flag_attempts()` 返回有序尝试列表：优先 `breakaway_from_job`，失败则回退到 `inherit_dashboard_job`（移除 `CREATE_BREAKAWAY_FROM_JOB` 标志）。`is_windows_job_breakaway_denied` 仅识别 WinError 5 或 errno 5/13。启动循环按序尝试，仅在该错误且还有备选时才继续，否则抛出。状态记录 `process_launch_mode`。
- 测试证据：新增 `test_dashboard_background_workers_fall_back_inside_restrictive_windows_job`（验证尝试顺序和标志位）和 `test_download_launch_retries_without_breakaway_after_windows_access_denied`（模拟第一次 PermissionError、第二次成功，断言 `popen.call_count==2`、`process_launch_mode==inherit_dashboard_job`）。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** P0 优先级。这是 Windows 后台进程可靠启动的关键修复。
- 未知风险：回退到 `inherit_dashboard_job` 意味着下载进程仍在仪表盘的 Job 内，可能被 Job 限制影响。但相比完全无法启动，这是可接受的折中。注意：**此修复在 HEAD 中已被 7fa67926 回退且未恢复**，候选版本必须重新引入。

### 4.11 3ed53b58 — 仪表盘自动化身份

- 日期：2026-08-24 12:49
- 修改模块：`geo_ring_cloud_dash.ps1`
- 修复问题：修改 `geo_ring_cloud_dash.ps1`（0ebd1e8d 新增的守护脚本）中的某些身份标识。由于该文件在 7fa67926 中被删除且 HEAD 未恢复，此提交的影响在 HEAD 中不存在。
- 测试证据：无。
- 是否依赖后续提交：是，依赖 0ebd1e8d 的 `geo_ring_cloud_dash.ps1`。
- 是否适合纳入候选版本：**暂不纳入。** 该提交仅修改一个在 HEAD 中已被删除的文件。若候选版本重新引入仪表盘守护脚本，应基于配置文件而非硬编码身份。
- 未知风险：无。

### 4.12 d5d85083 — 上传凭据状态

- 日期：2026-08-24 12:54
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：仪表盘状态中的 `credential_mode` 始终硬编码为 `"ssh-agent"`，但实际使用的是受限无人值守密钥（文件名以 `_automation` 结尾）。修复为：若 `identity_file` 存在且名称以 `_automation` 结尾，则报告 `restricted_unattended_key`，否则报告 `ssh-agent`。
- 测试证据：新增 `test_dashboard_reports_restricted_unattended_key_mode`，使用名为 `id_ed25519_node05_automation` 的密钥文件，断言 `credential_mode==restricted_unattended_key`。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** P0 优先级（凭据状态准确报告）。改动最小且逻辑清晰。
- 未知风险：凭据模式仅凭文件名后缀判断，可能不够严谨。但作为状态展示用途已足够。

### 4.13 b0c14b86 — SSH 卡死处理

- 日期：2026-08-24 16:29
- 修改模块：`geo_ring_cloud_auto_uploader.py`、`tests/`
- 修复问题：SSH 命令在 S4U（非交互）计划任务下会继承不可用的 Session-0 stdin 句柄并阻塞等待。修复为：`run_ssh` 在 `input_text is None` 时显式设置 `stdin=subprocess.DEVNULL`，避免等待不可用句柄。新增 `command_timeout` 参数，超时抛出 `RuntimeError`。连接检查 `true` 命令设置 `command_timeout=max(30, connect_timeout + 10)`。
- 测试证据：新增三个测试：`test_run_ssh_uses_devnull_without_input`（验证 `stdin=DEVNULL`）、`test_run_ssh_uses_pipe_for_payload`（验证有输入时用 `input=`）、`test_run_ssh_reports_command_timeout`（验证超时抛出 RuntimeError）。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** P0 优先级（SSH 超时和有限重试）。这是解决 SSH 卡死的核心修复。
- 未知风险：`command_timeout` 仅用于连接检查 `true` 命令。其他 SSH 命令（如远程预flight、校验）未设置超时。若这些命令卡死，仍可能阻塞。候选版本应考虑为所有 SSH 命令设置合理的超时上限。

### 4.14 fc58f258 — 上传重试

- 日期：2026-08-24 19:47
- 修改模块：`geo_ring_cloud_auto_uploader.py`、`tests/`
- 修复问题：上传单个文件失败后无重试，瞬时网络抖动会导致整个批次失败。修复为：
  1. `UploadFileFailure`：单个文件耗尽所有重试尝试后抛出。
  2. `is_retryable_upload_error`：区分瞬时故障（可重试）和永久故障（不可重试，如权限拒绝、认证失败、源文件改变、远程文件大小不符）。
  3. `upload_manifest_item_with_retry`：有界重试（默认 4 次，上限 10 次），指数退避（基数 5 秒），每次重试前刷新远程 `.part` 状态。
  4. `append_jsonl_durable`：持久化失败审计日志（`os.fsync` 强制刷盘）。
  5. `archive_failure_snapshot`：写入唯一非覆盖的终态快照。
  6. 连续上传的下载失败也记录失败日志和快照。
  7. 连续上传重试改为先记录日志再休眠。
- 测试证据：新增约 10 个测试，覆盖可重试/不可重试判断、重试次数、指数退避、失败日志、快照存档、连续上传下载失败记录等。
- 是否依赖后续提交：否。独立修复。
- 是否适合纳入候选版本：**是。** P0 优先级。有界重试是上传可靠性的核心。但注意：**此修复在 HEAD 中已被 7fa67926 回退且未恢复**，候选版本必须重新引入。
- 未知风险：
  1. `is_retryable_upload_error` 通过错误消息字符串匹配判断永久故障，列表可能不全。新的错误类型可能被误判为可重试。
  2. 重试期间再次调用 `inspect_remote` 刷新远程状态会增加 SSH 调用次数和耗时。
  3. `FAILURE_LOG_LOCK` 是进程级锁，多线程上传时可能成为瓶颈（但 `append_jsonl_durable` 持久化很快，影响有限）。

### 4.15 8a115bdc — 仪表盘启动恢复

- 日期：2026-08-25 13:07
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：仪表盘重启后不恢复中断的上传。修复为新增 `recover_interrupted_uploads`：遍历所有任务，对处于 `STARTING/RUNNING/STALLED/STOPPED` 状态且本地载荷存在且传输清单就绪的上传，根据下载状态选择 `batch_upload`（下载已完成）或 `continuous_upload`（下载仍在运行）模式恢复。已通过（PASS）或终态失败（FAIL）的不恢复。恢复异步执行（`start_startup_upload_recovery`），不阻塞 HTTP 绑定。恢复审计写入 `dashboard_startup_upload_recovery.json`。`main()` 中在 `serve_forever` 前调用启动恢复。
- 测试证据：新增两个测试：`test_dashboard_startup_recovery_uses_managed_batch_upload`（验证恢复调用 `start_auto_upload`、审计记录正确）、`test_dashboard_startup_recovery_does_not_retry_terminal_failure`（验证 FAIL 状态不恢复）。
- 是否依赖后续提交：否。但依赖 0ebd1e8d 的 `_start_dashboard_upload_worker`（恢复时调用 `start_auto_upload`/`start_continuous_upload`，这些方法内部使用托管线程）。
- 是否适合纳入候选版本：**是。** P1 优先级（仪表盘重启后的任务恢复）。但注意：**此修复在 HEAD 中已被 7fa67926 回退且未恢复**，候选版本必须重新引入。
- 未知风险：
  1. 恢复逻辑不区分"仪表盘崩溃后重启"和"用户手动停止后重启"。用户手动停止的 `STOPPED` 状态也会被恢复，可能违背用户意图。需确认 `STOPPED` 是否应纳入恢复范围。
  2. 恢复在 `serve_forever` 前异步启动，但 `task_summaries(limit=None)` 可能需要扫描全部批次目录，在批次很多时可能耗时较长。

### 4.16 7fa67926 — 恢复旧基线（回退提交）

- 日期：2026-08-26 01:06
- 修改模块：所有核心文件（-3372 行，+219 行）
- 修复问题：**无。此提交不是修复，而是大规模回退。** 标题"Restore pre-FY4B baseline"表明意图是恢复到 FY4B 之前的版本。
- **回退原因（用户确认）**：b0ce5c1b 引入的下载器改动（`AdaptiveS3RangeController` 自适应分块、下载完整性审计等）导致下载器 bug 太多，连正常下载都做不了。7fa67926 回退 `downloader.py` 到 e02c2776 状态是为了去掉这些有问题的改动，恢复正常下载。这是合理的操作。但 7fa67926 同时将 `auto_uploader.py` 和 `dashboard.py` 回退到了比 e02c2776 更早的版本（08-17 时期），**过度回退**了与下载器 bug 无关的 FY4B 功能、上传进度、控制台隐藏等。
- 具体回退内容（按文件分类）：
  1. 删除 `AdaptiveS3RangeController` 和所有自适应分块逻辑（回退 `geo_cloud_downloader.py`）。
  2. 删除下载完整性审计（回退 `geo_cloud_downloader.py`）。
  3. 删除 `UploadFileFailure`、`is_retryable_upload_error`、`upload_manifest_item_with_retry`、`append_jsonl_durable`、`archive_failure_snapshot`（回退 `auto_uploader.py` 至 `a659e076`）。
  4. 删除 `current_process_created_epoch`、`ledger_progress_for_files`、SHA-256 缓存复用、服务器端多线程校验、`chunked_items`、远程预flight分批（回退 `auto_uploader.py`）。
  5. 删除 `geo_ring_cloud_resume_uploader_task.py`（删除文件）。
  6. 删除仪表盘托管上传工作线程、脱离 Job 上传启动、启动恢复、队列快照缓存、趋势写入容错、状态持久化（回退 `dashboard.py` 至 `289a5c8a`）。
  7. 删除 `geo_ring_cloud_dash.ps1`、`geo_ring_cloud_run_auto_uploader.ps1`（删除文件）。
  8. 删除 FY4B 官方导入功能（`_fy4b_source_files`、`_fy4b_batch_label`、`preview_fy4b_official_upload`、`start_fy4b_official_upload`）——**这是 e02c2776 基线的核心功能，被一并回退**。
  9. 回退 `notification_service.py` 的间隔默认值。
  10. 回退 `transfer_batch.ps1` 的 Conda 临时目录隔离和 `-PythonExe` 参数。
  11. 回退 HTML 的任务归档区域。
  12. 回退测试文件（从 56 个测试减至少量）。
- 测试证据：回退测试文件，删除大量测试。
- 是否依赖后续提交：否。后续提交（ab7363af）在此回退基础上构建。
- 是否适合纳入候选版本：**否。** 此提交是本次审计区间内**风险最高**的提交。它不仅回退了后续修复，还回退了 e02c2776 基线自身的 FY4B 功能。**候选版本绝不能基于 7fa67926 或其后的 HEAD 构建。**
- 未知风险：
  1. 回退的 `auto_uploader.py`（`a659e076`）和 `dashboard.py`（`289a5c8a`）来自 e02c2776 之前的版本，其状态未经本次审计验证。
  2. 回退删除了 b0ce5c1b 新增的 `geo_ring_cloud_resume_uploader_task.py`，但该文件可能已被用户添加到 Windows 任务调度器。回退后调度器调用会失败。
  3. 回退后的 `auto_uploader.py` 缺少 `process_created_epoch` 字段，与 `process_matches_status` 的 PID 复用防护不兼容。

### 4.17 ab7363af — Windows Job 启动修复（当前 HEAD）

- 日期：2026-08-26 01:38
- 修改模块：`geo_ring_cloud_transfer_dashboard.py`、`tests/`
- 修复问题：在 7fa67926 回退后的 dashboard.py 基础上，重新引入 `background_subprocess_creation_flags()`（`CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB`）和 `hidden_startupinfo()`（`STARTF_USESHOWWINDOW | SW_HIDE`），替换原来内联的 `creationflags` 计算。三处 `subprocess.Popen` 调用（下载启动、连续上传启动、自动上传启动）统一使用这两个函数。
- 测试证据：新增测试断言 Windows 下 `creationflags` 包含 `CREATE_BREAKAWAY_FROM_JOB` 且 `startupinfo` 非空。
- 是否依赖后续提交：否。这是当前 HEAD。
- 是否适合纳入候选版本：**部分适合。** `background_subprocess_creation_flags()` 和 `hidden_startupinfo()` 的抽象是好的，但：
  1. 此提交未引入 fbb5f7f6 的回退重试机制（`background_subprocess_creation_flag_attempts`）。在限制性 Windows Job 下，`CREATE_BREAKAWAY_FROM_JOB` 仍会直接失败。
  2. 此提交的 dashboard.py 基线是 7fa67926 回退版，缺少 FY4B 功能、启动恢复、托管上传线程等。
- 未知风险：此提交给人"Windows Job 已修复"的假象，但实际上它只修复了标志位抽象，未修复限制性 Job 下的回退重试。测试通过不代表真实 Windows Job 环境下能正常启动。

## 五、依赖闭包分析

### 5.1 模块依赖图

基于 e02c2776 基线的 `import` 语句分析，下载器及依赖的完整闭包如下：

```
geo_cloud_download/
├─ geo_ring_cloud_transfer_dashboard.py  (仪表盘主程序)
│  ├─ geo_ring_cloud.notifications       (邮件通知: PersistentEmailNotifier, save_secure_email_config)
│  ├─ geo_ring_cloud.batch_queue         (批次队列: ACTIVE_QUEUE_STATUSES, estimate_required_space, make_queue_item, normalize_request, ...)
│  ├─ monitor_dashboard                  (本地监控: MET_DOWNLOAD_RE, S3_EVENT_RE, format_bytes, parse_download_log, read_json, ...)
│  ├─ geo_ring_cloud_auto_uploader       (自动上传器, 同目录)
│  └─ geo_ring_cloud_transfer_batch      (传输批次工具, 同目录)
│
├─ geo_ring_cloud_auto_uploader.py       (自动上传器)
│  ├─ geo_ring_cloud.lineage             (代码谱系: code_commit, generating_script_state)
│  ├─ geo_ring_cloud.paths               (路径: PROJECT_ROOT)
│  └─ geo_ring_cloud_transfer_batch      (同目录: PLATFORM_REMOTE_RELATIVE, iter_batch_files, parse_day, sha256_file)
│
├─ geo_cloud_downloader.py               (下载器)
│  ├─ geo_ring_cloud.lineage             (write_manifest)
│  └─ geo_ring_cloud.paths               (EXTERNAL_GEO_CLOUD_ROOT, PROJECT_ROOT)
│
├─ geo_ring_cloud_transfer_batch.py      (传输批次工具)
│  └─ (仅标准库: argparse, csv, hashlib, json, os, re, sys, datetime, pathlib, typing)
│
├─ geo_ring_cloud_notification_service.py (通知服务)
│  ├─ geo_ring_cloud.notifications       (PersistentEmailNotifier)
│  ├─ geo_ring_cloud.lineage             (code_commit, generating_script_state)
│  ├─ geo_ring_cloud.paths               (PROJECT_ROOT)
│  └─ geo_ring_cloud_transfer_dashboard  (DashboardState)
│
├─ monitor_dashboard.py                  (本地监控仪表盘)
│  └─ geo_ring_cloud.paths               (EXTERNAL_GEO_CLOUD_ROOT, THIRD_REPORT_ROOT)
│
└─ geo_ring_cloud_transfer_batch.ps1     (PowerShell 编排)
   └─ geo_ring_cloud_path_configuration.ps1 (路径配置, 位于 geo_ring_cloud_stage1/)
```

`geo_ring_cloud` 包内部依赖：
```
geo_ring_cloud/
├─ __init__.py        (PROJECT_ID, __version__)
├─ paths.py           (仅依赖 os, pathlib; 硬编码 D:\AAAresearch_paper 等默认路径)
├─ lineage.py         (依赖 .PROJECT_ID, .sources.REGISTRY_VERSION)
├─ sources.py         (仅依赖 dataclasses, typing)
├─ batch_queue.py     (仅依赖标准库: csv, hashlib, json, os, time, datetime, pathlib, typing)
└─ notifications.py   (仅依赖标准库: hashlib, base64, json, os, re, smtplib, shutil, subprocess, threading, time, datetime, email, pathlib, typing)
```

### 5.2 必须迁移的文件清单

基于依赖闭包，候选版本至少需要以下文件（均从 `e02c2776` 提取）：

| 源路径（相对 `third_report/code/`） | 目标路径（建议） | 依赖说明 |
|-------------------------------------|-----------------|---------|
| `geo_cloud_download/geo_ring_cloud_transfer_dashboard.py` | `src/geo_downloader/dashboard.py` | 仪表盘主程序 |
| `geo_cloud_download/geo_ring_cloud_auto_uploader.py` | `src/geo_downloader/uploader.py` | 自动上传器 |
| `geo_cloud_download/geo_cloud_downloader.py` | `src/geo_downloader/downloader.py` | 下载器 |
| `geo_cloud_download/geo_ring_cloud_transfer_batch.py` | `src/geo_downloader/transfer.py` | 传输批次工具 |
| `geo_cloud_download/geo_ring_cloud_notification_service.py` | `src/geo_downloader/notifications.py` | 通知服务 |
| `geo_cloud_download/monitor_dashboard.py` | `src/geo_downloader/monitor.py` | 本地监控 |
| `geo_cloud_download/geo_ring_cloud_transfer_dashboard.html` | `src/geo_downloader/web/dashboard.html` | 前端页面 |
| `geo_cloud_download/geo_ring_cloud_transfer_batch.ps1` | `scripts/start_batch.ps1` | PowerShell 编排 |
| `geo_ring_cloud_stage1/geo_ring_cloud/__init__.py` | `src/geo_downloader/__init__.py` 或保留包结构 | 包标识 |
| `geo_ring_cloud_stage1/geo_ring_cloud/paths.py` | `src/geo_downloader/paths.py` | 路径解析（需重构去除硬编码） |
| `geo_ring_cloud_stage1/geo_ring_cloud/lineage.py` | `src/geo_downloader/lineage.py` | 代码谱系 |
| `geo_ring_cloud_stage1/geo_ring_cloud/sources.py` | `src/geo_downloader/sources.py` | 源定义（lineage 依赖） |
| `geo_ring_cloud_stage1/geo_ring_cloud/batch_queue.py` | `src/geo_downloader/batch_queue.py` | 批次队列 |
| `geo_ring_cloud_stage1/geo_ring_cloud/notifications.py` | `src/geo_downloader/notifications_impl.py` | 邮件通知实现 |
| `geo_ring_cloud_stage1/geo_ring_cloud_path_configuration.ps1` | `scripts/configure.ps1` | 路径配置（需重构） |
| `geo_cloud_download/tests/test_geo_ring_cloud_transfer_batch.py` | `tests/test_transfer_batch.py` | 测试套件 |

### 5.3 第三方依赖

从 `import` 语句识别的第三方依赖：

| 依赖 | 使用者 | 用途 | 是否必需 |
|------|--------|------|---------|
| `boto3` | `geo_cloud_downloader.py` | S3 对象存储下载（GOES/Himawari） | 是（S3 下载） |
| `requests` | `geo_cloud_downloader.py` | EUMETSAT API 元数据查询 | 是（EUMETSAT 下载） |
| `psutil` | `dashboard.py`（f08ea0cd 后）、`auto_uploader.py`（b0ce5c1b 后） | PID 存活判断、进程创建时间 | 是（Windows PID 探测）；f08ea0cd 之前用 `os.kill`（不安全） |

### 5.4 操作系统依赖

| 依赖 | 用途 | 平台 |
|------|------|------|
| `conda` | Python 环境管理（`transfer_batch.ps1` 调用 `conda run`） | Windows |
| `ssh` / `sftp` | 远程服务器上传和校验 | 全平台 |
| `python3` | 服务器端 SHA-256 校验脚本 | 远程 Linux 服务器 |
| PowerShell 5.1+ | 编排脚本 | Windows |
| Windows Task Scheduler | 定时启动仪表盘 | Windows |
| `os.name == "nt"` 分支 | 进程标志位、窗口隐藏、PID 探测 | Windows 特定 |

### 5.5 路径硬编码问题

`paths.py` 中的硬编码默认路径（需迁移时改为配置提供）：

| 变量 | 硬编码默认值 | 环境变量覆盖 |
|------|-------------|-------------|
| `PROJECT_ROOT` | `D:\AAAresearch_paper` | `GEO_RING_PROJECT_ROOT` |
| `EXTERNAL_GEO_CLOUD_ROOT` | `E:\GEO_Cloud_2024` | `GEO_RING_EXTERNAL_GEO_CLOUD_ROOT` |
| `EXTERNAL_EPIC_L2_ROOT` | `F:\DSCOVR_EPIC_L2_CLOUD_03_2024.03` | `GEO_RING_EXTERNAL_EPIC_L2_ROOT` |
| `EXTERNAL_EPIC_COMPOSITE_ROOT` | `F:\DSCOVR_EPIC_L2_COMPOSITE_02_2024.01` | `GEO_RING_EXTERNAL_EPIC_COMPOSITE_ROOT` |
| `EUMETSAT_CREDENTIALS_FILE` | `third_report/eumetsat_dataservices_API.txt` | 无（需添加） |

`sys.path` 注入机制：三个核心 Python 文件均在头部通过 `CORE_CODE_ROOT = Path(__file__).resolve().parents[1] / "geo_ring_cloud_stage1"` 将 `geo_ring_cloud_stage1` 加入 `sys.path`，使 `from geo_ring_cloud.xxx import yyy` 能被解析。迁移后需改为包内导入（`from .xxx import yyy` 或 `from geo_downloader.xxx import yyy`）。

`geo_ring_cloud_path_configuration.ps1` 中的硬编码默认路径与 `paths.py` 对应，且 `$GeoRingProjectRoot` 默认回退到 `Join-Path $PSScriptRoot "..\..\."`（即 `AAAresearch_paper` 根目录）。

## 六、第一阶段验收结论

### 6.1 哪些功能属于 8 月 20 日

e02c2776 基线包含的功能：
- GOES-16/18、Himawari-9、Meteosat-0deg/IODC 的 S3 下载
- EUMETSAT API 元数据查询
- 断点续传下载（`Range` 请求，固定分块大小）
- 下载完整性校验（`run_validate`）
- 传输清单生成（`prepare_manifest`）
- 自动上传（`upload_batch`，含远程预flight、SFTP 上传、服务器 SHA-256 校验）
- 连续上传（`watch_and_upload`，下载与上传并行）
- FY4B 官方应用本地导入（`preview_fy4b_official_upload`、`start_fy4b_official_upload`，产品范围批次命名）
- 仪表盘 HTTP 服务（任务中心、批次选择、磁盘门禁、趋势图）
- 批次队列调度（空间门禁、自动启动下一批次）
- 邮件通知（DPAPI 加密配置、状态转换通知）
- Windows 后台进程启动（`CREATE_NO_WINDOW`，但**无** `CREATE_BREAKAWAY_FROM_JOB` 和窗口隐藏）
- PowerShell 编排（`transfer_batch.ps1`，通过 `conda run` 调用）
- 56 个单元测试

### 6.2 哪些是后续必要修复

按优先级分类，以下修复应当纳入候选版本（但必须从 e02c2776 基线之上逐项移植，不能从 HEAD 反向裁剪）：

**P0（必须优先评估）：**

| 修复 | 来源提交 | 纳入理由 | HEAD 中是否存在 |
|------|---------|---------|----------------|
| Windows PID 探测不调用 os.kill | f08ea0cd | 原代码会意外杀死进程（含仪表盘自身） | 是（但测试名不同） |
| SSH 超时和 stdin DEVNULL | b0c14b86 | S4U 计划任务下 SSH 卡死 | 否（被回退） |
| 上传有界重试 | fc58f258 | 瞬时网络抖动导致整批失败 | 否（被回退） |
| Windows Job 回退重试 | fbb5f7f6 | 限制性 Job 下下载无法启动 | 否（被回退） |
| 上传进程消失容错 | 487139da | PID 竞态导致 HTTP 处理器崩溃 | 否（被回退） |
| 凭据状态准确报告 | d5d85083 | 状态展示错误 | 否（被回退） |
| 窗口隐藏 (hidden_startupinfo) | ab7363af | 黑框闪现 | 是 |
| CREATE_BREAKAWAY_FROM_JOB 标志 | ab7363af | 后台进程脱离 Job | 是（但无回退重试） |

**P1（通过测试后纳入）：**

| 修复 | 来源提交 | 纳入理由 | HEAD 中是否存在 |
|------|---------|---------|----------------|
| 下载完成状态协调 | a7e70177 | 启动器消失后已完成的批次显示为 FAIL | 否（被回退） |
| 上传断点续传进度保留 | a81e20b9 | 重启上传时进度归零 | 否（被回退） |
| 仪表盘启动恢复 | 8a115bdc | 重启后不恢复中断的上传 | 否（被回退） |
| 任务中心批次选择 | 890c0e1e | 无归档任务时点击绑定失效 | 否（被回退） |
| SHA-256 缓存复用 | b0ce5c1b | 续传时避免全量重哈希 | 否（被回退） |
| 下载完整性审计 | b0ce5c1b | 分离远端不可用和本地缺失 | 否（被回退） | **暂不纳入**（属于下载器改动，用户确认有 bug；a7e70177 的下载状态协调依赖此改动，需一并评估） |
| 连续上传账本进度匹配 | b0ce5c1b | 保守计算已完成进度 | 否（被回退） |
| 服务器端多线程校验 | b0ce5c1b | 大批次校验耗时 | 否（被回退） |
| 远程预flight分批 | 0ebd1e8d | 大批次单次 SSH 超时 | 否（被回退） |
| 队列状态快照缓存 | 0ebd1e8d | HTTP 状态端点等待 | 否（被回退） |
| 趋势写入容错 | 0ebd1e8d | 文件共享冲突导致无响应 | 否（被回退） |
| 状态持久化 | 0ebd1e8d | 刷新后显示陈旧 RUNNING | 否（被回退） |
| Conda 临时目录隔离 | b0ce5c1b | Conda 包装器临时文件竞争 | 否（被回退） |
| 直传 Python 解释器 | 0ebd1e8d | 避免 conda run 包装器问题 | 否（被回退） |
| PID 复用防护 | b0ce5c1b | PID 复用误判 | 否（被回退） |
| ~~S3 自适应分块~~ | b0ce5c1b | ~~固定分块大小不适应网络波动~~ | 否（被回退） | **排除**（用户确认导致下载器 bug） |
| 任务归档 | b0ce5c1b | 已完成任务与活跃任务混杂 | 否（被回退） |
| 仪表盘托管上传线程 | 0ebd1e8d | Windows Job 杀死子进程 | 否（被回退） |

### 6.3 哪些修改应排除

| 修改 | 来源提交 | 排除理由 |
|------|---------|---------|
| 7fa67926 整体回退 | 7fa67926 | 回退了 e02c2776 基线的 FY4B 功能和所有后续修复 |
| S3 自适应分块（AdaptiveS3RangeController） | b0ce5c1b | **用户确认导致下载器 bug，正常下载失败** |
| `run_validate` 下载完整性审计改动 | b0ce5c1b | 属于下载器改动，与自适应分块同提交，用户确认有 bug |
| `geo_ring_cloud_dash.ps1` 硬编码 SSH 目标 | 0ebd1e8d | 硬编码凭据和服务器地址 |
| `geo_ring_cloud_resume_uploader_task.py` 硬编码默认值 | b0ce5c1b | 硬编码目标地址和密钥路径 |
| 工作区未提交的 EPIC L2 路径修改 | 工作区 | 本地磁盘环境调整，非功能修复 |
| 3ed53b58 仪表盘自动化身份 | 3ed53b58 | 仅修改已被回退删除的文件 |

### 6.4 候选版本的准确组成

**候选版本 = e02c2776 基线 + 逐项移植的后续修复。**

具体而言：
1. **起点**：从 `e02c2776` 提取全部核心文件和依赖，不从当前工作树或 HEAD 复制。
2. **路径重构**：去除 `paths.py` 和 PS1 中的硬编码路径，改为配置文件提供。
3. **导入重构**：将 `sys.path` 注入改为包内导入。
4. **逐项移植 P0 修复**：按 f08ea0cd → 487139da → b0c14b86 → fc58f258 → fbb5f7f6 → d5d85083 → ab7363af(hidden_startupinfo 部分) 的顺序，每项独立提交。
5. **逐项移植 P1 修复**：在 P0 通过测试后，按依赖顺序移植。**注意**：b0ce5c1b 的上传器/仪表盘改动（SHA-256 缓存、账本进度等）需从该提交中单独提取，不携带其下载器改动（`AdaptiveS3RangeController`、`run_validate` 改动），后者已确认有 bug。
6. **标签**：先打 `legacy-2026.08.20`（历史基线），最终打 `v1.0.0-rc1`（候选版）。

**候选版本绝不基于 HEAD（ab7363af）或 7fa67926 构建**，因为它们缺少 e02c2776 基线的 FY4B 功能和大量后续修复。

**候选版本的 `downloader.py` 保留 e02c2776 基线版本**（blob 4c78c3d1），不移植 b0ce5c1b 对 `downloader.py` 的改动（`AdaptiveS3RangeController` 等），因为用户确认这些改动导致下载器 bug。

### 6.5 当前仍存在的风险

1. **~~7fa67926 的回退原因不明~~**（已更新）：用户确认回退原因是 b0ce5c1b 引入的下载器改动（`AdaptiveS3RangeController` 等）导致下载器 bug 太多，连正常下载都做不了。7fa67926 回退 `downloader.py` 是合理的。但过度回退了 `auto_uploader.py` 和 `dashboard.py`。后续修复（SSH 超时、上传重试、PID 探测等）与下载器 bug 无关，可以安全纳入候选版本。
2. **b0ce5c1b 的下载器改动有已知问题**：用户确认 b0ce5c1b 引入的 `AdaptiveS3RangeController` 等下载器改动导致正常下载失败。候选版本移植 b0ce5c1b 时，**必须将其下载器改动（`geo_cloud_downloader.py`）与上传器改动（`geo_ring_cloud_auto_uploader.py`）和仪表盘改动（`dashboard.py`）分离**。下载器改动暂不纳入或需修复后单独评估；上传器和仪表盘改动（SHA-256 缓存、账本进度、完整性审计等）与下载器 bug 无关，可以单独纳入。
3. **b0ce5c1b 和 0ebd1e8d 过大**：这两个提交分别混杂了 12 项和 11 项功能，无法单独验证或撤销其中一项。移植时必须拆分为独立提交。
4. **测试覆盖不足**：现有测试主要是单元测试，缺少临时目录集成测试和前端交互测试。f08ea0cd 的 PID 探测修复在真实 Windows Job 环境下的行为未验证。
5. **SHA-256 缓存复用的安全性**：依赖 mtime_ns 精度，在某些文件系统（如 FAT32）上可能不足。
6. **仪表盘托管线程模式与 PID 语义冲突**：0ebd1e8d 将上传移入仪表盘线程后，状态中的 `pid` 字段记录的是仪表盘进程 PID，需要确认状态判断逻辑是否相应调整。
7. **服务器端环境未审计**：远程校验脚本依赖服务器端 `python3` 和特定校验脚本，本次审计未验证服务器端环境。
8. **测试在 HEAD 上的可运行性未知**：HEAD 的测试引用了 `background_subprocess_creation_flag_attempts`（fbb5f7f6 引入），但该函数在 HEAD 中已被回退。**HEAD 的测试套件可能无法通过。**
9. **e02c2776 基线的下载器可靠性**：用户确认 e02c2776 之前的版本（即 8 月 13 日至 8 月 20 日的版本）能够正常下载。e02c2776 的 `downloader.py`（blob 4c78c3d1）与 8 月 13 日的版本一致（e02c2776 没有修改 downloader.py），因此 e02c2776 基线的下载器是可靠的。

### 6.6 下一阶段准备做什么

第二阶段：导入历史功能基线
1. 在目标仓库创建 `src/geo_downloader/` 目录结构。
2. 从 `e02c2776` 提取核心文件和依赖，记录每个文件的 `source_blob_sha`。
3. 重构路径解析和导入结构。
4. 打 `legacy-2026.08.20` 标签。
5. 运行基线测试，确认 56 个测试通过。

在开始第二阶段前，需向用户确认：
- ~~7fa67926 回退的原因是否已知？~~（已确认：下载器 bug 太多）
- 是否授权基于 e02c2776 基线构建候选版本？
- 服务器端 SHA-256 校验脚本是否需要一并迁移？
- b0ce5c1b 的下载器改动（`AdaptiveS3RangeController`）具体是什么 bug？是否有修复版本，还是应当永久排除？

## 七、聊天记录补充取证（来源：docs/chatwithcodex.md）

用户提供了与 codex 的完整聊天记录（21889 行），记录了下载归档器从规划到开发到故障到回退的全过程。以下提取与本次审计直接相关的关键事实。

### 7.1 仪表盘功能膨胀的量化证据

聊天记录第 21218-21223 行提供了仪表盘后端文件的增长量化：
- 2026 年 8 月 10 日初始自动化版本：约 1177 行
- 当前控制台后端：2571 行、72 个函数/方法级定义
- 8 月 10 日至 26 日，单是该文件就经历了约 26 次有内容变更的提交
- 累计增加约 2704 行、删除约 1310 行
- 后端文件约 109 KB，上传器另有 41 KB，监控器约 26 KB

同期连续加入的功能（第 21225-21238 行）：空间感知队列、自动续批、多任务中心、FY4B 导入、持续上传、自适应并发、趋势图和真实速度、邮件通知、本地清理、后台计划任务、Windows 进程恢复、状态误报修复。

聊天记录明确指出："每项功能单独看都合理，但它们共享同一批状态文件、PID、锁和批次选择，因此交互复杂度增长得非常快。"（第 21240 行）

### 7.2 执行上下文变化是已证实的根因

聊天记录第 21242-21279 行明确指出最严重的已证实问题是执行上下文变化：

初期控制台从用户的交互式桌面会话启动，能访问已解锁的 SSH Agent。后来为实现"关闭窗口后继续运行""黑框不再闪现""控制台崩溃后自动重启""远程桌面退出后进程不消失"，控制台被改成后台进程、计划任务和 Windows Job 相关方式启动。此时上传器不一定能访问交互式会话里的 SSH Agent。

实际错误不是猜测：`agent refused operation` 和 `Permission denied (publickey,password)`。完整证据已写入控制台调试记录。

后来的解决方案是改用专门配置的、服务器端受限的自动化密钥 `id_ed25519_node05_automation`，不依赖交互式 SSH Agent。

### 7.3 Windows Job 的已证实行为

聊天记录第 19850-19857 行提供了 Windows Job 问题的精确证据：
1. 仪表盘使用 `CREATE_BREAKAWAY_FROM_JOB` 创建下载进程
2. Windows 立即返回 `[WinError 5] 拒绝访问`
3. 使用完全相同的程序、路径、日志文件和参数，只去掉 `CREATE_BREAKAWAY_FROM_JOB`
4. 下载进程立即成功创建，并实际下载了数百个文件

因此可以高置信度判断：当时的仪表盘运行环境禁止子进程脱离所在 Job。

### 7.4 计划任务异常终止的精确时间线

聊天记录第 19970-19986 行提供了计划任务异常终止的精确时间线：
1. `GeoRingCloud-Dashboard` 计划任务在 02:24:24 启动
2. 11:23:52 终止旧仪表盘 PID 7948
3. supervisor 于 11:23:57 重新启动新仪表盘
4. 新仪表盘成功启动下载 PID 7000
5. 仪表盘趋势最后更新于 11:27:10
6. 连续上传账本最后更新于 11:28:09，上传到 76/2976
7. 仪表盘和内置上传线程约在 11:28 消失
8. **下载子进程没有同时消失**，继续独立工作到 11:46:41，完成 2976/2976、0 损坏
9. 下载随后在最终校验/生成传输清单之前退出
10. 12:10:17 独立通知服务发现进程已不存在，将状态改写为 `STOPPED/FAIL`

关键结论：下载子进程虽然由仪表盘启动，但并没有立即随仪表盘一起死亡。它最终仍没有顺利执行完批次收尾。

### 7.5 "直传流程"——用户最终采用的替代方案

聊天记录第 21173-21183 行描述了用户最终采用的替代方案：完全绕开仪表盘，使用近似线性的链路：

```text
PowerShell 7 启动下载
→ 生成不可变清单
→ 单路 SFTP 上传到 .part
→ rename 成正式文件
→ 服务器 SHA-256 复核
```

这个流程稳定的原因（第 21387-21396 行）：
- 下载失败不会改写上传状态
- 上传失败不会让批次队列混乱
- 页面消失不会影响进程
- 每次上传都通过 `.part → rename`
- 远端已有文件按路径和大小判断
- 最终还有 SHA-256 复核兜底
- 每 30 分钟一次的外部监控

### 7.6 聊天记录对"回退原因"的修正

聊天记录第 19920 行明确指出："FY4B 功能本身不是关键，关键是同一时期发生了上传托管方式重构。回退到'没有 FY4B'的版本会同时回退很多无关功能，无法精准验证根因。"

这与我的审计结论一致：7fa67926 回退的范围远超问题本身。聊天记录还指出（第 21336-21360 行）"回退代码并不等于回退整个系统"——即使把代码退回一周前，已生成的新格式状态 JSON、批次队列、上传 ledger、趋势记录、Windows 计划任务、已启动的旧版子进程、PID 记录、残留锁、SSH Agent 和后台会话、浏览器保存的旧批次 URL 都不会自动回退。因此可能出现"旧版后端 + 新版状态文件 + 更旧版本启动的子进程 + 浏览器仍选择已删除批次"的不兼容状态。

### 7.7 聊天记录对候选版本架构方向的指导

聊天记录第 21407 行明确了长期架构方向："未来如果重做控制台，正确方向不是继续增加状态修补，而是让控制台只负责展示和提交命令，下载器、上传器、验证器分别作为独立长期 Worker 运行。"

这与迁移计划的目标一致。候选版本应当：
1. 保留 e02c2776 基线的下载器、上传器、验证器作为独立模块
2. 仪表盘仅作为展示和提交命令的薄层
3. 不再将上传线程嵌入仪表盘进程（0ebd1e8d 的 `_start_dashboard_upload_worker` 方案虽然解决了子进程被杀的问题，但引入了进程生命周期耦合）
4. 通过配置提供 SSH 密钥路径而非依赖交互式 SSH Agent

### 7.8 聊天记录对 0ebd1e8d 仪表盘托管上传线程的评价

聊天记录第 19914-19918 行指出："旧上传方式是独立子进程；后来因为独立进程反复异常消失，上传改成了仪表盘内部线程。这样做解决了一部分孤儿进程和状态误报，但引入了新的耦合：仪表盘进程退出时，内部上传线程一定随之退出。"

这意味着 0ebd1e8d 的 `_run_dashboard_upload_worker` 方案虽然在短期内减少了孤儿进程，但长期来看恰恰是导致"仪表盘消失时上传必然停止"的原因。候选版本应当谨慎评估是否纳入此方案，或改用独立 S4U 计划任务方式运行上传器（聊天记录第 20233 行提到的方案）。

### 7.9 聊天记录揭示的下载器 bug 可能不仅仅是 AdaptiveS3RangeController

聊天记录中多次提到下载问题，但多数是关于状态误报、进程管理、EUMETSAT 503 错误、PowerShell stderr 处理等，而非 specifically AdaptiveS3RangeController。用户所说的"下载器 bug 太多"可能是指整个仪表盘-下载器-上传器系统的综合问题，而非单纯的 `geo_cloud_downloader.py` 代码 bug。

建议在第二阶段导入基线后，先运行 56 个基线测试确认下载器核心逻辑正确，再逐项评估后续修复是否引入了实际问题。
