"""
Motore di raccomandazione per suggerire carte da aggiungere alla collezione
"""
import logging
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

from scryfall_api import get_scryfall_api
from commander_precons import CommanderPrecon, get_precon_database
from synergy_analyzer import get_synergy_analyzer, SynergyScore

logger = logging.getLogger(__name__)


@dataclass
class CardRecommendation:
    """Rappresenta una raccomandazione di carta"""
    card_name: str
    precon_name: str
    priority: str  # 'high', 'medium', 'low'
    score: float
    reasons: List[str]
    is_key_card: bool
    card_details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'card_name': self.card_name,
            'precon_name': self.precon_name,
            'priority': self.priority,
            'score': self.score,
            'reasons': self.reasons,
            'is_key_card': self.is_key_card,
            'card_details': self.card_details
        }


class RecommendationEngine:
    """Motore per raccomandare carte da aggiungere"""

    def __init__(self):
        self.scryfall = get_scryfall_api()
        self.analyzer = get_synergy_analyzer()
        self.precon_db = get_precon_database()

    def recommend_cards_for_precon(
        self,
        precon: CommanderPrecon,
        owned_cards: Set[str],
        max_recommendations: int = 20
    ) -> List[CardRecommendation]:
        """
        Raccomanda carte da aggiungere per un precon specifico

        Args:
            precon: Mazzo precon per cui raccomandare carte
            owned_cards: Set di nomi di carte già possedute
            max_recommendations: Numero massimo di raccomandazioni

        Returns:
            Lista di CardRecommendation ordinate per priorità
        """
        recommendations = []
        owned_cards_lower = {card.lower() for card in owned_cards}

        # 1. Raccomanda le carte chiave del precon che non sono possedute
        for key_card in precon.key_cards:
            if key_card.lower() not in owned_cards_lower:
                card_details = self.scryfall.get_card_details(key_card)

                if card_details:
                    recommendations.append(CardRecommendation(
                        card_name=key_card,
                        precon_name=precon.name,
                        priority='high',
                        score=95.0,
                        reasons=[
                            f"Carta chiave per {precon.name}",
                            f"Tema: {', '.join(precon.themes)}",
                            f"Archetipo: {precon.archetype}"
                        ],
                        is_key_card=True,
                        card_details=card_details
                    ))

        # 2. Cerca carte che supportano i temi del precon
        for theme in precon.themes:
            theme_cards = self._find_cards_for_theme(
                theme,
                precon.color_identity,
                owned_cards_lower,
                limit=5
            )

            for card_name, score in theme_cards:
                card_details = self.scryfall.get_card_details(card_name)

                if card_details:
                    priority = self._calculate_priority(score)
                    recommendations.append(CardRecommendation(
                        card_name=card_name,
                        precon_name=precon.name,
                        priority=priority,
                        score=score,
                        reasons=[
                            f"Supporta tema: {theme}",
                            f"Sinergia con {precon.archetype}",
                        ],
                        is_key_card=False,
                        card_details=card_details
                    ))

        # 3. Rimuovi duplicati e ordina per score
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec.card_name.lower() not in seen:
                seen.add(rec.card_name.lower())
                unique_recommendations.append(rec)

        unique_recommendations.sort(key=lambda x: x.score, reverse=True)

        return unique_recommendations[:max_recommendations]

    def _find_cards_for_theme(
        self,
        theme: str,
        color_identity: List[str],
        exclude_cards: Set[str],
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Trova carte che supportano un tema specifico

        Returns:
            Lista di tuple (card_name, score)
        """
        # Mappa temi a query Scryfall
        theme_queries = {
            'artifacts': 'type:artifact',
            'tokens': 'o:"create" o:"token"',
            'graveyard': 'o:"graveyard"',
            'dragons': 'type:dragon',
            'tribal': 'o:"creature type"',
            'sacrifice': 'o:"sacrifice"',
            'counters': 'o:"+1/+1 counter"',
            '+1/+1': 'o:"+1/+1 counter"',
            'draw': 'o:"draw"',
            'treasures': 'o:"treasure"',
            'clues': 'o:"clue"',
            'enchantments': 'type:enchantment',
            'spellslinger': '(type:instant OR type:sorcery)',
            'voltron': '(type:equipment OR (type:aura o:"enchant creature"))',
            'eldrazi': 'type:eldrazi',
            'political': 'o:"each opponent"',
        }

        query = theme_queries.get(theme.lower(), f'o:"{theme}"')

        # Aggiungi filtro colori
        if color_identity:
            color_query = ' '.join(f'id:{color}' for color in color_identity)
            query = f'{query} {color_query}'

        # Cerca su Scryfall
        try:
            results = self.scryfall.search_cards(query)
            if not results or 'data' not in results:
                return []

            cards = []
            for card in results['data'][:limit * 2]:  # Prendi più carte del necessario
                card_name = card.get('name', '')
                if card_name.lower() not in exclude_cards:
                    # Calcola uno score basato sulla rilevanza
                    score = self._calculate_theme_relevance(card, theme)
                    cards.append((card_name, score))

            # Ordina per score e limita
            cards.sort(key=lambda x: x[1], reverse=True)
            return cards[:limit]

        except Exception as e:
            logger.error(f"Errore nella ricerca per tema {theme}: {e}")
            return []

    def _calculate_theme_relevance(self, card_data: Dict[str, Any], theme: str) -> float:
        """Calcola quanto una carta è rilevante per un tema"""
        score = 60.0  # Base score

        oracle_text = card_data.get('oracle_text', '').lower()
        type_line = card_data.get('type_line', '').lower()
        keywords = [k.lower() for k in card_data.get('keywords', [])]

        theme_lower = theme.lower()

        # Bonus se il tema appare nel testo
        occurrences = oracle_text.count(theme_lower)
        score += occurrences * 10

        # Bonus se appare nei tipi
        if theme_lower in type_line:
            score += 15

        # Bonus per keywords rilevanti
        if theme_lower in keywords:
            score += 20

        return min(90.0, score)

    def _calculate_priority(self, score: float) -> str:
        """Calcola la priorità basata sullo score"""
        if score >= 80:
            return 'high'
        elif score >= 60:
            return 'medium'
        else:
            return 'low'

    def get_recommendations_for_collection(
        self,
        owned_cards: List[str],
        top_precons: int = 3,
        cards_per_precon: int = 10
    ) -> Dict[str, List[CardRecommendation]]:
        """
        Genera raccomandazioni per una collezione di carte

        Args:
            owned_cards: Lista di carte possedute
            top_precons: Numero di precon da considerare
            cards_per_precon: Numero di carte da raccomandare per precon

        Returns:
            Dizionario: precon_name -> lista di CardRecommendation
        """
        # Trova i migliori precon per la collezione
        all_precons = self.precon_db.get_all_precons()
        recommended_precons = self.analyzer.recommend_precons_for_cards(
            owned_cards,
            all_precons,
            top_n=top_precons
        )

        recommendations = {}
        owned_cards_set = set(card.lower() for card in owned_cards)

        for precon, stats in recommended_precons:
            precon_recommendations = self.recommend_cards_for_precon(
                precon,
                owned_cards_set,
                max_recommendations=cards_per_precon
            )
            recommendations[precon.name] = precon_recommendations

        return recommendations

    def get_general_recommendations(
        self,
        owned_cards: List[str],
        budget_friendly: bool = True,
        max_recommendations: int = 20
    ) -> List[CardRecommendation]:
        """
        Genera raccomandazioni generali per migliorare la collezione

        Args:
            owned_cards: Lista di carte possedute
            budget_friendly: Se True, evita carte costose
            max_recommendations: Numero massimo di raccomandazioni

        Returns:
            Lista di CardRecommendation
        """
        all_recommendations = self.get_recommendations_for_collection(
            owned_cards,
            top_precons=5,
            cards_per_precon=10
        )

        # Aggrega tutte le raccomandazioni
        aggregated = []
        seen = set()

        for precon_name, recs in all_recommendations.items():
            for rec in recs:
                if rec.card_name.lower() not in seen:
                    seen.add(rec.card_name.lower())
                    aggregated.append(rec)

        # Ordina per score
        aggregated.sort(key=lambda x: x.score, reverse=True)

        return aggregated[:max_recommendations]

    def analyze_collection_gaps(
        self,
        owned_cards: List[str],
        target_precon: CommanderPrecon
    ) -> Dict[str, Any]:
        """
        Analizza le lacune della collezione rispetto a un precon target

        Returns:
            Dizionario con:
            - missing_key_cards: carte chiave mancanti
            - theme_coverage: percentuale di copertura per tema
            - recommendations: raccomandazioni prioritarie
        """
        owned_cards_lower = {card.lower() for card in owned_cards}

        # Carte chiave mancanti
        missing_key_cards = [
            card for card in target_precon.key_cards
            if card.lower() not in owned_cards_lower
        ]

        # Analizza copertura dei temi
        theme_coverage = {}
        for theme in target_precon.themes:
            # Conta quante carte possedute supportano questo tema
            supporting_cards = 0
            for card in owned_cards:
                synergies = self.scryfall.analyze_card_synergies(card)
                if theme.lower() in [t.lower() for t in synergies.get('themes', [])]:
                    supporting_cards += 1

            # Stima copertura (arbitraria: 10 carte = 100%)
            coverage = min(100, (supporting_cards / 10) * 100)
            theme_coverage[theme] = {
                'coverage_percent': coverage,
                'supporting_cards': supporting_cards
            }

        # Raccomandazioni prioritarie
        recommendations = self.recommend_cards_for_precon(
            target_precon,
            owned_cards_lower,
            max_recommendations=15
        )

        return {
            'missing_key_cards': missing_key_cards,
            'theme_coverage': theme_coverage,
            'recommendations': recommendations,
            'precon': target_precon
        }


# Istanza singleton
_recommendation_engine = None

def get_recommendation_engine() -> RecommendationEngine:
    """Ottiene l'istanza singleton del motore di raccomandazione"""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine
