"""操作日志服务"""

from sqlalchemy.orm import Session

from models.operation_log import OperationLog


def log_operation(db: Session, operator_id: int, action: str,
                  target_type: str = None, target_id: int = None,
                  detail: str = None, ip_address: str = None):
    db.add(OperationLog(
        operator_id=operator_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    ))
    db.commit()
