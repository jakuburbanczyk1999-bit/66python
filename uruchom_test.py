import sys
import random
import logging
from silnik_gry import Mecz, FazaGry

# --- KONFIGURACJA ---
LICZBA_PARTII = 30
NAZWA_PLIKU_LOGU = "log_finalny.txt"

# --- Konfiguracja Logowania ---
logger = logging.getLogger('szesc_szesc_logger')
logger.setLevel(logging.DEBUG)
if logger.hasHandlers():
    logger.handlers.clear()
handler = logging.FileHandler(NAZWA_PLIKU_LOGU, mode='w', encoding='utf-8')
# Prostszy formatter, bo silnik dodaje swoje wcięcia
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def formatuj_akcje_dla_logu(akcje: list[dict]) -> str:
    """Pomocnicza funkcja do ładnego wyświetlania możliwych akcji w logu."""
    opisy = []
    for akcja in akcje:
        if akcja.get('kontrakt'):
            atut_str = f" ({akcja['atut'].name})" if akcja.get('atut') else ""
            typ_akcji = akcja['typ'].replace('_', ' ').capitalize()
            if typ_akcji == 'Deklaracja': typ_akcji = akcja['kontrakt'].name
            elif typ_akcji == 'Przebicie': typ_akcji = f"Przebij na {akcja['kontrakt'].name}"
            elif typ_akcji == 'Zmiana kontraktu': typ_akcji = f"Zmień na {akcja['kontrakt'].name}"
            opisy.append(f"{typ_akcji}{atut_str}")
        else:
            opisy.append(akcja['typ'].replace('_', ' ').capitalize())
    return ", ".join(opisy)

def uruchom_symulacje():
    """Główna funkcja, która uruchamia i loguje symulację N partii."""
    
    for i in range(1, LICZBA_PARTII + 1):
        logger.info("\n" + "#"*40)
        logger.info(f"### ROZPOCZYNAMY PARTIĘ #{i} ###")
        logger.info("#"*40)
        
        mecz = Mecz(nazwy_graczy=["Jakub", "Przeciwnik1", "Nasz", "Przeciwnik2"])
        mecz.rozpocznij_mecz()
        
        licznik_ruchow_w_partii = 0
        while not mecz.zwyciezca_meczu:
            licznik_ruchow_w_partii += 1
            if licznik_ruchow_w_partii > 500:
                logger.error("!!! PRZERWANO PARTIĘ - PRZEKROCZONO LIMIT RUCHÓW !!!")
                break
                
            rozdanie = mecz.rozdanie

            if rozdanie.rozdanie_zakonczone:
                logger.info("\n" + "="*25)
                logger.info("--- WYNIK KOŃCOWY ROZDANIA ---")
                grany_kontrakt_str = f"{rozdanie.kontrakt.name} (gra: {rozdanie.grajacy.nazwa})" if rozdanie.kontrakt else "Brak"
                logger.info(f"  Grany kontrakt: {grany_kontrakt_str}")

                if rozdanie.powod_zakonczenia:
                    logger.info(f"!!! Rozdanie zakończone przed czasem: {rozdanie.powod_zakonczenia} !!!")

                zwyciezca, punkty, mnoznik = rozdanie.rozlicz_rozdanie()
                
                logger.info(f"  Punkty z kart: My {rozdanie.punkty_w_rozdaniu['My']} - {rozdanie.punkty_w_rozdaniu['Oni']} Oni")
                logger.info(f"  Rozdanie wygrywa: {zwyciezca.nazwa}")
                logger.info(f"  Przyznane punkty meczowe: {punkty} (mnożnik: x{mnoznik})")
                logger.info(f"  OGÓLNY WYNIK MECZU: My {mecz.druzyna_a.punkty_meczu} - Oni {mecz.druzyna_b.punkty_meczu}")
                logger.info("="*25)
                
                mecz.sprawdz_koniec_meczu()
                if not mecz.zwyciezca_meczu:
                    mecz.przygotuj_nastepne_rozdanie()
                continue

            aktualny_gracz = rozdanie.gracze[rozdanie.kolej_gracza_idx]

            if rozdanie.faza == FazaGry.ROZGRYWKA:
                if len(rozdanie.aktualna_lewa) == 0:
                    logger.info(f"\n--- Lewa #{rozdanie.numer_lewy + 1} (zaczyna: {aktualny_gracz.nazwa}) ---")
                    # Logowanie rąk graczy na początku lewy
                    for p in sorted(rozdanie.gracze, key=lambda x: x.nazwa):
                        if p == rozdanie.nieaktywny_gracz: continue
                        reka_str = ", ".join(sorted([str(k) for k in p.reka]))
                        logger.info(f"    {p.nazwa:<12}: [{reka_str}]")

                mozliwe_karty = rozdanie.get_legalne_karty(aktualny_gracz)
                if not mozliwe_karty:
                    logger.error(f"BŁĄD KRYTYCZNY: Gracz {aktualny_gracz.nazwa} nie ma żadnego legalnego ruchu!")
                    break
                wybrana_karta = random.choice(mozliwe_karty)
                rozdanie.zagraj_karte(aktualny_gracz, wybrana_karta)
            else: 
                # Logowanie faz licytacji
                if rozdanie.faza != getattr(rozdanie, '_ostatnia_faza_logu', None):
                    logger.info(f"\n--- ETAP: {rozdanie.faza.name.replace('_', ' ')} ---")
                    rozdanie._ostatnia_faza_logu = rozdanie.faza
                
                mozliwe_akcje = rozdanie.get_mozliwe_akcje(aktualny_gracz)
                if not mozliwe_akcje:
                    logger.error(f"BŁĄD KRYTYCZNY: Brak możliwych akcji dla gracza {aktualny_gracz} w fazie {rozdanie.faza.name}!")
                    break
                wybrana_akcja = random.choice(mozliwe_akcje)
                
                logger.info(f"  Tura gracza: {aktualny_gracz.nazwa}")
                logger.info(f"    Możliwe akcje: {formatuj_akcje_dla_logu(mozliwe_akcje)}")
                logger.info(f"    Decyzja: {formatuj_akcje_dla_logu([wybrana_akcja])}")
                rozdanie.wykonaj_akcje(aktualny_gracz, wybrana_akcja)
        
        if mecz.zwyciezca_meczu:
            logger.info("\n" + "#"*30)
            logger.info("!!! KONIEC GRY !!!")
            logger.info(f"Partię wygrywa drużyna: {mecz.zwyciezca_meczu.nazwa}")
            logger.info(f"OSTATECZNY WYNIK: {mecz.druzyna_a.nazwa} {mecz.druzyna_a.punkty_meczu} - {mecz.druzyna_b.punkty_meczu} {mecz.druzyna_b.nazwa}")
            logger.info("#"*30)

if __name__ == "__main__":
    try:
        uruchom_symulacje()
        print(f"✅ Symulacja zakończona. Pełny log z {LICZBA_PARTII} partii został zapisany do pliku: {NAZWA_PLIKU_LOGU}")
    except Exception as e:
        logging.exception("Krytyczny błąd w trakcie symulacji") # Loguje stack trace do pliku
        print(f"❌ WYSTĄPIŁ KRYTYCZNY BŁĄD PODCZAS SYMULACJI: {e}")
        print(f"Sprawdź plik {NAZWA_PLIKU_LOGU}, aby zobaczyć zapis partii i szczegóły błędu.")