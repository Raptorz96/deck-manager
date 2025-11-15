"""
Magic: The Gathering Commander Deck Synergy Analyzer
Analizza la tua collezione e raccomanda carte basate su mazzi precon Commander
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field
import streamlit as st
import pandas as pd

# Configurazione del logging
logging.basicConfig(level=logging.WARNING)
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
    .card-recommendation {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .priority-high { border-left: 5px solid #ff4444; }
    .priority-medium { border-left: 5px solid #ffaa00; }
    .priority-low { border-left: 5px solid #44ff44; }
</style>
""", unsafe_allow_html=True)

# Costanti
DATA_FOLDER = Path(__file__).parent / 'data'
COLLECTION_FILE = DATA_FOLDER / 'collection.json'
DATA_FOLDER.mkdir(exist_ok=True)


@dataclass
class Card:
    name: str
    quantity: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "quantity": self.quantity}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        return cls(name=data["name"], quantity=data.get("quantity", 1))


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


@st.cache_resource
def get_services():
    """Carica i servizi una sola volta con caching"""
    try:
        from scryfall_api import get_scryfall_api
        from commander_precons import get_precon_database
        from synergy_analyzer import get_synergy_analyzer
        from recommendation_engine import get_recommendation_engine

        return {
            'scryfall': get_scryfall_api(),
            'precon_db': get_precon_database(),
            'analyzer': get_synergy_analyzer(),
            'recommender': get_recommendation_engine()
        }
    except Exception as e:
        st.error(f"Errore nel caricamento dei servizi: {e}")
        return None


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
    except Exception as e:
        logger.error(f"Errore nel caricamento: {e}")
        empty = Collection()
        save_collection(empty)
        return empty


def save_collection(collection: Collection) -> None:
    """Salva la collezione nel file JSON"""
    try:
        with open(COLLECTION_FILE, 'w', encoding='utf-8') as f:
            json.dump(collection.to_dict(), f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")


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
                card_name = parts[1].split('(')[0].strip()
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

    # Carica servizi con caching
    services = get_services()
    if not services:
        st.error("⚠️ Impossibile caricare i servizi. Ricarica la pagina.")
        return

    # Carica collezione
    if 'collection' not in st.session_state:
        st.session_state.collection = load_collection()

    collection = st.session_state.collection

    # Sidebar
    with st.sidebar:
        st.header("📚 Gestione Collezione")

        # Rinomina collezione
        with st.expander("✏️ Rinomina Collezione"):
            new_name = st.text_input("Nuovo nome", value=collection.name, key="rename_input")
            if st.button("Rinomina", key="rename_btn"):
                collection.name = new_name
                save_collection(collection)
                st.success("✅ Collezione rinominata!")

        # Import
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
                st.error(f"❌ Errore: {e}")

        # Aggiungi carta
        st.subheader("➕ Aggiungi Carta")
        with st.form("add_card_form"):
            card_name = st.text_input("Nome carta")
            quantity = st.number_input("Quantità", min_value=1, value=1, step=1)

            if st.form_submit_button("Aggiungi"):
                if card_name.strip():
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

        # Statistiche
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
            df = pd.DataFrame([
                {"Nome": card.name, "Quantità": card.quantity}
                for card in collection.cards
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("🗑️ Rimuovi Carte"):
                if collection.cards:
                    card_to_remove = st.selectbox(
                        "Seleziona carta",
                        options=[f"{c.name} (x{c.quantity})" for c in collection.cards]
                    )
                    if st.button("Rimuovi", key="remove_btn"):
                        idx = [f"{c.name} (x{c.quantity})" for c in collection.cards].index(card_to_remove)
                        collection.cards.pop(idx)
                        save_collection(collection)
                        st.success("✅ Carta rimossa!")
                        st.rerun()
        else:
            st.info("📭 La tua collezione è vuota. Aggiungi carte dalla sidebar!")

    # TAB 2: Precon Raccomandati
    with tab2:
        st.header("🎯 Mazzi Precon Commander Raccomandati")

        if not collection.cards:
            st.warning("⚠️ Aggiungi carte alla collezione per vedere i precon raccomandati!")
        else:
            if st.button("🔍 Analizza Sinergie", key="analyze_precons"):
                with st.spinner("Analizzo le sinergie..."):
                    try:
                        card_names = [card.name for card in collection.cards]
                        all_precons = services['precon_db'].get_all_precons()

                        recommended_precons = services['analyzer'].recommend_precons_for_cards(
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
                                    f"(Score: {stats['avg_score']:.1f}/100)",
                                    expanded=(idx == 1)
                                ):
                                    col1, col2 = st.columns([1, 1])

                                    with col1:
                                        st.markdown(f"**Commander:** {', '.join(precon.commanders)}")
                                        st.markdown(f"**Colori:** {', '.join(precon.color_identity) if precon.color_identity else 'Colorless'}")
                                        st.markdown(f"**Archetipo:** {precon.archetype}")
                                        st.markdown(f"**Temi:** {', '.join(precon.themes)}")

                                    with col2:
                                        st.metric("Carte Compatibili", stats['total_cards'])
                                        st.metric("Score Medio", f"{stats['avg_score']:.1f}/100")

                                    st.markdown("**🌟 Le tue migliori carte:**")
                                    for card_score in stats['top_cards'][:5]:
                                        st.markdown(f"- **{card_score.card_name}** ({card_score.score:.1f}/100)")
                        else:
                            st.warning("⚠️ Nessun precon compatibile trovato.")
                    except Exception as e:
                        st.error(f"❌ Errore nell'analisi: {e}")

    # TAB 3: Raccomandazioni (semplificato)
    with tab3:
        st.header("💎 Carte Raccomandate")

        if not collection.cards:
            st.warning("⚠️ Aggiungi carte alla collezione!")
        else:
            st.info("⚠️ Questa funzionalità richiede molte chiamate API. Usa il tab 'Analisi Dettagliata' per raccomandazioni specifiche.")

    # TAB 4: Analisi Dettagliata
    with tab4:
        st.header("📊 Analisi Dettagliata")

        if not collection.cards:
            st.warning("⚠️ Aggiungi carte alla collezione!")
        else:
            all_precons = services['precon_db'].get_all_precons()
            precon_names = [p.name for p in all_precons]

            selected_precon_name = st.selectbox(
                "Seleziona un precon",
                options=precon_names
            )

            selected_precon = next(p for p in all_precons if p.name == selected_precon_name)

            if st.button("🔍 Analizza Lacune", key="analyze_gaps"):
                with st.spinner("Analisi in corso..."):
                    try:
                        card_names = [card.name for card in collection.cards]
                        gaps = services['recommender'].analyze_collection_gaps(card_names, selected_precon)

                        st.subheader(f"Analisi: {selected_precon.name}")

                        st.markdown("### 🔑 Carte Chiave Mancanti")
                        if gaps['missing_key_cards']:
                            for card in gaps['missing_key_cards'][:10]:
                                st.markdown(f"- ❌ {card}")
                        else:
                            st.success("✅ Hai tutte le carte chiave!")

                        st.markdown("### 🎨 Copertura Temi")
                        for theme, data in gaps['theme_coverage'].items():
                            coverage = data['coverage_percent']
                            st.progress(coverage / 100)
                            st.markdown(f"**{theme.capitalize()}**: {coverage:.1f}%")

                    except Exception as e:
                        st.error(f"❌ Errore: {e}")


if __name__ == '__main__':
    main()
