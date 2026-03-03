import importlib
import inspect
import pkgutil

from scanner.base import BaseCheck


def discover_checks() -> list[BaseCheck]:
    checks: list[BaseCheck] = []
    package = importlib.import_module("scanner.checks")
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"scanner.checks.{module_name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseCheck) and obj is not BaseCheck:
                checks.append(obj())
    return checks
