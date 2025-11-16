import asyncio
from typing import List, Dict, Tuple, Optional

from app.services.vector_store import vector_store
from app.services.gemini_service import gemini_service
from app.database import get_database
from app.models.qa import QA
from app.utils.db_helpers import convert_objectid_to_str


class RAGService:
    """
    Retrieval-Augmented Generation service for video Q&A.
    """

    def __init__(self):
        self.prompt_template = """Bạn là trợ lý AI hỗ trợ trả lời câu hỏi về nội dung video giáo dục.

QUY TẮC TRÍCH DẪN:
- Sau mỗi câu trả lời, thêm [số] để trích dẫn nguồn từ Context tương ứng
- Số bắt đầu từ 0 (Context 0, Context 1, Context 2,...)
- Nếu một câu dùng nhiều context: "Câu trả lời.[0][2]"
- CHỈ trích dẫn context thực sự được sử dụng
- KHÔNG sử dụng dấu ngoặc vuông [] cho bất kỳ mục đích nào khác ngoài trích dẫn nguồn
- Trả lời chính xác, súc tích bằng tiếng Việt

Ngữ cảnh từ video:
{context}

Câu hỏi: {question}

Trả lời:"""

    async def answer_question(
        self, workspace_id: str, question: str, video_ids: Optional[List[str]] = None
    ) -> Tuple[str, List[str]]:
        # Refine query for better vector search
        query_refinement_prompt = """Hãy mở rộng và cải thiện câu hỏi sau để tìm kiếm thông tin tốt hơn:

Câu hỏi gốc: {query}

Yêu cầu:
- Mở rộng các từ viết tắt (nếu có)
- Thêm từ đồng nghĩa hoặc từ liên quan
- Giữ nguyên thuật ngữ kỹ thuật quan trọng
- Ngắn gọn, súc tích (tối đa 2-3 câu)
- Bằng tiếng Việt

Câu hỏi đã cải thiện:"""

        refined_query = await gemini_service.generate_content(
            query_refinement_prompt.format(query=question)
        )

        # Use refined query if available, otherwise use original
        search_query = refined_query if refined_query is not None else question

        retrieved_contexts = vector_store.query_similar_contexts(
            workspace_id, search_query, 5, video_ids
        )

        if not retrieved_contexts:
            return (
                "I don't have enough information from the uploaded videos to answer this question.",
                [],
            )

        # Build context text and collect context IDs
        context_text = ""
        context_ids = []

        for idx, ctx in enumerate(retrieved_contexts):
            context_text += f"\n[Context {idx+1}]\n"
            context_text += f"Video: {ctx['metadata']['video_path']}\n"
            context_text += f"Time: {ctx['metadata']['start_time']:.2f}s - {ctx['metadata']['end_time']:.2f}s\n"
            context_text += f"Content: {ctx['text']}\n"

            # Collect context ID if available
            if "id" in ctx:
                context_ids.append(ctx["id"])
            elif "_id" in ctx["metadata"]:
                context_ids.append(str(ctx["metadata"]["_id"]))

        # Generate answer using shared Gemini service
        prompt = self.prompt_template.format(context=context_text, question=question)
        answer = await gemini_service.generate_content(prompt)

        # Handle case where Gemini returns None (blocked by safety/copyright)
        if answer is None:
            answer = "Xin lỗi, tôi không thể tạo câu trả lời lúc này. Vui lòng thử diễn đạt lại câu hỏi."

        return answer, context_ids


# Global instance
rag_service = RAGService()
