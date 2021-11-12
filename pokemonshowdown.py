import argparse
import json
import pathlib
import re

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def load_replays_from_file(file_path):
    with open(file_path, "r") as jsonl_file:
        yield from jsonl_file.readlines()

def load_replays_from_dir(dir_path: pathlib.Path):
    for file_path in dir_path.iterdir():
        yield from load_replays_from_file(file_path)

def extract_matches(args):
    replay_file_path = args.replay_path
    replays = None

    if pathlib.Path(replay_file_path).is_file():
        replays = load_replays_from_file(replay_file_path)

    elif pathlib.Path(replay_file_path).is_dir():
        replays = load_replays_from_dir(replay_file_path)

    for index, replay in enumerate(replays):
        if index < args.max_replays:
            print(extract_match_info(json.loads(replay)))

def process_replay_file(args):
    with open(args.replay_file, "r") as jsonl_file:
        for replay in jsonl_file.readlines()[:1]:
            processed_replay = extract_match_info(json.loads(replay))
            print(json.dumps(processed_replay))

def extract_match_info(replay):
    p1_name = re.compile("^\|player\|p1\|(\w+)\|.*$", flags=re.MULTILINE)
    p2_name = re.compile("^\|player\|p2\|(\w+)\|.*$", flags=re.MULTILINE)

    winner  = re.compile("^\|win\|(\w+)\|.*$", flags=re.MULTILINE)

    p1_team = re.compile("^\|poke\|p1\|(\w+).*\|$", flags=re.MULTILINE)
    p2_team = re.compile("^\|poke\|p2\|(\w+).*\|$", flags=re.MULTILINE)

    winner = winner.search(replay["log"])
    p1_name = p1_name.search(replay["log"])
    p2_name = p2_name.search(replay["log"])

    if p1_name == winner:
        winner = 0
    elif p2_name == winner:
        winner = 1
    else:
        winner = "nan"

    return {
        "id": replay["id"].split("-")[1],
        "format": replay["formatid"],
        "uploadtime": replay["uploadtime"],
        "winner": winner,
        "teams": [
            p1_team.findall(replay["log"]),
            p2_team.findall(replay["log"])
        ]
    }

def crawl_replays(args):
    # https://docs.scrapy.org/en/latest/topics/practices.html#run-scrapy-from-a-script
    process = CrawlerProcess(get_project_settings())
    process.crawl("replays",
                  format=args.format,
                  feed_base_dir=args.output_dir,
                  max_replays=args.max_replays)

    process.start()

def get_parser():
    parser = argparse.ArgumentParser(description="Commands for manipulating replay data from Pokemon Showdown",
                                     formatter_class=argparse.RawTextHelpFormatter)

    subparser = parser.add_subparsers(title="subcommands")

    scraper = subparser.add_parser(name="scrape",
                                   description="Scrape Pokemon Showdown for replays",
                                   help="Scrape Pokemon Showdown for replay")

    scraper.set_defaults(func=crawl_replays)

    #https://stackoverflow.com/a/18507871
    #printing default value for options in help text
    scraper.add_argument("-f",
                        "--format",
                        type=str,
                        help="Battle format to crawl for\ndefault: %(default)s",
                        default="gen8ou")

    scraper.add_argument("-o",
                        "--output-dir",
                        type=pathlib.Path,
                        help="Directory to save replays to\ndefault: %(default)s",
                        default=".")

    scraper.add_argument("-m",
                        "--max-replays",
                        type=int,
                        default=10,
                        help="Maximum number of replays to crawl for\ndefault: %(default)d")

    extracter = subparser.add_parser(name="extract",
                                   description="Extract match info from raw replay files",
                                   help="Extract match info from raw replay files")

    extracter.add_argument("replay_path",
                         help="Replay file to process",
                         type=pathlib.Path)

    extracter.add_argument("-m",
                           "--max-replays",
                           type=int,
                           help="Max number of raw replay files to process for match info",
                           default=10)

    extracter.set_defaults(func=extract_matches)

    return parser

def main(args):
    args.func(args)

if __name__ == "__main__":
   main(get_parser().parse_args())

