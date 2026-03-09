"""Google Gemini-based podcast script generator."""

from google import genai

from src.exceptions import ScriptGenerationError


class GoogleScriptGenerator:
    """Generates podcast scripts using Google Gemini."""

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        """Send a prompt to Gemini and return the generated script text.

        Args:
            prompt: Complete prompt including content and formatting instructions.

        Returns:
            Raw script text from the model.

        Raises:
            ScriptGenerationError: If the API call fails or returns empty content.
        """
        try:
            response = self._client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
            )
        except Exception as e:
            raise ScriptGenerationError(f"Script generation failed: {e}") from e

        text = getattr(response, "text", None)
        if not text:
            raise ScriptGenerationError("Script generation returned empty content.")

        return text
