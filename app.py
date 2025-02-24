import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = 'deck_manager_secret_key'  # Necessario per i messaggi flash

# Costanti
DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DECK_FILE = os.path.join(DATA_FOLDER, 'deck.json')

# Assicurati che la cartella data esista
os.makedirs(DATA_FOLDER, exist_ok=True)

# Struttura di un deck vuoto
EMPTY_DECK = {
    "name": "Nuovo Deck",
    "cards": []
}

def load_deck():
    """Carica il deck dal file JSON."""
    if not os.path.exists(DECK_FILE):
        # Se il file non esiste, crea un deck vuoto
        with open(DECK_FILE, 'w') as f:
            json.dump(EMPTY_DECK, f, indent=4)
        return EMPTY_DECK.copy()
    
    try:
        with open(DECK_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Se il file è danneggiato, crea un nuovo deck
        with open(DECK_FILE, 'w') as f:
            json.dump(EMPTY_DECK, f, indent=4)
        return EMPTY_DECK.copy()

def save_deck(deck):
    """Salva il deck nel file JSON."""
    with open(DECK_FILE, 'w') as f:
        json.dump(deck, f, indent=4)

def import_deck_from_file(file_content):
    """Importa un deck da un file .deck."""
    deck = {
        "name": "Deck Importato",
        "cards": []
    }
    
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
                
                deck["cards"].append({
                    "name": card_name,
                    "type": card_type,
                    "quantity": quantity
                })
            except ValueError:
                # Se la prima parte non è un numero, considera l'intera riga come nome
                deck["cards"].append({
                    "name": line,
                    "type": "",
                    "quantity": 1
                })
        else:
            # Se non c'è uno spazio, considerala come una singola carta
            deck["cards"].append({
                "name": line,
                "type": "",
                "quantity": 1
            })
    
    return deck

def export_deck_to_file(deck):
    """Esporta un deck nel formato .deck."""
    content = f"# {deck['name']}\n\n"
    
    for card in deck["cards"]:
        name = card["name"]
        card_type = card["type"]
        quantity = card["quantity"]
        
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
    total_cards = sum(card["quantity"] for card in deck["cards"])
    unique_cards = len(deck["cards"])
    
    return render_template('index.html', 
                          deck=deck, 
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
    
    if file and file.filename.endswith('.deck'):
        file_content = file.read().decode('utf-8')
        deck = import_deck_from_file(file_content)
        save_deck(deck)
        flash('Deck importato con successo!', 'success')
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
        "filename": f"{deck['name'].replace(' ', '_')}.deck"
    })

@app.route('/add_card', methods=['POST'])
def add_card():
    """Aggiunge una carta al deck."""
    deck = load_deck()
    
    name = request.form.get('card_name', '').strip()
    card_type = request.form.get('card_type', '').strip()
    quantity = int(request.form.get('quantity', 1))
    
    if not name:
        flash('Il nome della carta non può essere vuoto', 'error')
        return redirect(url_for('index'))
    
    # Controlla se la carta esiste già
    for card in deck["cards"]:
        if card["name"].lower() == name.lower() and card["type"].lower() == card_type.lower():
            card["quantity"] += quantity
            save_deck(deck)
            flash(f'Aggiunte {quantity} copie di {name}', 'success')
            return redirect(url_for('index'))
    
    # Aggiungi la nuova carta
    deck["cards"].append({
        "name": name,
        "type": card_type,
        "quantity": quantity
    })
    
    save_deck(deck)
    flash(f'Aggiunte {quantity} copie di {name}', 'success')
    return redirect(url_for('index'))

@app.route('/remove_card/<int:index>', methods=['POST'])
def remove_card(index):
    """Rimuove una carta dal deck."""
    deck = load_deck()
    
    if 0 <= index < len(deck["cards"]):
        card = deck["cards"][index]
        quantity = int(request.form.get('quantity', 1))
        
        if quantity >= card["quantity"]:
            # Rimuovi completamente la carta
            removed_card = deck["cards"].pop(index)
            flash(f'Rimossa {removed_card["name"]}', 'success')
        else:
            # Riduci la quantità
            card["quantity"] -= quantity
            flash(f'Rimosse {quantity} copie di {card["name"]}', 'success')
        
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
        deck["name"] = new_name
        save_deck(deck)
        flash('Deck rinominato con successo', 'success')
    else:
        flash('Il nome del deck non può essere vuoto', 'error')
    
    return redirect(url_for('index'))

@app.route('/clear_deck', methods=['POST'])
def clear_deck():
    """Svuota completamente il deck."""
    deck = load_deck()
    deck["cards"] = []
    save_deck(deck)
    flash('Deck svuotato con successo', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)