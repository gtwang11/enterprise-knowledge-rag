"""FAQ 知识库路由"""

import time
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from database import get_db
from dependencies import require_role
from models.user import User
from schemas.faq import FaqCreate, FaqUpdate, FaqQuery, FaqOut, FaqBatchDelete
from schemas.common import ApiResponse, PageData
from services import faq_service

router = APIRouter(prefix="/api/faq", tags=["FAQ管理"])


@router.get("")
def list_faqs(
    keyword: str = None, category: str = None, status: str = None,
    start_date: str = None, end_date: str = None, page: int = 1, page_size: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "expert")),
):
    params = {"keyword": keyword, "category": category, "status": status,
              "start_date": start_date, "end_date": end_date,
              "page": page, "page_size": page_size}
    items, total = faq_service.query_faqs(db, params)
    out_items = [FaqOut(
        id=f.id, question=f.question, answer=f.answer, category=f.category,
        tags=f.tags, keywords=f.keywords, status=f.status, version=f.version,
        source_ticket_id=f.source_ticket_id, created_by=f.created_by,
        created_at=f.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=f.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    ) for f in items]
    total_pages = (total + page_size - 1) // page_size
    return ApiResponse(code=200, message="success", data=PageData(
        items=[o.model_dump() for o in out_items], total=total,
        page=page, page_size=page_size, total_pages=total_pages,
    ).model_dump(), timestamp=int(time.time() * 1000))


@router.post("")
def create_faq(req: FaqCreate, db: Session = Depends(get_db),
               admin: User = Depends(require_role("admin"))):
    faq = faq_service.create_faq(db, req.model_dump(), admin.id)
    return ApiResponse(code=201, message="success", data={"id": faq.id},
                       timestamp=int(time.time() * 1000))


@router.get("/{faq_id}")
def get_faq(faq_id: int, db: Session = Depends(get_db),
            user: User = Depends(require_role("admin", "expert"))):
    from models.faq import Faq as FaqModel
    faq = db.query(FaqModel).get(faq_id)
    if not faq:
        return ApiResponse(code=404, message="FAQ不存在", data=None, timestamp=int(time.time() * 1000))
    return ApiResponse(code=200, message="success", data=FaqOut(
        id=faq.id, question=faq.question, answer=faq.answer, category=faq.category,
        tags=faq.tags, keywords=faq.keywords, status=faq.status, version=faq.version,
        source_ticket_id=faq.source_ticket_id, created_by=faq.created_by,
        created_at=faq.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=faq.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    ).model_dump(), timestamp=int(time.time() * 1000))


@router.put("/{faq_id}")
def update_faq(faq_id: int, req: FaqUpdate, db: Session = Depends(get_db),
               admin: User = Depends(require_role("admin"))):
    try:
        faq_service.update_faq(db, faq_id, req.model_dump(exclude_none=True), admin.id)
        return ApiResponse(code=200, message="success", data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.delete("/{faq_id}")
def delete_faq(faq_id: int, db: Session = Depends(get_db),
               admin: User = Depends(require_role("admin"))):
    try:
        faq_service.delete_faqs(db, [faq_id])
        return ApiResponse(code=200, message="success", data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/batch-delete")
def batch_delete_faqs(req: FaqBatchDelete, db: Session = Depends(get_db),
                      admin: User = Depends(require_role("admin"))):
    try:
        faq_service.delete_faqs(db, req.ids)
        return ApiResponse(code=200, message=f"已删除 {len(req.ids)} 条FAQ",
                           data=None, timestamp=int(time.time() * 1000))
    except ValueError as e:
        return ApiResponse(code=400, message=str(e), data=None, timestamp=int(time.time() * 1000))


@router.post("/import")
def import_faqs(file: UploadFile = File(...), db: Session = Depends(get_db),
                admin: User = Depends(require_role("admin"))):
    content = file.file.read()
    filename = (file.filename or "").lower()

    from utils.faq_importer import parse_excel, parse_csv, parse_json
    if filename.endswith(".json"):
        items, errors = parse_json(content)
    elif filename.endswith(".csv"):
        items, errors = parse_csv(content)
    else:
        items, errors = parse_excel(content)

    if not items and errors:
        return ApiResponse(code=400, message="导入失败", data={"errors": errors},
                           timestamp=int(time.time() * 1000))

    result = faq_service.bulk_import_faqs(db, items, admin.id)
    result["errors"] = errors
    return ApiResponse(code=200, message=f"成功导入 {result['success_count']} 条，跳过 {result['skip_count']} 条",
                       data=result, timestamp=int(time.time() * 1000))


@router.post("/reindex", status_code=202)
def reindex_faqs(db: Session = Depends(get_db),
                  admin: User = Depends(require_role("admin"))):
    """后台全量重建向量索引 — 热切换，查询不中断"""
    result = faq_service.reindex_all_faqs(db)
    if result["success"]:
        return ApiResponse(code=202, message=result["message"], data=result,
                           timestamp=int(time.time() * 1000))
    else:
        return ApiResponse(code=409, message=result["message"], data=result,
                           timestamp=int(time.time() * 1000))


@router.get("/reindex/status")
def reindex_status(user: User = Depends(require_role("admin", "expert"))):
    """查询重建进度"""
    from engine.vector_store import get_reindex_status
    status = get_reindex_status()
    return ApiResponse(code=200, message="success", data=status,
                       timestamp=int(time.time() * 1000))
