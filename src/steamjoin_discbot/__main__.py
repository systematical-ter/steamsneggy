import sys
import argparse
import configparser
from bot import SteamSneggy

def main(configFile: str):
    cfp = configparser.ConfigParser()

    cfp.read(configFile)

    discord_token = cfp['TOKENS']['DISCORD']
    domain = cfp['DEFAULT']['domain']
    ss = SteamSneggy(discord_token, domain)
    ss.setup_commands()
    ss.start_bot()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str)
    args = vars(ap.parse_args(sys.argv[1:]))

    main(args['config'])