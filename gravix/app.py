from pathlib import Path

from loguru import logger as log
from openai import OpenAI

from gravix.config import GravixConfig
from gravix.storage import init_ladybug, init_raw_dir, init_sqlite, init_work_dir

_REQUIRED_SUBDIRS = ["graph.lbug", "abstract.db", "raw"]

_SUMMARY_SYSTEM_PROMPT = (
    "你是一个知识库摘要助手。用户会给你一段关于知识库的描述，"
    "请你生成一个简短的摘要，提纲挈领地说明这个知识库是做什么、有哪些主题。"
    "摘要应当尽量简短、概要，不超过200字。只输出摘要内容，不要输出其他任何文字。"
)


class Gravix:
    def __init__(self, config: GravixConfig) -> None:
        self.config = config
        self._work_dir: Path | None = None

    @property
    def work_dir(self) -> Path:
        if self._work_dir is None:
            p = Path(self.config.work_dir)
            if not p.is_absolute():
                p = Path.cwd() / p
            self._work_dir = p
        return self._work_dir

    def init(self) -> None:
        work_dir = init_work_dir(self.config.work_dir)
        init_ladybug(work_dir)
        init_sqlite(work_dir)
        init_raw_dir(work_dir)
        log.info("Gravix workspace initialized at: {}", work_dir)

    def check_work_dir(self) -> bool:
        if not self.work_dir.is_dir():
            log.error("Work directory does not exist: {}", self.work_dir)
            return False
        for sub in _REQUIRED_SUBDIRS:
            sub_path = self.work_dir / sub
            if not sub_path.exists():
                log.error("Required path missing in work directory: {}", sub_path)
                return False
        return True

    def set_topic(self, text: str | None = None, file: str | None = None) -> None:
        if not self.check_work_dir():
            log.error("Please run 'gravix init' first.")
            raise SystemExit(1)

        input_text = self._resolve_input(text, file)
        if not input_text.strip():
            log.error("No input text provided for set-topic.")
            raise SystemExit(1)

        summary = self._summarize(input_text)
        topic_path = self.work_dir / "topic.md"
        topic_path.write_text(summary, encoding="utf-8")
        log.info("Topic written to: {}", topic_path)

    def _resolve_input(self, text: str | None, file: str | None) -> str:
        if file is not None:
            p = Path(file)
            if not p.is_absolute():
                p = Path.cwd() / p
            if not p.is_file():
                log.error("File not found: {}", p)
                raise SystemExit(1)
            return p.read_text(encoding="utf-8")
        if text is not None:
            return text
        log.error("Either text or -file must be provided for set-topic.")
        raise SystemExit(1)

    def _summarize(self, text: str) -> str:
        client = OpenAI(
            base_url=self.config.full_base_url,
            api_key=self.config.full_key,
        )
        response = client.chat.completions.create(
            model=self.config.full_model,
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content or ""
