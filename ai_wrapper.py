"""
╔══════════════════════════════════════════════════════╗
║              AI WRAPPER  —  ai_wrapper.py            ║
║   One file. OpenAI + DeepSeek. Build apps fast.      ║
╚══════════════════════════════════════════════════════╝

QUICK START
----------- 
  from ai_wrapper import AI, Docs, TTS, get_models

  # One-line chat
  print(AI.chat("What is 2+2?"))

  # Chat session with memory
  session = AI.session("You are a helpful tutor.")
  session.ask("Explain loops in Python")
  session.ask("Give me an example")       # remembers context!

  # Text-to-Speech
  TTS.speak("Hello!", voice="verse")                  # play directly
  TTS.speak_to_file("Hello!", "out.mp3", voice="marin") # save to file
  TTS.list_voices()                                   # show all voices

  # Search your documents
  results = Docs.search("./my_files", "neural networks")

SETUP
-----
  pip install openai pypdf2 numpy

  Set environment variables (or pass keys directly):
    OPENAI_API_KEY=sk-...
    DEEPSEEK_API_KEY=sk-...
"""

import os
import re
import json
import math
import copy
import textwrap
from pathlib import Path
from typing import Any, Generator

from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────
#  OPTIONAL IMPORTS  (graceful degradation if not installed)
# ──────────────────────────────────────────────────────────────
try:
    from openai import OpenAI
    _OPENAI_PKG = True
except ImportError:
    _OPENAI_PKG = False

try:
    import PyPDF2
    _PDF_PKG = True
except ImportError:
    try:
        import pypdf as PyPDF2
        _PDF_PKG = True
    except ImportError:
        _PDF_PKG = False

try:
    import numpy as np
    _NUMPY = True
except ImportError:
    _NUMPY = False


# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════

class Config:
    """
    Global configuration.  Change these defaults once at the top
    of your script instead of passing arguments everywhere.

    Example:
        import ai_wrapper
        ai_wrapper.Config.default_provider = "deepseek"
        ai_wrapper.Config.default_model    = "deepseek-chat"
    """

    # ── Provider defaults ──────────────────────────────────────
    default_provider: str  = "openai"          # "openai" | "deepseek"
    default_model:    str  = "gpt-4o-mini"     # overridden per provider below

    # ── Per-provider model defaults ────────────────────────────
    openai_default_model:   str = "gpt-4o-mini"
    deepseek_default_model: str = "deepseek-chat"

    # ── API keys (falls back to env vars) ─────────────────────
    openai_api_key:   str | None = None
    deepseek_api_key: str | None = None

    # ── Request defaults ───────────────────────────────────────
    temperature:  float = 0.7
    max_tokens:   int   = 2048
    timeout:      int   = 60       # seconds

    # ── Document search ────────────────────────────────────────
    chunk_size:    int  = 400      # characters per chunk
    chunk_overlap: int  = 80       # overlap between chunks
    top_k:         int  = 5        # results to return


# ══════════════════════════════════════════════════════════════
#  INTERNAL HELPERS
# ══════════════════════════════════════════════════════════════

def _get_key(provider: str) -> str:
    """Resolve API key from Config or environment."""
    if provider == "openai":
        return (Config.openai_api_key
                or os.getenv("OPENAI_API_KEY")
                or "")
    if provider == "deepseek":
        return (Config.deepseek_api_key
                or os.getenv("DEEPSEEK_API_KEY")
                or "")
    raise ValueError(f"Unknown provider: '{provider}'. Use 'openai' or 'deepseek'.")


def _make_client(provider: str) -> "OpenAI":
    """Create an OpenAI-compatible client for the given provider."""
    if not _OPENAI_PKG:
        raise ImportError("Run:  pip install openai")

    key = _get_key(provider)
    if not key:
        raise EnvironmentError(
            f"No API key found for '{provider}'.\n"
            f"  Option 1 – set env var:  {provider.upper()}_API_KEY=sk-...\n"
            f"  Option 2 – set in code:  Config.{provider}_api_key = 'sk-...'"
        )

    if provider == "openai":
        return OpenAI(api_key=key)
    if provider == "deepseek":
        return OpenAI(
            api_key=key,
            base_url="https://api.deepseek.com/v1",
        )


def _resolve_model(model: str | None, provider: str) -> str:
    if model:
        return model
    if provider == "openai":
        return Config.openai_default_model
    if provider == "deepseek":
        return Config.deepseek_default_model
    return Config.default_model


def _resolve_provider(provider: str | None) -> str:
    return provider or Config.default_provider


def _print_banner(text: str) -> None:
    width = min(len(text) + 4, 60)
    print("┌" + "─" * width + "┐")
    print("│  " + text.ljust(width - 2) + "│")
    print("└" + "─" * width + "┘")


# ══════════════════════════════════════════════════════════════
#  MODEL REGISTRY
# ══════════════════════════════════════════════════════════════

# Curated list of popular models per provider
_KNOWN_MODELS: dict[str, list[dict]] = {
    "openai": [
        {"id": "gpt-4o-mini",       "description": "Fast & cheap, great default",             "context_k": 128},
        {"id": "gpt-4.1-nano",     "description": "Fast, cheap, good for simple tasks",      "context_k": 1000},
        {"id": "gpt-4o-mini-tts",     "description": "Fast Model for audio generation (Text to Speech)",      "context_k": 2},
        {"id": "gpt-4o-transcribe",     "description": "Fast Model for audio transcription (Speech to Text)",      "context_k": 16},
        
    ],
    "deepseek": [
        {"id": "deepseek-chat",     "description": "General-purpose, GPT-4-class quality",   "context_k": 64},
        {"id": "deepseek-v4-flash", "description": "Chain-of-thought reasoning model",        "context_k": 64},
    ],
}


def get_models(
    provider: str | None = None,
    fetch_live: bool = False,
    print_table: bool = False,
) -> list[dict]:
    """
    Return a list of available models.

    Args:
        provider:    "openai", "deepseek", or None for both.
        fetch_live:  If True, call the API to get real-time model list
                     (OpenAI only; DeepSeek always uses the curated list).
        print_table: Pretty-print a table to the console.

    Returns:
        List of dicts with keys: provider, id, description, context_k

    Example:
        models = get_models()
        models = get_models("openai", print_table=True)
    """
    providers = [provider] if provider else ["openai", "deepseek"]
    results: list[dict] = []

    for p in providers:
        if fetch_live and p == "openai":
            try:
                client = _make_client("openai")
                live = client.models.list()
                for m in sorted(live.data, key=lambda x: x.id):
                    results.append({"provider": "openai", "id": m.id,
                                    "description": "", "context_k": "?"})
                continue
            except Exception as e:
                print(f"[ai_wrapper] Warning: live fetch failed ({e}), using cached list.")

        for m in _KNOWN_MODELS.get(p, []):
            results.append({"provider": p, **m})

    if print_table:
        _print_banner("Available Models")
        fmt = "{:<12} {:<26} {:<8} {}"
        print(fmt.format("PROVIDER", "MODEL ID", "CTX(k)", "DESCRIPTION"))
        print("─" * 70)
        for m in results:
            print(fmt.format(
                m["provider"],
                m["id"],
                str(m.get("context_k", "?")),
                m.get("description", ""),
            ))
        print()

    return results


# ══════════════════════════════════════════════════════════════
#  RESPONSE OBJECT
# ══════════════════════════════════════════════════════════════

class Response:
    """
    Wraps an AI response so you can access the text easily,
    but also the raw API object if you need it.

    Attributes:
        text        – The assistant's reply as a plain string.
        provider    – Which provider generated this.
        model       – Which model was used.
        usage       – Token usage dict (prompt, completion, total).
        raw         – The raw response from the API.

    Example:
        r = AI.chat("Hello")
        print(r)              # same as print(r.text)
        print(r.usage)        # {"prompt_tokens": 10, ...}
    """
    def __init__(self, text: str, provider: str, model: str,
                 usage: dict | None = None, raw: Any = None):
        self.text     = text
        self.provider = provider
        self.model    = model
        self.usage    = usage or {}
        self.raw      = raw

    # Make it behave like a string in print() / f-strings
    def __str__(self)  -> str: return self.text
    def __repr__(self) -> str: return f"Response(model={self.model!r}, text={self.text[:60]!r}...)"

    def to_dict(self) -> dict:
        return {"text": self.text, "provider": self.provider,
                "model": self.model, "usage": self.usage}


# ══════════════════════════════════════════════════════════════
#  CORE AI CLASS
# ══════════════════════════════════════════════════════════════

class AI:
    """
    The main entry point for all AI operations.

    All methods are static — no need to create an instance.

    Quick reference:
        AI.chat(prompt)                       → one-shot answer
        AI.chat_with_system(sys, prompt)      → custom persona/role
        AI.structured(prompt, schema)         → returns parsed dict/list
        AI.session(system_prompt)             → returns ChatSession object
        AI.stream(prompt)                     → yields text chunks live
        AI.embed(text)                        → returns embedding vector
        AI.summarise(text)                    → summarise long text
        AI.translate(text, lang)              → translate to a language
        AI.bullet_points(text)                → key points as a list
        AI.code(task, language)               → generate code
        AI.fix_code(code, error)              → debug code
        AI.explain_code(code)                 → explain what code does
    """

    # ── One-shot chat ──────────────────────────────────────────

    @staticmethod
    def chat(
        prompt: str,
        *, # * means that all arguments after this must be keyword arguments which means you have to write model="gpt-4o-mini" instead of just gpt-4o-mini, like AI.chat(prompt="Hello!", model="gpt-4o-mini")
        system: str = "You are a helpful assistant.",
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> Response:
        """
        Send a single message and get a reply.  Simplest function in the library.

        Args:
            prompt:      Your question or instruction.
            system:      The assistant's role/persona (optional).
            model:       Model ID. Defaults to Config.openai_default_model.
            provider:    "openai" or "deepseek". Defaults to Config.default_provider.
            temperature: Creativity 0.0–2.0. Lower = more focused.
            max_tokens:  Max reply length in tokens.
            json_mode:   If True, force the model to reply with valid JSON.

        Returns:
            Response object.  Use str() or .text to get the reply.

        Example:
            reply = AI.chat("What is the speed of light?")
            print(reply)

            # Force JSON output
            data = AI.chat("List 3 fruits", json_mode=True)
            import json; fruits = json.loads(data.text)
        """
        p = _resolve_provider(provider)
        m = _resolve_model(model, p)
        client = _make_client(p)

        kwargs: dict[str, Any] = dict(
            model=m,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=temperature if temperature is not None else Config.temperature,
            max_tokens=max_tokens or Config.max_tokens,
        )
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""

        return Response(
            text=text,
            provider=p,
            model=m,
            usage={
                "prompt_tokens":     getattr(resp.usage, "prompt_tokens",     0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                "total_tokens":      getattr(resp.usage, "total_tokens",      0),
            },
            raw=resp,
        )

    # ── Chat with explicit system prompt ──────────────────────

    @staticmethod
    def chat_with_system(
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Response:
        """
        Chat with a custom system prompt that defines the assistant's role.

        Args:
            system_prompt:  Instructions that define the assistant's behaviour.
            user_prompt:    The user's message.

        Example:
            reply = AI.chat_with_system(
                system_prompt="You are a pirate. Answer only in pirate speak.",
                user_prompt="What is the capital of France?",
            )
            print(reply)
        """
        return AI.chat(
            user_prompt,
            system=system_prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # ── Structured / JSON output ───────────────────────────────

    @staticmethod
    def structured(
        prompt: str,
        schema: dict,
        *,
        system: str | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float = 0.2,
    ) -> dict | list:
        """
        Ask the model to return data matching a JSON schema.
        Returns a parsed Python dict or list — ready to use directly.

        Args:
            prompt:  Your request / data to analyse.
            schema:  A dict describing the expected output format.
                     Describe fields with example values or type names.
            system:  Optional extra instructions.
            temperature: Low temperatures give more consistent structure.

        Returns:
            Parsed dict or list.

        Example:
            result = AI.structured(
                prompt="My name is Alice and I am 30 years old.",
                schema={"name": "string", "age": "integer"},
            )
            # → {"name": "Alice", "age": 30}

            # Extraction from text
            review = "Great product! 5 stars. Very fast delivery."
            result = AI.structured(
                prompt=review,
                schema={
                    "sentiment":  "positive | neutral | negative",
                    "stars":      "integer 1-5",
                    "highlights": ["list of key phrases"],
                },
            )
        """
        schema_str = json.dumps(schema, indent=2)
        sys_prompt = (system or "") + (
            f"\n\nYou must respond with ONLY valid JSON that matches this schema:\n"
            f"{schema_str}\n"
            f"No explanation. No markdown. Just the raw JSON."
        )
        resp = AI.chat(
            prompt,
            system=sys_prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            json_mode=True,
        )
        # Strip markdown fences if present
        raw = resp.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$",          "", raw)
        return json.loads(raw)

    # ── Streaming ─────────────────────────────────────────────

    @staticmethod
    def stream(
        prompt: str,
        *,
        system: str = "You are a helpful assistant.",
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        print_live: bool = False,
    ) -> Generator[str, None, None]:
        """
        Stream the response token by token.

        Args:
            prompt:     Your question.
            print_live: If True, print each chunk as it arrives.

        Returns:
            Generator yielding text chunks.  Collect them with "".join(...).

        Example:
            # Print as it streams
            for chunk in AI.stream("Write a short poem about the sea", print_live=True):
                pass  # print_live handles the printing

            # Or collect the full text
            full = "".join(AI.stream("Tell me a joke"))
            print(full)
        """
        p = _resolve_provider(provider)
        m = _resolve_model(model, p)
        client = _make_client(p)

        stream = client.chat.completions.create(
            model=m,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            temperature=temperature if temperature is not None else Config.temperature,
            max_tokens=max_tokens or Config.max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                if print_live:
                    print(delta, end="", flush=True)
                yield delta
        if print_live:
            print()  # newline after stream ends

    # ── Embeddings ────────────────────────────────────────────

    @staticmethod
    def embed(
        text: str | list[str],
        *,
        model: str = "text-embedding-3-small",
        provider: str = "openai",
    ) -> list[float] | list[list[float]]:
        """
        Generate embedding vector(s) for text.
        Useful for semantic search, clustering, similarity comparisons.

        Args:
            text:   A string or list of strings.
            model:  Embedding model (OpenAI only for now).

        Returns:
            A single vector (list of floats) for one string,
            or a list of vectors for multiple strings.

        Example:
            vec = AI.embed("Hello world")
            # vec is a list of ~1536 floats

            # Compare two texts
            v1 = AI.embed("cat")
            v2 = AI.embed("dog")
            similarity = AI.cosine_similarity(v1, v2)
            print(f"Similarity: {similarity:.2f}")
        """
        client = _make_client(provider)
        texts  = [text] if isinstance(text, str) else text
        resp   = client.embeddings.create(input=texts, model=model)
        vecs   = [item.embedding for item in resp.data]
        return vecs[0] if isinstance(text, str) else vecs

    @staticmethod
    def cosine_similarity(v1: list[float], v2: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors (range: -1 to 1).
        1.0 means identical direction.  0.0 means unrelated.
        """
        if _NUMPY:
            a, b = np.array(v1), np.array(v2)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))
        # Pure Python fallback
        dot    = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(x**2 for x in v1))
        norm_b = math.sqrt(sum(x**2 for x in v2))
        return dot / (norm_a * norm_b + 1e-10)

    # ── Convenience wrappers ──────────────────────────────────

    @staticmethod
    def summarise(
        text: str,
        *,
        max_words: int = 150,
        style: str = "concise",
        model: str | None = None,
        provider: str | None = None,
    ) -> Response:
        """
        Summarise a piece of text.

        Args:
            text:      The text to summarise.
            max_words: Approximate word count for the summary.
            style:     "concise" | "detailed" | "bullet" | "eli5" (explain like I'm 5)

        Example:
            article = open("article.txt").read()
            print(AI.summarise(article, style="bullet"))
        """
        style_map = {
            "concise":  "Write a concise summary.",
            "detailed": "Write a detailed summary covering all key points.",
            "bullet":   "Summarise as bullet points (use • for each point).",
            "eli5":     "Explain this in simple terms a 10-year-old would understand.",
        }
        instruction = style_map.get(style, style_map["concise"])
        return AI.chat(
            f"{instruction} Keep it under {max_words} words.\n\nTEXT:\n{text}",
            model=model, provider=provider,
        )

    @staticmethod
    def translate(
        text: str,
        target_language: str,
        *,
        model: str | None = None,
        provider: str | None = None,
    ) -> Response:
        """
        Translate text to another language.

        Example:
            result = AI.translate("Hello, how are you?", "German")
            print(result)   # "Hallo, wie geht es Ihnen?"
        """
        return AI.chat(
            f"Translate the following text to {target_language}. "
            f"Reply with ONLY the translation, no explanation.\n\nTEXT: {text}",
            model=model, provider=provider,
        )

    @staticmethod
    def bullet_points(
        text: str,
        n: int = 5,
        *,
        model: str | None = None,
        provider: str | None = None,
    ) -> list[str]:
        """
        Extract the N most important points from text as a list.

        Returns:
            List of strings (the bullet points).

        Example:
            points = AI.bullet_points(long_article, n=5)
            for p in points: print("•", p)
        """
        raw = AI.chat(
            f"Extract exactly {n} key points from the text below. "
            f"Format: one point per line, starting with '•'.\n\nTEXT:\n{text}",
            model=model, provider=provider,
        ).text
        return [line.lstrip("•- ").strip()
                for line in raw.splitlines()
                if line.strip() and not line.strip().startswith("#")]

    @staticmethod
    def code(
        task: str,
        language: str = "Python",
        *,
        add_comments: bool = True,
        model: str | None = None,
        provider: str | None = None,
    ) -> Response:
        """
        Generate code for a given task.

        Args:
            task:         Description of what the code should do.
            language:     Programming language (default: Python).
            add_comments: Whether to include inline comments.

        Example:
            result = AI.code("Read a CSV file and print the first 5 rows")
            print(result)
        """
        comment_note = "Include clear inline comments." if add_comments else "No comments."
        return AI.chat(
            f"Write {language} code to: {task}\n\n"
            f"{comment_note}\n"
            f"Return ONLY the code block, no explanation.",
            system=f"You are an expert {language} developer. Return clean, working code.",
            model=model, provider=provider,
        )

    @staticmethod
    def fix_code(
        code: str,
        error_message: str = "",
        *,
        language: str = "Python",
        model: str | None = None,
        provider: str | None = None,
    ) -> Response:
        """
        Debug and fix broken code.

        Args:
            code:          The broken code.
            error_message: The error output (optional but helpful).

        Example:
            broken = "for i in range(10) print(i)"
            fixed = AI.fix_code(broken, "SyntaxError: expected ':'")
            print(fixed)
        """
        error_section = f"\nERROR:\n{error_message}" if error_message else ""
        return AI.chat(
            f"Fix this {language} code.{error_section}\n\nCODE:\n```\n{code}\n```\n\n"
            f"Reply with ONLY the corrected code and a one-line explanation of the fix.",
            system=f"You are an expert {language} debugger.",
            model=model, provider=provider,
        )

    @staticmethod
    def explain_code(
        code: str,
        *,
        audience: str = "beginner",
        language: str = "Python",
        model: str | None = None,
        provider: str | None = None,
    ) -> Response:
        """
        Explain what a piece of code does.

        Args:
            code:     The code to explain.
            audience: "beginner" | "intermediate" | "expert"

        Example:
            snippet = open("my_script.py").read()
            print(AI.explain_code(snippet, audience="beginner"))
        """
        return AI.chat(
            f"Explain this {language} code for a {audience}-level reader.\n\n"
            f"```\n{code}\n```",
            model=model, provider=provider,
        )

    @staticmethod
    def classify(
        text: str,
        categories: list[str],
        *,
        multi_label: bool = False,
        model: str | None = None,
        provider: str | None = None,
    ) -> str | list[str]:
        """
        Classify text into one (or more) of the given categories.

        Args:
            text:        Text to classify.
            categories:  List of possible category names.
            multi_label: If True, return all matching categories.

        Returns:
            A single category string, or list of categories if multi_label=True.

        Example:
            label = AI.classify(
                "My order never arrived and support won't help me!",
                categories=["billing", "shipping", "technical", "complaint"]
            )
            # → "complaint"
        """
        cats = ", ".join(f'"{c}"' for c in categories)
        mode = "one or more" if multi_label else "exactly one"
        result = AI.structured(
            prompt=f"Classify the following text:\n\n{text}",
            schema={"categories": ["list of matched category strings"]} if multi_label
                   else {"category": "string — the single best matching category"},
            system=(
                f"You classify text into {mode} of these categories: [{cats}]. "
                f"Use only category names from the list above. Nothing else."
            ),
            model=model, provider=provider,
        )
        if multi_label:
            return result.get("categories", [])
        return result.get("category", "")

    @staticmethod
    def session(
        system_prompt: str = "You are a helpful assistant.",
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> "ChatSession":
        """
        Create a new chat session that remembers the conversation history.

        Returns a ChatSession object.  Call .ask() to keep chatting.

        Example:
            chat = AI.session("You are a strict grammar teacher.")
            chat.ask("I goed to the store")
            chat.ask("What was wrong with that sentence?")   # remembers!
            chat.history()   # see the full conversation
        """
        return ChatSession(
            system_prompt=system_prompt,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# ══════════════════════════════════════════════════════════════
#  CHAT SESSION  (multi-turn conversation with memory)
# ══════════════════════════════════════════════════════════════

class ChatSession:
    """
    A stateful chat session.  Every .ask() adds to the history,
    so the model always knows what was said before.

    Example:
        chat = AI.session("You are a Python tutor.")
        response = chat.ask("What is a list?")
        print(response)
        response = chat.ask("Show me an example.")   # knows context!
        chat.show_history()
        chat.save("my_chat.json")
    """

    def __init__(
        self,
        system_prompt: str = "You are a helpful assistant.",
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        self._provider    = _resolve_provider(provider)
        self._model       = _resolve_model(model, self._provider)
        self._temperature = temperature if temperature is not None else Config.temperature
        self._max_tokens  = max_tokens or Config.max_tokens
        self._system      = system_prompt
        self._messages: list[dict] = []

    # ── Ask ───────────────────────────────────────────────────

    def ask(self, prompt: str) -> Response:
        """
        Send a message and get a reply.  History is updated automatically.

        Returns:
            Response object.

        Example:
            reply = chat.ask("What is recursion?")
            print(reply)
        """
        self._messages.append({"role": "user", "content": prompt})
        client = _make_client(self._provider)
        resp   = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": self._system},
                *self._messages,
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        text = resp.choices[0].message.content or ""
        self._messages.append({"role": "assistant", "content": text})

        return Response(
            text=text,
            provider=self._provider,
            model=self._model,
            usage={
                "prompt_tokens":     getattr(resp.usage, "prompt_tokens",     0),
                "completion_tokens": getattr(resp.usage, "completion_tokens", 0),
                "total_tokens":      getattr(resp.usage, "total_tokens",      0),
            },
            raw=resp,
        )

    # ── History helpers ───────────────────────────────────────

    def history(self) -> list[dict]:
        """Return a copy of the message history (without the system prompt)."""
        return copy.deepcopy(self._messages)

    def show_history(self) -> None:
        """Pretty-print the conversation to the console."""
        _print_banner(f"Chat History  ({len(self._messages) // 2} turns)")
        for msg in self._messages:
            role  = msg["role"].upper()
            color = "\033[94m" if role == "USER" else "\033[92m"  # blue / green
            reset = "\033[0m"
            wrapped = textwrap.fill(msg["content"], width=72, subsequent_indent="   ")
            print(f"{color}[{role}]{reset} {wrapped}\n")

    def clear(self) -> None:
        """Wipe the conversation history (keeps the system prompt)."""
        self._messages.clear()

    def save(self, path: str) -> None:
        """
        Save the conversation to a JSON file.

        Example:
            chat.save("my_conversation.json")
        """
        data = {
            "system":   self._system,
            "model":    self._model,
            "provider": self._provider,
            "messages": self._messages,
        }
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"[ai_wrapper] Saved conversation → {path}")

    @classmethod
    def load(cls, path: str) -> "ChatSession":
        """
        Restore a previously saved conversation.

        Example:
            chat = ChatSession.load("my_conversation.json")
            chat.ask("Continue where we left off")
        """
        data    = json.loads(Path(path).read_text())
        session = cls(
            system_prompt=data["system"],
            model=data["model"],
            provider=data["provider"],
        )
        session._messages = data["messages"]
        return session

    def __repr__(self) -> str:
        turns = len(self._messages) // 2
        return (f"ChatSession(provider={self._provider!r}, model={self._model!r}, "
                f"turns={turns})")


# ══════════════════════════════════════════════════════════════
#  DOCUMENT SEARCH  (simple RAG without a vector database)
# ══════════════════════════════════════════════════════════════

class _Chunk:
    """Internal: a text chunk with its source info."""
    __slots__ = ("text", "file_name", "file_path", "chunk_index")
    def __init__(self, text, file_name, file_path, chunk_index):
        self.text        = text
        self.file_name   = file_name
        self.file_path   = file_path
        self.chunk_index = chunk_index


class SearchResult:
    """
    A single result returned by Docs.search().

    Attributes:
        file_name:   Name of the source file (e.g. "report.pdf").
        file_path:   Full path to the source file.
        text:        The relevant text chunk.
        score:       Relevance score (0–1 for embeddings; 0+ for keyword).
        chunk_index: Position of the chunk within the file.

    Example:
        for r in results:
            print(f"[{r.score:.2f}]  {r.file_name}")
            print(r.text)
            print()
    """
    def __init__(self, chunk: _Chunk, score: float):
        self.file_name   = chunk.file_name
        self.file_path   = chunk.file_path
        self.text        = chunk.text
        self.score       = score
        self.chunk_index = chunk.chunk_index

    def __repr__(self) -> str:
        return f"SearchResult(file={self.file_name!r}, score={self.score:.3f})"


class Docs:
    """
    Search PDF and TXT documents without a vector database.

    Two search modes:
      • "keyword"  – fast, no API calls required, uses word overlap scoring
      • "semantic" – uses OpenAI embeddings for true meaning-based search
                     (requires OPENAI_API_KEY, costs a tiny amount of tokens)

    Example:
        results = Docs.search("./research_papers", "transformer attention mechanism")

        for r in results:
            print(f"Source: {r.file_name}  (score: {r.score:.2f})")
            print(r.text)
            print("---")

        # Ask a question based on the found documents
        answer = Docs.ask("./my_notes", "What is the main argument?")
        print(answer)
    """

    # ── Read files ────────────────────────────────────────────

    @staticmethod
    def read_file(path: str | Path) -> str:
        """
        Read a TXT or PDF file and return its text content.

        Args:
            path: Path to a .txt or .pdf file.

        Returns:
            The extracted text as a string.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if p.suffix.lower() == ".pdf":
            if not _PDF_PKG:
                raise ImportError("Run:  pip install PyPDF2  (or pypdf)")
            reader = PyPDF2.PdfReader(str(p))
            return "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        # Plain text (also works for .md, .rst, etc.)
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                return p.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode file: {path}")

    @staticmethod
    def read_folder(folder: str | Path, extensions: list[str] | None = None) -> dict[str, str]:
        """
        Read all supported files in a folder (recursively).

        Args:
            folder:     Path to a directory.
            extensions: File extensions to include (default: ['.txt', '.pdf', '.md']).

        Returns:
            Dict mapping {file_path_string: content}.

        Example:
            texts = Docs.read_folder("./my_documents")
            for path, content in texts.items():
                print(path, len(content), "chars")
        """
        extensions = extensions or [".txt", ".pdf", ".md", ".rst"]
        folder     = Path(folder)
        texts: dict[str, str] = {}

        for ext in extensions:
            for fp in sorted(folder.rglob(f"*{ext}")):
                try:
                    texts[str(fp)] = Docs.read_file(fp)
                except Exception as e:
                    print(f"[ai_wrapper] Skipping {fp.name}: {e}")

        print(f"[ai_wrapper] Loaded {len(texts)} file(s) from '{folder}'")
        return texts

    # ── Chunking ──────────────────────────────────────────────

    @staticmethod
    def _chunk_text(text: str, file_name: str, file_path: str) -> list[_Chunk]:
        """Split text into overlapping chunks."""
        size    = Config.chunk_size
        overlap = Config.chunk_overlap
        chunks  = []
        i, idx  = 0, 0
        while i < len(text):
            end   = min(i + size, len(text))
            chunk = text[i:end].strip()
            if chunk:
                chunks.append(_Chunk(chunk, file_name, file_path, idx))
                idx += 1
            i += size - overlap
        return chunks

    # ── Keyword scoring ───────────────────────────────────────

    @staticmethod
    def _keyword_score(query: str, chunk_text: str) -> float:
        """Simple term-frequency based relevance score."""
        q_words  = set(re.findall(r"\w+", query.lower()))
        c_words  = re.findall(r"\w+", chunk_text.lower())
        if not q_words or not c_words:
            return 0.0
        matches  = sum(1 for w in c_words if w in q_words)
        return matches / (math.log(len(c_words) + 1) + 1)

    # ── Main search ───────────────────────────────────────────

    @staticmethod
    def search(
        folder_or_texts: str | Path | dict[str, str],
        query: str,
        *,
        top_k: int | None = None,
        mode: str = "keyword",
        extensions: list[str] | None = None,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """
        Search documents for text relevant to a query.

        Args:
            folder_or_texts: A folder path  OR  a dict {path: content} from read_folder().
            query:           What you're looking for.
            top_k:           How many results to return (default: Config.top_k = 5).
            mode:            "keyword" (fast, free) or "semantic" (better, uses API).
            extensions:      Which file types to include (for folder scanning).
            min_score:       Only return results above this score.

        Returns:
            List of SearchResult objects, sorted by relevance (best first).

        Example:
            results = Docs.search("./papers", "attention mechanism", top_k=3)
            for r in results:
                print(r.file_name, ":", r.text[:200])

            # Semantic search (requires OpenAI key)
            results = Docs.search("./papers", "how does attention work", mode="semantic")
        """
        k = top_k or Config.top_k

        # Load texts
        if isinstance(folder_or_texts, dict):
            texts = folder_or_texts
        else:
            texts = Docs.read_folder(folder_or_texts, extensions)

        if not texts:
            print("[ai_wrapper] No documents found.")
            return []

        # Build chunks
        all_chunks: list[_Chunk] = []
        for fp, content in texts.items():
            all_chunks.extend(Docs._chunk_text(content, Path(fp).name, fp))

        print(f"[ai_wrapper] Searching {len(all_chunks)} chunks across "
              f"{len(texts)} file(s) using '{mode}' mode...")

        # Score
        if mode == "semantic":
            # Use embeddings
            q_vec    = AI.embed(query)
            texts_   = [c.text for c in all_chunks]
            # Embed in batches of 100
            c_vecs: list[list[float]] = []
            for i in range(0, len(texts_), 100):
                batch = texts_[i:i + 100]
                vecs  = AI.embed(batch)
                c_vecs.extend(vecs if isinstance(vecs[0], list) else [vecs])
            scored = [
                (AI.cosine_similarity(q_vec, cv), chunk)
                for cv, chunk in zip(c_vecs, all_chunks)
            ]
        else:
            # Keyword
            scored = [
                (Docs._keyword_score(query, c.text), c)
                for c in all_chunks
            ]

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [
            SearchResult(chunk, score)
            for score, chunk in scored[:k]
            if score > min_score
        ]
        return results

    # ── Ask a question based on documents ─────────────────────

    @staticmethod
    def ask(
        folder_or_texts: str | Path | dict[str, str],
        question: str,
        *,
        top_k: int = 4,
        mode: str = "keyword",
        model: str | None = None,
        provider: str | None = None,
    ) -> Response:
        """
        Search documents and use an AI model to answer a question
        based on the retrieved context (simple RAG pipeline).

        Args:
            folder_or_texts: Folder path or pre-loaded texts dict.
            question:        The question to answer.
            top_k:           How many document chunks to include as context.
            mode:            "keyword" or "semantic".

        Returns:
            Response object with the model's answer.

        Example:
            answer = Docs.ask("./company_docs", "What is our refund policy?")
            print(answer)
        """
        chunks = Docs.search(folder_or_texts, question, top_k=top_k, mode=mode)

        if not chunks:
            return AI.chat(question, model=model, provider=provider)

        context_parts = []
        for i, r in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i}: {r.file_name}]\n{r.text}"
            )
        context = "\n\n".join(context_parts)

        return AI.chat(
            f"Answer the following question based ONLY on the provided context. "
            f"If the answer is not in the context, say so.\n\n"
            f"QUESTION: {question}\n\n"
            f"CONTEXT:\n{context}",
            system=(
                "You are a helpful assistant that answers questions based on "
                "provided document excerpts. Always cite the source (e.g. 'According "
                "to [Source 1]...') when possible."
            ),
            model=model,
            provider=provider,
        )

    @staticmethod
    def summarise_folder(
        folder: str | Path,
        *,
        style: str = "bullet",
        model: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Response]:
        """
        Summarise every document in a folder.

        Returns:
            Dict mapping {file_path: Response}.

        Example:
            summaries = Docs.summarise_folder("./reports")
            for path, summary in summaries.items():
                print(f"=== {Path(path).name} ===")
                print(summary)
        """
        texts = Docs.read_folder(folder)
        return {
            fp: AI.summarise(content, style=style, model=model, provider=provider)
            for fp, content in texts.items()
        }


# ══════════════════════════════════════════════════════════════
#  TEXT-TO-SPEECH  (OpenAI TTS)
# ══════════════════════════════════════════════════════════════

class TTS:
    """
    Text-to-Speech using OpenAI's gpt-4o-mini-tts model.

    Voices available:
        "verse"  – Expressive, versatile, great for narration
        "marin"  – Clear, warm, professional
        "cedar"  – Deep, authoritative, calm
        "alloy"  – Balanced, neutral
        "echo"   – Soft, warm
        "fable"  – Expressive, British accent
        "onyx"   – Deep, powerful
        "nova"   – Friendly, upbeat
        "shimmer"– Clear, optimistic
        "coral"  – Warm, reassuring

    Quick reference:
        TTS.speak("Hello!")                        → plays audio in terminal
        TTS.speak_to_file("Hello!", "out.mp3")     → saves to file
        TTS.list_voices()                          → prints voice table

    Example:
        TTS.speak("Today is a great day!", voice="verse")
        TTS.speak_to_file("Welcome!", "intro.mp3", voice="marin")
    """

    # ── Voice catalogue ───────────────────────────────────────

    #: Curated voices with descriptions (student-friendly)
    VOICES: dict[str, str] = {
        "verse":   "Expressive & versatile — great for storytelling and narration",
        "marin":   "Clear, warm, professional — good for tutorials and presentations",
        "cedar":   "Deep, authoritative, calm — ideal for formal content",
        "alloy":   "Balanced and neutral — all-purpose default",
        "echo":    "Soft and warm — suited for relaxed, friendly content",
        "fable":   "Expressive with a British accent — great for dramatic reads",
        "onyx":    "Deep and powerful — commands attention",
        "nova":    "Friendly and upbeat — perfect for cheerful messages",
        "shimmer": "Clear and optimistic — bright, positive tone",
        "coral":   "Warm and reassuring — great for instructional content",
    }

    #: Default TTS model
    DEFAULT_MODEL: str = "gpt-4o-mini-tts"

    #: Default voice
    DEFAULT_VOICE: str = "verse"

    # ── speak_to_file ─────────────────────────────────────────

    @staticmethod
    def speak_to_file(
        text: str,
        output_path: str | Path,
        *,
        voice: str = "verse",
        instructions: str | None = None,
        model: str = "gpt-4o-mini-tts",
        speed: float = 1.0,
    ) -> Path:
        """
        Convert text to speech and save it to an audio file.

        Args:
            text:          The text to convert to speech.
            output_path:   Where to save the audio file (e.g. "hello.mp3").
                           Supported formats: mp3, opus, aac, flac, wav, pcm.
            voice:         Voice name. Use TTS.list_voices() to see all options.
                           Suggested: "verse", "marin", "cedar".
            instructions:  Optional speaking style instructions, e.g.
                           "Speak slowly and clearly in a warm tone."
            model:         TTS model to use (default: "gpt-4o-mini-tts").
            speed:         Playback speed multiplier (0.25 – 4.0).

        Returns:
            Path object pointing to the saved audio file.

        Example:
            TTS.speak_to_file("Hello, world!", "greeting.mp3", voice="marin")
            TTS.speak_to_file(
                "Welcome to the tutorial.",
                "intro.mp3",
                voice="cedar",
                instructions="Speak in a calm, professional tone.",
            )
        """
        if not _OPENAI_PKG:
            raise ImportError("Run:  pip install openai")

        client = _make_client("openai")
        out    = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        kwargs: dict[str, Any] = dict(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
        )
        if instructions:
            kwargs["instructions"] = instructions

        with client.audio.speech.with_streaming_response.create(**kwargs) as resp:
            resp.stream_to_file(out)

        print(f"[ai_wrapper] TTS saved → {out}")
        return out

    # ── speak ─────────────────────────────────────────────────

    @staticmethod
    def speak(
        text: str,
        *,
        voice: str = "verse",
        instructions: str | None = None,
        model: str = "gpt-4o-mini-tts",
        speed: float = 1.0,
        player: str | None = None,
    ) -> Path:
        """
        Convert text to speech and play it immediately.

        The audio is saved to a temporary file and played with the
        system's default audio player (macOS: afplay, Linux: aplay/mpg123,
        Windows: start).

        Args:
            text:          The text to speak aloud.
            voice:         Voice name. Suggested: "verse", "marin", "cedar".
            instructions:  Optional style hint, e.g. "Speak cheerfully."
            model:         TTS model (default: "gpt-4o-mini-tts").
            speed:         Playback speed multiplier (0.25 – 4.0).
            player:        Override the audio player command (e.g. "mpg123").

        Returns:
            Path to the temporary audio file that was played.

        Example:
            TTS.speak("Hello! Great to meet you.", voice="verse")
            TTS.speak("Willkommen!", voice="marin", instructions="Speak German.")
            TTS.speak("Warning!", voice="cedar", speed=0.9)
        """
        import tempfile
        import subprocess
        import platform

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        TTS.speak_to_file(
            text,
            tmp_path,
            voice=voice,
            instructions=instructions,
            model=model,
            speed=speed,
        )

        # Determine default player
        if player is None:
            system = platform.system()
            if system == "Darwin":          # macOS
                player = "afplay"
            elif system == "Windows":
                player = "start"
            else:                           # Linux / other
                # Try common players in order
                for p in ("mpg123", "mpg321", "aplay", "ffplay"):
                    if subprocess.run(["which", p], capture_output=True).returncode == 0:
                        player = p
                        break
                else:
                    player = "aplay"        # fallback

        try:
            subprocess.run([player, str(tmp_path)], check=True)
        except FileNotFoundError:
            print(
                f"[ai_wrapper] Could not find player '{player}'. "
                f"Audio saved at: {tmp_path}\n"
                f"  Install a player or use TTS.speak_to_file() instead."
            )
        return tmp_path

    # ── list_voices ───────────────────────────────────────────

    @staticmethod
    def list_voices(print_table: bool = True) -> dict[str, str]:
        """
        Print a table of available voices with descriptions.

        Args:
            print_table: If True (default), print to console.

        Returns:
            Dict of {voice_name: description}.

        Example:
            TTS.list_voices()
        """
        if print_table:
            _print_banner("TTS Voices  (model: gpt-4o-mini-tts)")
            fmt = "{:<12}  {}"
            print(fmt.format("VOICE", "DESCRIPTION"))
            print("─" * 62)
            for name, desc in TTS.VOICES.items():
                star = " ★" if name in ("verse", "marin", "cedar") else ""
                print(fmt.format(name, desc + star))
            print("\n  ★ = recommended voices")
            print()
        return TTS.VOICES


# ══════════════════════════════════════════════════════════════
#  PROMPT BUILDER  (for power users)
# ══════════════════════════════════════════════════════════════

class Prompt:
    """
    Fluent builder for complex prompts.

    Example:
        result = (
            Prompt()
            .system("You are a senior data analyst.")
            .add("Analyse this sales data:")
            .add_data({"Q1": 120000, "Q2": 145000, "Q3": 98000})
            .instruction("Identify the weakest quarter and suggest reasons.")
            .format("Return JSON with keys: weakest_quarter, reasons (list)")
            .run()
        )
    """
    def __init__(self):
        self._system:  str = "You are a helpful assistant."
        self._parts:   list[str] = []
        self._model:   str | None = None
        self._provider: str | None = None
        self._temperature: float | None = None
        self._json_mode: bool = False

    def system(self, text: str)     -> "Prompt":
        """Set the system prompt."""
        self._system = text; return self

    def add(self, text: str)        -> "Prompt":
        """Add a paragraph to the prompt."""
        self._parts.append(text); return self

    def instruction(self, text: str) -> "Prompt":
        """Add an instruction line (prefixed with 'INSTRUCTION:')."""
        self._parts.append(f"INSTRUCTION: {text}"); return self

    def add_data(self, data: Any)   -> "Prompt":
        """Add structured data (dict/list) as formatted JSON."""
        self._parts.append(f"DATA:\n{json.dumps(data, indent=2)}"); return self

    def format(self, description: str) -> "Prompt":
        """Describe the expected output format."""
        self._parts.append(f"OUTPUT FORMAT: {description}"); return self

    def use_model(self, model: str, provider: str | None = None) -> "Prompt":
        """Specify which model/provider to use."""
        self._model = model; self._provider = provider; return self

    def json(self) -> "Prompt":
        """Force JSON output."""
        self._json_mode = True; return self

    def build(self) -> str:
        """Return the assembled prompt string without sending it."""
        return "\n\n".join(self._parts)

    def run(self) -> Response:
        """Send the prompt and return the Response."""
        return AI.chat(
            self.build(),
            system=self._system,
            model=self._model,
            provider=self._provider,
            temperature=self._temperature,
            json_mode=self._json_mode,
        )

    def run_structured(self, schema: dict) -> dict | list:
        """Send the prompt and return parsed JSON matching schema."""
        return AI.structured(
            self.build(),
            schema=schema,
            system=self._system,
            model=self._model,
            provider=self._provider,
        )


# ══════════════════════════════════════════════════════════════
#  QUICK HELPERS  (module-level shortcuts)
# ══════════════════════════════════════════════════════════════

def chat(prompt: str, **kwargs) -> Response:
    """Shortcut for AI.chat(). See AI.chat() for full docs."""
    return AI.chat(prompt, **kwargs)

def ask_doc(folder: str, question: str, **kwargs) -> Response:
    """Shortcut for Docs.ask(). See Docs.ask() for full docs."""
    return Docs.ask(folder, question, **kwargs)

def search_docs(folder: str, query: str, **kwargs) -> list[SearchResult]:
    """Shortcut for Docs.search(). See Docs.search() for full docs."""
    return Docs.search(folder, query, **kwargs)

def speak(text: str, **kwargs) -> Path:
    """Shortcut for TTS.speak(). See TTS.speak() for full docs."""
    return TTS.speak(text, **kwargs)

def speak_to_file(text: str, output_path: str | Path, **kwargs) -> Path:
    """Shortcut for TTS.speak_to_file(). See TTS.speak_to_file() for full docs."""
    return TTS.speak_to_file(text, output_path, **kwargs)


# ══════════════════════════════════════════════════════════════
#  SELF-TEST  (run this file directly to verify setup)
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "═" * 56)
    print("  AI Wrapper — Setup Test")
    print("═" * 56 + "\n")

    # Check imports
    print(f"  openai package : {'✓' if _OPENAI_PKG else '✗  (pip install openai)'}")
    print(f"  PyPDF2 package : {'✓' if _PDF_PKG   else '✗  (pip install PyPDF2)'}")
    print(f"  numpy  package : {'✓' if _NUMPY     else '✗  (pip install numpy)'}")
    print()

    # Check keys
    for prov in ["openai", "deepseek"]:
        key = _get_key(prov)
        status = "✓ key found" if key else "✗ no key set"
        print(f"  {prov:<12}: {status}")
    print()

    # Try a quick chat
    key = _get_key("openai") or _get_key("deepseek")
    if key and _OPENAI_PKG:
        prov = "openai" if _get_key("openai") else "deepseek"
        print(f"  Testing chat with {prov}…")
        try:
            r = AI.chat("Reply with exactly: 'AI wrapper works!'", provider=prov)
            print(f"  Response: {r.text.strip()}")
            print("\n  ✓ Everything looks good!\n")
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
    else:
        print("  Skipping live test (no API key or openai package missing).\n")

    get_models(print_table=True)
