import random
import logging
import secrets
import threading
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Cookie, Response
from fastapi.staticfiles import StaticFiles
from silnik_gry import Mecz, FazaGry, Karta, Kontrakt

# --- Konfiguracja Logowania (bez zmian) ---
logger = logging.getLogger('szesc_szesc_logger')
if not logger.handlers:
    handler = logging.FileHandler('gra.log', mode='w', encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

app = FastAPI()

# --- Przechowywanie gier i blokada (bez zmian) ---
aktywne_gry: Dict[str, Mecz] = {}
game_lock = threading.Lock()

def get_or_create_mecz(session_id: Optional[str], response: Response) -> Mecz:
    """Pobiera mecz dla danego ID sesji lub tworzy nowy, jeśli nie istnieje."""
    if not session_id or session_id not in aktywne_gry:
        session_id = secrets.token_hex(16)
        logger.info(f"Tworzenie nowej sesji i gry o ID: {session_id}")
        mecz = Mecz(nazwy_graczy=["Ty", "Lewy", "Partner", "Prawy"])
        mecz.rozpocznij_mecz()
        aktywne_gry[session_id] = mecz
        response.set_cookie(key="session_id", value=session_id, httponly=True)
    return aktywne_gry[session_id]

def uruchom_ture_ai(mecz: Mecz):
    """Logika AI (bez zmian)"""
    rozdanie = mecz.rozdanie
    gracz_czlowieka = mecz.gracze[0]
    for _ in range(3):
        if not rozdanie or rozdanie.rozdanie_zakonczone or rozdanie.kolej_gracza_idx is None: break
        aktualny_gracz = rozdanie.gracze[rozdanie.kolej_gracza_idx]
        if aktualny_gracz == gracz_czlowieka: break
        if rozdanie.faza == FazaGry.ROZGRYWKA:
            mozliwe_karty = rozdanie.get_legalne_karty(aktualny_gracz)
            if mozliwe_karty:
                wybrana_karta = random.choice(mozliwe_karty)
                rozdanie.zagraj_karte(aktualny_gracz, wybrana_karta)
        else:
            mozliwe_akcje = rozdanie.get_mozliwe_akcje(aktualny_gracz)
            if mozliwe_akcje:
                wybrana_akcja = random.choice(mozliwe_akcje)
                rozdanie.wykonaj_akcje(aktualny_gracz, wybrana_akcja)
            else: break

@app.get("/stan_gry")
def get_stan_gry(response: Response, session_id: Optional[str] = Cookie(None)):
    logger.info(f"-> API /stan_gry dla sesji: {session_id or 'Nowa sesja'}")
    with game_lock:
        aktualny_mecz = get_or_create_mecz(session_id, response)
        uruchom_ture_ai(aktualny_mecz)
        
        rozdanie = aktualny_mecz.rozdanie
        if rozdanie and rozdanie.rozdanie_zakonczone and not aktualny_mecz.zwyciezca_meczu:
            zwyciezca, punkty, mnoznik = rozdanie.rozlicz_rozdanie()
            logger.info(f"--- KONIEC ROZDANIA --- Wygrywa: {zwyciezca.nazwa} (+{punkty} pkt)")
            aktualny_mecz.sprawdz_koniec_meczu()
            if not aktualny_mecz.zwyciezca_meczu:
                aktualny_mecz.przygotuj_nastepne_rozdanie()

        gracz_czlowieka = aktualny_mecz.gracze[0]
        mozliwe_akcje_dla_frontendu = []
        legalne_karty_dla_frontendu = []

        is_human_turn = rozdanie and rozdanie.kolej_gracza_idx is not None and rozdanie.gracze[rozdanie.kolej_gracza_idx] == gracz_czlowieka

        if is_human_turn:
            # ✅ === POCZĄTEK ZMIANY ===
            if rozdanie.faza == FazaGry.ROZGRYWKA:
                # W fazie rozgrywki pobieramy legalne karty
                legalne_karty = rozdanie.get_legalne_karty(gracz_czlowieka)
                legalne_karty_dla_frontendu = [str(k) for k in legalne_karty]
            else:
                # W innych fazach (np. licytacja) pobieramy akcje
                akcje_z_silnika = rozdanie.get_mozliwe_akcje(gracz_czlowieka)
                for idx, akcja in enumerate(akcje_z_silnika):
                    opis = akcja['typ'].replace('_', ' ').capitalize()
                    if akcja['typ'] == 'deklaracja':
                        opis = f"Graj {akcja['kontrakt'].name.capitalize()} w {akcja['atut'].name.capitalize()}" if akcja.get('atut') else f"Graj {akcja['kontrakt'].name.capitalize()}"
                    
                    mozliwe_akcje_dla_frontendu.append({
                        "url": f"/wykonaj_akcje/{idx}",
                        "opis": opis
                    })
            # ✅ === KONIEC ZMIANY ===

        return {
             "gracze": [g.nazwa for g in aktualny_mecz.gracze],
             "ilosc_kart_graczy": {g.nazwa: len(g.reka) for g in aktualny_mecz.rozdanie.gracze},
             "faza_gry": aktualny_mecz.rozdanie.faza.name,
             "kolej_na": aktualny_mecz.rozdanie.gracze[aktualny_mecz.rozdanie.kolej_gracza_idx].nazwa if aktualny_mecz.rozdanie.kolej_gracza_idx is not None else "",
             "reka_gracza": [{"nazwa": str(k), "nazwa_pliku": k.nazwa_pliku} for k in sorted(aktualny_mecz.gracze[0].reka, key=lambda k: (k.kolor.name, k.ranga.value))],
             "karty_na_stole": [{"gracz": g.nazwa, "karta": str(k), "nazwa_pliku": k.nazwa_pliku} for g, k in aktualny_mecz.rozdanie.aktualna_lewa],
             "kontrakt": {"typ": aktualny_mecz.rozdanie.kontrakt.name if aktualny_mecz.rozdanie.kontrakt else None, "atut": aktualny_mecz.rozdanie.atut.name if aktualny_mecz.rozdanie.atut else None, "gracz": aktualny_mecz.rozdanie.grajacy.nazwa if aktualny_mecz.rozdanie.grajacy else None},
             "punkty_w_rozdaniu": aktualny_mecz.rozdanie.punkty_w_rozdaniu,
             "ogolne_punkty_meczu": {"My": aktualny_mecz.druzyna_a.punkty_meczu, "Oni": aktualny_mecz.druzyna_b.punkty_meczu},
             "mozliwe_akcje": mozliwe_akcje_dla_frontendu,
             "legalne_karty_nazwy": legalne_karty_dla_frontendu, # ✅ NOWE POLE DLA FRONTENDU
             "historia_akcji": aktualny_mecz.rozdanie.historia_akcji,
             "aktualna_stawka": aktualny_mecz.rozdanie.get_aktualna_stawka(),
             "rozdajacy_idx": aktualny_mecz.rozdanie.rozdajacy_idx,
             "koniec_meczu": bool(aktualny_mecz.zwyciezca_meczu),
             "zwyciezca": aktualny_mecz.zwyciezca_meczu.nazwa if aktualny_mecz.zwyciezca_meczu else None,
             "wynik": f"My {aktualny_mecz.druzyna_a.punkty_meczu} - {aktualny_mecz.druzyna_b.punkty_meczu} Oni" if aktualny_mecz.zwyciezca_meczu else ""
        }

# Reszta pliku app.py pozostaje bez zmian
@app.get("/wykonaj_akcje/{akcja_idx}")
def wykonaj_akcje_gracza(akcja_idx: int, response: Response, session_id: Optional[str] = Cookie(None)):
    logger.info(f"-> API /wykonaj_akcje/{akcja_idx} dla sesji: {session_id}")
    with game_lock:
        aktualny_mecz = get_or_create_mecz(session_id, response)
        gracz_czlowieka = aktualny_mecz.gracze[0]
        rozdanie = aktualny_mecz.rozdanie
        if rozdanie and rozdanie.kolej_gracza_idx is not None and rozdanie.gracze[rozdanie.kolej_gracza_idx] == gracz_czlowieka:
            mozliwe_akcje = rozdanie.get_mozliwe_akcje(gracz_czlowieka)
            if 0 <= akcja_idx < len(mozliwe_akcje):
                wybrana_akcja = mozliwe_akcje[akcja_idx]
                rozdanie.wykonaj_akcje(gracz_czlowieka, wybrana_akcja)
    return {"status": "ok"}

@app.get("/zagraj_karte/{karta_str}")
def zagraj_karte_gracza(karta_str: str, response: Response, session_id: Optional[str] = Cookie(None)):
    logger.info(f"-> API /zagraj_karte/{karta_str} dla sesji: {session_id}")
    with game_lock:
        aktualny_mecz = get_or_create_mecz(session_id, response)
        gracz_czlowieka = aktualny_mecz.gracze[0]
        rozdanie = aktualny_mecz.rozdanie
        if rozdanie and rozdanie.kolej_gracza_idx is not None and rozdanie.gracze[rozdanie.kolej_gracza_idx] == gracz_czlowieka:
            legalne_karty = rozdanie.get_legalne_karty(gracz_czlowieka)
            # Używamy `urllib.parse.unquote` do dekodowania nazwy karty, jeśli zawiera specjalne znaki (choć w tym przypadku nie powinna)
            from urllib.parse import unquote
            karta_str_decoded = unquote(karta_str)
            wybrana_karta = next((k for k in legalne_karty if str(k) == karta_str_decoded), None)
            if wybrana_karta:
                rozdanie.zagraj_karte(gracz_czlowieka, wybrana_karta)
            else:
                logger.error(f"Nielegalny ruch! Próba zagrania {karta_str_decoded}. Legalne karty: {[str(k) for k in legalne_karty]}")
                raise HTTPException(status_code=400, detail="Nielegalny ruch lub zła karta")
    return {"status": "ok"}

@app.get("/nowy_mecz")
def nowy_mecz_endpoint(response: Response, session_id: Optional[str] = Cookie(None)):
    logger.info(f"-> API /nowy_mecz dla sesji: {session_id}")
    with game_lock:
        if session_id and session_id in aktywne_gry:
            del aktywne_gry[session_id]
            logger.info(f"Resetowanie gry dla sesji: {session_id}")
        get_or_create_mecz(None, response)
    return {"status": "nowy mecz rozpoczęty"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")