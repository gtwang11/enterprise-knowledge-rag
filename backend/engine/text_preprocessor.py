"""文本预处理：jieba 分词、去停用词、特殊字符过滤"""

import re

# 中文停用词表（精简版）
STOP_WORDS = set([
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "什么", "怎么", "如何", "为什么", "吗", "吧", "呢", "啊", "哦", "嗯",
    "可以", "这个", "那个", "哪个", "哪里", "还是", "或者", "但", "但是",
    "虽然", "因为", "所以", "如果", "的话", "而且", "然后", "已经", "正在",
])


class TextPreprocessor:
    """文本预处理"""

    def clean(self, text: str) -> str:
        """仅清洗特殊字符和多余空白，不去停用词，保留原始语义供 embedding 使用"""
        cleaned = re.sub(r'[^一-龥a-zA-Z0-9\s]', ' ', text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned if cleaned else text.strip()

    def process(self, text: str) -> str:
        # 去除特殊字符，保留中文、英文、数字
        cleaned = re.sub(r'[^一-龥a-zA-Z0-9\s]', ' ', text)
        # 去除多余空白
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if not cleaned:
            # 全特殊字符输入被洗为空串，返回原始文本（保留部分可识别内容）
            from utils.logger import app_logger
            app_logger.warning(f"文本预处理后为空，使用原始输入: '{text[:100]}'")
            return text.strip()

        # 尝试 jieba 分词
        try:
            import jieba
            words = jieba.cut(cleaned)
            words = [w.strip() for w in words if w.strip() and w.strip() not in STOP_WORDS]
            result = " ".join(words)
            # 如果分词后为空，回退到清理后的文本
            return result if result.strip() else cleaned
        except ImportError:
            return cleaned
