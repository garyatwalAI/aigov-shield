"""Plugin and component registry for aigov-shield."""

from __future__ import annotations

from aigov_shield.core.exceptions import RegistryError


class ComponentRegistry:
    """Central registry for discovering and retrieving pluggable components.

    Components are organized by category (e.g., ``"guard"``, ``"exporter"``)
    and registered under a unique name within that category.
    """

    _registries: dict[str, dict[str, type]] = {}

    @classmethod
    def register(cls, category: str, name: str, component: type) -> None:
        """Register a component under a category and name.

        Args:
            category: The component category (e.g., "guard").
            name: A unique name for the component within the category.
            component: The class to register.
        """
        if category not in cls._registries:
            cls._registries[category] = {}
        cls._registries[category][name] = component

    @classmethod
    def get(cls, category: str, name: str) -> type:
        """Retrieve a registered component by category and name.

        Args:
            category: The component category.
            name: The component name.

        Returns:
            The registered component class.

        Raises:
            RegistryError: If the category or component name is not found.
        """
        if category not in cls._registries:
            raise RegistryError(f"Unknown component category: '{category}'")
        if name not in cls._registries[category]:
            available = ", ".join(cls._registries[category].keys())
            raise RegistryError(
                f"Component '{name}' not found in category '{category}'. Available: [{available}]"
            )
        return cls._registries[category][name]

    @classmethod
    def list_components(cls, category: str) -> list[str]:
        """List all component names registered under a category.

        Args:
            category: The component category.

        Returns:
            Sorted list of component names in the category.
        """
        if category not in cls._registries:
            return []
        return sorted(cls._registries[category].keys())

    @classmethod
    def clear(cls) -> None:
        """Remove all registered components from every category."""
        cls._registries.clear()
