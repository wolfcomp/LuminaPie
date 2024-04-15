def get_definition(schema: dict[str, str]) -> dict[str, str]:
    if 'type' in schema:
        if schema['type'] == 'array':
            return RepeatDefinition(schema)
    return Definition(schema)


class Definition:
    def __init__(self, obj: dict[str, str]) -> None:
        self.name = obj['name']

    def __repr__(self) -> str:
        return self.name


class RepeatDefinition(Definition):
    def __init__(self, obj: dict[str, str]) -> None:
        super().__init__(obj)
        self.obj = obj
        self.count = obj['count']
        self.inner_defs = []
        self.process_inner()

    def process_inner(self):
        if 'fields' in self.obj:
            for field in self.obj['fields']:
                if 'name' in field:
                    self.inner_defs.append(get_definition(field))
                else:
                    self.inner_defs.append(Definition({'name': ""}))
        if self.inner_defs == []:
            self.inner_defs.append(Definition({'name': ""}))

    def flatten(self, extern: str) -> list[Definition]:
        defs = []
        extern = extern + self.name
        for i in range(0, int(self.count)):
            for inner in self.inner_defs:
                if isinstance(inner, RepeatDefinition):
                    defs.extend(inner.flatten(extern + i.__str__()))
                else:
                    defs.append(Definition({'name': extern + i.__str__() + inner.name}))
        return defs

    def __repr__(self) -> str:
        return f'{self.flatten("")}'
