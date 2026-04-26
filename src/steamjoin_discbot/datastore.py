import json
from typing import Dict, Any
from helpers import MessageType

class Datastore():
    backup_loc: str
    server_settings: Dict[int, Dict[str,Any]]

    def __init__(self, backup_loc: str):
        self.backup_loc = backup_loc
        self.server_settings = {}

    def _save(self):
        with open(self.backup_loc, 'w') as f:
            json.dump(self.server_settings, f, indent=4)

    def _load(self):
        with open(self.backup_loc, 'r') as f:
            self.server_settings = json.load(f)

    def _ensure_server_in_settings(self, server_id: int):
        if server_id not in self.server_settings.keys():
            self.server_settings[server_id] = {}

    def set_message_type(self, server_id: int, message_type: MessageType):
        self._ensure_server_in_settings(server_id)
        self.server_settings[server_id]['message_type'] = message_type

    def get_message_type(self, server_id: int) -> MessageType:
        self._ensure_server_in_settings(server_id)
        return self.server_settings[server_id].get('message_type', MessageType.Default)
