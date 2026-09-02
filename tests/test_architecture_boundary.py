from pathlib import Path
from ncaaf_aita.cli import main


def test_no_embedded_trading_agent_package():
    assert not Path("src/ncaaf_aita/trading_agent").exists()


def test_no_postgame_audit_package():
    assert not Path("src/ncaaf_aita/audit").exists()


def test_boundary_doc_present():
    text=Path("docs/ARCHITECTURE_LOCK.md").read_text(encoding="utf-8")
    assert "external NCAAF Trading Agent" in text
