import importlib
import inspect
import pkgutil

from scanner.azure_base import AzureCheck


def discover_azure_checks() -> list[AzureCheck]:
    checks: list[AzureCheck] = []
    package = importlib.import_module("scanner.azure_checks")
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"scanner.azure_checks.{module_name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, AzureCheck) and obj is not AzureCheck:
                checks.append(obj())
    return checks
