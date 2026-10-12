"""Plugins internos: extensión explícita y revisable, nunca descarga de código."""


class PluginManager:
    def __init__(self, registry):
        self.registry = registry
        self.loaded = []

    def load_builtin(self, name, installer, core):
        if name not in self.loaded:
            installer(core)
            self.loaded.append(name)
