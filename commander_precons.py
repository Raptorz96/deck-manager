"""
Modulo per gestire i mazzi precon Commander
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Path al database dei precon
PRECONS_DB_PATH = Path(__file__).parent / 'data' / 'commander_precons.json'


@dataclass
class CommanderPrecon:
    """Rappresenta un mazzo precon Commander"""
    name: str
    year: int
    set_code: str
    commanders: List[str]
    color_identity: List[str]
    themes: List[str]
    key_cards: List[str] = field(default_factory=list)
    archetype: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'year': self.year,
            'set_code': self.set_code,
            'commanders': self.commanders,
            'color_identity': self.color_identity,
            'themes': self.themes,
            'key_cards': self.key_cards,
            'archetype': self.archetype,
            'description': self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CommanderPrecon':
        return cls(
            name=data['name'],
            year=data['year'],
            set_code=data['set_code'],
            commanders=data['commanders'],
            color_identity=data['color_identity'],
            themes=data['themes'],
            key_cards=data.get('key_cards', []),
            archetype=data.get('archetype', ''),
            description=data.get('description', '')
        )


class CommanderPreconDatabase:
    """Database dei mazzi precon Commander"""

    def __init__(self, db_path: Path = PRECONS_DB_PATH):
        self.db_path = db_path
        self.precons: List[CommanderPrecon] = []
        self._load_database()

    def _load_database(self) -> None:
        """Carica il database dei precon dal file JSON"""
        if not self.db_path.exists():
            logger.warning(f"Database precon non trovato: {self.db_path}")
            self._create_default_database()
            return

        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.precons = [CommanderPrecon.from_dict(p) for p in data]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Errore nel caricamento del database: {e}")
            self._create_default_database()

    def _create_default_database(self) -> None:
        """Crea un database di default con alcuni mazzi precon popolari"""
        # Database con mazzi precon Commander recenti
        default_precons = [
            {
                "name": "Mishra's Burnished Banner",
                "year": 2024,
                "set_code": "BRC",
                "commanders": ["Mishra, Eminent One"],
                "color_identity": ["U", "B", "R"],
                "themes": ["artifacts", "tokens", "graveyard"],
                "archetype": "artifact tokens",
                "key_cards": [
                    "Ashnod's Altar", "Cursed Mirror", "Myr Battlesphere",
                    "Digsite Engineer", "Scrap Trawler", "Junk Diver"
                ],
                "description": "Mazzo basato su artefatti e token, con focus sul riciclaggio da graveyard"
            },
            {
                "name": "Urza's Iron Alliance",
                "year": 2024,
                "set_code": "BRC",
                "commanders": ["Urza, Chief Artificer"],
                "color_identity": ["W", "U"],
                "themes": ["artifacts", "tokens", "sacrifice"],
                "archetype": "artifact sacrifice",
                "key_cards": [
                    "Sai, Master Thopterist", "Efficient Construction", "Thopter Spy Network",
                    "Myr Battlesphere", "Steel Overseer", "Cranial Plating"
                ],
                "description": "Strategia basata su artefatti creature e token thopter"
            },
            {
                "name": "Draconic Dissent",
                "year": 2024,
                "set_code": "CLB",
                "commanders": ["Miirym, Sentinel Wyrm"],
                "color_identity": ["G", "U", "R"],
                "themes": ["dragons", "tribal", "tokens"],
                "archetype": "dragon tribal",
                "key_cards": [
                    "Terror of the Peaks", "Scourge of Valkas", "Dragon Tempest",
                    "Old Gnawbone", "Klauth, Unrivaled Ancient", "Utvara Hellkite"
                ],
                "description": "Mazzo tribale draghi con focus sulla duplicazione"
            },
            {
                "name": "Planar Portal",
                "year": 2024,
                "set_code": "CLB",
                "commanders": ["The Council of Four"],
                "color_identity": ["W", "U"],
                "themes": ["draw", "tokens", "political"],
                "archetype": "draw matters",
                "key_cards": [
                    "Alms Collector", "Archivist of Oghma", "Keeper of Keys",
                    "Propaganda", "Ghostly Prison", "Consecrated Sphinx"
                ],
                "description": "Strategia basata su pescare carte e creare token"
            },
            {
                "name": "Heads I Win, Tails You Lose",
                "year": 2024,
                "set_code": "PIP",
                "commanders": ["Mr. House, President and CEO"],
                "color_identity": ["U", "B", "R"],
                "themes": ["artifacts", "dice", "treasures"],
                "archetype": "treasure artifacts",
                "key_cards": [
                    "Marionette Master", "Reckless Fireweaver", "Disciple of the Vault",
                    "Academy Manufactor", "Galazeth Prismari", "Goldspan Dragon"
                ],
                "description": "Strategia basata su tesori e artefatti sacrificabili"
            },
            {
                "name": "Scrappy Survivors",
                "year": 2024,
                "set_code": "PIP",
                "commanders": ["Preston Garvey, Minuteman"],
                "color_identity": ["G", "W"],
                "themes": ["tokens", "counters", "+1/+1"],
                "archetype": "token +1/+1 counters",
                "key_cards": [
                    "Doubling Season", "Parallel Lives", "Anointed Procession",
                    "Cathar's Crusade", "Hardened Scales", "Branching Evolution"
                ],
                "description": "Strategia basata su token e segnalini +1/+1"
            },
            {
                "name": "Blame Game",
                "year": 2024,
                "set_code": "MKM",
                "commanders": ["Alquist Proft, Master Sleuth"],
                "color_identity": ["W", "U"],
                "themes": ["clues", "artifacts", "draw"],
                "archetype": "clue artifacts",
                "key_cards": [
                    "Search the Premises", "Thorough Investigation", "Ongoing Investigation",
                    "Tamiyo's Journal", "Wavesifter", "Academy Manufactor"
                ],
                "description": "Strategia basata su indizi e pescare carte"
            },
            {
                "name": "Deadly Disguise",
                "year": 2024,
                "set_code": "MKM",
                "commanders": ["Kaust, Eyes of the Glade"],
                "color_identity": ["B", "G"],
                "themes": ["disguise", "graveyard", "sacrifice"],
                "archetype": "disguise morph",
                "key_cards": [
                    "Kadena, Slinking Sorcerer", "Ixidron", "Secret Plans",
                    "Den Protector", "Willbender", "Vesuvan Shapeshifter"
                ],
                "description": "Mazzo basato su meccanica disguise e morph"
            },
            {
                "name": "Peace Offering",
                "year": 2024,
                "set_code": "OTC",
                "commanders": ["Kynaios and Tiro of Meletis"],
                "color_identity": ["G", "W", "U", "R"],
                "themes": ["group hug", "political", "draw"],
                "archetype": "group hug",
                "key_cards": [
                    "Selvala, Explorer Returned", "Howling Mine", "Temple Bell",
                    "Rites of Flourishing", "Collective Voyage", "Veteran Explorer"
                ],
                "description": "Strategia group hug con vantaggi condivisi"
            },
            {
                "name": "Eldrazi Unbound",
                "year": 2024,
                "set_code": "OTC",
                "commanders": ["Zhulodok, Void Gorger"],
                "color_identity": ["C"],
                "commanders_color": ["Colorless"],
                "themes": ["eldrazi", "ramp", "big creatures"],
                "archetype": "eldrazi ramp",
                "key_cards": [
                    "Ulamog, the Ceaseless Hunger", "Kozilek, Butcher of Truth",
                    "Conduit of Ruin", "Eldrazi Temple", "Eye of Ugin", "Spawnsire of Ulamog"
                ],
                "description": "Mazzo tribale Eldrazi con ramp veloce"
            }
        ]

        self.precons = [CommanderPrecon.from_dict(p) for p in default_precons]
        self._save_database()

    def _save_database(self) -> None:
        """Salva il database su file JSON"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in self.precons], f, indent=2, ensure_ascii=False)

    def get_all_precons(self) -> List[CommanderPrecon]:
        """Ritorna tutti i mazzi precon"""
        return self.precons

    def get_precons_by_year(self, year: int) -> List[CommanderPrecon]:
        """Filtra i precon per anno"""
        return [p for p in self.precons if p.year == year]

    def get_precons_by_colors(self, colors: List[str]) -> List[CommanderPrecon]:
        """
        Filtra i precon per identità di colore

        Args:
            colors: Lista di colori (es: ['W', 'U'] per Azorius)
        """
        colors_set = set(colors)
        return [p for p in self.precons if set(p.color_identity) == colors_set]

    def get_precons_by_theme(self, theme: str) -> List[CommanderPrecon]:
        """Filtra i precon per tema"""
        theme_lower = theme.lower()
        return [p for p in self.precons if theme_lower in [t.lower() for t in p.themes]]

    def search_precons(self, query: str) -> List[CommanderPrecon]:
        """
        Cerca precon per nome, commander, o tema

        Args:
            query: Stringa di ricerca
        """
        query_lower = query.lower()
        results = []

        for precon in self.precons:
            # Cerca nel nome
            if query_lower in precon.name.lower():
                results.append(precon)
                continue

            # Cerca nei commander
            if any(query_lower in cmd.lower() for cmd in precon.commanders):
                results.append(precon)
                continue

            # Cerca nei temi
            if any(query_lower in theme.lower() for theme in precon.themes):
                results.append(precon)
                continue

            # Cerca nell'archetipo
            if query_lower in precon.archetype.lower():
                results.append(precon)
                continue

        return results

    def add_precon(self, precon: CommanderPrecon) -> None:
        """Aggiunge un nuovo precon al database"""
        self.precons.append(precon)
        self._save_database()


# Istanza singleton
_precon_db = None

def get_precon_database() -> CommanderPreconDatabase:
    """Ottiene l'istanza singleton del database precon"""
    global _precon_db
    if _precon_db is None:
        _precon_db = CommanderPreconDatabase()
    return _precon_db
