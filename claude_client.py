"""Claude LLM client via Google Vertex AI for generating documentation."""

import os
import time
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for Claude via Google Vertex AI."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        region: Optional[str] = None,
        model_name: str = "claude-sonnet-4-6",
    ):
        project_id = project_id or os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
        region = region or os.getenv("CLOUD_ML_REGION", "us-east5")

        if not project_id:
            raise ValueError(
                "ANTHROPIC_VERTEX_PROJECT_ID is required for Claude Vertex AI"
            )

        try:
            from anthropic import AnthropicVertex
        except ImportError:
            raise ImportError(
                'anthropic[vertex] is required. Install with: '
                'pip install "anthropic[vertex]" google-cloud-aiplatform'
            )

        self.client = AnthropicVertex(project_id=project_id, region=region)
        self.model_name = model_name
        logger.info(
            f"Initialized Claude Vertex client: project={project_id}, "
            f"region={region}, model={model_name}"
        )

    def generate(self, prompt: str, max_retries: int = 3) -> str:
        """Generate content using Claude via Vertex AI.

        Accepts the same single-string prompt interface as GeminiClient.
        """
        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Generating content with Claude ({self.model_name}) "
                    f"(attempt {attempt + 1}/{max_retries})"
                )

                message = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )

                text_parts = []
                for block in message.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)

                result = "\n".join(text_parts)
                if result:
                    logger.info("Successfully generated content with Claude")
                    return result

                logger.warning("Empty response from Claude")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return ""

            except Exception as e:
                logger.error(f"Error generating content with Claude: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

        return ""
