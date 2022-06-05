import logging
import re
from utils import json_config
from conf import settings
from bangumi_parser.episode import Episode

logger = logging.getLogger(__name__)


class ParserLV2:
    def __init__(self) -> None:
        self.info = json_config.load(settings.rule_path)

    def pre_process(self, raw_name):
        pro_name = raw_name.replace("【", "[").replace("】", "]")
        return pro_name

    def get_group(self, name):
        group = re.split(r"[\[\]]", name)[1]
        return group

    def second_process(self, raw_name):
        if re.search(r"新番|月?番", raw_name):
            pro_name = re.sub(".*新番.", "", raw_name)
        else:
            pro_name = re.sub(r"^[^]】]*[]】]", "", raw_name).strip()
        return pro_name

    def season_process(self, name_season):
        season_rule = r"S\d{1,2}|Season \d{1,2}|[第].[季期]"
        season_map = {
            "一": 1,
            "二": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "十": 10,
        }
        name_season = re.sub(r"[\[\]]", " ", name_season)
        seasons = re.findall(season_rule, name_season)
        if not seasons:
            name = name_season
            season_number = 1
            if settings.season_one_tag:
                season_raw = "S01"
            else:
                season_raw = ""
        else:
            name = re.sub(season_rule, "", name_season)
            for season in seasons:
                season_raw = season
                if re.search(r"S|Season", season) is not None:
                    season_number = int(re.sub(r"S|Season", "", season))
                    break
                elif re.search(r"[第 ].*[季期]", season) is not None:
                    season_pro = re.sub(r"[第季期 ]", "", season)
                    try:
                        season_number = int(season_pro)
                    except ValueError:
                        season_number = season_map[season_pro]
                        break
        return name, season_number, season_raw

    def name_process(self, name):
        name = name.strip()
        split = re.split("/|  |-  ", name.replace("（仅限港澳台地区）", ""))
        while "" in split:
            split.remove("")
        if len(split) == 1:
            if re.search("_{1}", name) is not None:
                split = re.split("_", name)
            elif re.search(" - {1}", name) is not None:
                split = re.split("-", name)
        if len(split) == 1:
            match_obj = re.match(r"([^\x00-\xff]{1,})(\s)([\x00-\xff]{4,})", name)
            if match_obj is not None:
                return match_obj.group(3)
        for name in split:
            compare = 0
            l = re.findall("[aA-zZ]{1}", name).__len__()
            if l > compare:
                compare = l
        for name in split:
            if re.findall("[aA-zZ]{1}", name).__len__() == compare:
                return name

    def find_tags(self, other):
        elements = re.sub(r"[\[\]()（）]", " ", other).split(" ")
        while "" in elements:
            elements.remove("")
        # find CHT
        sub = None
        dpi = None
        source = None
        for element in elements:
            if re.search(r"[简繁日字幕]|CH|BIG5|GB", element) is not None:
                sub = element.replace("_MP4","")
            elif re.search(r"1080|720|2160|4K", element) is not None:
                dpi = element
            elif re.search(r"B-Global|[Bb]aha|[Bb]ilibili|AT-X|Web", element) is not None:
                source = element
        return sub, dpi, source

    def process(self, raw_name):
        raw_name = self.pre_process(raw_name)
        group = self.get_group(raw_name)
        match_obj = re.match(
            r"(.*|\[.*])( -? \d{1,3} |\[\d{1,3}]|\[\d{1,3}.?[vV]\d{1}]|[第第]\d{1,3}[话話集集]|\[\d{1,3}.?END])(.*)",
            raw_name,
        )
        name_season = self.second_process(match_obj.group(1))
        name, season_number, season_raw = self.season_process(name_season)
        name = self.name_process(name).strip()
        episode = int(re.findall(r"\d{1,3}", match_obj.group(2))[0])
        other = match_obj.group(3).strip()
        sub, dpi, source= self.find_tags(other)
        return group, name, season_number, season_raw, episode, sub, dpi, source

    def analyse(self, raw) -> Episode:
        try:
            info = Episode()
            info.group, info.title, info.season_info.number,\
            info.season_info.raw, info.ep_info.number,\
            info.subtitle, info.dpi, info.source \
                = self.process(raw)
            return info
        except:
            logger.warning(f"ERROR match {raw}")


if __name__ == "__main__":
    import sys, os

    sys.path.append(os.path.dirname(".."))
    from const import BCOLORS
    from bangumi_parser.episode import Episode

    parser = ParserLV2()
    with (open("bangumi_parser/names.txt", "r", encoding="utf-8") as f):
        err_count = 0
        for name in f:
            if name != "":
                try:
                    # parser.get_group(name)
                    title, season, episode = parser.analyse(name)
                    # print(name)
                    # print(title)
                    # print(season)
                    # print(episode)
                except:
                    if (
                        re.search(
                            r"\d{1,3}[-~]\d{1,3}|OVA|BD|電影|剧场版|老番|冷番|OAD|合集|劇場版|柯南|海賊王|蜡笔小新|整理|樱桃小丸子",
                            name,
                        )
                        is None
                    ):
                        print(f"{BCOLORS._(BCOLORS.HEADER, name)}")
                        err_count += 1
        print(BCOLORS._(BCOLORS.WARNING, err_count))