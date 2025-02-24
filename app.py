import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import streamlit as st
import pandas as pd

# Configurazione del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definizione delle strutture dati
@dataclass
class Card:
    name: str
    type: str = ""
    quantity: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "quantity": self.quantity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        return cls(
            name=data["name"],
            type=data.get("type", ""),
            quantity=data.get("quantity", 1)
        )

@dataclass
class Deck:
    name: str = "Nuovo Deck"
    cards: List[Card] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "cards": [card.to_dict() for card in self.cards]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deck':
        return cls(
            name=data["name"],
            cards=[Card.from_dict(card) for card in data.get("cards", [])]
        )

# Costanti
DATA_FOLDER = Path(__file__).parent / 'data'
DECK_FILE = DATA_FOLDER / 'deck.json'

# Assicurati che la cartella data esista
DATA_FOLDER.mkdir(exist_ok=True)

# Struttura di un deck vuoto
EMPTY_DECK = Deck()

def load_deck() -> Deck:
    """Carica il deck dal file JSON."""
    if not DECK_FILE.exists():
        # Se il file non esiste, crea un deck vuoto
        with open(DECK_FILE, 'w') as f:
            json.dump(EMPTY_DECK.to_dict(), f, indent=4)
        return EMPTY_DECK
    
    try:
        with open(DECK_FILE, 'r') as f:
            data = json.load(f)
        return Deck.from_dict(data)
    except json.JSONDecodeError:
        # Se il file è danneggiato, crea un nuovo deck
        logger.warning(f"File JSON danneggiato. Creazione di un nuovo deck.")
        with open(DECK_FILE, 'w') as f:
            json.dump(EMPTY_DECK.to_dict(), f, indent=4)
        return EMPTY_DECK

def save_deck(deck: Deck) -> None:
    """Salva il deck nel file JSON."""
    with open(DECK_FILE, 'w') as f:
        json.dump(deck.to_dict(), f, indent=4)

def import_deck_from_file(file_content: str) -> Deck:
    """Importa un deck da un file .deck."""
    deck = Deck(name="Deck Importato")
    
    # Analizza il file .deck riga per riga
    lines = file_content.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):  # Ignora linee vuote e commenti
            continue
        
        # Formato tipico: "2 Carta Esempio (SET123)"
        parts = line.split(' ', 1)
        if len(parts) == 2:
            try:
                quantity = int(parts[0])
                card_name = parts[1]
                
                # Estrai il set se presente
                card_type = ""
                if '(' in card_name and ')' in card_name:
                    end_idx = card_name.rfind('(')
                    card_type = card_name[end_idx:].strip()
                    card_name = card_name[:end_idx].strip()
                
                deck.cards.append(Card(
                    name=card_name,
                    type=card_type,
                    quantity=quantity
                ))
            except ValueError:
                # Se la prima parte non è un numero, considera l'intera riga come nome
                deck.cards.append(Card(
                    name=line,
                    type="",
                    quantity=1
                ))
        else:
            # Se non c'è uno spazio, considerala come una singola carta
            deck.cards.append(Card(
                name=line,
                type="",
                quantity=1
            ))
    
    return deck

def export_deck_to_file(deck: Deck) -> str:
    """Esporta un deck nel formato .deck."""
    content = f"# {deck.name}\n\n"
    
    for card in deck.cards:
        name = card.name
        card_type = card.type
        quantity = card.quantity
        
        if card_type:
            content += f"{quantity} {name} {card_type}\n"
        else:
            content += f"{quantity} {name}\n"
    
    return content

def main():
    st.set_page_config(
        page_title="Deck Manager",
        page_icon="🃏",
        layout="wide"
    )
    
    st.title("Deck Manager")
    
    # Carica il deck
    deck = load_deck()
    
    # Sidebar
    with st.sidebar:
        st.header("Menu")
        
        # Rinomina deck
        with st.form("rename_deck_form"):
            st.subheader("Rinomina Deck")
            new_name = st.text_input("Nuovo nome", value=deck.name)
            rename_submit = st.form_submit_button("Rinomina")
            
            if rename_submit and new_name.strip():
                deck.name = new_name.strip()
                save_deck(deck)
                st.success("Deck rinominato con successo")
                st.rerun()
        
        # Upload deck
        st.subheader("Importa Deck")
        uploaded_file = st.file_uploader("Carica un file .deck", type=["deck"])
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.getvalue().decode('utf-8')
                deck = import_deck_from_file(file_content)
                save_deck(deck)
                st.success("Deck importato con successo!")
                st.rerun()
            except UnicodeDecodeError:
                st.error("Il file non è in formato UTF-8 valido")
            except Exception as e:
                logger.error(f"Errore durante l'importazione del deck: {str(e)}")
                st.error(f"Errore durante l'importazione: {str(e)}")
        
        # Download deck
        st.subheader("Esporta Deck")
        content = export_deck_to_file(deck)
        st.download_button(
            label="Scarica deck",
            data=content,
            file_name=f"{deck.name.replace(' ', '_')}.deck",
            mime="text/plain"
        )
        
        # Svuota deck
        if st.button("Svuota Deck"):
            if st.session_state.get('confirm_clear', False):
                deck.cards = []
                save_deck(deck)
                st.success("Deck svuotato con successo")
                st.session_state.confirm_clear = False
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Sei sicuro di voler svuotare il deck? Clicca di nuovo per confermare.")
    
    # Contenuto principale
    st.header(f"Deck: {deck.name}")
    
    # Statistiche
    total_cards = sum(card.quantity for card in deck.cards)
    unique_cards = len(deck.cards)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Carte totali", total_cards)
    with col2:
        st.metric("Carte uniche", unique_cards)
    
    # Aggiungi carta
    with st.form("add_card_form"):
        st.subheader("Aggiungi Carta")
        
        add_col1, add_col2, add_col3 = st.columns([3, 2, 1])
        
        with add_col1:
            card_name = st.text_input("Nome della carta")
        
        with add_col2:
            card_type = st.text_input("Tipo (Set)")
        
        with add_col3:
            quantity = st.number_input("Quantità", min_value=1, value=1, step=1)
        
        add_card_submit = st.form_submit_button("Aggiungi")
        
        if add_card_submit:
            if not card_name.strip():
                st.error("Il nome della carta non può essere vuoto")
            else:
                # Controlla se la carta esiste già
                found = False
                for card in deck.cards:
                    if card.name.lower() == card_name.lower() and card.type.lower() == card_type.lower():
                        card.quantity += quantity
                        found = True
                        save_deck(deck)
                        st.success(f"Aggiunte {quantity} copie di {card_name}")
                        break
                
                if not found:
                    # Aggiungi la nuova carta
                    deck.cards.append(Card(
                        name=card_name,
                        type=card_type,
                        quantity=quantity
                    ))
                    save_deck(deck)
                    st.success(f"Aggiunte {quantity} copie di {card_name}")
                
                st.rerun()
    
    # Tabella delle carte
    if deck.cards:
        st.subheader("Carte nel deck")
        
        cards_data = [{
            "Indice": i,
            "Nome": card.name,
            "Tipo": card.type,
            "Quantità": card.quantity
        } for i, card in enumerate(deck.cards)]
        
        df = pd.DataFrame(cards_data)
        
        # Modifica la tabella per aggiungere il bottone di rimozione
        st.dataframe(
            df.drop(columns=["Indice"]),
            hide_index=True
        )
        
        # Form per rimuovere carte
        with st.form("remove_card_form"):
            st.subheader("Rimuovi Carta")
            
            remove_col1, remove_col2 = st.columns([3, 1])
            
            with remove_col1:
                card_options = [f"{card.name} {card.type}" for card in deck.cards]
                selected_card = st.selectbox("Seleziona una carta", options=card_options)
            
            with remove_col2:
                card_index = card_options.index(selected_card)
                max_quantity = deck.cards[card_index].quantity
                remove_quantity = st.number_input("Quantità da rimuovere", min_value=1, max_value=max_quantity, value=1, step=1)
            
            remove_submit = st.form_submit_button("Rimuovi")
            
            if remove_submit:
                if 0 <= card_index < len(deck.cards):
                    card = deck.cards[card_index]
                    if remove_quantity >= card.quantity:
                        # Rimuovi completamente la carta
                        removed_card = deck.cards.pop(card_index)
                        st.success(f"Rimossa {removed_card.name}")
                    else:
                        # Riduci la quantità
                        card.quantity -= remove_quantity
                        st.success(f"Rimosse {remove_quantity} copie di {card.name}")
                    
                    save_deck(deck)
                    st.rerun()
    else:
        st.info("Il deck è vuoto. Aggiungi delle carte!")

if __name__ == '__main__':
    main()