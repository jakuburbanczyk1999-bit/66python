import random
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from silnik_gry import Mecz, FazaGry, Karta

# --- Konfiguracja Logowania ---
logger = logging.getLogger('szesc_szesc_logger')
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.FileHandler('gra.log', mode='w', encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
# --- Koniec Konfiguracji ---

app = FastAPI()
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# --- Główna Logika Gry ---

aktualny_mecz = Mecz(nazwy_graczy=["Jakub", "Przeciwnik1", "Nasz", "Przeciwnik2"])
aktualny_mecz.rozpocznij_mecz()



def formatuj_akcje_json(akcje: list[dict], akcja_url_prefix: str) -> list[dict]:
    formatowane = []
    for i, akcja in enumerate(akcje):
        opis = "Nieznana akcja"
        if akcja.get('kontrakt'):
            atut_str = f" ({akcja['atut'].name})" if akcja.get('atut') else ""
            typ_akcji = akcja['typ'].replace('_', ' ').capitalize()
            if typ_akcji == 'Deklaracja': typ_akcji = akcja['kontrakt'].name
            elif typ_akcji == 'Przebicie': typ_akcji = f"Przebij na {akcja['kontrakt'].name}"
            elif typ_akcji == 'Zmiana kontraktu': typ_akcji = f"Zmień na {akcja['kontrakt'].name}"
            opis = f"{typ_akcji}{atut_str}"
        else:
            opis = akcja['typ'].replace('_', ' ').capitalize()
        
        formatowane.append({"opis": opis, "url": f"/{akcja_url_prefix}/{i}"})
    return formatowane

def formatuj_karty_json(karty: list[Karta], akcja_url_prefix: str) -> list[dict]:
    formatowane = []
    posortowane_karty = sorted(karty, key=lambda k: (k.kolor.name, k.ranga.value))
    for i, karta in enumerate(posortowane_karty):
        formatowane.append({"opis": str(karta), "url": f"/{akcja_url_prefix}/{i}"})
    return formatowane

def uruchom_ture_ai(mecz: Mecz):
    rozdanie = mecz.rozdanie
    gracz_czlowieka = mecz.gracze[0]
    
    for _ in range(4): 
        if not rozdanie or rozdanie.rozdanie_zakonczone: break
        
        aktualny_gracz = rozdanie.gracze[rozdanie.kolej_gracza_idx]
        if aktualny_gracz == gracz_czlowieka: break

        gracz_ai = aktualny_gracz
        
        if rozdanie.faza == FazaGry.ROZGRYWKA:
            legalne_karty = rozdanie.get_legalne_karty(gracz_ai)
            if legalne_karty:
                wybrana_karta = random.choice(legalne_karty)
                rozdanie.zagraj_karte(gracz_ai, wybrana_karta)
        else: 
            mozliwe_akcje_ai = rozdanie.get_mozliwe_akcje(gracz_ai)
            if mozliwe_akcje_ai:
                if rozdanie.faza in [FazaGry.LUFA, FazaGry.LICYTACJA]:
                    wybrana_akcja_ai = next((a for a in mozliwe_akcje_ai if 'pas' in a['typ']), None) or random.choice(mozliwe_akcje_ai)
                else: 
                    wybrana_akcja_ai = random.choice(mozliwe_akcje_ai)
                
                if wybrana_akcja_ai:
                    logger.info(f"Tura AI: {gracz_ai.nazwa} (Faza: {rozdanie.faza.name})")
                    logger.info(f"  AI '{gracz_ai.nazwa}' wykonuje akcję: {wybrana_akcja_ai}")
                    rozdanie.wykonaj_akcje(gracz_ai, wybrana_akcja_ai)
            else:
                logger.warning(f"  AI '{gracz_ai.nazwa}' nie ma żadnych możliwych akcji w fazie {rozdanie.faza.name}.")
                break
# --- Endpointy API ---

@app.get("/")
def get_stan_gry():
    global aktualny_mecz
    
    uruchom_ture_ai(aktualny_mecz)
    rozdanie = aktualny_mecz.rozdanie

    if rozdanie and rozdanie.rozdanie_zakonczone and not aktualny_mecz.zwyciezca_meczu:
        logger.info("\n" + "="*25)
        logger.info("--- WYNIK KOŃCOWY ROZDANIA ---")
        logger.info(f"  Grany kontrakt: {rozdanie.kontrakt.name}")
        logger.info(f"  Powód zakończenia: {rozdanie.powod_zakonczenia}")

        zwyciezca, punkty, mnoznik = rozdanie.rozlicz_rozdanie()
        
        logger.info(f"  Rozdanie wygrywa: {zwyciezca.nazwa}")
        logger.info(f"  Przyznane punkty meczowe: {punkty} (mnożnik: x{mnoznik})")
        logger.info(f"  OGÓLNY WYNIK MECZU: My {aktualny_mecz.druzyna_a.punkty_meczu} - Oni {aktualny_mecz.druzyna_b.punkty_meczu}")
        logger.info("="*25 + "\n")

        aktualny_mecz.sprawdz_koniec_meczu()
        if aktualny_mecz.zwyciezca_meczu:
            logger.info("##############################")
            logger.info("!!! KONIEC GRY !!!")
            logger.info(f"Partię wygrywa drużyna: {aktualny_mecz.zwyciezca_meczu.nazwa}")
            logger.info(f"OSTATECZNY WYNIK: My {aktualny_mecz.druzyna_a.punkty_meczu} - {aktualny_mecz.druzyna_b.punkty_meczu}")
            logger.info("##############################")
        else:
            aktualny_mecz.przygotuj_nastepne_rozdanie()
            rozdanie = aktualny_mecz.rozdanie

    # Budowanie odpowiedzi JSON
    if aktualny_mecz.zwyciezca_meczu:
        return {"koniec_meczu": True, "zwyciezca": aktualny_mecz.zwyciezca_meczu.nazwa, "wynik": f"My {aktualny_mecz.druzyna_a.punkty_meczu} - {aktualny_mecz.druzyna_b.punkty_meczu} Oni"}

    gracz_widza = aktualny_mecz.gracze[0]
    faza = rozdanie.faza
    akcje_do_wyslania = []
    if rozdanie.gracze[rozdanie.kolej_gracza_idx] == gracz_widza:
        if faza == FazaGry.ROZGRYWKA:
            akcje_do_wyslania = formatuj_karty_json(rozdanie.get_legalne_karty(gracz_widza), "zagraj_karte")
        else: 
            akcje_do_wyslania = formatuj_akcje_json(rozdanie.get_mozliwe_akcje(gracz_widza), "wykonaj_akcje")
            
    return {
        "faza_gry": faza.name,
        "kolej_na": rozdanie.gracze[rozdanie.kolej_gracza_idx].nazwa,
        "reka_gracza": [{"nazwa": str(k)} for k in sorted(gracz_widza.reka, key=lambda k: (k.kolor.name, k.ranga.value))],
        "karty_na_stole": [{"gracz": g.nazwa, "karta": str(k)} for g, k in rozdanie.aktualna_lewa],
        "kontrakt": {"typ": rozdanie.kontrakt.name if rozdanie.kontrakt else None, "atut": rozdanie.atut.name if rozdanie.atut else None},
        "punkty_w_rozdaniu": rozdanie.punkty_w_rozdaniu,
        "ogolne_punkty_meczu": {"My": aktualny_mecz.druzyna_a.punkty_meczu, "Oni": aktualny_mecz.druzyna_b.punkty_meczu},
        "mozliwe_akcje": akcje_do_wyslania
    }


@app.get("/wykonaj_akcje/{akcja_idx}")
def wykonaj_akcje_gracza(akcja_idx: int):
    gracz_czlowieka = aktualny_mecz.gracze[0]
    rozdanie = aktualny_mecz.rozdanie
    if rozdanie.gracze[rozdanie.kolej_gracza_idx] == gracz_czlowieka:
        mozliwe_akcje = rozdanie.get_mozliwe_akcje(gracz_czlowieka)
        if 0 <= akcja_idx < len(mozliwe_akcje):
            wybrana_akcja = mozliwe_akcje[akcja_idx]
            rozdanie.wykonaj_akcje(gracz_czlowieka, wybrana_akcja)
            uruchom_ture_ai(aktualny_mecz)
    return get_stan_gry()

@app.get("/zagraj_karte/{karta_idx}")
def zagraj_karte_gracza(karta_idx: int):
    gracz_czlowieka = aktualny_mecz.gracze[0]
    rozdanie = aktualny_mecz.rozdanie
    if rozdanie.gracze[rozdanie.kolej_gracza_idx] == gracz_czlowieka:
        legalne_karty = rozdanie.get_legalne_karty(gracz_czlowieka)
        posortowane_legalne = sorted(legalne_karty, key=lambda k: (k.kolor.name, k.ranga.value))
        if 0 <= karta_idx < len(posortowane_legalne):
            wybrana_karta = posortowane_legalne[karta_idx]
            rozdanie.zagraj_karte(gracz_czlowieka, wybrana_karta)
            uruchom_ture_ai(aktualny_mecz)
    return get_stan_gry()

@app.get("/nowy_mecz")
def nowy_mecz_endpoint():
    global aktualny_mecz
    aktualny_mecz = Mecz(nazwy_graczy=["Jakub", "Przeciwnik1", "Nasz", "Przeciwnik2"])
    aktualny_mecz.rozpocznij_mecz()
    return get_stan_gry()