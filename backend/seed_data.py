"""种子数据：预置 20+ 条示例 FAQ + admin 账号"""

from models.user import User
from models.faq import Faq
from utils.security import hash_password
from engine.vector_store import get_vector_store
from utils.logger import app_logger


SEED_FAQS = [
    {"question": "账号被冻结了怎么处理？", "answer": "请通过自助方式访问网址 http://itsm.company.com/unfreeze 进行自助解冻，或拨打 IT 服务热线 10000 转 3。", "category": "账号问题", "keywords": "冻结,解冻,账号"},
    {"question": "忘记登录密码怎么办？", "answer": "请联系部门系统管理员进行密码重置。重置后的初始密码会在首次登录时强制要求修改。", "category": "账号问题", "keywords": "密码,忘记,重置"},
    {"question": "新员工如何申请运维系统账号？", "answer": "由部门系统管理员在运维门户的'账号管理'模块中创建账号。创建时需填写账号名、姓名、手机号、部门、角色（一线运维人员或资深运维专家）。创建后系统会自动生成初始密码。", "category": "账号问题", "keywords": "新员工,申请账号,创建"},
    {"question": "网络连接不稳定怎么排查？", "answer": "1. 检查网线是否松动或网口指示灯是否正常。\n2. 使用 ping 命令测试网关连通性：ping 192.168.1.1\n3. 检查 DNS 配置是否正确。\n4. 尝试重启网络设备。\n5. 如果问题持续，提交网络故障工单。", "category": "网络问题", "keywords": "网络,连接,不稳定,排查"},
    {"question": "VPN 连接失败如何处理？", "answer": "1. 确认 VPN 客户端版本是否为最新版本。\n2. 检查账号密码是否正确。\n3. 确认网络防火墙没有阻止 VPN 端口。\n4. 尝试切换 VPN 服务器节点。\n5. 如仍无法连接，联系网络安全团队。", "category": "网络问题", "keywords": "VPN,连接失败"},
    {"question": "服务器无法远程登录怎么办？", "answer": "1. 确认目标服务器 IP 地址和端口号是否正确。\n2. 检查服务器是否处于运行状态（可通过 IPMI/iLO 查看）。\n3. 检查防火墙规则是否阻止了 SSH/RDP 端口。\n4. 确认账号是否有远程登录权限。\n5. 如果服务器宕机，需到机房现场处理或提交硬件故障工单。", "category": "网络问题", "keywords": "服务器,远程,登录,失败"},
    {"question": "交换机端口指示灯异常怎么处理？", "answer": "1. 记录异常端口的指示灯状态（灭、橙色、闪烁频率）。\n2. 检查端口连接的设备是否正常供电。\n3. 尝试更换网线排除线路问题。\n4. 登录交换机管理界面查看端口状态和错误计数。\n5. 如果是端口硬件故障，需更换端口或交换机。\n6. 参考交换机型号手册：华为 S5700 系列端口故障排查指南。", "category": "硬件故障", "keywords": "交换机,端口,指示灯,异常"},
    {"question": "服务器硬盘故障告警如何响应？", "answer": "1. 确认告警来源和硬盘位置（通过 iLO/iDRAC 或 IPMI）。\n2. 检查 RAID 阵列状态，确认是否已触发自动重建。\n3. 如果是热备盘已接管，安排更换故障硬盘。\n4. 如果 RAID 降级且无热备，立即备份关键数据。\n5. 联系硬件厂商安排硬盘更换（华为/浪潮/Dell 对应不同的报修流程）。", "category": "硬件故障", "keywords": "硬盘,故障,告警,RAID"},
    {"question": "服务器内存不足如何排查？", "answer": "1. 使用 free -m 或 top 命令查看内存使用情况。\n2. 检查是否有异常进程占用大量内存。\n3. 查看系统日志 /var/log/messages 是否有 OOM Killer 记录。\n4. 如果是应用内存泄漏，重启相关服务暂时释放。\n5. 评估是否需要增加物理内存或优化应用配置。", "category": "硬件故障", "keywords": "内存,不足,OOM"},
    {"question": "设备过热告警怎么处理？", "answer": "1. 立即检查机房空调是否正常运行。\n2. 检查设备进风口和出风口是否被堵塞。\n3. 使用温度计测量设备进风温度，正常应在 18-27℃。\n4. 清理设备内部灰尘（需停机操作）。\n5. 如果空调故障，立即联系动力环境维护团队。", "category": "硬件故障", "keywords": "过热,温度,告警"},
    {"question": "应用服务进程意外停止如何恢复？", "answer": "1. 登录服务器检查服务状态：systemctl status <service_name>\n2. 查看服务日志排查停止原因：journalctl -u <service_name> -n 50\n3. 重启服务：systemctl restart <service_name>\n4. 配置 systemd 自动重启策略：Restart=always\n5. 如果频繁停止，需深入排查根因（内存不足、配置错误、依赖服务异常等）。", "category": "软件故障", "keywords": "服务,停止,重启,systemd"},
    {"question": "数据库连接池耗尽如何处理？", "answer": "1. 查看数据库当前连接数：SHOW PROCESSLIST (MySQL) 或 SELECT count(*) FROM pg_stat_activity (PostgreSQL)。\n2. 找出长时间未释放的连接，Kill 掉空闲连接。\n3. 检查应用代码是否有连接泄漏（未关闭的连接）。\n4. 临时增大连接池上限：修改 max_connections 参数。\n5. 长期方案：优化应用连接管理，增加连接池监控告警。", "category": "软件故障", "keywords": "数据库,连接池,耗尽"},
    {"question": "系统日志磁盘空间满了怎么办？", "answer": "1. 查看磁盘使用情况：df -h\n2. 找出大文件：du -sh /var/log/* | sort -rh | head -10\n3. 压缩归档旧日志：gzip /var/log/<old_log>\n4. 删除过期归档日志（保留策略内）。\n5. 配置 logrotate 自动轮转和清理。\n6. 如果日志增长速度异常，排查是否有应用产生大量错误日志。", "category": "软件故障", "keywords": "日志,磁盘,空间,满"},
    {"question": "没有访问某个系统的权限怎么办？", "answer": "1. 确认自己是否已申请该系统权限。\n2. 访问 IT 服务门户 http://itsm.company.com 提交权限申请。\n3. 选择需要申请的系统和权限级别（只读/操作/管理）。\n4. 填写申请理由并提交，等待部门主管审批。\n5. 审批通过后权限自动开通，通常需要 1-2 个工作日。", "category": "权限问题", "keywords": "权限,访问,申请"},
    {"question": "文件共享目录无法访问如何解决？", "answer": "1. 检查网络连通性：ping <file_server_ip>\n2. 确认自己有该共享目录的访问权限。\n3. Windows：检查 SMB 服务是否启用。Linux：检查 NFS/CIFS 挂载状态。\n4. 尝试使用 IP 地址直接访问（排除 DNS 问题）。\n5. 如果权限不足，申请相应权限后重试。", "category": "权限问题", "keywords": "文件共享,访问,权限不足"},
    {"question": "需要 root/管理员权限执行操作怎么办？", "answer": "1. 普通运维人员不允许直接持有 root 权限。\n2. 通过堡垒机提交特权操作申请，说明操作内容和原因。\n3. 申请需经过直属主管审批。\n4. 审批通过后获得临时授权（默认 4 小时有效）。\n5. 所有特权操作自动录屏和审计。", "category": "权限问题", "keywords": "root,管理员,特权,审批"},
    {"question": "系统安全基线检查不通过怎么整改？", "answer": "1. 查看安全扫描报告，确认不合规项的具体内容。\n2. 常见问题：密码策略不满足、未关闭不必要的端口、系统未打补丁。\n3. 按照安全基线清单逐项整改。\n4. 整改完成后重新执行安全扫描验证。\n5. 整改过程中如有疑问，联系安全合规团队。", "category": "安全合规", "keywords": "安全基线,合规,整改"},
    {"question": "发现系统被暴力破解攻击怎么办？", "answer": "1. 立即通知网络安全团队和安全管理员。\n2. 查看攻击来源 IP，在防火墙上临时封禁该 IP。\n3. 检查受影响账号的登录日志，确认是否有成功入侵。\n4. 如有账号被攻破，立即冻结该账号并重置密码。\n5. 配合安全团队进行溯源分析。", "category": "安全合规", "keywords": "暴力破解,攻击,安全"},
    {"question": "系统需要配置定时任务怎么操作？", "answer": "1. Linux 使用 crontab 配置：crontab -e\n2. Windows 使用任务计划程序。\n3. 配置前确认任务的执行频率和时间窗口。\n4. 确保任务脚本有执行权限且路径正确。\n5. 配置日志输出，便于后续排查问题。\n6. 关键定时任务需要配置监控告警。", "category": "系统配置", "keywords": "定时任务,crontab,配置"},
    {"question": "如何更新服务器的 hosts 文件？", "answer": "1. Linux：编辑 /etc/hosts，格式为 'IP 主机名 别名'\n2. Windows：编辑 C:\\Windows\\System32\\drivers\\etc\\hosts（需管理员权限）\n3. 修改后无需重启即可生效。\n4. 使用 ping 主机名验证是否解析正确。\n5. 注意：hosts 文件修改属于配置变更，需要在变更管理系统中记录。", "category": "系统配置", "keywords": "hosts,DNS,主机名"},
    {"question": "运维值班交接需要注意什么？", "answer": "1. 填写值班交接记录表，说明本班次处理的关键事件。\n2. 遗留问题需明确标注并告知接班人员。\n3. 确认监控告警系统运行正常。\n4. 确认值班手机/对讲机电量充足。\n5. 交班人和接班人双方签字确认。", "category": "其他", "keywords": "值班,交接,流程"},
    {"question": "发生重大故障如何启动应急预案？", "answer": "1. 判断故障等级（一般/重大/特大）和影响范围。\n2. 立即上报值班主管和部门负责人。\n3. 按照应急预案手册中对应场景的处置流程执行。\n4. 建立应急沟通群/电话会议，协调相关团队。\n5. 故障处理过程中每 30 分钟通报一次进展。\n6. 故障恢复后 24 小时内提交故障分析报告。", "category": "其他", "keywords": "重大故障,应急,预案"},
]


def seed_if_empty(db):
    """首次启动时填充种子数据"""
    # 创建 admin 账号
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=hash_password("123456"),
            display_name="系统管理员",
            phone="13800000000",
            department="IT运维部",
            role="admin",
        )
        db.add(admin)
        db.flush()
        app_logger.info("已创建 admin 账号 (初始密码: 123456)")

    # 检查 FAQ 是否为空
    faq_count = db.query(Faq).count()
    if faq_count > 0:
        app_logger.info(f"FAQ 表已有 {faq_count} 条数据，跳过种子数据初始化")
        return

    # 插入示例 FAQ
    store = get_vector_store()
    for item in SEED_FAQS:
        faq = Faq(
            question=item["question"],
            answer=item["answer"],
            category=item["category"],
            keywords=item.get("keywords"),
            created_by=admin.id,
        )
        db.add(faq)
        db.flush()

        # 同步向量库
        try:
            store.add_faq(faq.id, faq.question, faq.answer, faq.category, faq.keywords or "")
        except Exception as e:
            app_logger.error(f"种子FAQ向量化失败: faq_id={faq.id}, error={e}")

    db.commit()
    app_logger.info(f"已预置 {len(SEED_FAQS)} 条示例 FAQ")
    app_logger.info("提示：首次登录后请修改默认密码")
