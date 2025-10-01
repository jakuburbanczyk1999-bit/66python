import uuid
from flask import Flask, jsonify, request, abort
# Import z prawidłowej nazwy pliku 'silnik_gry'
from silnik_gry import Gracz, Druzyna, Rozdanie, FazaGry, Karta, Ranga, Kolor, Kontrakt

app = Flask(__name__)

# Tymczasowe przechowywanie gier w pamięci serwera.
games = {}

def serialize_card(card):
    """Konwertuje obiekt Karty do formatu słownika."""
    if not card:
        return None
    return {'rank': card.ranga.name, 'suit': card.kolor.name}

def serialize_game_state(rozdanie, game_id):
    """
    Konwertuje obiekt Rozdanie z silnika na format JSON (słownik),
    który może być wysłany do interfejsu użytkownika.
    """
    if not rozdanie:
        return None

    current_player_obj = rozdanie.gracze[rozdanie.kolej_gracza_idx]
    
    # POPRAWKA: Prawidłowa inicjalizacja pustej listy
    possible_actions =
    if rozdanie.faza == FazaGry.ROZGRYWKA:
        possible_actions = [serialize_card(k) for k in rozdanie.get_legalne_karty(current_player_obj)]
    else:
        raw_actions = rozdanie.get_mozliwe_akcje(current_player_obj)
        for action in raw_actions:
            serialized_action = {}
            for key, value in action.items():
                if isinstance(value, (Kontrakt, Kolor)):
                    serialized_action[key] = value.name if value else None
                else:
                    serialized_action[key] = value
            possible_actions.append(serialized_action)

    player_hands = {
        p.nazwa: sorted([serialize_card(k) for k in p.reka], key=lambda x: (x['suit'], x['rank'])) for p in rozdanie.gracze
    }

    return {
        "game_id": game_id,
        "phase": rozdanie.faza.name,
        "players": [p.nazwa for p in rozdanie.gracze],
        "dealer": rozdanie.gracze[rozdanie.rozdajacy_idx].nazwa,
        "turn_of_player": current_player_obj.nazwa,
        "contract": {
            "player": rozdanie.grajacy.nazwa if rozdanie.grajacy else None,
            "type": rozdanie.kontrakt.name if rozdanie.kontrakt else None,
            "suit": rozdanie.atut.name if rozdanie.atut else None,
            "multiplier": rozdanie.mnoznik_lufy
        },
        "scores": {
            d.nazwa: d.punkty_meczu for d in rozdanie.druzyny
        },
        "hand_scores": rozdanie.punkty_w_rozdaniu,
        "current_trick": [(p.nazwa, serialize_card(k)) for p, k in rozdanie.aktualna_lewa],
        "player_hands": player_hands,
        "legal_actions_for_current_player": possible_actions
    }

@app.route('/game/new', methods=)
def create_new_game():
    """Tworzy nową instancję gry i zwraca jej unikalny identyfikator."""
    gracze = [Gracz("Gracz1"), Gracz("Gracz2"), Gracz("Gracz3"), Gracz("Gracz4")]
    druzyna_a = Druzyna("My")
    druzyna_b = Druzyna("Oni")
    druzyna_a.dodaj_gracza(gracze)
    druzyna_a.dodaj_gracza(gracze[1])
    druzyna_b.dodaj_gracza(gracze[2])
    druzyna_b.dodaj_gracza(gracze[3])
    druzyna_a.przeciwnicy = druzyna_b
    druzyna_b.przeciwnicy = druzyna_a

    rozdanie = Rozdanie(gracze=gracze, druzyny=[druzyna_a, druzyna_b], rozdajacy_idx=0)
    rozdanie.rozpocznij_nowe_rozdanie()

    game_id = str(uuid.uuid4())
    games[game_id] = rozdanie

    return jsonify(serialize_game_state(rozdanie, game_id))

@app.route('/game/<game_id>/state', methods=)
def get_game_state(game_id):
    """Zwraca pełny, aktualny stan gry o podanym ID."""
    rozdanie = games.get(game_id)
    if not rozdanie:
        abort(404, description="Gra o podanym ID nie została znaleziona.")
    
    return jsonify(serialize_game_state(rozdanie, game_id))

@app.route('/game/<game_id>/move', methods=)
def make_move(game_id):
    """Przetwarza ruch wykonany przez gracza."""
    rozdanie = games.get(game_id)
    if not rozdanie:
        abort(404, description="Gra o podanym ID nie została znaleziona.")

    data = request.get_json()
    if not data or 'player_name' not in data or 'action' not in data:
        abort(400, description="Nieprawidłowe zapytanie. Wymagane pola: 'player_name' i 'action'.")

    player_name = data['player_name']
    action_data = data['action']

    gracz = next((p for p in rozdanie.gracze if p.nazwa == player_name), None)
    if not gracz:
        abort(404, description=f"Gracz o nazwie '{player_name}' nie został znaleziony w tej grze.")

    if gracz!= rozdanie.gracze[rozdanie.kolej_gracza_idx]:
        abort(403, description="To nie jest kolej tego gracza.")

    try:
        if rozdanie.faza == FazaGry.ROZGRYWKA:
            card_rank = Ranga[action_data['rank']]
            card_suit = Kolor[action_data['suit']]
            karta_do_zagrania = next((k for k in gracz.reka if k.ranga == card_rank and k.kolor == card_suit), None)
            
            if karta_do_zagrania is None:
                 abort(400, description="Gracz nie posiada takiej karty na ręce.")

            rozdanie.zagraj_karte(gracz, karta_do_zagrania)
        else:
            if 'kontrakt' in action_data and action_data['kontrakt'] is not None:
                action_data['kontrakt'] = Kontrakt[action_data['kontrakt']]
            if 'atut' in action_data and action_data['atut'] is not None:
                action_data['atut'] = Kolor[action_data['atut']]
            
            rozdanie.wykonaj_akcje(gracz, action_data)
    except (KeyError, AttributeError, TypeError) as e:
        abort(400, description=f"Błąd przetwarzania akcji: {e}. Otrzymane dane: {action_data}")

    return jsonify(serialize_game_state(rozdanie, game_id))


if __name__ == '__main__':
    app.run(debug=True)