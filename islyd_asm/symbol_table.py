import attr
from collections import OrderedDict


class SymbolRedefinedError(Exception):
    pass


class UndefinedSymbol(Exception):
    pass


@attr.s
class SymbolTable:
    # identifier -> Symbol
    symbols = attr.ib(factory=OrderedDict)
    # set of symbol identifiers
    dependencies = attr.ib(factory=set)

    def add(self, symbol):
        identifier = symbol.identifier

        if identifier in self.symbols:
            raise SymbolRedefinedError(identifier)
        else:
            self.symbols[identifier] = symbol
            try:
                self.dependencies.remove(identifier)
            except KeyError:
                pass

    def add_dependency(self, identifier):
        identifier = identifier.strip()
        if identifier not in self.symbols:
            self.dependencies.add(identifier)

    def get(self, identifier):
        identifier = identifier.strip()
        try:
            return self.symbols[identifier]
        except KeyError:
            raise UndefinedSymbol(identifier)
