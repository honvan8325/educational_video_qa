import asyncio
from typing import List, Tuple, Optional, Dict
import time
from app.services.retrievers import get_retriever
from app.services.generators import get_generator
from app.services.reranker_service import reranker_service


def format_conversation_history(history: List[Dict[str, str]]) -> str:
    if not history:
        return ""

    history_text = "\nLịch sử hội thoại trước đó:\n"
    for i, qa in enumerate(history, 1):
        question = qa.get("question", "")
        answer = qa.get("answer", "")
        if len(answer) > 200:
            answer = answer[:200] + "..."
        history_text += f"[{i}] Người dùng: {question}\n"
        history_text += f"    Trả lời: {answer}\n\n"

    return history_text


def get_query_refinement_prompt(
    retriever_type: str,
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> str:

    history_section = (
        format_conversation_history(conversation_history)
        if conversation_history
        else ""
    )

    history_instruction = ""
    if history_section:
        history_instruction = """
- Dựa vào lịch sử hội thoại để hiểu ngữ cảnh
- Thay thế các đại từ (nó, này, đó, mạng đó, phương pháp này...) bằng danh từ cụ thể từ lịch sử
- Câu viết lại phải độc lập, không cần lịch sử vẫn hiểu được"""

    if retriever_type == "vector":
        return f"""
Viết lại câu hỏi cho phù hợp với semantic search (vector).
{history_section}
Câu hỏi hiện tại: {query}

Yêu cầu:
- Giữ đúng ý nghĩa câu hỏi{history_instruction}
- Chỉ trích xuất từ khóa quan trọng
- Không viết giải thích, không thêm thông tin mới
- Chỉ trả về câu query cuối cùng

Query đã tối ưu:
""".strip()

    elif retriever_type == "bm25":
        return f"""
Viết lại câu hỏi cho phù hợp với text search (BM25).
{history_section}
Câu hỏi hiện tại: {query}

Yêu cầu:
- Giữ đúng ý nghĩa{history_instruction}
- Tập trung vào từ khóa tìm kiếm
- Không giải thích, không thêm ví dụ
- Chỉ trả về câu query cuối cùng

Query đã tối ưu:
""".strip()

    elif retriever_type == "hybrid":
        return f"""
Viết lại câu hỏi phù hợp với semantic search (vector) và text search (BM25).
{history_section}
Câu hỏi hiện tại: {query}

Yêu cầu:
- Giữ đúng ý nghĩa{history_instruction}
- Trích từ khóa quan trọng
- Không giải thích, không thêm thông tin
- Chỉ trả về query đã tối ưu

Query đã tối ưu:
""".strip()

    return query


class RAGService:

    def __init__(self):
        self.prompt_template = """
Bạn là trợ lý AI trả lời dựa hoàn toàn vào nội dung trong video.

LUẬT DÙNG NGỮ CẢNH:
- Chỉ dùng thông tin trong mục "Ngữ cảnh từ video".
- Không được bịa thêm.
- Nếu thiếu thông tin → phải nói rõ "không đủ thông tin để kết luận".

LUẬT TRÍCH DẪN NGUỒN:
- Mọi ý lấy từ context phải gắn trích dẫn dạng [1], [2], [3], ...
- Đánh số context theo thứ tự xuất hiện trong phần "Ngữ cảnh từ video".
- Ý dùng nhiều context → [1][3][5].
- Không dùng [] cho mục đích khác ngoài trích dẫn.
- Không dùng [1] bên trong công thức toán.

LUẬT VIẾT CÔNG THỨC TOÁN:
- Công thức inline: $...$
- Công thức block: $$...$$
- Không dùng code block ```...``` cho công thức.
- Không xuống dòng tùy ý trong $...$ hoặc $$...$$.
- Trong công thức, dùng ngoặc tròn và ngoặc nhọn cho ký hiệu toán, tránh ngoặc vuông để không nhầm với trích dẫn.
- Luôn đóng/mở đủ dấu $ và $$.

YÊU CẦU TRẢ LỜI:
- Trả lời tiếng Việt, rõ ràng, chính xác.
- Tuân thủ đầy đủ luật trích dẫn & công thức toán.
- Không lặp lại câu hỏi nếu không cần.

Ngữ cảnh từ video:
{context}

Câu hỏi: {question}

Trả lời:
"""

    async def answer_question(
        self,
        workspace_id: str,
        question: str,
        video_ids: Optional[List[str]] = None,
        retriever_type: str = "vector",
        generator_type: str = "gemini",
        embedding_model: str = "dangvantuan",
        use_reranker: bool = False,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, List[str]]:
        # Get retriever and generator instances
        retriever = get_retriever(retriever_type, embedding_model)
        generator = get_generator(generator_type)

        # Refine query for better vector search (with conversation history if available)
        query_refinement_prompt = get_query_refinement_prompt(
            retriever_type, question, conversation_history
        )

        start_time = time.time()
        refined_query = await generator.generate_content(query_refinement_prompt)
        end_time = time.time()
        print(f"Query refinement took {(end_time - start_time):.2f} seconds.")
        print(f"Refined query: {refined_query}")

        # Use refined query if available, otherwise use original
        search_query = refined_query if refined_query is not None else question

        retrieval_count = 20 if use_reranker else 8
        final_count = 8

        start_time = time.time()
        retrieved_contexts = await retriever.query_similar_contexts(
            workspace_id, search_query, retrieval_count, video_ids
        )
        end_time = time.time()
        print(f"Retrieval took {(end_time - start_time):.2f} seconds.")

        if use_reranker and retrieved_contexts:
            retrieved_contexts = reranker_service.rerank(
                query=search_query,
                contexts=retrieved_contexts,
                top_n=final_count,
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

        # Generate answer using selected generator
        prompt = self.prompt_template.format(context=context_text, question=question)

        start_time = time.time()
        answer = await generator.generate_content(prompt)
        end_time = time.time()
        print(f"Answer generation took {(end_time - start_time):.2f} seconds.")

        # Handle case where Gemini returns None (blocked by safety/copyright)
        if answer is None:
            answer = "Xin lỗi, tôi không thể tạo câu trả lời lúc này. Vui lòng thử diễn đạt lại câu hỏi."

        return answer, context_ids


# Global instance
rag_service = RAGService()
