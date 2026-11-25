"""Run the test functions without pytest, for machines where it is not installed.

The real command is ``python -m pytest -q``. This runner only exists so the suite can be
checked on a bare Python: it understands the four things the tests use — ``pytest.fixture``,
``tmp_path``, ``monkeypatch`` and plain ``assert``.
"""

from __future__ import annotations

import importlib
import inspect
import os
import sys
import tempfile
import traceback
import types
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class MonkeyPatch:
    def __init__(self):
        self._undo = []

    def setenv(self, key, value):
        old = os.environ.get(key)
        os.environ[key] = str(value)
        self._undo.append(lambda: os.environ.pop(key, None) if old is None else os.environ.__setitem__(key, old))

    def setattr(self, target, name, value=None, _sentinel=object()):
        if value is None:
            # pytest's two-argument form: setattr("pkg.mod.attr", new_value)
            module_path, _, attr = target.rpartition(".")
            obj = importlib.import_module(module_path)
            old = getattr(obj, attr)
            setattr(obj, attr, name)
            self._undo.append(lambda: setattr(obj, attr, old))
            return
        module_path, _, attr = target.rpartition(".")
        obj = importlib.import_module(module_path) if module_path else None
        old = getattr(obj, attr)
        setattr(obj, attr, value)
        self._undo.append(lambda: setattr(obj, attr, old))

    def undo(self):
        for fn in reversed(self._undo):
            fn()
        self._undo.clear()


def _install_fake_pytest():
    mod = types.ModuleType("pytest")

    def fixture(fn=None, **_kw):
        def mark(f):
            f.__is_fixture__ = True
            return f
        return mark(fn) if callable(fn) else mark

    mod.fixture = fixture
    sys.modules["pytest"] = mod
    return mod


def _fixtures(module):
    out = {}
    for name, obj in vars(module).items():
        if callable(obj) and getattr(obj, "__is_fixture__", False):
            out[name] = obj
    return out


def run_all(pattern: str = "test_*.py") -> int:
    _install_fake_pytest()
    passed = failed = skipped = 0
    failures = []
    tests_dir = os.path.join(ROOT, "tests")
    for name in sorted(os.listdir(tests_dir)):
        if not (name.startswith("test_") and name.endswith(".py")):
            continue
        module = importlib.import_module(f"tests.{name[:-3]}")
        fixtures = _fixtures(module)
        for fn_name, fn in inspect.getmembers(module, inspect.isfunction):
            if not fn_name.startswith("test_"):
                continue
            params = list(inspect.signature(fn).parameters)
            need = set(params)
            if not need <= set(fixtures) | {"tmp_path", "monkeypatch"}:
                skipped += 1
                continue
            tmp = None
            mp = None
            kwargs = {}
            try:
                tmp = tempfile.TemporaryDirectory()
                kwargs["tmp_path"] = Path(tmp.name)
                mp = MonkeyPatch()
                kwargs["monkeypatch"] = mp
                pending = [p for p in params if p not in ("tmp_path", "monkeypatch")]
                while pending:
                    progressed = False
                    for p in list(pending):
                        sub = list(inspect.signature(fixtures[p]).parameters)
                        if all(x in kwargs for x in sub):
                            kwargs[p] = fixtures[p](**{x: kwargs[x] for x in sub})
                            pending.remove(p)
                            progressed = True
                    if not progressed:
                        raise RuntimeError(f"cannot resolve fixtures {pending}")
                fn(**{k: v for k, v in kwargs.items() if k in params})
                passed += 1
                print(f"ok      {name}::{fn_name}")
            except Exception as e:                      # noqa: BLE001
                failed += 1
                failures.append((name, fn_name, e, traceback.format_exc()))
                print(f"FAILED  {name}::{fn_name}: {e}")
            finally:
                if mp:
                    mp.undo()
                if tmp:
                    tmp.cleanup()
    print()
    for name, fn_name, e, tb in failures:
        print("=" * 70)
        print(f"{name}::{fn_name}")
        print(tb)
    print(f"{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(run_all())
