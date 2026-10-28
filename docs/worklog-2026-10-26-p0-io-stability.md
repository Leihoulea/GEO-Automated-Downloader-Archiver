# 工作记录：仪表盘 / 队列 I/O 压力治理（P0-1～P0-4）与上传器/下载器优化（P0-5b、P0-6）

- 日期：2026-10-26
- 仓库：`GEO-Automated-Downloader-Archiver`
- 相关提交：
  - `a24831a` `fix: reduce dashboard I/O load to prevent system instability`（上一版，已在 `origin/main`）
  - `9a1f87e` `perf: reduce dashboard and queue scheduling I/O pressure`（第一轮，已 push）
  - 第二轮（P0-6 boto3 client 复用 + P0-5b checksum cache）：`07da3e7`，已 push
  - 第三轮（P0-5a 上传器 pending 索引）：见 `git log` 最新提交；提交状态见第 10 节
- 测试：第一轮 `69 passed`；第二轮 `74 passed`；第三轮 `79 passed`
- 数据安全：未修改任何自动删除策略；`automatic_delete` 仍为 `False`

---

## 1. 背景

### 1.1 用户现象

用户怀疑当前项目的设计会导致这台 Windows 电脑蓝屏重启，要求先做审计，再按 P0-1～P0-4 修复。第一轮完成后，继续处理 P0-6（boto3 client 复用）、P0-5b（重复 SHA-256）和 P0-5a（上传器全树扫描）。

### 1.2 系统日志证据

Windows 系统日志中确认存在多次内核级 bugcheck，不是普通应用崩溃：

| 日期 | Bugcheck | 含义 |
|---|---|---|
| 2026-10-26 | `0x20001` | HYPERVISOR_ERROR |
| 2026-09-23 | `0x0000000A` | IRQL_NOT_LESS_OR_EQUAL |
| 2026-09-16 | `0x0000003B` | SYSTEM_SERVICE_EXCEPTION |
| 2026-09-15 | `0x0000001A (0x403)` | MEMORY_MANAGEMENT |
| 2026-09-14 | `0x20001` | HYPERVISOR_ERROR |
| 2026-07-31 | `0x00000050` | PAGE_FAULT_IN_NONPAGED_AREA |

其中 `0x1A (0x403)` 与上一版提交 `a24831a` 中描述的 dashboard I/O 压力问题直接对应。

### 1.3 硬件/环境要点

- `F:` 数据盘位于机械硬盘（Disk 0，`ST4000DM004`）。
- `C:` 系统盘位于 NVMe（`WD_BLACK SN7100`）。
- 内存约 68 GB，20 个逻辑处理器。
- 页面文件在 `C:`。
- 系统里存在 10 个 `GeoRingCloud-*` 计划任务，其中多个指向旧副本
  `D:\AAAresearch_paper\third_report\code\geo_cloud_download\...`，部分处于 `Ready` 且 `StartWhenAvailable=True`。

### 1.4 关键判断

Python 应用本身通常不能直接让内核崩溃。这些 bugcheck 更像是**内存/驱动/存储栈的潜在缺陷被持续高 I/O、海量 `stat`、内存抖动和线程堆积“压出来”**。机械盘 F: 放大了这种风险。

因此本次工作有两个目标：

1. 降低应用侧对磁盘、线程和隐藏子进程的持续压力。
2. 为后续硬件/驱动排查留出清晰记录，避免把“应用慢”和“内核蓝屏”混为一谈。

---

## 2. 审计发现的高风险设计（P0）

### P0-1 队列调度在持有全局锁时做全量扫描，HTTP 线程无上限

- `geo_ring_cloud_transfer_dashboard.py` 的队列调度在 `_queue_lock` 内调用
  `task_summaries()`、`_queue_estimate()`、`_queue_gate()`。
- `/api/status` 请求又需要同一把 `_queue_lock`。
- 服务端使用无并发上限的 `ThreadingHTTPServer`。
- 当扫描变慢时，HTTP 线程不断堆积，每个线程随后又发起新一轮扫描，形成正反馈。

### P0-2 每次状态刷新全量扫描，并重复读同一份清单 6 遍

- `status()` 对同一份 `manifest_inventory.csv` 调用了 3 次 `read_inventory()`。
- `summarize_download()` 内部又对同一清单调用 3 次 `read_manifest_sizes()`。
- 每次刷新还会做 `.part` 全树 `rglob`、批次遍历和 A:\–Z:\ 盘符探测。
- 设置/邮件状态每次刷新还会通过隐藏 PowerShell 做 DPAPI 解密。

### P0-3 失败/停止批次没有被轻量摘要覆盖

上一版只把 `upload PASS/FAIL` 或 `raw status == complete` 判为终态，导致：

- 下载失败（`raw.status == "failed"`）
- 用户停止（launcher `STOPPED`）
- 上传 `STOPPED/STALLED`

仍然走完整 `_task_summary()`，继续对大目录做 `rglob("*.part")`。

### P0-4 排队估算每 15 秒对整张清单逐行 `stat`

`batch_queue.refine_estimate_from_inventory()` 会对清单里每个 S3 行执行
`local_path.is_file() and local_path.stat()`。该函数被每个等待队列项、每个 15 秒调度周期反复调用，在机械盘上形成随机 `stat` 风暴。

---

## 3. 本次修改内容（commit `9a1f87e`）

### 3.1 P0-1：队列锁与 HTTP 线程

文件：`src/geo_downloader/geo_ring_cloud_transfer_dashboard.py`

- 重写 `_process_batch_queue_once_unlocked()`：
  - 先在锁外完成 `task_summaries()`、`_queue_estimate()`、`_queue_gate()`。
  - 只在锁内做轻量状态更新、启动决策和状态文件写入。
- 队列为空或只有已完成项时直接返回，**空闲调度 tick 不再扫描批次**。
- `_active_download_task(tasks=...)` 支持传入已扫描结果，避免重复扫描。
- `_sync_launched_queue_items(state, tasks_by_name=...)` 复用同一次扫描结果。
- 新增 `BoundedThreadingHTTPServer`，通过 `BoundedSemaphore` 限制并发 HTTP 线程数，默认 `MAX_HTTP_WORKERS = 8`。

### 3.2 P0-2：减少重复读取和隐藏子进程

文件：`src/geo_downloader/geo_ring_cloud_transfer_dashboard.py`

- 新增 `read_inventory_by_remote_type()`：一次流式读取同一份清单，分别聚合
  `s3`、`eumetsat`、`earthdata` 的统计结果，保持原有 result 形状。
- `summarize_download(..., sizes=...)` 支持传入共享的 size map；`status()` 用
  `sizes_for()` 对同一路径只读一次。
- 清单读取从原来的约 6 遍降为 2 遍：
  - 1 遍聚合 inventory 计数
  - 1 遍读取 size map
- 新增 `status_cached()`：
  - `STATUS_CACHE_TTL_SECONDS = 8`
  - 8 秒内复用同一份快照
  - 计算期间持有 `_status_cache_lock`，并发标签页合并为一次扫描
- `/api/status` 改为调用 `status_cached()`。
- `do_POST()` 在请求前后都调用 `invalidate_status_cache()`，避免动作后看到旧页面。
- 新增运行信息缓存：
  - `_public_settings_cached()`
  - `_notification_status_cached()`
  - `RUNTIME_INFO_CACHE_TTL_SECONDS = 60`
  - 设置/邮件状态不再每次刷新都通过隐藏 PowerShell 做 DPAPI 解密
  - `update_settings()`、`configure_email()` 会清除缓存

### 3.3 P0-3：失败/停止批次轻量摘要

文件：`src/geo_downloader/geo_ring_cloud_transfer_dashboard.py`

- `task_summaries()` 的终态集合扩展为：
  - upload：`PASS`、`FAIL`、`FAILED`、`STOPPED`、`STALLED`
  - raw：`complete`、`failed`
  - launcher：`FAIL`、`FAILED`、`COMPLETE`、`COMPLETED`、`PASS`、`EXITED`、
    `CANCELLED`、`CANCELED`、`STOPPED`
- 终态批次只有在**下载心跳仍存活**时才走完整 `_task_summary()`；否则使用
  `_task_summary_lite()`，避免 `rglob("*.part")`。
- `_task_summary_lite()` 修正状态优先级：
  - launcher `FAIL/STOPPED` 不会再被 `batch_status.json` 里过期的 `running` 覆盖。
  - 轻量摘要返回真实 `error` 和 `parse_disk_gate(error)`。

### 3.4 P0-4：排队估算缓存与节流

文件：`src/geo_downloader/geo_ring_cloud/batch_queue.py`

- 新增 `_collect_authoritative_inventory()`：
  - 按清单文件 `(resolve_path, mtime_ns, size, platforms)` 缓存逐行统计结果。
  - 清单不变时，不再对每个本地文件执行 `stat()`。
  - 缓存上限 32 条，超过后清空。
- `refine_estimate_from_inventory()` 改为使用上述缓存。
- 文件：`geo_ring_cloud_transfer_dashboard.py`
  - 新增 `ESTIMATE_REFRESH_SECONDS = 300`
  - 等待队列项的估算最多每 300 秒刷新一次
  - 新队列项 / 旧格式无时间戳的项仍会立即刷新

### 3.5 额外安全改动

- `BoundedThreadingHTTPServer` 给 HTTP 请求线程加了硬上限。
- 空闲队列 tick 提前返回，避免无意义的批次扫描。
- 以上改动都不改变自动删除策略，也不删除任何原始数据。

---

## 4. 测试与验证

执行命令：

```powershell
python -m pytest -q
```

结果：

```text
第一轮：69 passed
第二轮：74 passed
第三轮：79 passed
```

第二轮新增：

```powershell
python -m py_compile `
  src\geo_downloader\geo_ring_cloud\checksums.py `
  src\geo_downloader\geo_ring_cloud_auto_uploader.py `
  src\geo_downloader\geo_ring_cloud_transfer_batch.py `
  src\geo_downloader\geo_cloud_downloader.py
```

结果：编译通过。

新增的回归测试覆盖：

- `read_inventory_by_remote_type()` 单遍统计且分源计数正确
- 失败终态批次使用轻量摘要，不触发完整扫描和 `rglob`
- 失败批次存在新鲜下载心跳时仍使用完整摘要
- launcher `STOPPED` 覆盖过期的 `running` 状态
- `status_cached()` 在 TTL 内复用快照，失效后重新计算
- 等待队列估算跨 tick 节流
- 空闲队列 tick 不扫描批次
- S3 inventory 估算缓存复用
- HTTP 并发线程上限
- checksum cache 命中时不再重复读取文件
- checksum cache 在 size/mtime 变化时失效
- 两个 `ChecksumCache` 实例共享同一 JSONL
- `prepare_manifest()` 第二次运行复用 checksum cache
- 同一运行状态下 `thread_s3_client()` 只创建一个 client
- 带 `client_state` 的每日 inventory 复用同一 client

---

## 5. 教训与经验

### 5.1 不要在每个 HTTP 请求里做“全量事实查询”

仪表盘的正确形态通常是：

- 后台生成快照
- 请求只读缓存
- 明确的 TTL 和失效策略
- 并发请求单飞（single-flight）

“每个请求重新扫描所有批次”在数据量小的时候看不出问题，数据量一大就会演变成 I/O 风暴。

### 5.2 不要在全局锁内做文件系统 I/O

锁内只应做内存状态更新和轻量决策。扫描、`stat`、CSV 解析、目录遍历都应该在锁外完成，然后用快照合并回状态。

### 5.3 “终态”必须包含所有真实终态，并用心跳兜底

失败、停止、卡住、上传终止都属于终态。但“状态文件说失败了”不等于“没有子进程还在写 `.part`”。用一次很小的心跳读取作为廉价兜底，比每轮全树 `rglob` 更合理。

### 5.4 隐藏成本往往比显式代码更贵

本次审计发现的高成本操作包括：

- 每次状态刷新通过 PowerShell 做 DPAPI 解密
- 每 15 秒对整张 inventory 逐行 `stat`
- 每 10 秒对整批数据 `sorted(rglob("*"))`
- 每个下载文件新建一个 boto3 client
- 并发打开 NetCDF/HDF5 做校验
- 在高频调用的地方枚举 A:\–Z:\

这些都不是“明显的死循环”，但在机械盘上会持续放大系统压力。

### 5.5 应用侧证据和硬件侧证据要分开

Windows 蓝屏需要同时看：

- 应用是否制造了极端 I/O / 内存 / 线程压力
- 是否存在内存、SSD/HDD、存储驱动、文件过滤驱动、Hyper-V/WSL 的问题

不能因为代码有 I/O 问题就断定蓝屏一定是代码造成的；也不能因为蓝屏可能是硬件问题就忽略代码的放大作用。

### 5.6 回归测试要断言“不要做什么”

这次新增的测试不仅验证结果，还显式断言：

- 空闲队列不得调用 `task_summaries()`
- 终态轻量路径不得调用 `_task_summary()` 或 `has_recent_download_part()`

这种“负向断言”比单纯测返回值更能防止性能问题回归。

---

## 6. 未改内容与后续建议

以下内容在第三轮之后**仍未修改**，下一个对话应优先评估。

### 6.1 上传器全树扫描（原审计 P0-5a，已完成）

文件：`src/geo_downloader/geo_ring_cloud_auto_uploader.py`

已修：

- `watch_and_upload()` 在 inventory 存在时使用 pending 索引，不再每 10 秒 `sorted(rglob("*"))`。
- 按目录 `mtime_ns` 跳过未变化目录，只 `stat` pending 文件。
- `batch_status.json` 增加 `excluded_products`，pending 分母不再包含被排除的产品。
- inventory 缺失时回退到 `reconcile_seconds`（默认 300 秒）的慢速全树对账。

仍然存在的边界：

- pending 索引依赖 inventory 的 `local_path` 与 `batch_root` 一致；不一致的行会被跳过。
- inventory 完全缺失时，上传器只能依赖慢速回退对账。

### 6.2 下载器资源使用（原审计 P0-6，部分完成）

文件：`src/geo_downloader/geo_cloud_downloader.py`

已修：

- `run_download_s3_range()` 的 worker 不再每个文件新建 boto3 client；改为按运行/线程复用。
- `inventory_goes_day()` / `inventory_himawari_day()` 支持共享 `client_state`。

仍未改：

- `run_inventory()` 一次性提交所有 job，所有结果累积在内存后写 CSV。
- 16 路下载并发打开 NetCDF/HDF5 校验。
- 每文件完成后写 `download_parallelism_status.json`，与大数据写入在同一块机械盘上交错。

建议：

- inventory 分批落盘。
- NetCDF/HDF5 校验限制为 1–2 路，或批次结束后统一校验。
- 降低并发默认值（尤其机械盘）。

### 6.3 PS1 输出缓冲

文件：`src/geo_downloader/geo_ring_cloud_transfer_batch.ps1`

- `Invoke-DownloadPython` 用 `$commandOutput = & ... 2>&1` 先缓存全部子进程输出，再写日志。
- 长任务/大量 stderr 时可能占用较大内存。

建议改为逐行流式写入日志。

### 6.4 旧版监控脚本

文件：`src/geo_downloader/monitor_dashboard.py`

- 每次刷新启动 PowerShell 子进程。
- 对 `DOWNLOAD_ROOT` 做 `rglob("*.part")`。
- 前端 10 秒刷新。

主仪表盘目前只 import 了它的几个函数，但如果单独运行该脚本，风险仍然很高。

### 6.5 清理脚本硬编码路径

文件：`scripts/cleanup_verified_data.ps1`

- 硬编码 `F:\GEO_Cloud_2024_batches`。
- 使用 `Remove-Item -Recurse -Force`。

建议改为必填参数，并做根路径/驱动器校验，避免误删其他盘数据。

### 6.6 旧计划任务与旧副本

系统里仍存在指向旧副本的计划任务：

```text
D:\AAAresearch_paper\third_report\code\geo_cloud_download\...
```

建议：

- 禁用所有不再使用的 `GeoRingCloud-*` 计划任务。
- 确认本机只运行一套代码（当前仓库或旧副本，不要混跑）。

### 6.7 硬件/驱动排查

仍需并行进行：

- Windows 内存诊断或 MemTest86
- `F:` 机械盘 SMART、`chkdsk F: /scan`
- 存储/芯片组驱动更新
- Hyper-V / WSL / Docker / VBS 相关组件检查
- 杀毒/文件过滤驱动对数据目录的实时扫描排除
- 页面文件与崩溃转储配置检查

---

## 7. 新对话快速接手清单

1. 查看提交：

   ```powershell
   git log --oneline -5
   git show --stat 9a1f87e
   ```

2. 查看第一轮完整改动：

   ```powershell
   git show 9a1f87e -- src/geo_downloader/geo_ring_cloud_transfer_dashboard.py
   git show 9a1f87e -- src/geo_downloader/geo_ring_cloud/batch_queue.py
   git show 9a1f87e -- src/geo_downloader/tests/test_geo_ring_cloud_transfer_batch.py
   ```

3. 查看第二轮改动（提交后用实际 hash）：

   ```powershell
   git log --oneline -5
   git show HEAD -- src/geo_downloader/geo_ring_cloud/checksums.py
   git show HEAD -- src/geo_downloader/geo_cloud_downloader.py
   git show HEAD -- src/geo_downloader/geo_ring_cloud_auto_uploader.py
   git show HEAD -- src/geo_downloader/geo_ring_cloud_transfer_batch.py
   ```

4. 关键函数：

   - `DashboardState._process_batch_queue_once_unlocked`
   - `DashboardState.task_summaries`
   - `DashboardState._task_summary_lite`
   - `DashboardState._compute_waiting_queue_updates`
   - `DashboardState.status_cached`
   - `DashboardState.__init__` 中的缓存字段
   - `read_inventory_by_remote_type`
   - `BoundedThreadingHTTPServer`
   - `batch_queue._collect_authoritative_inventory`
   - `geo_cloud_downloader.thread_s3_client`
   - `geo_ring_cloud.checksums.ChecksumCache`
   - `geo_ring_cloud.checksums.sha256_for_file`
   - `prepare_manifest()` 内部的 checksum cache 接入
   - `watch_and_upload()` / `build_auto_upload_manifest()` 的 cache 接入

5. 跑测试：

   ```powershell
   python -m pytest -q
   ```

6. 下一步优先级：

   1. 上传器 pending 索引（P0-5a）：消除每 10 秒 `rglob`
   2. inventory 分批落盘 + NetCDF 校验限流（P0-6 剩余）
   3. PS1 输出改为流式写入
   4. 禁用旧计划任务/旧副本
   5. 硬件/驱动排查
   6. 视情况降低默认下载/上传并发

---

## 8. 当前 Git 状态

截至本文档更新时：

- 第一轮 `9a1f87e` 已 push：

  ```text
  a24831a..9a1f87e  main -> main
  ```

- 第二轮 `07da3e7` 已 push：

  ```text
  9dc6e2f..07da3e7  main -> main
  ```

- 第三轮代码已修改并通过 `79 passed`，但**尚未提交**。
- 以下文件仍是未跟踪状态，未纳入任何一轮提交：

  ```text
  AGENTS.md
  SETUP.md
  docs/system-flow.mmd
  scripts/cleanup_verified_data.ps1
  src/geo_downloader/tests/__init__.py
  ```

  这些文件在本次工作开始前就已存在，是否提交需要用户单独确认。

---

## 9. 第二轮改动明细（P0-6 + P0-5b）

### 9.1 P0-6：boto3 client 按运行/线程复用

文件：`src/geo_downloader/geo_cloud_downloader.py`

- 新增 `thread_s3_client(state)`：
  - 从调用方提供的 `threading.local()` 中取 client。
  - 没有则创建一次并缓存。
- `run_inventory()`：
  - 创建 `inventory_client_state = threading.local()`。
  - GOES / Himawari 每日 job 通过 lambda 传入同一个 state。
- `inventory_goes_day()`、`inventory_himawari_day()`：
  - 新增可选 `client_state` 参数。
  - 不传时保持旧行为（直接 `get_s3_client()`），方便直接调用和测试。
- `run_download_s3_range()`：
  - 创建 `download_client_state = threading.local()`。
  - worker 使用 `thread_s3_client(download_client_state)`。

效果：

- 16 个下载线程最多 16 个 client，而不是每个文件一个。
- inventory 的每个工作线程也复用 client。
- 没有引入全局 thread-local，避免测试之间互相污染。

### 9.2 P0-5b：持久化 SHA-256 cache

新增文件：`src/geo_downloader/geo_ring_cloud/checksums.py`

- `ChecksumCache`：
  - JSONL 缓存，默认 `<batch>/transfer/checksum_cache.jsonl`。
  - 键为 `(resolved local_path, size_bytes, mtime_ns)`。
  - 支持增量读取，避免每次加载整个文件。
- `sha256_for_file(path, cache)`：
  - 先查缓存。
  - miss 时获取跨进程锁 `transfer/checksum.lock`。
  - 拿锁后重新查一次，再计算 SHA-256。
  - 计算前后校验 `size/mtime_ns`，文件变化则重试一次，避免缓存坏摘要。
- 跨进程锁：
  - Windows 使用 `msvcrt.locking()`。
  - POSIX 使用 `fcntl.flock()`。
  - 等待超时默认 3600 秒。

接入点：

- `prepare_manifest()`：
  - 本地执行时使用 `ChecksumCache(output_dir / "checksum_cache.jsonl")`。
  - 服务器端独立验证脚本没有该模块时，自动回退到原来的 `sha256_file()`。
- `build_auto_upload_manifest()`：
  - 只有 manifest 里缺 `sha256` 时才计算，且优先使用 cache。
- `watch_and_upload()`：
  - 上传前计算前先查 cache。
  - ledger 行新增 `mtime_ns`，方便后续审计和复用。

效果：

- 同一文件在 `prepare`、连续上传、自动上传 manifest 之间最多计算一次。
- 第二次对未变化批次执行 `prepare` 时，不再全量读取数据文件。
- PS1 `prepare` 与连续上传器即使并发，也会通过锁串行化同一文件的哈希，避免重复读盘。

### 9.3 第二轮新增测试

- `test_checksum_cache_reuses_digest_and_invalidates_on_change`
- `test_checksum_cache_is_shared_across_instances`
- `test_prepare_manifest_reuses_checksum_cache`
- `test_thread_s3_client_reuses_one_client_per_run_state`
- `test_goes_daily_inventory_reuses_supplied_client_state`

测试结果：`74 passed`。

---

## 10. 第三轮改动明细（P0-5a：上传器 pending 索引）

文件：`src/geo_downloader/geo_ring_cloud_auto_uploader.py`

### 10.1 新增数据结构与辅助函数

- `PendingUpload`：`platform / local_path / relative / expected_size`。
- `parse_excluded_products()`：解析 `platform:product1,product2;...`。
- `inventory_files_for_batch()`：优先 `manifest_inventory.csv`，否则回退
  `manifest_meteosat_inventory.csv`。
- `expected_inventory_entries()`：
  - 只保留 `status=found`、日期/平台范围内、未被排除的 inventory 行。
  - S3 行使用权威 `size_bytes`；EUMETSAT/EPIC 使用 `None`，依赖两次轮询稳定。
  - 用 `local_path` 去重。
- `group_pending_files()`：按父目录分组。
- `scan_pending_files()`：
  - 目录 `mtime_ns` 未变化时跳过该目录下所有 pending 文件。
  - S3 预期大小匹配立即 ready；其他源需要连续两次 `(size, mtime_ns)` 一致。
  - `force=True` 用于周期性完整对账。

### 10.2 watch_and_upload 行为

- 有 inventory 时：
  - 建立 pending 索引，只 `stat` pending 文件。
  - `ready_queue` 保存已判定 ready 但尚未上传的文件。
  - 每轮最多上传 8 个；未上传的留在队列，下一轮继续，不受目录 mtime 跳过影响。
  - 成功上传后从 pending 和 ready queue 移除。
  - 上传失败/文件变化时保留在队列，下一轮重试。
- 无 inventory 时：
  - 回退到 `discover_completed_files()`。
  - 扫描间隔由 `--reconcile-seconds` 控制，默认 300 秒；不再每 10 秒全树扫描。
- `expected_files` 使用 inventory 条目总数，排除产品不再计入分母。
- 目录 mtime 优化对下载器安全：下载器先写 `.part`，再 `os.replace` 成最终文件，目录 mtime 会变化。

### 10.3 PS1 变更

`geo_ring_cloud_transfer_batch.ps1`：

- `Write-BatchStatus` 增加：

  ```powershell
  excluded_products = $ExcludedProducts
  ```

- 上传器从 `batch_status.json` 读取该字段，重建 pending 索引时会自动应用排除产品。

### 10.4 第三轮新增测试

- `test_parse_excluded_products_supports_platform_pairs`
- `test_expected_upload_count_includes_prior_ledger_entries`
- `test_expected_inventory_entries_filters_and_uses_s3_size`
- `test_scan_pending_files_uses_size_and_two_poll_stability`
- `test_watch_and_upload_uses_inventory_index_instead_of_rglob`

测试结果：`79 passed`。

### 10.5 第三轮验证要点

- 有 inventory 时，`discover_completed_files()` 不被调用（测试用 `AssertionError` 断言）。
- 第一次扫描时对象大小匹配即 ready。
- 目录 mtime 不变时第二次扫描不重复 `stat`。
- `force=True` 时稳定性检查仍能发现 ready 文件。
- `excluded_products` 正确过滤 pending 分母。
- `expected_upload_count()` 会把“已上传但不在当前 inventory 中”的 ledger 记录计入分母，避免混合 inventory/ledger 时进度超过 100%。
