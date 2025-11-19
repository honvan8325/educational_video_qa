from app.services.generators.base_generator import BaseGenerator
from app.services.generators.gemini_generator import GeminiGenerator


def get_generator(generator_type: str = "gemini") -> BaseGenerator:
    print(f"Initializing generator of type: {generator_type}")
    if generator_type == "gemini":
        return GeminiGenerator()
    else:
        raise ValueError(f"Unknown generator type: {generator_type}.")


__all__ = ["BaseGenerator", "GeminiGenerator" "get_generator"]
