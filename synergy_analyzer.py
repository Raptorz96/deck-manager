"""
Modulo per analizzare le sinergie tra carte e mazzi Commander
"""
import logging
from typing import Dict, List, Set, Tuple, Any
from collections import Counter, defaultdict
from dataclasses import dataclass

from scryfall_api import get_scryfall_api
from commander_precons import CommanderPrecon

logger = logging.getLogger(__name__)


@dataclass
class SynergyScore:
    """Rappresenta un punteggio di sinergia tra una carta e un precon"""
    card_name: str
    precon_name: str
    score: float
    reasons: List[str]
    color_match: bool
    theme_matches: List[str]
    mechanic_matches: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'card_name': self.card_name,
            'precon_name': self.precon_name,
            'score': self.score,
            'reasons': self.reasons,
            'color_match': self.color_match,
            'theme_matches': self.theme_matches,
            'mechanic_matches': self.mechanic_matches
        }


class SynergyAnalyzer:
    """Analizza le sinergie tra carte e mazzi Commander"""

    def __init__(self):
        self.scryfall = get_scryfall_api()

    def analyze_card_for_precon(self, card_name: str, precon: CommanderPrecon) -> SynergyScore:
        """
        Analizza quanto una carta è in sinergia con un precon

        Returns:
            SynergyScore con punteggio da 0 a 100
        """
        # Ottieni i dettagli della carta
        card_details = self.scryfall.get_card_details(card_name)
        if not card_details:
            return SynergyScore(
                card_name=card_name,
                precon_name=precon.name,
                score=0.0,
                reasons=["Carta non trovata"],
                color_match=False,
                theme_matches=[],
                mechanic_matches=[]
            )

        # Analizza sinergie
        card_synergies = self.scryfall.analyze_card_synergies(card_name)

        score = 0.0
        reasons = []
        theme_matches = []
        mechanic_matches = []

        # 1. Controllo identità di colore (30 punti)
        color_identity = set(card_details.get('color_identity', []))
        precon_colors = set(precon.color_identity)

        color_match = color_identity.issubset(precon_colors) if precon_colors else True

        if color_match:
            score += 30
            reasons.append(f"✓ Identità di colore compatibile ({', '.join(color_identity) if color_identity else 'Colorless'})")
        else:
            reasons.append(f"✗ Identità di colore incompatibile")
            return SynergyScore(
                card_name=card_name,
                precon_name=precon.name,
                score=0.0,
                reasons=reasons,
                color_match=False,
                theme_matches=[],
                mechanic_matches=[]
            )

        # 2. Match dei temi (40 punti max)
        card_themes = set(card_synergies.get('themes', []))
        precon_themes = set(theme.lower() for theme in precon.themes)

        common_themes = card_themes.intersection(precon_themes)
        theme_score = min(40, len(common_themes) * 15)
        score += theme_score

        if common_themes:
            theme_matches = list(common_themes)
            reasons.append(f"✓ Temi condivisi: {', '.join(common_themes)}")

        # 3. Match delle meccaniche (20 punti max)
        card_mechanics = set(card_synergies.get('mechanics', []))

        # Mappa le meccaniche ai temi del precon
        mechanic_to_theme = {
            'tokens': ['token', 'create'],
            'graveyard': ['graveyard', 'dies', 'sacrifice'],
            'artifacts': ['artifact'],
            'enchantments': ['enchantment', 'aura'],
            'counters': ['+1/+1', 'counter'],
            'spellslinger': ['draw', 'instant', 'sorcery'],
            'tribal': ['creature type'],
            'sacrifice': ['sacrifice'],
        }

        mechanic_score = 0
        for theme in precon.themes:
            theme_lower = theme.lower()
            if theme_lower in mechanic_to_theme:
                relevant_mechanics = mechanic_to_theme[theme_lower]
                for mechanic in card_mechanics:
                    if any(rm in mechanic for rm in relevant_mechanics):
                        mechanic_score += 5
                        mechanic_matches.append(mechanic)

        mechanic_score = min(20, mechanic_score)
        score += mechanic_score

        if mechanic_matches:
            reasons.append(f"✓ Meccaniche rilevanti: {', '.join(set(mechanic_matches))}")

        # 4. Match con carte chiave del precon (10 punti)
        card_types = card_details.get('type_line', '').lower()
        oracle_text = card_details.get('oracle_text', '').lower()

        key_card_synergy = False
        for key_card in precon.key_cards:
            # Semplice controllo se menziona carte simili
            if key_card.lower() in oracle_text:
                score += 10
                reasons.append(f"✓ Sinergia con carta chiave: {key_card}")
                key_card_synergy = True
                break

        # Bonus per archetipi specifici
        archetype_bonus = self._calculate_archetype_bonus(
            card_details, card_synergies, precon.archetype
        )
        score += archetype_bonus
        if archetype_bonus > 0:
            reasons.append(f"✓ Bonus archetipo '{precon.archetype}': +{archetype_bonus} punti")

        return SynergyScore(
            card_name=card_name,
            precon_name=precon.name,
            score=min(100, score),
            reasons=reasons,
            color_match=color_match,
            theme_matches=theme_matches,
            mechanic_matches=mechanic_matches
        )

    def _calculate_archetype_bonus(
        self,
        card_details: Dict[str, Any],
        card_synergies: Dict[str, Any],
        archetype: str
    ) -> float:
        """Calcola bonus per archetipi specifici"""
        bonus = 0.0
        archetype_lower = archetype.lower()
        oracle_text = card_details.get('oracle_text', '').lower()
        type_line = card_details.get('type_line', '').lower()

        # Archetipi specifici
        archetype_keywords = {
            'artifact': ['artifact'],
            'token': ['token', 'create'],
            'dragon': ['dragon'],
            'tribal': ['creature type', 'share'],
            'graveyard': ['graveyard', 'dies'],
            'voltron': ['equipment', 'aura', 'attach'],
            'spellslinger': ['instant', 'sorcery', 'cast'],
            'ramp': ['land', 'mana'],
            'group hug': ['each player', 'draw', 'opponent'],
        }

        for arch_key, keywords in archetype_keywords.items():
            if arch_key in archetype_lower:
                for keyword in keywords:
                    if keyword in oracle_text or keyword in type_line:
                        bonus += 5
                        break

        return min(10, bonus)

    def find_best_precons_for_collection(
        self,
        card_names: List[str],
        precons: List[CommanderPrecon],
        min_score: float = 30.0
    ) -> Dict[str, List[SynergyScore]]:
        """
        Trova i migliori precon per una collezione di carte

        Args:
            card_names: Lista di nomi di carte
            precons: Lista di precon da analizzare
            min_score: Punteggio minimo per considerare una sinergia

        Returns:
            Dizionario: precon_name -> lista di SynergyScore
        """
        results = defaultdict(list)

        for card_name in card_names:
            for precon in precons:
                score_result = self.analyze_card_for_precon(card_name, precon)

                if score_result.score >= min_score:
                    results[precon.name].append(score_result)

        # Ordina i risultati per score
        for precon_name in results:
            results[precon_name].sort(key=lambda x: x.score, reverse=True)

        return dict(results)

    def get_precon_statistics(
        self,
        synergy_scores: List[SynergyScore]
    ) -> Dict[str, Any]:
        """
        Calcola statistiche aggregate per un precon

        Returns:
            Dizionario con statistiche:
            - total_cards: numero totale di carte
            - avg_score: punteggio medio
            - max_score: punteggio massimo
            - min_score: punteggio minimo
            - theme_distribution: distribuzione dei temi
            - top_cards: top 5 carte per score
        """
        if not synergy_scores:
            return {
                'total_cards': 0,
                'avg_score': 0.0,
                'max_score': 0.0,
                'min_score': 0.0,
                'theme_distribution': {},
                'top_cards': []
            }

        scores = [s.score for s in synergy_scores]
        all_themes = []
        for s in synergy_scores:
            all_themes.extend(s.theme_matches)

        theme_counter = Counter(all_themes)

        return {
            'total_cards': len(synergy_scores),
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'theme_distribution': dict(theme_counter),
            'top_cards': sorted(synergy_scores, key=lambda x: x.score, reverse=True)[:5]
        }

    def recommend_precons_for_cards(
        self,
        card_names: List[str],
        precons: List[CommanderPrecon],
        top_n: int = 5
    ) -> List[Tuple[CommanderPrecon, Dict[str, Any]]]:
        """
        Raccomanda i migliori precon basati su una collezione di carte

        Returns:
            Lista di tuple (precon, statistiche) ordinate per compatibilità
        """
        synergy_results = self.find_best_precons_for_collection(card_names, precons)

        recommendations = []
        for precon in precons:
            scores = synergy_results.get(precon.name, [])
            if scores:
                stats = self.get_precon_statistics(scores)
                stats['synergy_scores'] = scores
                recommendations.append((precon, stats))

        # Ordina per numero di carte compatibili e punteggio medio
        recommendations.sort(
            key=lambda x: (x[1]['total_cards'], x[1]['avg_score']),
            reverse=True
        )

        return recommendations[:top_n]


# Istanza singleton
_synergy_analyzer = None

def get_synergy_analyzer() -> SynergyAnalyzer:
    """Ottiene l'istanza singleton dell'analizzatore di sinergie"""
    global _synergy_analyzer
    if _synergy_analyzer is None:
        _synergy_analyzer = SynergyAnalyzer()
    return _synergy_analyzer
