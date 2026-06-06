"""RAG 管线编排：预处理 → Embedding → 检索 → 判阈 → 生成/降级"""

from config import RAG_SIMILARITY_THRESHOLD
from engine.prompts import SYSTEM_INSTRUCTION, QA_TEMPLATE
from engine.text_preprocessor import TextPreprocessor
from engine.embedding_manager import EmbeddingManager
from engine.vector_store import get_vector_store
from engine.llm_manager import LLMManager


class RAGPipeline:
    """RAG 管线"""

    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.embedder = EmbeddingManager()
        self.vector_store = get_vector_store()
        self.llm = LLMManager()

    def execute(self, question: str) -> dict:
        """执行完整 RAG 流程"""
        # Step 1: 文本预处理
        cleaned = self.preprocessor.process(question)

        # Step 2: Embedding 向量化
        query_vector = self.embedder.embed(cleaned)
        if not query_vector or all(v == 0.0 for v in query_vector):
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

        answer = self.llm.generate(prompt)

        return {
            "has_answer": True,
            "answer": answer,
            "similarity": results[0]["similarity"],
            "references": [{"faq_id": r["faq_id"], "question": r["question"]} for r in results],
            "message": None,
        }
