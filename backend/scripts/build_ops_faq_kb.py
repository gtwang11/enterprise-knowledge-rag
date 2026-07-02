"""Build and import an operations FAQ knowledge base.

The generated FAQ entries are Chinese operational Q&A pairs distilled from
official technical documentation and cloud-vendor troubleshooting guides.
They are intentionally paraphrased instead of copied from the source pages.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import time
import uuid
from array import array
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
KNOWLEDGE_DIR = REPO_DIR / "knowledge_base"
OLD_FAQ_PATH = REPO_DIR / "FAQ_1000条.json"
OFFICIAL_OUTPUT = KNOWLEDGE_DIR / "official_ops_faq_1000.json"
MERGED_OUTPUT = KNOWLEDGE_DIR / "merged_ops_faq_2000.json"

sys.path.insert(0, str(BACKEND_DIR))


ALLOWED_CATEGORIES = {
    "账号问题",
    "网络问题",
    "硬件故障",
    "软件故障",
    "权限问题",
    "安全合规",
    "系统配置",
    "其他",
}


SOURCE_URLS = {
    "linux_proc": (
        "Linux man-pages proc(5)",
        "https://man7.org/linux/man-pages/man5/proc.5.html",
    ),
    "linux_vm": (
        "Linux Kernel sysctl vm documentation",
        "https://docs.kernel.org/admin-guide/sysctl/vm.html",
    ),
    "docker_daemon": (
        "Docker Docs - Troubleshooting the Docker daemon",
        "https://docs.docker.com/engine/daemon/troubleshoot/",
    ),
    "docker_logging": (
        "Docker Docs - Configure logging drivers",
        "https://docs.docker.com/engine/logging/configure/",
    ),
    "k8s_cluster": (
        "Kubernetes Docs - Troubleshooting Clusters",
        "https://kubernetes.io/docs/tasks/debug/debug-cluster/",
    ),
    "k8s_app": (
        "Kubernetes Docs - Debug Applications",
        "https://kubernetes.io/docs/tasks/debug/debug-application/",
    ),
    "nginx_logging": (
        "NGINX Docs - Configuring Logging",
        "https://docs.nginx.com/nginx/admin-guide/monitoring/logging/",
    ),
    "nginx_debug": (
        "NGINX Docs - A debugging log",
        "https://nginx.org/en/docs/debugging_log.html",
    ),
    "apache_logs": (
        "Apache HTTP Server Docs - Log Files",
        "https://httpd.apache.org/docs/current/logs.html",
    ),
    "mysql_problems": (
        "MySQL Reference Manual - Problems and Common Errors",
        "https://dev.mysql.com/doc/refman/8.4/en/problems.html",
    ),
    "postgres_logging": (
        "PostgreSQL Docs - Error Reporting and Logging",
        "https://www.postgresql.org/docs/current/runtime-config-logging.html",
    ),
    "postgres_start": (
        "PostgreSQL Docs - Starting the Database Server",
        "https://www.postgresql.org/docs/current/server-start.html",
    ),
    "redis_latency": (
        "Redis Docs - Diagnosing latency issues",
        "https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/",
    ),
    "redis_memory": (
        "Redis Docs - Memory optimization",
        "https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/",
    ),
    "aliyun_ssh": (
        "Alibaba Cloud ECS - SSH login troubleshooting",
        "https://www.alibabacloud.com/help/en/ecs/troubleshooting-guidelines-when-you-cannot-remotely-log-on-to-a-linux-instance-through-ssh",
    ),
    "aliyun_ping": (
        "Alibaba Cloud ECS - Public IP ping and port troubleshooting",
        "https://help.aliyun.com/zh/ecs/troubleshooting-for-ping-attempts-to-pass-the-server-and-port-disconnection",
    ),
    "huawei_ecs": (
        "Huawei Cloud ECS - Linux troubleshooting",
        "https://support.huaweicloud.com/trouble-ecs/ecs_trouble_0375.html",
    ),
    "tencent_login": (
        "Tencent Cloud CVM - Unable to log in to Linux instance",
        "https://cloud.tencent.com/document/product/213/35574",
    ),
    "tencent_ssh": (
        "Tencent Cloud CVM - SSH login troubleshooting",
        "https://cloud.tencent.com/document/product/213/37925",
    ),
    "tencent_web": (
        "Tencent Cloud CVM - Website cannot be accessed",
        "https://cloud.tencent.com/document/product/213/14633",
    ),
}


@dataclass(frozen=True)
class Scenario:
    product: str
    issue: str
    impact: str
    category: str
    checks: tuple[str, ...]
    actions: tuple[str, ...]
    verify: tuple[str, ...]
    escalate: str
    keywords: tuple[str, ...]
    source_key: str
    source_type: str = "官方技术文档"

    @property
    def source_name(self) -> str:
        return SOURCE_URLS[self.source_key][0]

    @property
    def source_url(self) -> str:
        return SOURCE_URLS[self.source_key][1]


def s(
    product: str,
    issue: str,
    impact: str,
    category: str,
    checks: Iterable[str],
    actions: Iterable[str],
    verify: Iterable[str],
    escalate: str,
    keywords: Iterable[str],
    source_key: str,
    source_type: str = "官方技术文档",
) -> Scenario:
    return Scenario(
        product=product,
        issue=issue,
        impact=impact,
        category=category,
        checks=tuple(checks),
        actions=tuple(actions),
        verify=tuple(verify),
        escalate=escalate,
        keywords=tuple(keywords),
        source_key=source_key,
        source_type=source_type,
    )


SCENARIOS: list[Scenario] = [
    s("Linux", "CPU 使用率持续过高", "主机响应变慢或接口超时", "系统配置",
      ["用 top、pidstat 或 ps 定位高 CPU 进程", "查看 /proc/loadavg、iowait 和上下文切换", "核对近期发布、定时任务和批处理"],
      ["保留现场输出后先限流或暂停非核心任务", "确认进程可安全重启再执行重启", "把异常命令行、PID、时间窗口记录到工单"],
      ["CPU 利用率回落并持续观察 10 分钟", "核心接口延迟恢复", "同类告警不再触发"],
      "涉及核心数据库、中间件或无法判断进程作用时升级给资深运维。", ["Linux", "CPU", "top", "pidstat", "proc"], "linux_proc"),
    s("Linux", "内存和 swap 压力升高", "服务被 OOM 或页面响应缓慢", "系统配置",
      ["用 free、vmstat、/proc/meminfo 判断内存结构", "检查是否有 OOM kill 记录", "确认缓存增长、大进程和 swap in/out"],
      ["先释放可确认的临时缓存或停止非核心任务", "评估进程泄漏后安排重启或扩容", "不要盲目清理 page cache 影响业务判断"],
      ["可用内存和 swap 活动恢复稳定", "业务进程没有继续被 OOM", "监控曲线趋于正常"],
      "内存持续泄漏、数据库缓存异常或需要调整内核参数时升级。", ["Linux", "内存", "swap", "OOM", "vmstat"], "linux_vm"),
    s("Linux", "磁盘空间不足", "日志无法写入或服务启动失败", "系统配置",
      ["用 df -h 确认文件系统占用", "用 du 定位大目录", "检查日志、缓存、容器层和备份文件"],
      ["优先清理过期日志、临时文件和无效备份", "压缩或转移可归档文件", "补充 logrotate 或保留策略"],
      ["磁盘使用率降到告警阈值以下", "新日志可以正常写入", "业务进程不再报 no space left"],
      "系统盘接近满且无法确认文件用途时升级，避免误删核心数据。", ["Linux", "磁盘", "df", "du", "logrotate"], "linux_proc"),
    s("Linux", "inode 被耗尽", "磁盘有空间但无法创建文件", "系统配置",
      ["用 df -i 查看 inode 使用率", "定位小文件密集目录", "检查缓存、session、邮件队列和临时目录"],
      ["删除已确认过期的小文件", "调整应用清理策略", "必要时迁移到更合适的文件系统"],
      ["inode 使用率恢复", "应用可以创建新文件", "目录增长速度受控"],
      "小文件属于业务数据或无法判断保留周期时升级。", ["Linux", "inode", "文件系统", "小文件"], "linux_proc"),
    s("Linux", "systemd 服务启动失败", "服务不可用或端口未监听", "软件故障",
      ["用 systemctl status 查看失败原因", "用 journalctl -u 查看启动日志", "核对配置文件、权限和依赖服务"],
      ["先执行配置校验或回滚最近变更", "修正权限、路径或环境变量", "确认依赖正常后再重启服务"],
      ["systemctl 状态为 active", "端口监听正常", "业务健康检查通过"],
      "涉及生产核心服务配置变更或反复重启失败时升级。", ["Linux", "systemd", "journalctl", "服务启动"], "linux_proc"),
    s("Linux", "时间同步偏差", "认证失败、日志时间错乱或任务误触发", "系统配置",
      ["查看 timedatectl 或 chronyc 状态", "确认 NTP 源和 UDP 123 连通", "对比业务日志时间线"],
      ["修复 NTP 源或网络策略", "小步校正时间，避免数据库和队列受到跳变影响", "记录偏差范围和恢复时间"],
      ["时间偏差回到阈值内", "认证和定时任务恢复", "日志顺序可追溯"],
      "偏差较大且涉及数据库、消息队列或审计系统时升级。", ["Linux", "NTP", "chrony", "时间同步"], "linux_proc"),
    s("Linux", "端口不通", "客户端连接超时或拒绝", "网络问题",
      ["确认服务是否监听目标端口", "检查本机防火墙和安全策略", "用 ss、curl、nc 分别验证本机和远端连通"],
      ["先恢复服务监听或修正绑定地址", "补齐防火墙放行规则", "保留源 IP、目标端口和测试结果"],
      ["端口从客户端可达", "应用日志有正常请求", "监控探测恢复"],
      "涉及跨网段路由、安全组或负载均衡时升级。", ["Linux", "端口", "ss", "firewalld", "iptables"], "linux_proc"),
    s("Linux", "文件句柄耗尽", "服务报 too many open files", "系统配置",
      ["查看进程打开文件数和 ulimit", "检查连接数、日志文件和 socket 泄漏", "核对 systemd LimitNOFILE 配置"],
      ["短期可重启异常进程释放句柄", "长期调整服务级文件句柄上限", "定位连接泄漏或未关闭文件的代码路径"],
      ["错误日志不再出现文件句柄告警", "连接数保持稳定", "新请求成功率恢复"],
      "需要调整系统级限制或怀疑程序泄漏时升级。", ["Linux", "ulimit", "文件句柄", "lsof"], "linux_proc"),
    s("Linux", "内核参数调整后异常", "网络、内存或文件系统行为异常", "系统配置",
      ["核对 sysctl 当前值和变更记录", "确认参数是否写入持久化配置", "对比调整前后的监控曲线"],
      ["先回滚未经验证的参数", "在测试环境复现再评估", "记录参数名、旧值、新值和影响范围"],
      ["系统指标恢复到基线", "相关告警消除", "参数配置与变更单一致"],
      "涉及 vm、net、fs 等内核参数并影响生产时升级。", ["Linux", "sysctl", "内核参数", "vm"], "linux_vm"),
    s("Linux", "/proc 信息无法查看", "排障时无法看到进程细节", "权限问题",
      ["确认当前用户权限和 /proc 挂载选项", "检查 hidepid 等安全配置", "判断是否通过堡垒机或受限账号登录"],
      ["按最小权限申请临时排障权限", "使用受批准的观测命令收集信息", "不要绕过审计策略"],
      ["可以查看被授权范围内的进程信息", "审计记录完整", "排障数据满足定位需要"],
      "需要提升权限或查看敏感进程信息时走审批并升级。", ["Linux", "proc", "hidepid", "权限"], "linux_proc", "官方技术文档"),

    s("Docker", "Docker daemon 启动失败", "容器平台不可用", "软件故障",
      ["查看 dockerd 或 Docker Desktop 日志", "检查 daemon.json 语法", "确认存储驱动、证书和 socket 权限"],
      ["回滚最近的 daemon 配置", "修正 JSON 格式或路径权限", "确认依赖目录可读写后重启 Docker"],
      ["docker info 可以返回", "已有容器状态可查询", "新容器可正常启动"],
      "存储驱动损坏、证书异常或生产容器无法恢复时升级。", ["Docker", "dockerd", "daemon.json", "启动失败"], "docker_daemon"),
    s("Docker", "容器异常退出", "业务实例不可用", "软件故障",
      ["用 docker ps -a 查看退出码", "用 docker logs 查看应用错误", "检查资源限制、健康检查和启动命令"],
      ["按退出码判断是应用错误、OOM 还是配置问题", "修正环境变量或挂载后重建容器", "保留日志再重启"],
      ["容器状态为 Up", "健康检查通过", "业务端口可访问"],
      "退出码反复出现、涉及数据卷或状态服务时升级。", ["Docker", "container", "exit code", "logs"], "docker_daemon"),
    s("Docker", "镜像拉取失败", "发布或扩容失败", "网络问题",
      ["确认镜像名、tag 和仓库权限", "检查代理、DNS 和仓库连通", "查看 Docker daemon 网络配置"],
      ["修正镜像地址或登录凭据", "配置可信代理或镜像加速", "避免在生产直接使用 latest"],
      ["docker pull 成功", "部署流水线继续执行", "节点缓存中有目标镜像"],
      "私有仓库证书、跨境网络或凭据系统异常时升级。", ["Docker", "image pull", "registry", "proxy"], "docker_daemon"),
    s("Docker", "容器端口无法访问", "外部用户连接失败", "网络问题",
      ["核对 docker port 和端口映射", "确认应用在容器内监听 0.0.0.0", "检查主机防火墙和安全组"],
      ["修正 compose 或 run 的端口映射", "恢复应用监听地址", "补齐主机侧放行规则"],
      ["从主机和远端都能访问端口", "访问日志出现请求", "错误率恢复"],
      "涉及宿主机网络策略、NAT 或多容器网络时升级。", ["Docker", "端口映射", "bridge", "iptables"], "docker_daemon"),
    s("Docker", "容器日志占满磁盘", "宿主机磁盘告警", "系统配置",
      ["确认 json-file 或 local 日志驱动配置", "定位容器日志文件大小", "检查日志轮转参数"],
      ["先归档或清理过期容器日志", "配置 max-size 和 max-file", "推动应用降低异常日志量"],
      ["磁盘空间恢复", "日志继续写入且会轮转", "容器没有因日志清理被破坏"],
      "日志属于审计证据或磁盘空间无法快速恢复时升级。", ["Docker", "logging driver", "json-file", "日志轮转"], "docker_logging"),
    s("Docker", "容器 OOM", "服务被系统杀死或频繁重启", "软件故障",
      ["查看 docker inspect 中 OOMKilled", "检查内存限制和应用堆配置", "对比容器内外内存指标"],
      ["先扩容或降低并发保护业务", "修正应用内存参数", "保留 OOM 时间点日志供分析"],
      ["容器不再被 OOMKill", "内存曲线稳定", "请求成功率恢复"],
      "内存持续增长或涉及数据库缓存参数时升级。", ["Docker", "OOM", "memory limit", "inspect"], "docker_daemon"),
    s("Docker", "Docker socket 权限不足", "普通用户无法执行 docker 命令", "权限问题",
      ["确认用户是否在 docker 组", "检查 /var/run/docker.sock 权限", "判断是否应使用 rootless 模式"],
      ["按安全规范申请用户组权限", "重新登录使组权限生效", "禁止随意放宽 socket 权限"],
      ["授权用户可执行必要命令", "审计记录完整", "未扩大无关权限"],
      "需要生产主机 Docker 管理权限时必须升级审批。", ["Docker", "socket", "权限", "rootless"], "docker_daemon"),
    s("Docker", "容器 DNS 解析失败", "容器内无法访问依赖域名", "网络问题",
      ["在容器内测试 DNS 解析", "检查 Docker DNS、宿主机 resolv.conf 和网络策略", "确认依赖域名是否可达"],
      ["修复 DNS 服务器配置", "必要时指定容器 DNS", "避免写死临时 hosts 造成后续漂移"],
      ["容器内 nslookup/curl 成功", "依赖调用恢复", "错误日志下降"],
      "涉及企业 DNS、服务发现或跨网络访问时升级。", ["Docker", "DNS", "resolv.conf", "network"], "docker_daemon"),
    s("Docker", "数据卷挂载异常", "容器启动后找不到数据或配置", "系统配置",
      ["核对 volume/bind mount 路径", "检查宿主机目录权限和 SELinux/AppArmor", "确认 compose 文件是否变更"],
      ["修正挂载路径和权限", "恢复配置文件后重建容器", "对状态数据先备份再操作"],
      ["容器内文件可见", "应用读取配置成功", "业务数据完整"],
      "涉及数据库、消息队列等有状态数据卷时升级。", ["Docker", "volume", "bind mount", "权限"], "docker_daemon"),
    s("Docker", "Docker 对象堆积", "宿主机磁盘和 inode 告警", "系统配置",
      ["用 docker system df 查看镜像、容器、卷占用", "识别未使用对象", "确认卷是否仍被业务依赖"],
      ["清理停止容器和悬空镜像", "谨慎处理 volume", "把清理规则写入运维周期任务"],
      ["磁盘占用下降", "现有容器不受影响", "清理动作有记录"],
      "无法确认 volume 归属或清理影响生产时升级。", ["Docker", "prune", "磁盘", "volume"], "docker_daemon"),

    s("Kubernetes", "Pod CrashLoopBackOff", "应用副本反复重启", "软件故障",
      ["kubectl describe pod 查看事件", "kubectl logs --previous 查看上次退出日志", "检查探针、资源限制和启动参数"],
      ["先定位退出原因再调整配置", "必要时回滚最近镜像", "保留事件和日志给开发或专家"],
      ["Pod restart 次数不再增长", "Ready 状态稳定", "服务端点恢复"],
      "涉及生产核心服务、数据初始化失败或无法解释退出码时升级。", ["Kubernetes", "Pod", "CrashLoopBackOff", "logs"], "k8s_app"),
    s("Kubernetes", "ImagePullBackOff", "工作负载无法拉起", "网络问题",
      ["describe pod 查看拉取错误", "确认镜像地址、tag 和 imagePullSecret", "检查节点到镜像仓库网络"],
      ["修正镜像名或密钥", "确认仓库证书和代理", "必要时回滚到可用镜像"],
      ["Pod 成功拉取镜像", "状态进入 Running", "发布流水线恢复"],
      "私有仓库权限、证书或大范围节点拉取失败时升级。", ["Kubernetes", "ImagePullBackOff", "imagePullSecret"], "k8s_app"),
    s("Kubernetes", "Pod Pending", "应用无法调度", "系统配置",
      ["describe pod 查看调度失败事件", "检查节点资源、污点容忍和亲和性", "确认 PVC 是否绑定"],
      ["释放资源或调整 requests", "补充 tolerations 或 nodeSelector", "修复存储绑定问题"],
      ["Pod 被调度到节点", "容器正常启动", "资源水位保持安全"],
      "集群资源不足、调度策略复杂或存储异常时升级。", ["Kubernetes", "Pending", "scheduler", "requests"], "k8s_cluster"),
    s("Kubernetes", "Service 无 endpoints", "服务名可解析但请求失败", "网络问题",
      ["检查 Service selector 与 Pod label 是否匹配", "查看 EndpointSlice", "确认 Pod Ready 状态"],
      ["修正标签或 selector", "处理 Pod 不 Ready 的根因", "避免直接改生产 Service 造成流量漂移"],
      ["endpoints 出现后端地址", "ClusterIP 访问成功", "业务调用恢复"],
      "涉及服务发现、大规模流量切换或 ingress 联动时升级。", ["Kubernetes", "Service", "endpoints", "selector"], "k8s_app"),
    s("Kubernetes", "Node NotReady", "节点上 Pod 不可调度或被驱逐", "系统配置",
      ["查看 node condition 和 kubelet 状态", "检查磁盘、内存、网络和容器运行时", "查看 kubelet 日志"],
      ["先隔离异常节点避免继续调度", "恢复 kubelet 或运行时", "必要时排水并迁移业务"],
      ["节点恢复 Ready", "系统 Pod 正常", "业务副本满足期望数量"],
      "多节点异常、控制面告警或节点需要重启时升级。", ["Kubernetes", "NodeNotReady", "kubelet", "runtime"], "k8s_cluster"),
    s("Kubernetes", "CoreDNS 异常", "集群内域名解析失败", "网络问题",
      ["检查 coredns Pod 状态和日志", "测试 Service 域名解析", "确认上游 DNS 和网络策略"],
      ["恢复 coredns 副本", "修正 Corefile 或上游 DNS", "避免直接修改生产 DNS 规则"],
      ["nslookup 服务名成功", "依赖调用恢复", "CoreDNS 错误率下降"],
      "全集群解析异常或 Corefile 变更不明确时升级。", ["Kubernetes", "CoreDNS", "DNS", "Service"], "k8s_cluster"),
    s("Kubernetes", "Ingress 502 或 504", "入口访问失败", "网络问题",
      ["查看 ingress controller 日志", "确认 Service endpoints 和后端端口", "检查超时、TLS 和路由规则"],
      ["修正后端服务或端口配置", "回滚错误路由", "对慢请求调整超时前先确认根因"],
      ["外部域名访问成功", "入口日志状态码恢复", "后端应用有正常请求"],
      "涉及公网入口、证书或跨团队服务依赖时升级。", ["Kubernetes", "Ingress", "502", "504"], "k8s_app"),
    s("Kubernetes", "PVC 挂载失败", "Pod 无法读取持久化数据", "系统配置",
      ["describe pod 和 pvc 查看事件", "确认 PV 绑定、存储类和节点挂载", "检查权限和容量"],
      ["修复 PVC/PV 绑定或存储后端", "不要删除有数据的 PV", "对应用做停机窗口评估"],
      ["PVC Bound 且 Pod Running", "应用能读写挂载目录", "数据完整性校验通过"],
      "涉及数据库卷、存储后端故障或数据风险时升级。", ["Kubernetes", "PVC", "PV", "mount"], "k8s_app"),
    s("Kubernetes", "健康探针失败", "Pod 被反复重启或流量摘除", "软件故障",
      ["查看 readiness/liveness 配置", "检查探针路径、端口和超时", "对比应用实际启动耗时"],
      ["修正探针参数或应用健康接口", "延长 initialDelay 前先确认慢启动原因", "避免关闭探针掩盖故障"],
      ["探针成功率恢复", "Pod Ready 稳定", "流量恢复"],
      "探针失败源于应用依赖或数据库不可用时升级。", ["Kubernetes", "probe", "readiness", "liveness"], "k8s_app"),
    s("Kubernetes", "资源限额导致性能抖动", "接口延迟升高或容器被限流", "系统配置",
      ["查看 requests/limits 与实际使用", "检查 CPU throttling 和 OOM 事件", "确认 HPA 指标是否有效"],
      ["调整资源配额需走变更", "短期扩副本缓解", "长期优化容量模型"],
      ["延迟和错误率回落", "容器不再被限流或 OOM", "HPA 扩缩容正常"],
      "需要调整生产配额、扩容节点或修改 HPA 策略时升级。", ["Kubernetes", "resources", "limit", "HPA"], "k8s_cluster"),

    s("Nginx", "反向代理 502", "页面返回 Bad Gateway", "软件故障",
      ["查看 error_log 中 upstream 错误", "确认后端端口和进程状态", "检查 proxy_pass、DNS 和防火墙"],
      ["恢复后端服务或修正 upstream 配置", "配置变更前执行 nginx -t", "重载而不是随意强杀进程"],
      ["502 状态码消失", "upstream 响应时间正常", "访问日志有成功请求"],
      "涉及核心入口、灰度发布或多 upstream 同时异常时升级。", ["Nginx", "502", "upstream", "error_log"], "nginx_logging"),
    s("Nginx", "反向代理 504", "请求超时", "软件故障",
      ["查看 upstream_response_time", "确认后端是否慢查询或阻塞", "检查 proxy_read_timeout 等超时配置"],
      ["先定位后端耗时根因", "必要时临时扩容后端", "谨慎调整超时避免掩盖慢故障"],
      ["超时请求下降", "后端耗时恢复", "入口监控恢复"],
      "后端数据库、队列或跨系统调用慢时升级。", ["Nginx", "504", "timeout", "upstream"], "nginx_logging"),
    s("Nginx", "配置校验失败", "重载或启动失败", "系统配置",
      ["执行 nginx -t 查看具体文件和行号", "检查 include 路径、分号和块结构", "核对证书、upstream 和变量"],
      ["修正配置后再次校验", "变更前备份当前配置", "只在校验通过后 reload"],
      ["nginx -t successful", "reload 后 worker 正常", "业务访问无异常"],
      "配置涉及入口路由、安全策略或证书替换时升级复核。", ["Nginx", "nginx -t", "配置", "reload"], "nginx_logging"),
    s("Nginx", "访问日志缺失", "无法追踪请求", "安全合规",
      ["检查 access_log 指令和日志路径权限", "确认 location/server 级别是否覆盖", "查看磁盘空间和日志轮转"],
      ["修正日志路径和权限", "恢复标准日志格式", "补充日志轮转避免再次写满"],
      ["新请求写入 access_log", "日志字段完整", "审计链路可追溯"],
      "涉及审计留痕缺失或日志集中采集故障时升级。", ["Nginx", "access_log", "日志", "审计"], "nginx_logging"),
    s("Nginx", "错误日志过大", "磁盘被日志占满", "系统配置",
      ["查看 error_log 级别", "定位重复错误来源", "检查 logrotate 是否生效"],
      ["先修复产生错误的 upstream 或配置", "恢复合理日志级别", "设置轮转和保留周期"],
      ["日志增长速度下降", "磁盘使用率恢复", "关键错误仍可记录"],
      "日志可能包含安全事件或证据时先升级确认再清理。", ["Nginx", "error_log", "logrotate", "磁盘"], "nginx_logging"),
    s("Nginx", "TLS 证书异常", "HTTPS 访问失败或浏览器告警", "安全合规",
      ["检查证书有效期、链完整性和私钥匹配", "查看 nginx -t 和 error_log", "确认 SNI/server_name 配置"],
      ["替换正确证书链", "修正权限后 reload", "保留证书变更记录"],
      ["HTTPS 握手成功", "证书链校验通过", "业务域名访问正常"],
      "生产证书更换、私钥泄露疑似事件或多域名证书异常时升级。", ["Nginx", "TLS", "证书", "SNI"], "nginx_logging"),
    s("Nginx", "403 Forbidden", "静态资源或目录访问被拒绝", "权限问题",
      ["检查 root/alias 路径", "确认文件权限和执行目录权限", "查看 location 匹配和 autoindex 策略"],
      ["修正路径和权限", "避免为排障直接放开目录列表", "按最小权限恢复访问"],
      ["目标资源返回 200", "目录未暴露敏感文件", "错误日志无 permission denied"],
      "涉及敏感目录、下载权限或安全策略时升级。", ["Nginx", "403", "权限", "alias"], "nginx_logging"),
    s("Nginx", "worker_connections 耗尽", "新连接失败", "系统配置",
      ["查看 error_log 中连接数告警", "核对 worker_connections 和系统 ulimit", "分析长连接和 upstream 慢请求"],
      ["短期限流或扩容入口", "调整连接上限需同步系统限制", "处理后端慢导致的连接堆积"],
      ["连接告警消失", "活跃连接回到安全水位", "请求成功率恢复"],
      "入口流量突增、攻击流量或需要调整系统参数时升级。", ["Nginx", "worker_connections", "ulimit"], "nginx_logging"),
    s("Nginx", "需要开启 debug 日志定位问题", "普通日志不足以定位请求路径", "系统配置",
      ["确认 Nginx 是否编译 debug 支持", "限定 debug_connection 或最小范围", "评估日志量和磁盘空间"],
      ["只对指定客户端或短时间开启", "复现后立即恢复日志级别", "保存关键片段到工单"],
      ["问题路径被捕获", "日志量受控", "定位完成后 debug 已关闭"],
      "生产入口开启 debug 前必须升级审批。", ["Nginx", "debug log", "debug_connection"], "nginx_debug"),
    s("Nginx", "upstream 连接被拒绝", "代理请求直接失败", "网络问题",
      ["在 Nginx 主机 curl 后端地址", "确认 upstream IP、端口和防火墙", "检查后端监听地址"],
      ["恢复后端进程", "修正 upstream 地址或端口", "同步服务发现配置"],
      ["Nginx 到后端连通", "502 错误消失", "后端访问日志有流量"],
      "后端地址由服务发现或负载均衡自动生成时升级。", ["Nginx", "connect refused", "upstream", "端口"], "nginx_logging"),

    s("Apache", "httpd 启动失败", "站点无法提供服务", "软件故障",
      ["执行 apachectl configtest", "查看 error_log", "核对端口占用、模块和配置语法"],
      ["修正配置错误或端口冲突", "确认模块加载路径", "校验通过后启动服务"],
      ["httpd 状态正常", "监听端口恢复", "站点返回正常状态码"],
      "涉及生产虚拟主机、证书或核心模块变更时升级。", ["Apache", "httpd", "configtest", "error_log"], "apache_logs"),
    s("Apache", "403 Forbidden", "用户访问目录被拒绝", "权限问题",
      ["查看 error_log 中权限原因", "检查 Directory/Require 配置", "确认文件系统权限和 SELinux"],
      ["按最小权限修正 Require 或目录权限", "避免直接开放全部目录", "记录访问控制变更"],
      ["目标 URL 返回正常", "未暴露无关目录", "错误日志不再出现拒绝记录"],
      "涉及外网访问控制、敏感路径或认证策略时升级。", ["Apache", "403", "Require", "Directory"], "apache_logs"),
    s("Apache", "访问日志没有请求记录", "无法定位用户访问", "安全合规",
      ["检查 CustomLog 配置", "确认虚拟主机是否单独定义日志", "检查日志路径权限和磁盘空间"],
      ["恢复标准访问日志", "修复日志目录权限", "同步日志采集规则"],
      ["新请求写入 access_log", "字段格式满足审计", "日志采集平台有数据"],
      "审计日志缺失或日志平台异常时升级。", ["Apache", "CustomLog", "access_log", "审计"], "apache_logs"),
    s("Apache", "虚拟主机匹配异常", "访问到错误站点", "系统配置",
      ["检查 ServerName、ServerAlias 和 VirtualHost 顺序", "查看访问日志 Host 字段", "确认 DNS 指向"],
      ["修正虚拟主机名称和证书绑定", "重载前执行 configtest", "保留变更记录"],
      ["域名访问到正确站点", "证书和 Host 匹配", "错误站点访问不再出现"],
      "涉及多域名入口或证书切换时升级。", ["Apache", "VirtualHost", "ServerName", "域名"], "apache_logs"),
    s("Apache", ".htaccess 规则异常", "重写或访问控制不生效", "系统配置",
      ["确认 AllowOverride 是否允许", "查看 error_log 中 rewrite 或权限错误", "检查规则顺序"],
      ["修正规则并在测试环境验证", "优先把稳定规则放入主配置", "避免循环重写"],
      ["目标 URL 跳转正确", "没有重写循环", "访问控制符合预期"],
      "复杂重写影响多个业务路径时升级。", ["Apache", ".htaccess", "RewriteRule", "AllowOverride"], "apache_logs"),
    s("Apache", "连接数过高", "新请求排队或超时", "系统配置",
      ["查看 server-status 或进程数", "检查 MPM 配置和后端耗时", "确认是否有异常流量"],
      ["先限流或扩容", "优化后端慢请求", "调整 MPM 参数需变更审批"],
      ["活跃连接下降", "请求延迟恢复", "错误率回落"],
      "疑似攻击流量或需要调整并发参数时升级。", ["Apache", "MPM", "连接数", "server-status"], "apache_logs"),
    s("Apache", "模块未加载", "配置指令无法识别", "软件故障",
      ["查看启动错误中的未知指令", "确认 LoadModule 配置", "检查模块包是否安装"],
      ["安装或启用对应模块", "清理无用配置片段", "configtest 通过后 reload"],
      ["服务正常启动", "相关功能可用", "日志无未知指令错误"],
      "模块变更影响安全、代理或认证能力时升级。", ["Apache", "LoadModule", "模块", "配置"], "apache_logs"),
    s("Apache", "反向代理 502", "代理后端访问失败", "软件故障",
      ["查看 error_log 的 proxy 错误", "确认后端地址和端口", "检查 ProxyPass 规则"],
      ["恢复后端服务", "修正代理规则", "重载前进行配置校验"],
      ["代理路径返回正常", "后端日志有请求", "502 告警消失"],
      "涉及多个后端或灰度路由时升级。", ["Apache", "ProxyPass", "502", "proxy"], "apache_logs"),
    s("Apache", "日志轮转异常", "日志文件持续增长", "系统配置",
      ["检查 rotatelogs 或系统 logrotate 配置", "确认 httpd 是否重新打开日志", "查看磁盘占用"],
      ["修复轮转规则", "必要时平滑重载服务", "补充保留周期"],
      ["新日志按周期切分", "磁盘空间稳定", "审计日志完整"],
      "日志为审计证据或磁盘已满影响业务时升级。", ["Apache", "rotatelogs", "logrotate", "日志"], "apache_logs"),
    s("Apache", "SSL 证书配置错误", "HTTPS 握手失败", "安全合规",
      ["检查证书、私钥和链文件路径", "执行 configtest", "查看 SSL 相关 error_log"],
      ["替换匹配的证书和私钥", "修复权限后 reload", "记录证书变更"],
      ["HTTPS 握手成功", "浏览器无证书告警", "站点正常访问"],
      "证书过期影响外网业务或疑似私钥泄露时升级。", ["Apache", "SSL", "证书", "HTTPS"], "apache_logs"),

    s("MySQL", "Access denied 登录失败", "应用无法连接数据库", "账号问题",
      ["确认用户名、来源主机和认证插件", "查看错误日志和授权表", "核对密码是否过期或变更"],
      ["修正账号授权或密码配置", "按最小权限补充 host 授权", "避免直接使用高权限账号替代"],
      ["应用连接成功", "失败登录告警消失", "账号权限符合审批"],
      "涉及生产账号授权、root 权限或批量账号异常时升级。", ["MySQL", "Access denied", "账号", "权限"], "mysql_problems"),
    s("MySQL", "Too many connections", "应用连接数据库失败", "软件故障",
      ["查看当前连接数和 max_connections", "识别长连接和空闲连接", "检查应用连接池配置"],
      ["短期清理异常会话或扩容连接池", "长期优化连接释放", "谨慎调整 max_connections"],
      ["连接数回落", "应用连接成功", "数据库 CPU/内存可承受"],
      "连接暴涨原因不明或需要改生产参数时升级。", ["MySQL", "max_connections", "连接池"], "mysql_problems"),
    s("MySQL", "服务无法启动", "数据库不可用", "软件故障",
      ["查看 MySQL error log", "检查配置文件语法、端口和数据目录权限", "确认磁盘空间"],
      ["修正配置或权限", "保留错误日志", "不要直接删除数据文件"],
      ["mysqld 正常运行", "端口监听", "应用连接恢复"],
      "涉及 InnoDB 恢复、数据目录损坏或生产库不可用时升级。", ["MySQL", "启动失败", "error log", "datadir"], "mysql_problems"),
    s("MySQL", "慢查询增多", "接口响应变慢", "软件故障",
      ["确认 slow query log 是否开启", "分析执行时间、扫描行数和索引使用", "对比发布或数据量变化"],
      ["优先优化 SQL 或索引", "短期可限流或扩容只读实例", "避免未经验证直接改全局参数"],
      ["慢查询数量下降", "接口延迟恢复", "数据库负载回落"],
      "涉及核心 SQL、表结构变更或索引风险时升级。", ["MySQL", "slow query", "索引", "性能"], "mysql_problems"),
    s("MySQL", "表锁或行锁等待", "事务长时间阻塞", "软件故障",
      ["查看 processlist 和 InnoDB 锁等待", "确认长事务来源", "保留阻塞链路"],
      ["联系业务确认后处理阻塞事务", "优化事务范围", "避免随意 kill 写事务"],
      ["锁等待消失", "事务提交恢复", "业务错误率下降"],
      "生产写事务阻塞、无法判断影响范围时升级。", ["MySQL", "锁等待", "InnoDB", "事务"], "mysql_problems"),
    s("MySQL", "数据库磁盘空间不足", "写入失败或复制中断", "系统配置",
      ["查看数据目录、binlog 和临时文件占用", "确认磁盘水位和增长速度", "核对 binlog 保留策略"],
      ["清理过期 binlog 需按规范执行", "扩容磁盘或迁移归档", "禁止删除数据文件"],
      ["磁盘空间恢复", "写入和复制正常", "保留策略生效"],
      "生产库磁盘满或 binlog 清理不确定时升级。", ["MySQL", "磁盘", "binlog", "datadir"], "mysql_problems"),
    s("MySQL", "主从复制延迟", "读到旧数据或切换风险升高", "软件故障",
      ["查看复制线程状态和延迟指标", "确认网络、SQL 执行和大事务", "检查从库资源水位"],
      ["先降低读流量或切换读源", "处理大事务和慢 SQL", "避免强制跳过错误"],
      ["延迟回落", "复制线程正常", "读写一致性风险解除"],
      "复制报错、需要跳过事务或涉及主从切换时升级。", ["MySQL", "复制延迟", "replication", "大事务"], "mysql_problems"),
    s("MySQL", "连接被拒绝", "应用无法建立 TCP 连接", "网络问题",
      ["确认 mysqld 端口监听", "检查 bind-address、防火墙和安全组", "从应用主机测试连通"],
      ["恢复服务监听", "修正绑定地址或网络策略", "确认账号 host 授权"],
      ["应用主机可连接端口", "数据库日志有连接", "业务恢复"],
      "涉及跨网段访问、云安全组或数据库代理时升级。", ["MySQL", "connection refused", "bind-address", "端口"], "mysql_problems"),
    s("MySQL", "字符集乱码", "查询结果出现异常字符", "软件故障",
      ["检查库表、连接和客户端字符集", "确认应用连接参数", "对比写入链路"],
      ["统一连接字符集", "谨慎处理历史数据转换", "先备份再做批量修复"],
      ["新写入数据正常", "查询显示一致", "历史数据修复有校验"],
      "涉及历史数据转换或批量更新时升级。", ["MySQL", "字符集", "collation", "乱码"], "mysql_problems"),
    s("MySQL", "临时表或排序导致性能异常", "查询期间磁盘或 CPU 抖动", "软件故障",
      ["分析 explain 和执行计划", "查看临时表、排序和磁盘使用", "确认 SQL 是否缺索引"],
      ["优化索引和查询条件", "必要时拆分大查询", "参数调整需基准验证"],
      ["查询耗时下降", "临时文件减少", "数据库负载恢复"],
      "涉及核心报表 SQL 或参数调优时升级。", ["MySQL", "临时表", "排序", "explain"], "mysql_problems"),

    s("PostgreSQL", "数据库服务启动失败", "业务连接全部失败", "软件故障",
      ["查看 PostgreSQL 日志", "检查 data directory 权限和配置文件", "确认端口占用和磁盘空间"],
      ["修复配置或权限", "不要直接删除 WAL 或数据文件", "必要时从备份流程恢复"],
      ["服务监听端口", "应用连接成功", "日志无启动错误"],
      "涉及 WAL、数据目录损坏或生产库不可用时升级。", ["PostgreSQL", "启动失败", "日志", "WAL"], "postgres_start"),
    s("PostgreSQL", "连接被拒绝", "应用无法访问数据库", "网络问题",
      ["确认 listen_addresses 和端口监听", "检查 pg_hba.conf、主机防火墙和安全组", "从应用主机测试"],
      ["修正监听地址和访问控制", "reload 或 restart 前评估影响", "保留变更记录"],
      ["应用主机可连通", "认证日志正常", "业务恢复"],
      "涉及访问控制放开或跨网段数据库访问时升级。", ["PostgreSQL", "listen_addresses", "pg_hba", "端口"], "postgres_start"),
    s("PostgreSQL", "密码认证失败", "应用或用户登录失败", "账号问题",
      ["查看认证失败日志", "确认 pg_hba.conf 匹配规则", "核对用户名、数据库名和密码状态"],
      ["修正认证规则或重置密码", "按最小权限授权", "避免临时放开 trust"],
      ["目标账号登录成功", "失败认证告警消失", "访问规则符合审批"],
      "生产账号、批量认证失败或需要调整 pg_hba 时升级。", ["PostgreSQL", "认证", "pg_hba", "密码"], "postgres_logging"),
    s("PostgreSQL", "日志没有记录关键错误", "问题无法追溯", "安全合规",
      ["检查 logging_collector 和 log_destination", "确认 log_min_messages 等参数", "查看日志目录权限"],
      ["开启必要日志级别", "确保日志目录可写并设置轮转", "避免开启过细日志导致磁盘压力"],
      ["错误可在日志中追踪", "日志轮转正常", "磁盘水位安全"],
      "审计要求变更或需要提高生产日志级别时升级。", ["PostgreSQL", "logging_collector", "日志", "审计"], "postgres_logging"),
    s("PostgreSQL", "连接数耗尽", "新连接失败", "软件故障",
      ["查看当前连接和 max_connections", "识别 idle in transaction", "检查应用连接池"],
      ["清理异常空闲事务需确认影响", "优化连接池配置", "参数调整需评估内存"],
      ["连接数回落", "新连接成功", "空闲事务数量受控"],
      "核心库连接耗尽或需调整 max_connections 时升级。", ["PostgreSQL", "max_connections", "连接池"], "postgres_logging"),
    s("PostgreSQL", "表膨胀或 vacuum 不及时", "查询变慢、磁盘增长", "系统配置",
      ["查看表大小、死元组和 autovacuum 状态", "确认长事务是否阻塞清理", "分析增长趋势"],
      ["处理长事务", "调整 autovacuum 策略需验证", "必要时安排维护窗口 vacuum"],
      ["死元组下降", "磁盘增长受控", "查询延迟恢复"],
      "需要 VACUUM FULL、REINDEX 或停机维护时升级。", ["PostgreSQL", "vacuum", "膨胀", "autovacuum"], "postgres_logging"),
    s("PostgreSQL", "锁等待严重", "业务写入或查询阻塞", "软件故障",
      ["查询阻塞链路和等待事件", "定位持锁事务", "保存 SQL、用户和时间"],
      ["联系业务确认后处理阻塞会话", "优化事务范围", "避免直接终止关键写入"],
      ["锁等待解除", "事务吞吐恢复", "错误率下降"],
      "涉及生产写事务、DDL 或无法判断影响时升级。", ["PostgreSQL", "lock", "事务", "等待事件"], "postgres_logging"),
    s("PostgreSQL", "WAL 目录占满", "数据库写入受阻或复制异常", "系统配置",
      ["查看 pg_wal 占用和归档状态", "检查复制槽和归档命令", "确认磁盘增长速度"],
      ["修复归档或复制消费", "谨慎处理无效复制槽", "禁止手工删除 WAL 文件"],
      ["WAL 占用下降", "归档/复制恢复", "写入恢复正常"],
      "WAL 空间告急或复制槽处理不确定时升级。", ["PostgreSQL", "WAL", "archive", "replication slot"], "postgres_logging"),
    s("PostgreSQL", "复制延迟升高", "读库数据滞后", "软件故障",
      ["查看复制状态、延迟和网络", "检查主库大事务和从库资源", "确认复制槽堆积"],
      ["短期减少读库流量", "处理慢查询和资源瓶颈", "避免盲目重建复制"],
      ["复制延迟回落", "读库查询正常", "WAL 堆积下降"],
      "涉及主从切换、复制槽异常或跨机房链路时升级。", ["PostgreSQL", "复制延迟", "streaming replication"], "postgres_logging"),
    s("PostgreSQL", "checkpoint 过于频繁", "I/O 抖动和延迟升高", "系统配置",
      ["查看日志中的 checkpoint 信息", "分析写入量和 WAL 参数", "检查磁盘 I/O 水位"],
      ["评估 checkpoint 参数和写入峰值", "优化批量写入节奏", "参数变更需压测"],
      ["I/O 抖动下降", "checkpoint 频率合理", "业务延迟稳定"],
      "生产数据库参数调优或磁盘性能瓶颈时升级。", ["PostgreSQL", "checkpoint", "WAL", "I/O"], "postgres_logging"),

    s("Redis", "延迟突然升高", "缓存请求变慢", "软件故障",
      ["用 latency doctor 或监控确认延迟类型", "检查慢命令、大 key、fork 和网络", "对比 CPU、内存和持久化时间点"],
      ["先限制大命令和批量任务", "优化 key 结构", "必要时扩容或迁移热点"],
      ["P99 延迟回落", "慢命令减少", "业务缓存命中恢复"],
      "核心缓存大面积延迟或涉及集群迁移时升级。", ["Redis", "latency", "slowlog", "大key"], "redis_latency"),
    s("Redis", "内存接近 maxmemory", "写入失败或频繁淘汰", "软件故障",
      ["查看 used_memory、maxmemory 和淘汰指标", "识别大 key 和过期策略", "确认业务写入增长"],
      ["清理可过期数据", "修正 TTL 策略", "评估扩容或调整淘汰策略"],
      ["内存水位下降", "evicted_keys 稳定", "业务无缓存雪崩"],
      "需要调整淘汰策略或清理核心 key 时升级。", ["Redis", "maxmemory", "eviction", "TTL"], "redis_memory"),
    s("Redis", "RDB 或 AOF 持久化失败", "数据持久化风险升高", "软件故障",
      ["查看 Redis 日志和 persistence 指标", "检查磁盘空间、权限和 fork 失败", "确认 AOF rewrite 状态"],
      ["恢复磁盘空间和目录权限", "避免在高峰期强制重写", "保留持久化错误现场"],
      ["持久化状态恢复", "最后保存时间更新", "日志无持续错误"],
      "涉及数据可靠性、AOF 损坏或主库持久化失败时升级。", ["Redis", "RDB", "AOF", "持久化"], "redis_latency"),
    s("Redis", "连接被拒绝", "应用无法访问缓存", "网络问题",
      ["确认 Redis 进程和端口监听", "检查 bind、protected-mode、防火墙和安全组", "从应用主机测试连通"],
      ["恢复服务监听或修正网络策略", "按规范配置访问来源", "避免临时关闭保护模式暴露公网"],
      ["应用主机连接成功", "认证和命令正常", "缓存错误率下降"],
      "公网暴露、跨网段访问或安全策略调整时升级。", ["Redis", "connection refused", "bind", "protected-mode"], "redis_latency"),
    s("Redis", "客户端阻塞增多", "请求排队或超时", "软件故障",
      ["查看 blocked_clients 和慢命令", "检查阻塞命令、Lua 脚本和大 key 操作", "确认网络是否拥塞"],
      ["停止或拆分阻塞任务", "优化 Lua 和批量操作", "限制危险命令执行窗口"],
      ["blocked_clients 回落", "慢日志减少", "请求超时消失"],
      "阻塞来自核心任务或需要 kill 脚本时升级。", ["Redis", "blocked_clients", "Lua", "slowlog"], "redis_latency"),
    s("Redis", "大 key 影响性能", "单次操作延迟高或网络抖动", "软件故障",
      ["用 bigkeys 或采样工具识别大 key", "确认类型、大小和访问频率", "评估删除或拆分风险"],
      ["分批迁移或拆分数据结构", "设置合理 TTL", "避免 DEL 大 key，优先异步或分批处理"],
      ["大 key 数量下降", "慢命令减少", "延迟曲线恢复"],
      "大 key 属于核心业务数据或清理影响不明时升级。", ["Redis", "bigkey", "性能", "TTL"], "redis_memory"),
    s("Redis", "主从复制延迟", "读缓存可能不一致", "软件故障",
      ["查看 master_link_status 和复制偏移", "检查网络、从库负载和大 key 写入", "确认 backlog 是否足够"],
      ["减少从库读流量或扩容", "处理网络和资源瓶颈", "避免频繁全量同步"],
      ["复制延迟回落", "主从链路稳定", "读写一致性风险下降"],
      "涉及主从切换、全量同步或跨机房复制时升级。", ["Redis", "复制延迟", "replication"], "redis_latency"),
    s("Redis", "集群槽位异常", "部分 key 访问失败", "软件故障",
      ["查看 cluster nodes 和 slots 状态", "确认节点健康和迁移状态", "检查客户端是否支持重定向"],
      ["恢复异常节点", "完成槽位迁移或修复集群", "确认客户端配置"],
      ["cluster_state 为 ok", "槽位全部覆盖", "业务 key 访问恢复"],
      "集群节点故障、槽位迁移或数据不一致风险时升级。", ["Redis", "cluster", "slots", "MOVED"], "redis_latency"),
    s("Redis", "AUTH 认证失败", "应用连接缓存失败", "账号问题",
      ["确认密码或 ACL 用户", "查看 Redis 日志中的认证失败", "核对应用配置和密钥变更"],
      ["按密钥管理流程更新密码", "修正 ACL 权限", "避免在日志和工单暴露明文密码"],
      ["应用认证成功", "失败认证告警消失", "权限范围正确"],
      "生产密码轮换、批量认证失败或疑似泄露时升级。", ["Redis", "AUTH", "ACL", "密码"], "redis_latency"),
    s("Redis", "慢日志持续增长", "缓存响应不稳定", "软件故障",
      ["查看 slowlog get", "识别慢命令类型和 key 模式", "关联业务调用链"],
      ["优化命令复杂度", "拆分大集合操作", "推动业务避免全量扫描"],
      ["慢日志增长停止", "延迟指标恢复", "相关接口稳定"],
      "慢命令来自核心交易链路或需要改业务代码时升级。", ["Redis", "slowlog", "慢命令", "scan"], "redis_latency"),

    s("阿里云 ECS", "Linux 实例无法通过 SSH 登录", "无法远程维护服务器", "网络问题",
      ["确认实例运行状态和公网/私网 IP", "检查安全组、系统防火墙和 SSH 服务", "核对密钥或密码认证方式"],
      ["先通过控制台或救援通道收集日志", "恢复 sshd 配置和端口放行", "避免直接重装系统"],
      ["SSH 登录成功", "审计记录完整", "业务端口不受影响"],
      "系统盘异常、sshd 配置损坏或无法使用控制台时升级。", ["阿里云", "ECS", "SSH", "安全组"], "aliyun_ssh", "云厂商故障处理文档"),
    s("阿里云 ECS", "公网 IP ping 不通", "外部无法探测主机", "网络问题",
      ["确认实例、公网 IP 和路由状态", "检查安全组 ICMP 规则", "核对系统防火墙和云网络 ACL"],
      ["按最小范围放行 ICMP 或业务端口", "确认运营商或本地网络无拦截", "记录源 IP 和测试路径"],
      ["从指定来源 ping 或端口探测成功", "安全组规则符合规范", "业务访问恢复"],
      "涉及公网暴露、DDoS 防护或跨地域网络时升级。", ["阿里云", "ECS", "公网IP", "ping", "安全组"], "aliyun_ping", "云厂商故障处理文档"),
    s("阿里云 ECS", "业务端口无法访问", "网站或接口不可达", "网络问题",
      ["检查安全组入方向规则", "确认实例内服务监听端口", "从内外部同时测试端口"],
      ["补齐安全组和系统防火墙规则", "恢复业务进程监听", "避免开放过大端口范围"],
      ["外部端口探测成功", "应用访问日志有请求", "安全组规则留痕"],
      "生产公网端口变更或负载均衡链路异常时升级。", ["阿里云", "ECS", "端口", "安全组"], "aliyun_ping", "云厂商故障处理文档"),
    s("阿里云 ECS", "SSH 密钥登录失败", "运维账号无法进入实例", "账号问题",
      ["确认使用的私钥与实例公钥匹配", "检查 authorized_keys 权限", "确认 sshd 是否允许密钥认证"],
      ["通过控制台修复公钥或权限", "必要时重置登录凭据", "保留操作审计"],
      ["密钥登录成功", "密码登录策略符合安全要求", "异常登录告警消失"],
      "密钥疑似泄露、root 登录策略变更或批量实例异常时升级。", ["阿里云", "SSH key", "authorized_keys", "ECS"], "aliyun_ssh", "云厂商故障处理文档"),
    s("阿里云 ECS", "系统盘满导致登录异常", "SSH 卡顿或命令无法执行", "系统配置",
      ["通过控制台或救援模式查看磁盘空间", "定位日志、缓存和快照残留", "确认 inode 是否耗尽"],
      ["清理可确认的过期文件", "扩容系统盘并同步文件系统", "不要删除未知系统目录"],
      ["磁盘水位恢复", "SSH 登录正常", "系统服务稳定"],
      "系统盘无法进入或文件用途不明时升级。", ["阿里云", "ECS", "系统盘", "磁盘"], "aliyun_ssh", "云厂商故障处理文档"),
    s("阿里云 ECS", "实例 CPU 突增", "云主机响应变慢", "系统配置",
      ["查看云监控 CPU 曲线", "登录实例定位进程", "核对定时任务、攻击流量和发布变更"],
      ["先限流或暂停非核心任务", "保留进程和网络连接信息", "需要时扩容规格"],
      ["CPU 回落", "业务延迟恢复", "云监控告警解除"],
      "疑似入侵、挖矿进程或核心业务进程异常时升级。", ["阿里云", "ECS", "CPU", "云监控"], "aliyun_ssh", "云厂商故障处理文档"),
    s("阿里云 ECS", "安全组规则误配置", "业务被拦截或暴露风险", "安全合规",
      ["对照变更单核对入/出方向规则", "确认源地址、协议和端口范围", "检查是否存在 0.0.0.0/0 高风险开放"],
      ["按最小权限修正规则", "删除无效临时放行", "记录影响实例和时间"],
      ["业务必要端口可访问", "高风险端口关闭", "安全审计通过"],
      "公网端口大范围开放或涉及生产安全策略时升级。", ["阿里云", "安全组", "ECS", "合规"], "aliyun_ping", "云厂商故障处理文档"),
    s("阿里云 ECS", "控制台远程连接失败", "无法通过 Web 控制台进入主机", "软件故障",
      ["确认实例状态和控制台连接组件", "检查浏览器网络和权限", "尝试救援连接方式"],
      ["刷新连接凭据或更换救援通道", "确认账号 RAM 权限", "保留失败截图和时间"],
      ["控制台连接成功", "账号权限符合最小授权", "后续 SSH 也恢复"],
      "账号权限、实例系统异常或无法取得任何登录通道时升级。", ["阿里云", "控制台", "远程连接", "RAM"], "aliyun_ssh", "云厂商故障处理文档"),
    s("阿里云 ECS", "系统防火墙阻断业务", "安全组已放行但端口仍不通", "网络问题",
      ["实例内检查 firewalld/iptables/nftables", "确认服务监听和绑定地址", "从实例本机和外部交叉测试"],
      ["补齐本机防火墙规则", "保存规则并纳入配置管理", "避免关闭整个防火墙"],
      ["端口外部可达", "防火墙规则持久化", "业务访问恢复"],
      "规则复杂或涉及安全基线调整时升级。", ["阿里云", "ECS", "firewall", "iptables"], "aliyun_ping", "云厂商故障处理文档"),
    s("阿里云 ECS", "实例网络丢包", "业务访问时断时续", "网络问题",
      ["查看云监控网络指标", "从多源执行 ping/mtr", "排查安全组、带宽上限和实例负载"],
      ["先确认是否带宽打满", "优化异常流量或限流", "必要时调整带宽或路由"],
      ["丢包率下降", "业务访问稳定", "网络指标恢复"],
      "跨运营商、跨地域或疑似攻击流量时升级。", ["阿里云", "ECS", "丢包", "带宽"], "aliyun_ping", "云厂商故障处理文档"),

    s("华为云 ECS", "错误系统配置导致远程登录失败", "无法进入 Linux 云主机", "系统配置",
      ["通过控制台查看实例状态", "检查 sshd、fstab、网络配置等近期变更", "收集启动和登录错误信息"],
      ["使用控制台或救援模式回滚错误配置", "修复前先备份配置文件", "恢复后补充变更复盘"],
      ["远程登录恢复", "系统启动日志无关键错误", "配置与变更单一致"],
      "启动配置损坏、文件系统异常或无法使用救援模式时升级。", ["华为云", "ECS", "远程登录", "系统配置"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "Linux 实例启动异常", "云主机无法正常提供服务", "软件故障",
      ["查看控制台状态和启动日志", "检查 fstab、内核参数和系统服务", "确认系统盘状态"],
      ["进入救援模式修复错误配置", "回滚近期内核或系统变更", "不要直接重装覆盖数据"],
      ["实例正常启动", "关键服务 active", "业务健康检查通过"],
      "涉及系统盘损坏、启动链路或内核异常时升级。", ["华为云", "ECS", "启动失败", "fstab"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "安全组阻断 SSH", "无法远程登录实例", "网络问题",
      ["检查安全组入方向 22 端口规则", "确认源 IP 是否匹配", "核对实例内防火墙"],
      ["按最小范围放行运维来源", "恢复后删除临时过宽规则", "记录规则变更"],
      ["指定来源 SSH 成功", "安全组无高风险开放", "审计记录完整"],
      "需要公网放行或规则影响多个实例时升级。", ["华为云", "ECS", "安全组", "SSH"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "网络配置错误", "实例无法访问内外网", "网络问题",
      ["核对网卡、IP、网关和 DNS 配置", "检查路由表和安全组", "从控制台确认弹性公网 IP 绑定"],
      ["修复网卡配置或回滚网络脚本", "不要随意删除默认路由", "保存修复前后配置"],
      ["内外网连通恢复", "DNS 解析正常", "业务访问恢复"],
      "涉及多网卡、路由策略或生产网络变更时升级。", ["华为云", "ECS", "网络配置", "路由"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "关键系统文件配置错误", "启动或登录链路异常", "系统配置",
      ["检查近期修改的系统文件", "通过救援模式查看配置内容", "确认权限和格式"],
      ["备份后恢复正确配置", "修复权限和语法", "建立配置变更记录"],
      ["系统服务恢复", "登录链路正常", "配置文件被纳入备份"],
      "涉及 passwd、shadow、sudoers、fstab 等关键文件时升级。", ["华为云", "ECS", "系统文件", "救援模式"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "磁盘挂载配置错误", "重启后实例进入异常状态", "系统配置",
      ["检查 /etc/fstab 条目", "确认 UUID、挂载点和文件系统类型", "查看启动日志"],
      ["在救援模式注释错误挂载项", "修复 UUID 或挂载参数", "恢复后执行 mount -a 验证"],
      ["实例重启正常", "磁盘挂载正确", "业务数据可访问"],
      "涉及数据盘损坏、生产数据库挂载或无法确认 UUID 时升级。", ["华为云", "ECS", "fstab", "磁盘挂载"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "实例密码或密钥异常", "授权用户无法登录", "账号问题",
      ["确认登录方式和账号状态", "检查密钥文件权限", "查看 sshd 认证日志"],
      ["按云平台流程重置密码或更换密钥", "修复 authorized_keys 权限", "保留凭据变更审计"],
      ["授权用户可登录", "异常认证失败停止", "凭据管理符合规范"],
      "涉及 root 凭据、批量实例或疑似泄露时升级。", ["华为云", "ECS", "密钥", "密码"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "云主机高负载", "远程登录卡顿或业务慢", "系统配置",
      ["查看云监控 CPU、内存、磁盘 I/O", "登录后定位高负载进程", "确认是否有异常任务或攻击流量"],
      ["先保留现场并限流", "重启非核心异常进程需确认", "必要时扩容规格"],
      ["负载回落", "登录恢复", "业务监控稳定"],
      "疑似安全事件、数据库高负载或无法登录收集信息时升级。", ["华为云", "ECS", "高负载", "云监控"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "云服务器端口不可达", "应用入口无法访问", "网络问题",
      ["检查安全组、网络 ACL 和系统防火墙", "确认应用监听端口", "从不同网络源测试"],
      ["修复规则和服务监听", "限制放行来源", "同步负载均衡后端健康检查"],
      ["端口探测成功", "健康检查恢复", "访问日志出现请求"],
      "涉及公网服务、负载均衡或网络 ACL 策略时升级。", ["华为云", "ECS", "端口", "安全组"], "huawei_ecs", "云厂商故障处理文档"),
    s("华为云 ECS", "DNS 配置错误", "实例无法解析域名", "网络问题",
      ["检查 resolv.conf 或网络管理器配置", "测试内外部 DNS", "确认安全组是否限制 DNS"],
      ["恢复正确 DNS 服务器", "避免手工配置被网络管理器覆盖", "记录配置来源"],
      ["域名解析成功", "应用依赖访问恢复", "重启后配置仍生效"],
      "企业 DNS、专线 DNS 或批量实例解析异常时升级。", ["华为云", "ECS", "DNS", "resolv.conf"], "huawei_ecs", "云厂商故障处理文档"),

    s("腾讯云 CVM", "无法登录 Linux 实例", "无法远程维护云服务器", "网络问题",
      ["确认 CVM 状态、公网 IP 和登录方式", "检查安全组、系统防火墙和 sshd 状态", "核对密码或密钥"],
      ["使用控制台登录或救援方式收集信息", "恢复 SSH 服务和网络放行", "避免重装覆盖数据"],
      ["SSH 或控制台登录成功", "安全组规则合理", "业务服务稳定"],
      "系统启动异常、sshd 配置损坏或凭据疑似泄露时升级。", ["腾讯云", "CVM", "Linux", "登录失败"], "tencent_login", "云厂商故障处理文档"),
    s("腾讯云 CVM", "SSH 连接超时", "运维无法进入主机", "网络问题",
      ["检查安全组 22 端口和来源 IP", "确认实例内防火墙", "从不同网络测试 TCP 连通"],
      ["按最小来源放行 SSH", "恢复 sshd 监听", "记录临时规则有效期"],
      ["SSH 连接成功", "规则无过宽暴露", "失败登录告警下降"],
      "公网暴露、批量实例或跨网络链路异常时升级。", ["腾讯云", "SSH", "安全组", "CVM"], "tencent_ssh", "云厂商故障处理文档"),
    s("腾讯云 CVM", "网站无法访问", "用户打不开业务页面", "网络问题",
      ["检查域名解析、备案/证书和公网 IP", "确认 Web 服务监听和安全组", "查看访问日志和错误日志"],
      ["恢复 Web 服务或端口放行", "修复 DNS/证书配置", "同步负载均衡健康检查"],
      ["公网访问返回正常状态码", "访问日志有请求", "监控恢复"],
      "涉及域名、证书、负载均衡或公网安全策略时升级。", ["腾讯云", "CVM", "网站无法访问", "安全组"], "tencent_web", "云厂商故障处理文档"),
    s("腾讯云 CVM", "业务端口被安全组拦截", "应用端口外部不通", "网络问题",
      ["核对安全组入方向端口规则", "确认源地址和协议", "实例内测试服务监听"],
      ["补齐必要端口规则", "删除临时过宽放行", "记录业务端口和责任人"],
      ["外部端口可达", "应用日志出现请求", "安全审计通过"],
      "生产公网端口或多实例安全组变更时升级。", ["腾讯云", "CVM", "安全组", "端口"], "tencent_ssh", "云厂商故障处理文档"),
    s("腾讯云 CVM", "CPU 或内存异常升高", "云服务器响应慢", "系统配置",
      ["查看云监控资源曲线", "登录实例定位高占用进程", "核对定时任务、流量和发布变更"],
      ["保留现场后限流或停止非核心任务", "优化进程或扩容实例", "疑似异常进程先隔离"],
      ["资源水位回落", "业务延迟恢复", "异常进程不再出现"],
      "疑似入侵、挖矿或核心服务高负载时升级。", ["腾讯云", "CVM", "CPU", "内存"], "tencent_login", "云厂商故障处理文档"),
    s("腾讯云 CVM", "密钥登录失败", "授权人员无法 SSH", "账号问题",
      ["确认私钥和绑定实例是否匹配", "检查本地私钥权限", "查看实例内 authorized_keys"],
      ["按平台流程更换或重置密钥", "修复文件权限", "保留凭据变更记录"],
      ["密钥登录成功", "无异常认证失败", "凭据符合安全规范"],
      "root 密钥、批量密钥轮换或疑似泄露时升级。", ["腾讯云", "密钥", "SSH", "authorized_keys"], "tencent_ssh", "云厂商故障处理文档"),
    s("腾讯云 CVM", "系统盘空间不足", "登录卡顿或服务写入失败", "系统配置",
      ["通过监控和 df 确认磁盘占用", "定位日志、缓存和临时文件", "检查 inode"],
      ["清理可确认的过期文件", "扩容系统盘并扩展文件系统", "不要删除未知业务数据"],
      ["磁盘水位恢复", "服务可写入日志", "登录和业务恢复"],
      "系统盘满导致无法登录或文件用途不清楚时升级。", ["腾讯云", "CVM", "系统盘", "磁盘"], "tencent_login", "云厂商故障处理文档"),
    s("腾讯云 CVM", "防火墙与安全组规则冲突", "云端放行但实例仍不通", "网络问题",
      ["云端检查安全组", "实例内检查 iptables/firewalld", "确认服务监听地址"],
      ["同步云端和系统内规则", "保持规则持久化", "避免直接关闭主机防火墙"],
      ["端口连通恢复", "规则记录一致", "重启后仍有效"],
      "规则复杂、涉及安全基线或公网暴露时升级。", ["腾讯云", "CVM", "firewalld", "iptables"], "tencent_ssh", "云厂商故障处理文档"),
    s("腾讯云 CVM", "公网带宽打满", "访问延迟和丢包升高", "网络问题",
      ["查看云监控带宽曲线", "分析连接来源和流量方向", "确认是否有异常下载或攻击"],
      ["先限流或关闭异常流量", "调整带宽需走审批", "保留源 IP 和流量证据"],
      ["带宽回到正常水位", "丢包下降", "业务访问稳定"],
      "疑似攻击、跨地域链路或需要扩容公网带宽时升级。", ["腾讯云", "CVM", "带宽", "丢包"], "tencent_web", "云厂商故障处理文档"),
    s("腾讯云 CVM", "Web 服务健康检查失败", "负载均衡后端不可用", "软件故障",
      ["检查本机 Web 服务端口", "查看负载均衡健康检查路径", "确认安全组允许探测源"],
      ["修复健康检查路径或服务监听", "同步安全组规则", "确认应用返回码符合预期"],
      ["后端健康状态恢复", "负载均衡转发正常", "访问日志有请求"],
      "涉及生产负载均衡、灰度流量或多后端异常时升级。", ["腾讯云", "CVM", "健康检查", "负载均衡"], "tencent_web", "云厂商故障处理文档"),
]


QUESTION_PATTERNS = [
    "{env} {subject}怎么排查？",
    "一线运维收到 {subject}告警时先做什么？",
    "{subject}有哪些常见原因？",
    "{subject}可以先做哪些不影响业务的处理？",
    "{subject}恢复后如何验证？",
    "客户反馈{impact}，如何判断是否属于 {subject}？",
    "{subject}需要收集哪些日志和命令输出？",
    "{subject}什么时候应该转给资深运维？",
    "值班交接中如何记录 {subject}？",
    "处理 {subject}时有哪些风险控制点？",
]

ENVS = ["生产环境", "测试环境", "办公网", "核心业务区", "云上实例"]


def join_steps(steps: Iterable[str]) -> str:
    return "；".join(step.rstrip("。") for step in steps) + "。"


def answer_for(scenario: Scenario, variant_index: int) -> str:
    checks = join_steps(scenario.checks)
    actions = join_steps(scenario.actions)
    verify = join_steps(scenario.verify)
    source = f"来源参考：{scenario.source_name}，{scenario.source_url}"

    if variant_index == 0:
        body = f"先确认影响范围和时间窗口，再排查：{checks} 处理建议：{actions} {verify}"
    elif variant_index == 1:
        body = f"一线先收集告警时间、实例/节点、用户影响和最近变更；技术侧重点是：{checks} 收集后按工单记录，不确定影响时不要直接变更生产配置。"
    elif variant_index == 2:
        body = f"常见原因通常集中在配置变更、资源耗尽、权限/网络策略、依赖服务异常或版本发布。建议按证据链确认：{checks}"
    elif variant_index == 3:
        body = f"可先做无损动作：保存日志和监控截图、缩小影响面、暂停非核心任务、检查只读配置。需要变更时再执行：{actions}"
    elif variant_index == 4:
        body = f"恢复验证不要只看单次成功，应覆盖连通性、服务状态、日志和监控：{verify} 同时在工单中记录恢复时间和残余风险。"
    elif variant_index == 5:
        body = f"先把用户现象映射到系统指标：{scenario.impact} 时，重点看告警时间是否和 {scenario.issue} 的证据一致；建议核对：{checks}"
    elif variant_index == 6:
        body = f"建议收集：告警截图、影响范围、最近变更、关键日志、监控曲线，以及以下排查输出：{checks} 收集结果要附到工单，便于专家复核。"
    elif variant_index == 7:
        body = f"出现以下情况应转资深运维：无法确认根因、涉及生产核心服务、需要改配置/扩容/回滚、存在数据或安全风险。{scenario.escalate}"
    elif variant_index == 8:
        body = f"交接记录应包含现象、影响范围、已执行检查、临时处置、验证结果和待办事项。可按此顺序写：{checks} 已处理：{actions}"
    else:
        body = f"风险控制点包括先备份/保留现场、按最小权限和最小变更处理、避免扩大开放网络或权限、验证后再关闭工单。{scenario.escalate}"

    return f"{body}\n{source}"


def normalize_question(question: str) -> str:
    return " ".join(question.strip().lower().split())


def normalize_category(category: str | None) -> str:
    if category in ALLOWED_CATEGORIES:
        return category
    return "其他"


def make_official_faqs(count: int = 1000) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    variant_count = len(QUESTION_PATTERNS)

    for variant_index in range(variant_count):
        for scenario_index, scenario in enumerate(SCENARIOS):
            env = ENVS[(scenario_index + variant_index) % len(ENVS)]
            subject = (
                scenario.issue
                if scenario.issue.lower().startswith(scenario.product.lower())
                else f"{scenario.product} {scenario.issue}"
            )
            question = QUESTION_PATTERNS[variant_index].format(
                env=env,
                product=scenario.product,
                issue=scenario.issue,
                subject=subject,
                impact=scenario.impact,
            )
            key = normalize_question(question)
            if key in seen:
                continue
            seen.add(key)

            keywords = ";".join(
                [
                    scenario.product,
                    scenario.issue,
                    *scenario.keywords,
                    scenario.source_type,
                    scenario.source_url,
                ]
            )[:500]
            tags = f"{scenario.source_type};{scenario.product};可追溯来源"[:200]
            items.append(
                {
                    "question": question[:500],
                    "answer": answer_for(scenario, variant_index)[:10000],
                    "category": normalize_category(scenario.category),
                    "tags": tags,
                    "keywords": keywords,
                }
            )
            if len(items) >= count:
                return items

    raise RuntimeError(f"Only generated {len(items)} FAQ entries, expected {count}.")


def load_legacy_faqs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON array")

    items: list[dict] = []
    for raw in data:
        if not isinstance(raw, dict):
            continue
        question = str(raw.get("question", "")).strip()
        answer = str(raw.get("answer", "")).strip()
        if not question or not answer:
            continue
        category = normalize_category(str(raw.get("category", "")).strip())
        raw_keywords = str(raw.get("keywords", "") or "").strip()
        keywords = ";".join(filter(None, [raw_keywords, "历史模拟FAQ", "AI生成数据"]))
        items.append(
            {
                "question": question[:500],
                "answer": answer[:10000],
                "category": category,
                "tags": "历史模拟FAQ;AI生成数据",
                "keywords": keywords[:500],
            }
        )
    return items


def merge_faqs(primary: list[dict], secondary: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for item in [*primary, *secondary]:
        key = normalize_question(item["question"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def write_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def sqlite_backup(db_path: Path) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"eknowledge_before_faq_import_{stamp}.db"
    if not db_path.exists():
        return backup_path

    src = sqlite3.connect(str(db_path))
    try:
        dst = sqlite3.connect(str(backup_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    return backup_path


def import_to_database(items: list[dict], dry_run: bool = False) -> dict:
    from database import DB_PATH, SessionLocal, init_db
    from models.faq import Faq
    from models.user import User

    init_db()
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").order_by(User.id).first()
        if not admin:
            raise RuntimeError("No admin user found; cannot set Faq.created_by.")

        existing_questions = {
            normalize_question(row[0])
            for row in db.query(Faq.question).all()
        }
        to_add = [
            item for item in items
            if normalize_question(item["question"]) not in existing_questions
        ]
        if dry_run:
            return {
                "backup": None,
                "existing": len(existing_questions),
                "inserted": 0,
                "skipped": len(items) - len(to_add),
                "total_after": len(existing_questions) + len(to_add),
            }

        backup_path = sqlite_backup(Path(DB_PATH))
        for item in to_add:
            db.add(
                Faq(
                    question=item["question"],
                    answer=item["answer"],
                    category=item["category"],
                    tags=item.get("tags"),
                    keywords=item.get("keywords"),
                    status="published",
                    created_by=admin.id,
                )
            )
        db.commit()
        return {
            "backup": str(backup_path),
            "existing": len(existing_questions),
            "inserted": len(to_add),
            "skipped": len(items) - len(to_add),
            "total_after": db.query(Faq).count(),
        }
    finally:
        db.close()


def normalize_embedding(vector: list[float], dimension: int) -> list[float]:
    if len(vector) < dimension:
        return vector + [0.0] * (dimension - len(vector))
    if len(vector) > dimension:
        return vector[:dimension]
    return vector


def embed_texts(texts: list[str]) -> list[list[float]]:
    import requests
    from config import EMBEDDING_DIMENSION, EMBEDDING_MODEL, LLM_TIMEOUT_SECONDS, OLLAMA_BASE_URL

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": texts},
        timeout=max(120, LLM_TIMEOUT_SECONDS * max(1, len(texts))),
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    data = resp.json()
    embeddings = data.get("embeddings", [])
    if len(embeddings) != len(texts):
        raise RuntimeError(f"Ollama returned {len(embeddings)} embeddings for {len(texts)} inputs.")
    return [normalize_embedding(vec, EMBEDDING_DIMENSION) for vec in embeddings]


def vector_to_blob(vector: list[float]) -> bytes:
    return array("f", [float(x) for x in vector]).tobytes()


def prepare_embedding_rebuild_table(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS faq_embeddings_rebuild (
            faq_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            dim INTEGER NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute("DELETE FROM faq_embeddings_rebuild")
    conn.commit()
    return conn


def finish_embedding_rebuild_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS faq_embeddings_old")
    exists = conn.execute(
        """
        SELECT 1 FROM sqlite_master
        WHERE type = 'table' AND name = 'faq_embeddings'
        """
    ).fetchone()
    if exists:
        conn.execute("ALTER TABLE faq_embeddings RENAME TO faq_embeddings_old")
    conn.execute("ALTER TABLE faq_embeddings_rebuild RENAME TO faq_embeddings")
    conn.execute("DROP TABLE IF EXISTS faq_embeddings_old")
    conn.commit()


def rebuild_chroma_sync(batch_pause: float = 0.0, embed_batch_size: int = 16) -> dict:
    import chromadb
    from config import CHROMA_COLLECTION_NAME, CHROMA_DB_PATH, DATA_DIR, DB_PATH
    from database import SessionLocal
    from models.faq import Faq

    db = SessionLocal()
    embedding_conn = None
    try:
        faqs = (
            db.query(Faq)
            .filter(Faq.status == "published")
            .order_by(Faq.id)
            .all()
        )
        embedding_conn = prepare_embedding_rebuild_table(DB_PATH)
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        suffix = uuid.uuid4().hex[:8]
        temp_name = f"{CHROMA_COLLECTION_NAME}_v2_{suffix}"
        collection = client.get_or_create_collection(
            name=temp_name,
            metadata={"hnsw:space": "cosine", "hnsw:sync_threshold": 50},
        )

        started = time.time()
        for batch_start in range(0, len(faqs), embed_batch_size):
            batch = faqs[batch_start:batch_start + embed_batch_size]
            texts = [
                faq.question  # 仅用问题文本向量化（与查询侧对称）
                for faq in batch
            ]
            vectors = embed_texts(texts)
            for faq, vector in zip(batch, vectors):
                embedding_conn.execute(
                    """
                    INSERT OR REPLACE INTO faq_embeddings_rebuild (faq_id, embedding, dim, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (faq.id, vector_to_blob(vector), len(vector)),
                )
                collection.add(
                    ids=[str(faq.id)],
                    embeddings=[vector],
                    metadatas=[{
                        "faq_id": faq.id,
                        "question": faq.question[:500],
                        "category": faq.category,
                    }],
                    documents=[faq.question],
                )
            index = batch_start + len(batch)
            progress_interval = max(embed_batch_size * 5, 1)
            if index % progress_interval == 0 or index == len(faqs):
                embedding_conn.commit()
                elapsed = time.time() - started
                print(f"indexed {index}/{len(faqs)} FAQs in {elapsed:.1f}s", flush=True)
            if batch_pause and index % 50 == 0:
                time.sleep(batch_pause)

        active_path = Path(DATA_DIR) / ".active_collection"
        old_name = active_path.read_text(encoding="utf-8").strip() if active_path.exists() else CHROMA_COLLECTION_NAME
        fresh_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        fresh_count = fresh_client.get_collection(temp_name).count()
        if fresh_count != len(faqs):
            raise RuntimeError(f"Fresh Chroma verification failed: {fresh_count} != {len(faqs)}")
        finish_embedding_rebuild_table(embedding_conn)
        active_path.write_text(temp_name, encoding="utf-8")
        fresh_client.close()
        client.close()

        return {
            "collection": temp_name,
            "count": fresh_count,
            "old_collection": old_name,
        }
    finally:
        if embedding_conn is not None:
            embedding_conn.close()
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-count", type=int, default=1000)
    parser.add_argument("--import-db", action="store_true")
    parser.add_argument("--reindex", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch-pause", type=float, default=0.0)
    parser.add_argument("--embed-batch-size", type=int, default=16)
    args = parser.parse_args()

    official = make_official_faqs(args.official_count)
    legacy = load_legacy_faqs(OLD_FAQ_PATH)
    merged = merge_faqs(official, legacy)

    write_json(OFFICIAL_OUTPUT, official)
    write_json(MERGED_OUTPUT, merged)
    print(f"official_faqs={len(official)} -> {OFFICIAL_OUTPUT}")
    print(f"legacy_faqs={len(legacy)} from {OLD_FAQ_PATH}")
    print(f"merged_faqs={len(merged)} -> {MERGED_OUTPUT}")

    if args.import_db:
        result = import_to_database(merged, dry_run=args.dry_run)
        print("database_import=" + json.dumps(result, ensure_ascii=False))

    if args.reindex and not args.dry_run:
        result = rebuild_chroma_sync(
            batch_pause=args.batch_pause,
            embed_batch_size=args.embed_batch_size,
        )
        print("chroma_reindex=" + json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
