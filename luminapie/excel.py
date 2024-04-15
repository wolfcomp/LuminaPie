from luminapie.enums import ExcelColumnDataType
from luminapie.definitions import Definition


class ExcelListFile:
    def __init__(self, data: list[bytes]):
        self.data = b''.join(data).split('\r\n'.encode('utf-8'))
        self.parse()

    def parse(self):
        self.header = self.data[0].decode('utf-8').split(',')
        self.version = int(self.header[1])
        self.data = self.data[1:]
        self.dict: dict[int, str] = {}
        for line in [x.decode('utf-8') for x in self.data]:
            if line == '':
                continue
            linearr = line.split(',')
            if linearr[1] == '-1':
                continue
            self.dict[int(linearr[1])] = linearr[0]

    def __repr__(self):
        return f'''ExcelListFile: {self.header}, {self.dict}'''


class ExcelHeader:
    def __init__(self, data: bytes):
        self.data = data
        self.parse()

    def parse(self):
        self.magic = self.data[0:4]
        self.version = int.from_bytes(self.data[4:6], 'big')
        self.data_offset = int.from_bytes(self.data[6:8], 'big')
        self.column_count = int.from_bytes(self.data[8:10], 'big')
        self.page_count = int.from_bytes(self.data[10:12], 'big')
        self.language_count = int.from_bytes(self.data[12:14], 'big')
        self.unknown1 = int.from_bytes(self.data[14:16], 'big')
        self.unknown2 = self.data[17]
        self.variant = self.data[18]
        self.unknown3 = int.from_bytes(self.data[19:20], 'big')
        self.row_count = int.from_bytes(self.data[20:24], 'big')
        self.unknown4 = [int.from_bytes(self.data[24:28], 'big'), int.from_bytes(self.data[28:32], 'big')]

    def __repr__(self):
        return f'''Header: {self.magic}, version: {self.version}, data_offset: {self.data_offset}, column_count: {self.column_count}, page_count: {self.page_count}, language_count: {self.language_count}, unknown1: {self.unknown1}, unknown2: {self.unknown2}, variant: {self.variant}, unknown3: {self.unknown3}, row_count: {self.row_count}, unknown4: {self.unknown4}'''


class ExcelColumnDefinition:
    def __init__(self, data: bytes):
        self.data = data
        self.parse()

    def parse(self):
        self.type = ExcelColumnDataType(int.from_bytes(self.data[0:2], 'big'))
        self.offset = int.from_bytes(self.data[2:4], 'big')

    def __lt__(self, other: 'ExcelColumnDefinition') -> bool:
        return self.offset <= other.offset

    def __repr__(self) -> str:
        return f'''Column: {self.type.name}, offset: {self.offset:x}'''


class ExcelDataPagination:
    def __init__(self, data: bytes):
        self.data = data
        self.parse()

    def parse(self):
        self.start_id = int.from_bytes(self.data[0:2], 'big')
        self.row_count = int.from_bytes(self.data[2:4], 'big')

    def __repr__(self):
        return f'''Pagination: {self.start_id:x}, count: {self.row_count}'''


class ExcelHeaderFile:
    def __init__(self, data: list[bytes]):
        self.data = data[0]
        self.column_definitions: list[ExcelColumnDefinition] = []
        self.pagination: list[ExcelDataPagination] = []
        self.languages: list[int] = []
        self.header: ExcelHeader = None
        self.parse()

    def parse(self):
        self.header = ExcelHeader(self.data[0:32])
        if self.header.magic != b'EXHF':
            raise Exception('Invalid EXHF header')
        self.column_definitions: list[ExcelColumnDefinition] = []
        for i in range(self.header.column_count):
            self.column_definitions.append(ExcelColumnDefinition(self.data[32 + (i * 4) : 32 + ((i + 1) * 4)]))
        self.column_definitions = sorted(self.column_definitions)
        self.pagination: list[ExcelDataPagination] = []
        for i in range(self.header.page_count):
            self.pagination.append(
                ExcelDataPagination(
                    self.data[
                        32
                        + (self.header.column_count * 4)
                        + (i * 4) : 32
                        + (self.header.column_count * 4)
                        + ((i + 1) * 4)
                    ]
                )
            )
        self.languages: list[int] = []
        for i in range(self.header.language_count):
            self.languages.append(self.data[32 + (self.header.column_count * 4) + (self.header.page_count * 4) + i])

    def map_names(self, names: list[Definition]) -> tuple[dict[int, tuple[str, str]], int]:
        mapped: dict[int, tuple[str, str]] = {}
        largest_offset_index: int = 0
        for i in range(self.header.column_count):
            if self.column_definitions[i].offset > self.column_definitions[largest_offset_index].offset:
                largest_offset_index = i

        size = self.column_definitions[largest_offset_index].offset + column_data_type_to_size(
            self.column_definitions[largest_offset_index].type
        )

        for i in range(self.header.column_count):
            if self.column_definitions[i].offset in mapped and mapped[self.column_definitions[i].offset] is not None:
                [_, name] = mapped[self.column_definitions[i].offset]
                if name.split('_')[0] == 'Unknown':
                    continue
                if column_data_type_to_c_type(self.column_definitions[i].type) != 'unsigned __int8':
                    continue
                else:
                    mapped[self.column_definitions[i].offset] = (
                        column_data_type_to_c_type(self.column_definitions[i].type),
                        f'{name}_{names[i].name}',
                    )
            else:
                mapped[self.column_definitions[i].offset] = (
                    column_data_type_to_c_type(self.column_definitions[i].type),
                    names[i].name,
                )
        mapped = dict(sorted(mapped.items()))
        return [mapped, size]


def column_data_type_to_c_type(column_data_type: ExcelColumnDataType) -> str:
    if column_data_type == ExcelColumnDataType.Bool:
        return 'bool'
    elif column_data_type == ExcelColumnDataType.Int8:
        return '__int8'
    elif column_data_type == ExcelColumnDataType.UInt8:
        return 'unsigned __int8'
    elif column_data_type == ExcelColumnDataType.Int16:
        return '__int16'
    elif column_data_type == ExcelColumnDataType.UInt16:
        return 'unsigned __int16'
    elif column_data_type == ExcelColumnDataType.Int32:
        return '__int32'
    elif column_data_type == ExcelColumnDataType.UInt32:
        return 'unsigned __int32'
    elif column_data_type == ExcelColumnDataType.Float32:
        return 'float'
    elif column_data_type == ExcelColumnDataType.Int64:
        return '__int64'
    elif column_data_type == ExcelColumnDataType.UInt64:
        return 'unsigned __int64'
    elif (
        column_data_type == ExcelColumnDataType.PackedBool0
        or column_data_type == ExcelColumnDataType.PackedBool1
        or column_data_type == ExcelColumnDataType.PackedBool2
        or column_data_type == ExcelColumnDataType.PackedBool3
        or column_data_type == ExcelColumnDataType.PackedBool4
        or column_data_type == ExcelColumnDataType.PackedBool5
        or column_data_type == ExcelColumnDataType.PackedBool6
        or column_data_type == ExcelColumnDataType.PackedBool7
    ):
        return 'unsigned __int8'
    elif column_data_type == ExcelColumnDataType.String:
        return '__unsigned __int32'


def column_data_type_to_size(column_data_type: ExcelColumnDataType) -> int:
    if (
        column_data_type == ExcelColumnDataType.Bool
        or column_data_type == ExcelColumnDataType.Int8
        or column_data_type == ExcelColumnDataType.UInt8
        or column_data_type == ExcelColumnDataType.PackedBool0
        or column_data_type == ExcelColumnDataType.PackedBool1
        or column_data_type == ExcelColumnDataType.PackedBool2
        or column_data_type == ExcelColumnDataType.PackedBool3
        or column_data_type == ExcelColumnDataType.PackedBool4
        or column_data_type == ExcelColumnDataType.PackedBool5
        or column_data_type == ExcelColumnDataType.PackedBool6
        or column_data_type == ExcelColumnDataType.PackedBool7
    ):
        return 1
    elif column_data_type == ExcelColumnDataType.Int16 or column_data_type == ExcelColumnDataType.UInt16:
        return 2
    elif (
        column_data_type == ExcelColumnDataType.Int32
        or column_data_type == ExcelColumnDataType.UInt32
        or column_data_type == ExcelColumnDataType.Float32
        or column_data_type == ExcelColumnDataType.String
    ):
        return 4
    elif column_data_type == ExcelColumnDataType.Int64 or column_data_type == ExcelColumnDataType.UInt64:
        return 8
