"""Compatibilidade do antigo KnowledgeRegistry.

O nome público oficial agora é M.drives (Memory + Drives/Pendrives). Este módulo é
mantido temporariamente para extensões antigas não quebrarem; código novo deve
importar ``MDriveRegistry`` de ``core.mdrives``.
"""
from core.mdrives import MDriveRegistry


class KnowledgeRegistry(MDriveRegistry):
    """Alias compatível; use MDriveRegistry em código novo."""


__all__ = ["KnowledgeRegistry", "MDriveRegistry"]
