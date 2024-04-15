import os
import json
from luminapie.game_data import GameData, ParsedFileName
from luminapie.excel import ExcelListFile


def main():
    f = open(os.path.join(os.getenv('APPDATA'), 'XIVLauncher', 'launcherConfigV3.json'), 'r')
    config = json.load(f)
    f.close()
    # game_data = GameData(os.path.join(config['GamePath'], 'game'))
    game_data = GameData("C:\\Users\\magnu\\Downloads\\ffxiv-dawntrail-bench\\game")
    exd_map = ExcelListFile(game_data.get_file(ParsedFileName('exd/root.exl'))).dict
    for key in exd_map:
        print(key, exd_map[key])

main()
