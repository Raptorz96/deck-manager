import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

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

app = Flask(__name__)
# Usa variabili d'ambiente per la configurazione
app.secret_key = os.environ.get('SECRET_KEY', 'deck_manager_secret_key')  # Meglio usare variabili d'ambiente

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

@app.route('/')
def index():
    """Pagina principale che mostra il deck corrente."""
    deck = load_deck()
    
    # Calcola statistiche
    total_cards = sum(card.quantity for card in deck.cards)
    unique_cards = len(deck.cards)
    
    return render_template('index.html', 
                          deck=deck.to_dict(), 
                          total_cards=total_cards, 
                          unique_cards=unique_cards)

@app.route('/upload', methods=['POST'])
def upload_deck():
    """Gestisce l'upload di un file .deck."""
    if 'deck_file' not in request.files:
        flash('Nessun file selezionato', 'error')
        return redirect(url_for('index'))
    
    file = request.files['deck_file']
    
    if file.filename == '':
        flash('Nessun file selezionato', 'error')
        return redirect(url_for('index'))
    
    # Verifica la dimensione del file (max 5MB)
    if len(file.read()) > 5 * 1024 * 1024:
        flash('Il file è troppo grande (max 5MB)', 'error')
        return redirect(url_for('index'))
    
    # Riavvolgi il file per poterlo leggere di nuovo
    file.seek(0)
    
    if file and file.filename.endswith('.deck'):
        try:
            file_content = file.read().decode('utf-8')
            deck = import_deck_from_file(file_content)
            save_deck(deck)
            flash('Deck importato con successo!', 'success')
        except UnicodeDecodeError:
            flash('Il file non è in formato UTF-8 valido', 'error')
        except Exception as e:
            logger.error(f"Errore durante l'importazione del deck: {str(e)}")
            flash(f'Errore durante l\'importazione: {str(e)}', 'error')
    else:
        flash('Il file deve avere estensione .deck', 'error')
    
    return redirect(url_for('index'))

@app.route('/download')
def download_deck():
    """Scarica il deck come file .deck."""
    deck = load_deck()
    content = export_deck_to_file(deck)
    
    return jsonify({
        "content": content,
        "filename": f"{deck.name.replace(' ', '_')}.deck"
    })

@app.route('/add_card', methods=['POST'])
def add_card():
    """Aggiunge una carta al deck."""
    deck = load_deck()
    
    name = request.form.get('card_name', '').strip()
    card_type = request.form.get('card_type', '').strip()
    
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity <= 0:
            raise ValueError("La quantità deve essere positiva")
    except ValueError:
        flash('La quantità deve essere un numero positivo', 'error')
        return redirect(url_for('index'))
    
    if not name:
        flash('Il nome della carta non può essere vuoto', 'error')
        return redirect(url_for('index'))
    
    # Controlla se la carta esiste già
    for card in deck.cards:
        if card.name.lower() == name.lower() and card.type.lower() == card_type.lower():
            card.quantity += quantity
            save_deck(deck)
            flash(f'Aggiunte {quantity} copie di {name}', 'success')
            return redirect(url_for('index'))
    
    # Aggiungi la nuova carta
    deck.cards.append(Card(
        name=name,
        type=card_type,
        quantity=quantity
    ))
    
    save_deck(deck)
    flash(f'Aggiunte {quantity} copie di {name}', 'success')
    return redirect(url_for('index'))

@app.route('/remove_card/<int:index>', methods=['POST'])
def remove_card(index: int):
    """Rimuove una carta dal deck."""
    deck = load_deck()
    
    if 0 <= index < len(deck.cards):
        card = deck.cards[index]
        try:
            quantity = int(request.form.get('quantity', 1))
            if quantity <= 0:
                raise ValueError("La quantità deve essere positiva")
        except ValueError:
            flash('La quantità deve essere un numero positivo', 'error')
            return redirect(url_for('index'))
        
        if quantity >= card.quantity:
            # Rimuovi completamente la carta
            removed_card = deck.cards.pop(index)
            flash(f'Rimossa {removed_card.name}', 'success')
        else:
            # Riduci la quantità
            card.quantity -= quantity
            flash(f'Rimosse {quantity} copie di {card.name}', 'success')
        
        save_deck(deck)
    else:
        flash('Carta non trovata', 'error')
    
    return redirect(url_for('index'))

@app.route('/rename_deck', methods=['POST'])
def rename_deck():
    """Rinomina il deck."""
    deck = load_deck()
    
    new_name = request.form.get('deck_name', '').strip()
    if new_name:
        deck.name = new_name
        save_deck(deck)
        flash('Deck rinominato con successo', 'success')
    else:
        flash('Il nome del deck non può essere vuoto', 'error')
    
    return redirect(url_for('index'))

@app.route('/clear_deck', methods=['POST'])
def clear_deck():
    """Svuota completamente il deck."""
    deck = load_deck()
    deck.cards = []
    save_deck(deck)
    flash('Deck svuotato con successo', 'success')
    return redirect(url_for('index'))

# Gestione degli errori
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Pagina non trovata"), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Errore del server: {str(e)}")
    return render_template('index.html', error="Errore interno del server"), 500

if __name__ == '__main__':
    # Usa variabili d'ambiente per configurare la modalità debug
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    # Usa porta 5001 per evitare conflitti con altre applicazioni
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=debug_mode, port=port)