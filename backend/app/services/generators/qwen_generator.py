from typing import Optional
import asyncio

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from app.services.generators.base_generator import BaseGenerator


class QwenGenerator(BaseGenerator):
    def __init__(self):
        self.device = self._get_device()
        self.dtype = self._get_dtype()
        self.model_name = "Qwen/Qwen2.5-1.5B-Instruct"
        self.initialized = False

    def _get_device(self) -> torch.device:
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    def _get_dtype(self) -> torch.dtype:
        if torch.cuda.is_available():
            return torch.bfloat16
        elif torch.backends.mps.is_available():
            return torch.float16
        else:
            return torch.float32

    def _lazy_init(self):
        if self.initialized:
            return

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            dtype=self.dtype,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        ).to(self.device)

        self.model.eval()
        self.initialized = True

    async def generate_content(self, prompt: str) -> Optional[str]:
        self._lazy_init()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._generate_sync, prompt)

    def _build_messages(self, prompt: str):
        return [
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý AI hỗ trợ trả lời câu hỏi về nội dung video giáo dục "
                    "bằng tiếng Việt. Trả lời chính xác, súc tích, không bịa thêm ngoài ngữ cảnh."
                ),
            },
            {"role": "user", "content": prompt},
        ]

    def _generate_sync(self, prompt: str) -> Optional[str]:
        messages = self._build_messages(prompt)

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        eos_token_ids = [self.tokenizer.eos_token_id]
        try:
            im_end_id = self.tokenizer.convert_tokens_to_ids("<|im_end|>")
            if im_end_id is not None and im_end_id != self.tokenizer.eos_token_id:
                eos_token_ids.append(im_end_id)
        except Exception:
            pass

        with torch.inference_mode():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                eos_token_id=eos_token_ids,
                pad_token_id=self.tokenizer.pad_token_id,
                use_cache=True,
                no_repeat_ngram_size=4,
                repetition_penalty=1.1,
            )

        generated_ids = outputs[0][inputs.input_ids.shape[1] :]
        answer = self.tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        )

        return answer.strip() if answer else None
