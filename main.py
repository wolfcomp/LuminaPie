import os
import json
from luminapie.game_data import GameData, ParsedFileName
from luminapie.excel import ExcelListFile, ExcelHeaderFile
from luminapie.exdschema import get_definitions


def main():
    f = open(os.path.join(os.getenv('APPDATA'), 'XIVLauncher', 'launcherConfigV3.json'), 'r')
    config = json.load(f)
    f.close()
    game_data = GameData(os.path.join(config['GamePath'], 'game'))
    exd_map = ExcelListFile(game_data.get_file(ParsedFileName('exd/root.exl'))).dict

    exd_headers: dict[int, tuple[dict[int, tuple[str, str]], int]] = {}

    for key in exd_map:
        # print(f'Parsing schema for {exd_map[key]}')
        exd_headers[key] = ExcelHeaderFile(game_data.get_file(ParsedFileName(f'exd/{exd_map[key]}.exh'))).map_names(
            game_data.get_exd_schema(exd_map[key])
        )

    # print(exd_headers)


main()
