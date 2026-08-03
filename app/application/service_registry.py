from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


class ServiceRegistry:
    def __init__(self) -> None:
        self._factories: dict[type[object], Callable[[], object]] = {}
        self._singleton_factories: dict[type[object], Callable[[], object]] = {}
        self._singletons: dict[type[object], object] = {}

    def register(self, service_type: type[T], factory: Callable[[], T]) -> None:
        self._factories[service_type] = factory

    def register_singleton(self, service_type: type[T], factory: Callable[[], T]) -> None:
        self._singleton_factories[service_type] = factory

    def register_instance(self, service_type: type[T], instance: T) -> None:
        self._singletons[service_type] = instance

    def resolve(self, service_type: type[T]) -> T:
        instance = self._singletons.get(service_type)
        if instance is not None:
            return instance  # type: ignore[return-value]
        singleton_factory = self._singleton_factories.get(service_type)
        if singleton_factory is not None:
            created = singleton_factory()
            self._singletons[service_type] = created
            return created  # type: ignore[return-value]
        factory = self._factories.get(service_type)
        if factory is None:
            raise KeyError(f"Service {service_type.__name__} is not registered")
        return factory()  # type: ignore[return-value]
