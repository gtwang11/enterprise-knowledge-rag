"""RAG 管线编排：预处理 → Embedding → 检索 → 判阈 → 生成/降级"""

from config import RAG_SIMILARITY_THRESHOLD
from engine.prompts import SYSTEM_INSTRUCTION, QA_TEMPLATE
from engine.text_preprocessor import TextPreprocessor
from engine.embedding_manager import EmbeddingManager
from engine.vector_store import get_vector_store
from engine.llm_manager import LLMManager, LLMError


class RAGPipeline:
    """RAG 管线"""

    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.embedder = EmbeddingManager()
        self.vector_store = get_vector_store()
        self.llm = LLMManager()

    def execute(self, question: str) -> dict:
        """执行完整 RAG 流程"""
        # Step 1: 文本预处理（仅清洗特殊字符，保留原始语义用于 embedding）
        cleaned = self.preprocessor.clean(question)

        # Step 2: Embedding 向量化
        if not cleaned:
            return {
                "has_answer": False, "similarity": 0.0, "references": [],
                "message": "无法识别问题内容，请用中文描述您的问题，或提交工单。",
            }
        try:
            query_vector = self.embedder.embed(cleaned)  # 仅清洗特殊字符，不去停用词，与文档侧一致
        except Exception as e:
            from utils.logger import app_logger
            app_logger.error(f"Embedding 请求失败: {e}")
            return {
                "has_answer": False, "similarity": 0.0, "references": [],
                "message": "AI 服务暂不可用，请稍后再试或提交工单。",
            }

        # Step 3: ChromaDB 检索
        results = self.vector_store.search(query_vector)

        # Step 4: 阈值判断
        if not results or results[0]["similarity"] < RAG_SIMILARITY_THRESHOLD:
            return {
                "has_answer": False,
                "similarity": results[0]["similarity"] if results else 0.0,
                "references": [],
                "message": "无法找到相关答案，是否创建工单？",
            }

        # Step 5: LLM 生成
        from models.faq import Faq
        from database import SessionLocal

        context_parts = []
        db = SessionLocal()
        try:
            for r in results:
                faq = db.query(Faq).get(r["faq_id"])
                if faq:
                    context_parts.append(f"问题: {faq.question}\n答案: {faq.answer}")
                else:
                    context_parts.append(f"[FAQ #{r['faq_id']}] {r['question']}")
        finally:
            db.close()

        context = "\n\n---\n\n".join(context_parts)
        prompt = QA_TEMPLATE.format(
            system_instruction=SYSTEM_INSTRUCTION,
            context=context,
            question=question,
        )

        try:
            answer = self.llm.generate(prompt)
        except LLMError as e:
            from utils.logger import app_logger
            app_logger.error(f"LLM 生成失败: {e}")
            return {
                "has_answer": True,
                "answer": e.fallback,
                "similarity": results[0]["similarity"],
                "references": [{"faq_id": r["faq_id"], "question": r["question"]} for r in results],
                "message": f"LLM 生成失败: {e}",
            }

        return {
            "has_answer": True,
            "answer": answer,
            "similarity": results[0]["similarity"],
            "references": [{"faq_id": r["faq_id"], "question": r["question"]} for r in results],
            "message": None,
        }
