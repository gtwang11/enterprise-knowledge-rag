"""FAQ 批量导入解析器：支持 Excel (.xlsx)、CSV (.csv) 和 JSON (.json)"""

import csv
import io
import json
from typing import List, Tuple


ALLOWED_CATEGORIES = [
    "账号问题", "网络问题", "硬件故障", "软件故障",
    "权限问题", "安全合规", "系统配置", "其他",
]


def parse_excel(file_content: bytes) -> Tuple[List[dict], List[str]]:
    """解析 Excel 文件，返回 (成功解析的行, 错误列表)"""
    try:
        import openpyxl
    except ImportError:
        return [], ["需要安装 openpyxl 库：pip install openpyxl"]

    wb = openpyxl.load_workbook(io.BytesIO(file_content))
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))  # 跳过表头

    items = []
    errors = []
    for i, row in enumerate(rows, start=2):
        if not row or not any(row):
            continue
        question = str(row[0]).strip() if row[0] else ""
        answer = str(row[1]).strip() if len(row) > 1 and row[1] else ""
        category = str(row[2]).strip() if len(row) > 2 and row[2] else ""
        tags = str(row[3]).strip() if len(row) > 3 and row[3] else ""
        keywords = str(row[4]).strip() if len(row) > 4 and row[4] else ""

        if not question:
            errors.append(f"第{i}行：问题为空，跳过")
            continue
        if not answer:
            errors.append(f"第{i}行：答案为空，跳过")
            continue
        if category and category not in ALLOWED_CATEGORIES:
            errors.append(f"第{i}行：分类'{category}'不在预定义列表中，跳过")
            continue

        items.append({
            "question": question[:500],
            "answer": answer[:10000],
            "category": category or "其他",
            "tags": tags[:200] if tags else None,
            "keywords": keywords[:500] if keywords else None,
        })

    return items, errors


def parse_json(file_content: bytes) -> Tuple[List[dict], List[str]]:
    """解析 JSON 文件：[{"question":"Q","answer":"A","category":"分类",...}]"""
    try:
        data = json.loads(file_content.decode("utf-8"))
    except json.JSONDecodeError as e:
        return [], [f"JSON格式错误: {e}"]
    if not isinstance(data, list):
        return [], ["JSON应为数组格式: [{...}, {...}]"]

    items = []
    errors = []
    for i, obj in enumerate(data, start=1):
        question = str(obj.get("question", "") or "").strip()
        answer = str(obj.get("answer", "") or "").strip()
        category = str(obj.get("category", "") or "").strip()
        tags = str(obj.get("tags", "") or "").strip()
        keywords = str(obj.get("keywords", "") or "").strip()

        if not question:
            errors.append(f"第{i}条：问题为空，跳过")
            continue
        if not answer:
            errors.append(f"第{i}条：答案为空，跳过")
            continue
        if category and category not in ALLOWED_CATEGORIES:
            errors.append(f"第{i}条：分类'{category}'不在预定义列表中，跳过")
            continue

        items.append({
            "question": question[:500],
            "answer": answer[:10000],
            "category": category or "其他",
            "tags": tags[:200] if tags else None,
            "keywords": keywords[:500] if keywords else None,
        })

    return items, errors


def parse_csv(file_content: bytes) -> Tuple[List[dict], List[str]]:
    """解析 CSV 文件"""
    text = file_content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    items = []
    errors = []

    for i, row in enumerate(reader, start=2):
        question = (row.get("问题") or "").strip()
        answer = (row.get("答案") or "").strip()
        category = (row.get("分类") or "").strip()
        tags = (row.get("标签") or "").strip()
        keywords = (row.get("关键词") or "").strip()

        if not question:
            errors.append(f"第{i}行：问题为空，跳过")
            continue
        if not answer:
            errors.append(f"第{i}行：答案为空，跳过")
            continue
        if category and category not in ALLOWED_CATEGORIES:
            errors.append(f"第{i}行：分类'{category}'不在预定义列表中，跳过")
            continue

        items.append({
            "question": question[:500],
            "answer": answer[:10000],
            "category": category or "其他",
            "tags": tags[:200] if tags else None,
            "keywords": keywords[:500] if keywords else None,
        })

    return items, errors
