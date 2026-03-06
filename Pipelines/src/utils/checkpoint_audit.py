from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class CheckpointAudit_CVMFormularioInformacoesTrimestrais:
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir

    def _extract_code(self, data: dict[str, Any], file: Path) -> str:
        ticker = str(data.get("ticker", "")).strip().upper()
        if ticker:
            return ticker.replace(".SA", "")

        item_name = str(data.get("item_name", "")).strip().upper()
        if item_name and "_" in item_name:
            return item_name.split("_")[-1]

        return file.stem.split("_")[-1].upper()

    def audit(self) -> dict[str, Any]:
        """Lê checkpoints e retorna códigos únicos com falha + métricas simples."""
        results = {
            "total_files": 0,
            "failure_count": 0,
            "codes": [],
        }
        unique_codes: set[str] = set()

        if not self.checkpoint_dir.exists():
            return results

        for file in self.checkpoint_dir.rglob("*.json"):
            results["total_files"] += 1

            try:
                with open(file, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                continue

            status = str(data.get("status", "")).lower().strip()
            if status not in {"failed", "failure", "error"}:
                continue

            results["failure_count"] += 1
            unique_codes.add(self._extract_code(data, file))

        results["codes"] = sorted(unique_codes)

        return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resumo simples de códigos com erro em checkpoints.")
    parser.add_argument(
        "--root",
        default="Pipelines/state/checkpoints",
        help="Diretório raiz dos checkpoints.",
    )
    parser.add_argument(
        "--pipeline",
        default=None,
        help="Filtra por pipeline (subpasta dentro de checkpoints).",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    checkpoint_dir = Path(args.root)
    if args.pipeline:
        checkpoint_dir = checkpoint_dir / args.pipeline

    auditor = CheckpointAudit_CVMFormularioInformacoesTrimestrais(checkpoint_dir)
    results = auditor.audit()

    print("Códigos (sem repetição):")
    if results["codes"]:
        print(", ".join(results["codes"]))
    else:
        print("Nenhum")

    print(f"Quantidade de erros: {results['failure_count']}")
    print(f"Quantidade total de arquivos: {results['total_files']}")

if __name__ == "__main__":
    main()
