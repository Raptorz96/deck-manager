# Deck Manager

Una semplice applicazione web per gestire mazzi di carte.

## Funzionalità

- Visualizzazione del contenuto del mazzo con nome, tipo e quantità delle carte
- Importazione di mazzi da file .deck
- Esportazione del mazzo in formato .deck
- Aggiunta e rimozione di carte
- Visualizzazione di statistiche sul mazzo

## Installazione

1. Clona il repository o scarica i file
2. Crea un ambiente virtuale Python (opzionale ma consigliato)
3. Installa le dipendenze con `pip install -r requirements.txt`
4. Avvia l'applicazione con `python app.py`
5. Apri il browser all'indirizzo `http://localhost:5000`

## Formato del file .deck

Il formato .deck è un semplice formato di testo dove ogni riga rappresenta una carta nel formato:

```
<quantità> <nome carta> (<tipo>)
```

Esempio:
```
4 Carta Potente (Set1)
3 Carta Media (Set1)
2 Carta Rara (Set2)
4 Carta Comune (Set3)
1 Carta Leggendaria (Set4)
```

Le righe che iniziano con `#` sono considerate commenti e ignorate.

## Tecnologie utilizzate

- Flask (framework web)
- Bootstrap 5 (frontend)
- Font Awesome (icone)
- JSON (per la memorizzazione dei dati)