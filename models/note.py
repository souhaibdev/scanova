from dataclasses import dataclass
from typing import Optional


@dataclass
class Note:
    title: str
    date: str            # YYYY-MM-DD HH:MM
    content: str
    image_path: Optional[str] = None

    def to_row(self) -> list:
        return [
            self.title,
            self.date,
            self.content,
            self.image_path or "",
        ]

    @staticmethod
    def columns() -> list:
        return ["Title", "Date", "Content", "Image Path"]
