import json
from typing import Dict, Any
from helpers import MessageType
from os import path

class Datastore():
    backup_loc: str
    server_settings: Dict[int, Dict[str,Any]]

    def __init__(self, backup_loc: str):
        self.backup_loc = backup_loc
        if path.exists(backup_loc):
            self._load()
        else :
            self.server_settings = {}

    def _save(self):
        with open(self.backup_loc, 'w') as f:
            json.dump(self.server_settings, f, indent=4)

    def _load(self):
        with open(self.backup_loc, 'r') as f:
            settings = json.load(f)
        
        self.server_settings = {}
        for server in settings:
            self.server_settings[int(server)] = {}
            for property in settings[server]:
                match property:
                    case "message_type":
                        self.server_settings[int(server)][property] = MessageType(settings[server][property])
                        
    def _ensure_server_in_settings(self, server_id: int):
        if server_id not in self.server_settings.keys():
            self.server_settings[server_id] = {}

    def set_message_type(self, server_id: int, message_type: MessageType):
        self._ensure_server_in_settings(server_id)
        self.server_settings[server_id]['message_type'] = message_type
        self._save()

    def get_message_type(self, server_id: int) -> str:
        self._ensure_server_in_settings(server_id)
        return self.server_settings[server_id].get('message_type', MessageType.Default)
