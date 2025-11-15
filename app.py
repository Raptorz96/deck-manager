"""
Magic: The Gathering Commander Deck Synergy Analyzer
Analizza la tua collezione e raccomanda carte basate su mazzi precon Commander
"""
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import streamlit as st
import pandas as pd

from scryfall_api import get_scryfall_api
from commander_precons import get_precon_database, CommanderPrecon
from synergy_analyzer import get_synergy_analyzer
from recommendation_engine import get_recommendation_engine

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurazione pagina
st.set_page_config(
    page_title="MTG Commander Synergy Analyzer",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF6B6B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #4ECDC4;
        margin-bottom: 1rem;
    }
    .card-recommendation {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .priority-high {
        border-left: 5px solid #ff4444;
    }
    .priority-medium {
        border-left: 5px solid #ffaa00;
    }
    .priority-low {
        border-left: 5px solid #44ff44;
    }
</style>
""", unsafe_allow_html=True)

# Costanti
DATA_FOLDER = Path(__file__).parent / 'data'
COLLECTION_FILE = DATA_FOLDER / 'collection.json'

# Assicurati che la cartella data esista
DATA_FOLDER.mkdir(exist_ok=True)


# Definizione delle strutture dati
@dataclass
class Card:
    name: str
    quantity: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "quantity": self.quantity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        return cls(
            name=data["name"],
            quantity=data.get("quantity", 1)
        )


@dataclass
class Collection:
    name: str = "La Mia Collezione"
    cards: List[Card] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cards": [card.to_dict() for card in self.cards]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Collection':
        return cls(
            name=data["name"],
            cards=[Card.from_dict(card) for card in data.get("cards", [])]
        )


def load_collection() -> Collection:
    """Carica la collezione dal file JSON"""
    if not COLLECTION_FILE.exists():
        empty = Collection()
        save_collection(empty)
        return empty

    try:
        with open(COLLECTION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Collection.from_dict(data)
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Errore nel caricamento della collezione: {e}")
        empty = Collection()
        save_collection(empty)
        return empty


def save_collection(collection: Collection) -> None:
    """Salva la collezione nel file JSON"""
    with open(COLLECTION_FILE, 'w', encoding='utf-8') as f:
        json.dump(collection.to_dict(), f, indent=2, ensure_ascii=False)


def import_collection_from_file(file_content: str) -> Collection:
    """Importa una collezione da un file .deck"""
    collection = Collection(name="Collezione Importata")

    lines = file_content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split(' ', 1)
        if len(parts) == 2:
            try:
                quantity = int(parts[0])
                card_name = parts[1].split('(')[0].strip()  # Rimuovi info set
                collection.cards.append(Card(name=card_name, quantity=quantity))
            except ValueError:
                collection.cards.append(Card(name=line, quantity=1))
        else:
            collection.cards.append(Card(name=line, quantity=1))

    return collection


def main():
    # Header
    st.markdown('<div class="main-header">🃏 Magic: The Gathering Commander Synergy Analyzer</div>', unsafe_allow_html=True)
    st.markdown("**Analizza la tua collezione e scopri quali mazzi precon Commander sono perfetti per te!**")

    # Inizializza servizi
    scryfall = get_scryfall_api()
    precon_db = get_precon_database()
    analyzer = get_synergy_analyzer()
    recommender = get_recommendation_engine()

    # Carica collezione
    if 'collection' not in st.session_state:
        st.session_state.collection = load_collection()

    collection = st.session_state.collection

    # Sidebar
    with st.sidebar:
        st.header("📚 Gestione Collezione")

        # Rinomina collezione
        with st.expander("✏️ Rinomina Collezione"):
            new_name = st.text_input("Nuovo nome", value=collection.name)
            if st.button("Rinomina", key="rename_btn"):
                collection.name = new_name
                save_collection(collection)
                st.success("Collezione rinominata!")

        # Import/Export
        st.subheader("📥 Importa Collezione")
        uploaded_file = st.file_uploader("Carica file .deck o .txt", type=["deck", "txt"])
        if uploaded_file:
            try:
                file_content = uploaded_file.getvalue().decode('utf-8')
                collection = import_collection_from_file(file_content)
                st.session_state.collection = collection
                save_collection(collection)
                st.success(f"✅ Importate {len(collection.cards)} carte!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Errore nell'importazione: {e}")

        # Aggiungi carta manualmente
        st.subheader("➕ Aggiungi Carta")
        with st.form("add_card_form"):
            card_name = st.text_input("Nome carta")
            quantity = st.number_input("Quantità", min_value=1, value=1, step=1)

            if st.form_submit_button("Aggiungi"):
                if card_name.strip():
                    # Verifica se esiste
                    found = False
                    for card in collection.cards:
                        if card.name.lower() == card_name.lower():
                            card.quantity += quantity
                            found = True
                            break

                    if not found:
                        collection.cards.append(Card(name=card_name, quantity=quantity))

                    save_collection(collection)
                    st.success(f"✅ Aggiunte {quantity}x {card_name}")
                    st.rerun()

        # Statistiche rapide
        st.divider()
        st.metric("Carte totali", sum(c.quantity for c in collection.cards))
        st.metric("Carte uniche", len(collection.cards))

    # Tab principali
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Collezione",
        "🎯 Precon Raccomandati",
        "💎 Raccomandazioni Carte",
        "📊 Analisi Dettagliata"
    ])

    # TAB 1: Collezione
    with tab1:
        st.header(f"📦 {collection.name}")

        if collection.cards:
            # Crea DataFrame
            df = pd.DataFrame([
                {"Nome": card.name, "Quantità": card.quantity}
                for card in collection.cards
            ])

            # Mostra tabella
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Rimuovi carta
            with st.expander("🗑️ Rimuovi Carte"):
                card_to_remove = st.selectbox(
                    "Seleziona carta da rimuovere",
                    options=[f"{c.name} (x{c.quantity})" for c in collection.cards]
                )

                if st.button("Rimuovi", key="remove_btn"):
                    idx = [f"{c.name} (x{c.quantity})" for c in collection.cards].index(card_to_remove)
                    collection.cards.pop(idx)
                    save_collection(collection)
                    st.success("Carta rimossa!")
                    st.rerun()
        else:
            st.info("📭 La tua collezione è vuota. Aggiungi carte dalla sidebar!")

    # TAB 2: Precon Raccomandati
    with tab2:
        st.header("🎯 Mazzi Precon Commander Raccomandati")

        if not collection.cards:
            st.warning("⚠️ Aggiungi carte alla collezione per vedere i precon raccomandati!")
        else:
            with st.spinner("🔍 Analizzo le sinergie..."):
                card_names = [card.name for card in collection.cards]
                all_precons = precon_db.get_all_precons()

                recommended_precons = analyzer.recommend_precons_for_cards(
                    card_names,
                    all_precons,
                    top_n=5
                )

                if recommended_precons:
                    st.success(f"✅ Trovati {len(recommended_precons)} precon compatibili!")

                    for idx, (precon, stats) in enumerate(recommended_precons, 1):
                        with st.expander(
                            f"#{idx} - {precon.name} ({precon.year}) - "
                            f"{stats['total_cards']} carte compatibili "
                            f"(Score medio: {stats['avg_score']:.1f}/100)",
                            expanded=(idx == 1)
                        ):
                            col1, col2 = st.columns([1, 1])

                            with col1:
                                st.markdown(f"**Commander:** {', '.join(precon.commanders)}")
                                st.markdown(f"**Colori:** {', '.join(precon.color_identity) if precon.color_identity else 'Colorless'}")
                                st.markdown(f"**Archetipo:** {precon.archetype}")
                                st.markdown(f"**Temi:** {', '.join(precon.themes)}")
                                st.markdown(f"**Descrizione:** {precon.description}")

                            with col2:
                                st.metric("Carte Compatibili", stats['total_cards'])
                                st.metric("Score Medio", f"{stats['avg_score']:.1f}/100")
                                st.metric("Score Massimo", f"{stats['max_score']:.1f}/100")

                            # Top carte
                            st.markdown("**🌟 Le tue migliori carte per questo precon:**")
                            for card_score in stats['top_cards'][:5]:
                                st.markdown(
                                    f"- **{card_score.card_name}** ({card_score.score:.1f}/100): "
                                    f"{', '.join(card_score.reasons[:2])}"
                                )
                else:
                    st.warning("⚠️ Nessun precon trovato compatibile con la tua collezione.")

    # TAB 3: Raccomandazioni Carte
    with tab3:
        st.header("💎 Carte Raccomandate da Aggiungere")

        if not collection.cards:
            st.warning("⚠️ Aggiungi carte alla collezione per vedere le raccomandazioni!")
        else:
            with st.spinner("🔮 Generazione raccomandazioni..."):
                card_names = [card.name for card in collection.cards]
                recommendations = recommender.get_recommendations_for_collection(
                    card_names,
                    top_precons=3,
                    cards_per_precon=10
                )

                if recommendations:
                    for precon_name, recs in recommendations.items():
                        st.subheader(f"📖 {precon_name}")

                        for rec in recs:
                            priority_class = f"priority-{rec.priority}"
                            priority_emoji = {
                                'high': '🔴',
                                'medium': '🟡',
                                'low': '🟢'
                            }[rec.priority]

                            with st.container():
                                st.markdown(
                                    f'<div class="card-recommendation {priority_class}">',
                                    unsafe_allow_html=True
                                )

                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    st.markdown(f"### {priority_emoji} {rec.card_name}")
                                    st.markdown(f"**Score:** {rec.score:.1f}/100")
                                    st.markdown(f"**Motivi:**")
                                    for reason in rec.reasons:
                                        st.markdown(f"- {reason}")

                                    if rec.is_key_card:
                                        st.markdown("⭐ **CARTA CHIAVE DEL PRECON**")

                                with col2:
                                    card_details = rec.card_details
                                    if card_details.get('image_uri'):
                                        st.image(card_details['image_uri'], width=200)

                                    if card_details.get('scryfall_uri'):
                                        st.markdown(f"[🔗 Vedi su Scryfall]({card_details['scryfall_uri']})")

                                st.markdown('</div>', unsafe_allow_html=True)

                        st.divider()
                else:
                    st.info("ℹ️ Nessuna raccomandazione disponibile.")

    # TAB 4: Analisi Dettagliata
    with tab4:
        st.header("📊 Analisi Dettagliata")

        if not collection.cards:
            st.warning("⚠️ Aggiungi carte alla collezione per vedere l'analisi!")
        else:
            # Seleziona un precon per analisi approfondita
            all_precons = precon_db.get_all_precons()
            precon_names = [p.name for p in all_precons]

            selected_precon_name = st.selectbox(
                "Seleziona un precon da analizzare in dettaglio",
                options=precon_names
            )

            selected_precon = next(p for p in all_precons if p.name == selected_precon_name)

            if st.button("🔍 Analizza Lacune", key="analyze_btn"):
                with st.spinner("Analisi in corso..."):
                    card_names = [card.name for card in collection.cards]
                    gaps = recommender.analyze_collection_gaps(card_names, selected_precon)

                    st.subheader(f"Analisi per: {selected_precon.name}")

                    # Carte chiave mancanti
                    st.markdown("### 🔑 Carte Chiave Mancanti")
                    if gaps['missing_key_cards']:
                        for card in gaps['missing_key_cards']:
                            st.markdown(f"- ❌ {card}")
                    else:
                        st.success("✅ Hai tutte le carte chiave!")

                    # Copertura temi
                    st.markdown("### 🎨 Copertura Temi")
                    for theme, data in gaps['theme_coverage'].items():
                        coverage = data['coverage_percent']
                        supporting = data['supporting_cards']

                        st.progress(coverage / 100)
                        st.markdown(
                            f"**{theme.capitalize()}**: {coverage:.1f}% "
                            f"({supporting} carte nella collezione)"
                        )

                    # Top raccomandazioni
                    st.markdown("### ⭐ Top Raccomandazioni")
                    for rec in gaps['recommendations'][:5]:
                        st.markdown(
                            f"**{rec.card_name}** ({rec.priority.upper()}): "
                            f"{rec.score:.1f}/100"
                        )


if __name__ == '__main__':
    main()
