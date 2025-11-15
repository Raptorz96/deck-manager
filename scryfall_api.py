"""
Modulo per l'integrazione con l'API Scryfall di Magic: The Gathering
"""
import requests
import time
import logging
from typing import Dict, List, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# URL base dell'API Scryfall
SCRYFALL_API_BASE = "https://api.scryfall.com"

# Rate limiting: Scryfall richiede almeno 50-100ms tra le richieste
REQUEST_DELAY = 0.1


class ScryfallAPI:
    """Client per interagire con l'API Scryfall"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MTG-Deck-Manager/1.0'
        })
        self.last_request_time = 0

    def _rate_limit(self) -> None:
        """Implementa il rate limiting per rispettare le policy di Scryfall"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - time_since_last_request)

        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Effettua una richiesta all'API Scryfall con gestione errori"""
        self._rate_limit()

        url = f"{SCRYFALL_API_BASE}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Errore nella richiesta a Scryfall: {e}")
            return None

    @lru_cache(maxsize=1000)
    def get_card_by_name(self, name: str, fuzzy: bool = True) -> Optional[Dict[str, Any]]:
        """
        Cerca una carta per nome

        Args:
            name: Nome della carta
            fuzzy: Se True, usa ricerca fuzzy (più tollerante agli errori)

        Returns:
            Dizionario con i dati della carta o None se non trovata
        """
        endpoint = "/cards/named"
        params = {"fuzzy" if fuzzy else "exact": name}

        return self._make_request(endpoint, params)

    def search_cards(self, query: str, page: int = 1) -> Optional[Dict[str, Any]]:
        """
        Cerca carte usando la sintassi di ricerca di Scryfall

        Args:
            query: Query di ricerca (es: "c:red type:creature")
            page: Numero di pagina (default: 1)

        Returns:
            Dizionario con i risultati della ricerca
        """
        endpoint = "/cards/search"
        params = {"q": query, "page": page}

        return self._make_request(endpoint, params)

    def get_card_details(self, card_name: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene dettagli completi di una carta

        Returns:
            Dizionario con:
            - name: nome della carta
            - colors: lista dei colori
            - color_identity: identità di colore (importante per Commander)
            - type_line: riga del tipo
            - oracle_text: testo della carta
            - keywords: abilità chiave
            - mana_cost: costo di mana
            - cmc: costo di mana convertito
            - power/toughness: forza/costituzione (se creatura)
        """
        card_data = self.get_card_by_name(card_name)

        if not card_data:
            return None

        # Estrai le informazioni rilevanti
        details = {
            'name': card_data.get('name', ''),
            'colors': card_data.get('colors', []),
            'color_identity': card_data.get('color_identity', []),
            'type_line': card_data.get('type_line', ''),
            'oracle_text': card_data.get('oracle_text', ''),
            'keywords': card_data.get('keywords', []),
            'mana_cost': card_data.get('mana_cost', ''),
            'cmc': card_data.get('cmc', 0),
            'image_uri': card_data.get('image_uris', {}).get('normal', ''),
            'scryfall_uri': card_data.get('scryfall_uri', ''),
        }

        # Aggiungi power/toughness se è una creatura
        if 'power' in card_data:
            details['power'] = card_data['power']
            details['toughness'] = card_data['toughness']

        return details

    def get_commander_precons(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Cerca mazzi precon Commander

        Args:
            year: Anno specifico (es: 2024) o None per tutti

        Returns:
            Lista di mazzi precon trovati
        """
        # Query per cercare carte che sono commander di precon
        query = "is:commander"
        if year:
            query += f" year={year}"

        results = self.search_cards(query)

        if not results or 'data' not in results:
            return []

        return results['data']

    def analyze_card_synergies(self, card_name: str) -> Dict[str, Any]:
        """
        Analizza le potenziali sinergie di una carta

        Returns:
            Dizionario con informazioni su sinergie:
            - tribes: tribù/creature type che supporta
            - mechanics: meccaniche chiave
            - themes: temi generali (token, graveyard, etc)
        """
        card = self.get_card_details(card_name)

        if not card:
            return {}

        synergies = {
            'tribes': [],
            'mechanics': [],
            'themes': []
        }

        oracle_text = card.get('oracle_text', '').lower()
        type_line = card.get('type_line', '').lower()
        keywords = [k.lower() for k in card.get('keywords', [])]

        # Analizza tribù
        creature_types = ['human', 'elf', 'goblin', 'zombie', 'dragon', 'angel',
                         'demon', 'vampire', 'wizard', 'warrior', 'merfolk',
                         'soldier', 'knight', 'artifact', 'enchantment']

        for tribe in creature_types:
            if tribe in oracle_text or tribe in type_line:
                synergies['tribes'].append(tribe)

        # Analizza meccaniche
        mechanics = ['draw', 'discard', 'sacrifice', 'counter', '+1/+1',
                    'token', 'graveyard', 'exile', 'flash', 'haste',
                    'flying', 'trample', 'lifelink', 'deathtouch']

        for mechanic in mechanics:
            if mechanic in oracle_text or mechanic in keywords:
                synergies['mechanics'].append(mechanic)

        # Analizza temi
        themes_map = {
            'tokens': ['token', 'create', 'populate'],
            'graveyard': ['graveyard', 'dies', 'death trigger', 'recursion'],
            'artifacts': ['artifact', 'equipment', 'attach'],
            'enchantments': ['enchantment', 'aura', 'enchant'],
            'counters': ['+1/+1 counter', 'counter on', 'proliferate'],
            'spellslinger': ['instant', 'sorcery', 'spell', 'cast'],
            'tribal': ['creature type', 'share a type'],
            'voltron': ['equipment', 'aura', 'enchant creature', 'attach'],
            'reanimator': ['return', 'graveyard to battlefield', 'reanimate'],
            'sacrifice': ['sacrifice', 'dies', 'death trigger'],
        }

        for theme, keywords_list in themes_map.items():
            if any(keyword in oracle_text for keyword in keywords_list):
                if theme not in synergies['themes']:
                    synergies['themes'].append(theme)

        return synergies


# Istanza singleton
_scryfall_api = None

def get_scryfall_api() -> ScryfallAPI:
    """Ottiene l'istanza singleton dell'API Scryfall"""
    global _scryfall_api
    if _scryfall_api is None:
        _scryfall_api = ScryfallAPI()
    return _scryfall_api
