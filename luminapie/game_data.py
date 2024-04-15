from luminapie.sqpack import SqPack, SqPackIndexHashTable
from luminapie.file_handlers import get_game_data_folders, get_sqpack_index
from luminapie.se_crc import Crc32
import os

crc = Crc32()


class SemanticVersion:
    """Represents a semantic version string that can compare versions"""

    year: int
    month: int
    date: int
    patch: int
    build: int

    def __init__(self, year: int, month: int, date: int, patch: int, build: int = 0) -> None:
        self.year = year
        self.month = month
        self.date = date
        self.patch = patch
        self.build = build

    def __lt__(self, other: 'SemanticVersion') -> bool:
        return (
            self.year < other.year
            or self.month < other.month
            or self.date < other.date
            or self.patch < other.patch
            or self.build < other.build
        )

    def __repr__(self) -> str:
        return f'{self.year}.{self.month.__str__().rjust(2, "0")}.{self.date.__str__().rjust(2, "0")}.{self.patch.__str__().rjust(4, "0")}.{self.build.__str__().rjust(4, "0")}'

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, SemanticVersion):
            return False
        return (
            self.year == __value.year
            and self.month == __value.month
            and self.date == __value.date
            and self.patch == __value.patch
            and self.build == __value.build
        )

    def __hash__(self) -> int:
        return hash(repr(self))


class Repository:
    def __init__(self, name: str, root: str):
        self.root = root
        self.name = name
        self.sqpacks: list[SqPack] = []
        self.index: dict[int, tuple[SqPackIndexHashTable, SqPack]] = {}
        self.expansion_id = 0
        self.get_expansion_id()

    def get_expansion_id(self):
        if self.name.startswith('ex'):
            self.expansion_id = int(self.name.removeprefix('ex'))

    def parse_version(self):
        versionPath = ""
        if self.name == 'ffxiv':
            versionPath = os.path.join(self.root, 'ffxivgame.ver')
        else:
            versionPath = os.path.join(self.root, 'sqpack', self.name, self.name + '.ver')
        if os.path.exists(versionPath):
            with open(versionPath, 'r') as f:
                self.version = SemanticVersion(*(int(v) for v in f.read().strip().split('.')))
        else:
            self.version = SemanticVersion(0, 0, 0, 0)

    def setup_indexes(self):
        for file in get_sqpack_index(self.root, self.name):
            self.sqpacks.append(SqPack(self.root, file))

        for sqpack in self.sqpacks:
            sqpack.discover_data_files()
            for indexes in sqpack.hash_table:
                self.index[indexes.hash] = [indexes, sqpack]

    def get_index(self, hash: int):
        return self.index[hash]

    def get_file(self, hash: int):
        index, sqpack = self.get_index(hash)
        id = index.data_file_id()
        offset = index.data_file_offset()
        return SqPack(self.root, sqpack.data_files[id]).read_file(offset)

    def __repr__(self):
        return f'''Repository: {self.name} ({self.version}) - {self.expansion_id}'''


class GameData:
    def __init__(self, root: str):
        self.root = root
        self.repositories: dict[int, Repository] = {}
        self.setup()

    def get_repo_index(self, folder: str):
        if folder == 'ffxiv':
            return 0
        else:
            return int(folder.removeprefix('ex'))

    def setup(self):
        for folder in get_game_data_folders(self.root):
            self.repositories[self.get_repo_index(folder)] = Repository(folder, self.root)

        for folder in self.repositories:
            repo = self.repositories[folder]
            repo.parse_version()
            repo.setup_indexes()

    def get_file(self, file: 'ParsedFileName'):
        return self.repositories[self.get_repo_index(file.repo)].get_file(file.index)

    def __repr__(self):
        return f'''Repositories: {self.repositories}'''


class ParsedFileName:
    def __init__(self, path: str):
        self.path = path.lower().strip()
        parts = self.path.split('/')
        self.category = parts[0]
        self.index = crc.calc_index(self.path)
        self.index2 = crc.calc_index2(self.path)
        self.repo = parts[1]
        if self.repo[0] != 'e' or self.repo[1] != 'x' or not self.repo[2].isdigit():
            self.repo = 'ffxiv'

    def __repr__(self):
        return f'''ParsedFileName: {self.path}, category: {self.category}, index: {self.index:X}, index2: {self.index2:X}, repo: {self.repo}'''
