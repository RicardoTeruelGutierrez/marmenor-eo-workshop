"""Tiny helper to assemble .ipynb files cell-by-cell."""
import json
from pathlib import Path


class Notebook:
    def __init__(self, kernel="python3", lang="python"):
        self.cells = []
        self.meta = {
            "kernelspec": {
                "display_name": "Python 3",
                "language": lang,
                "name": kernel,
            },
            "language_info": {"name": lang},
        }

    def md(self, text):
        self.cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": text.splitlines(keepends=True),
        })
        return self

    def code(self, text):
        self.cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": text.splitlines(keepends=True),
        })
        return self

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "cells": self.cells,
            "metadata": self.meta,
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        path.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
