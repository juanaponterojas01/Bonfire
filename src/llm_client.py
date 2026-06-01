"""Minimal LLM client wrapper using litellm with two-model support."""

import json
import os
import re

from dotenv import load_dotenv
from litellm import completion
from pydantic import BaseModel, ValidationError

from src.config import CONFIG


def strip_json_fences(text: str) -> str:
    """Remove markdown JSON code fences and trim whitespace.

    Strips `` ```json ... ``` `` and `` ``` ... ``` `` wrappers if present.

    Args:
        text: Raw text that may be wrapped in markdown code fences.

    Returns:
        The inner content with fences removed and whitespace trimmed.
    """
    pattern = r"^```(?:json)?\s*\n?(.*?)\n?\s*```$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def parse_llm_json_response(raw_response: str, response_model: type[BaseModel]) -> BaseModel:
    """Parse and validate a raw LLM response against a Pydantic model.

    Args:
        raw_response: The raw text response from the LLM.
        response_model: The Pydantic model to validate against.

    Returns:
        A validated instance of the response model.

    Raises:
        ValueError: If the response is not valid JSON or does not match the schema.
    """
    cleaned = strip_json_fences(raw_response)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM response is not valid JSON. Raw response: {raw_response!r}"
        ) from e

    try:
        return response_model.model_validate(data)
    except ValidationError as e:
        raise ValueError(
            f"LLM response does not match {response_model.__name__} schema. "
            f"Raw response: {raw_response!r}. Errors: {e}"
        ) from e


def call_llm_parsed(
    system_prompt: str,
    user_prompt: str,
    response_model: type[BaseModel],
    model: str = CONFIG.models.extraction_model,
    temperature: float = 0.2,
    max_retries: int = 1,
    timeout: float = CONFIG.settings.timeout,
) -> BaseModel:
    """Call an LLM and return a validated Pydantic model instance.

    Calls ``call_llm()`` with the schema-appended prompt, then parses and
    validates the response. On a ``ValueError`` from parsing, retries once
    with an error-correction hint appended to the system prompt.

    Args:
        system_prompt: The system-level instruction text.
        user_prompt: The user-level prompt text.
        response_model: The Pydantic model to validate against.
        model: Model identifier constant.
        temperature: Sampling temperature.
        max_retries: Number of retries on parse failure (default 1).
        timeout: Maximum time in seconds to wait for each LLM call.

    Returns:
        A validated instance of the response model.

    Raises:
        ValueError: If parsing fails after all retries.
        RuntimeError: If the underlying LLM call fails.
    """
    retry_prompt = system_prompt
    for attempt in range(max_retries + 1):
        raw = call_llm(
            system_prompt=retry_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            response_model=response_model,
            timeout=timeout,
        )

        try:
            return parse_llm_json_response(raw, response_model)
        except ValueError:
            if attempt < max_retries:
                retry_prompt = (
                    system_prompt
                    + f"\n\nYour previous response could not be parsed as valid JSON "
                    f"matching the required schema. Please try again and ensure your "
                    f"output is strictly valid JSON with no extra text."
                )
            else:
                raise


def _append_schema_instruction(system_prompt: str, response_model: type[BaseModel] | None) -> str:
    """Append a JSON schema instruction to the system prompt when a response model is provided.

    Args:
        system_prompt: The original system-level instruction text.
        response_model: Optional Pydantic model whose JSON schema will be
            appended to the system prompt to enforce structured output.

    Returns:
        The system prompt, optionally extended with the schema instruction.
    """
    if response_model is None:
        return system_prompt

    schema = response_model.model_json_schema()
    schema_dump = json.dumps(schema, ensure_ascii=False)
    return system_prompt + (
        f"\n\nYou must respond with valid JSON matching this schema: {schema_dump}\n"
        "Do NOT include markdown fences (```json ... ```) or any text outside the JSON object."
    )


def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = CONFIG.models.extraction_model,
    temperature: float = 0.2,
    response_model: type[BaseModel] | None = None,
    timeout: float = CONFIG.settings.timeout,
) -> str:
    """Call an LLM via litellm through the OpenCode proxy.

    Args:
        system_prompt: The system-level instruction text.
        user_prompt: The user-level prompt text.
        model: Model identifier constant (EXTRACTION_MODEL or WRITER_MODEL).
        temperature: Sampling temperature.
        response_model: Optional Pydantic model whose JSON schema will be
            appended to the system prompt to enforce structured output.
        timeout: Maximum time in seconds to wait for a response.

    Returns:
        The raw text content of the LLM response.

    Raises:
        ValueError: If OPENCODE_API_KEY is missing.
        RuntimeError: If the LLM call fails for any reason.
    """
    load_dotenv()
    opencode_api_key = os.getenv("OPENCODE_API_KEY")

    if not opencode_api_key:
        raise ValueError(
            "OPENCODE_API_KEY is not set. "
            "Please configure it in your environment or .env file."
        )

    full_system_prompt = _append_schema_instruction(system_prompt, response_model)

    try:
        response = completion(
            model=f"openai/{model}",
            messages=[
                {"role": "system", "content": full_system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            api_base=CONFIG.api.base_url,
            api_key=opencode_api_key,
            timeout=timeout,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e
