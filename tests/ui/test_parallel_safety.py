"""Self-checks for the rules that make parallel (xdist) runs safe. No browser or stack needed."""
import pytest

from tests.ui.support.naming import Namer

pytestmark = pytest.mark.framework


def test_names_contain_the_xdist_worker_id(monkeypatch):
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw3")

    namer = Namer()

    assert "gw3" in namer.prefix
    assert namer.username().startswith(namer.prefix)
    assert namer.email().startswith(namer.prefix)
    assert namer.tag().startswith(namer.prefix)


def test_two_workers_never_produce_the_same_name(monkeypatch):
    names = set()
    for worker in ("gw0", "gw1", "gw2", "gw3"):
        monkeypatch.setenv("PYTEST_XDIST_WORKER", worker)
        namer = Namer()
        names |= {namer.username() for _ in range(25)}
    assert len(names) == 100


def test_one_workers_prefix_never_matches_anothers_names(monkeypatch):
    """The end-of-session sweep deletes by prefix, so a prefix must not cover foreign names."""
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw1")
    first = Namer()
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw10")
    second = Namer()

    assert not second.username().startswith(first.prefix)
    assert not first.username().startswith(second.prefix)


def test_sequential_runs_use_a_plain_worker_label(monkeypatch):
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)

    assert Namer().prefix.endswith("m_")
