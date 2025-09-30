import sys
import random
from typing import Union
from silnik_gry import Gracz, Druzyna, Rozdanie, Kontrakt, Kolor, Karta, Ranga

def znajdz_legalny_ruch(rozdanie: Rozdanie, gracz: Gracz) -> Union[Karta, None]:
    """Prosta AI: znajduje pierwszą legalną kartę do zagrania z ręki gracza."""
    for karta in gracz.reka:
        if rozdanie._waliduj_ruch(gracz, karta):
            return karta
    return None

def uruchom_symulacje_rozdania(numer_rozdania: int, druzyny: list[Druzyna]):
    """Uruchamia i loguje pojedyncze, pełne rozdanie."""
    print(f"--- ROZDANIE #{numer_rozdania} ---")

    # Setup
    gracze = [
        Gracz(nazwa="Jakub"), Gracz(nazwa="Przeciwnik1"),
        Gracz(nazwa="Nasz"), Gracz(nazwa="Przeciwnik2")
    ]
    for gracz in gracze:
        gracz.reka.clear()
        gracz.wygrane_karty.clear()
    druzyny[0].gracze.clear(); druzyny[1].gracze.clear()
    druzyny[0].dodaj_gracza(gracze[0]); druzyny[0].dodaj_gracza(gracze[2])
    druzyny[1].dodaj_gracza(gracze[1]); druzyny[1].dodaj_gracza(gracze[3])
    
    rozdajacy_idx = (numer_rozdania - 1) % 4
    rozdanie = Rozdanie(
        gracze=gracze, 
        druzyny=druzyny, 
        rozdajacy_idx=rozdajacy_idx
    )
    
    # --- Pełne sterowanie z pliku testowego z nowymi PRINTAMI ---
    print(f"Rozdającym jest: {gracze[rozdajacy_idx].nazwa}")

    # Etap 1: Rozdaj pierwsze 3 karty
    print("\n--- Faza 1: Rozdanie 3 kart ---")
    rozdanie.rozdaj_karty(3)
    for gracz in gracze:
        print(f"Ręka gracza '{gracz.nazwa}': {', '.join(map(str, gracz.reka))}")

    # Etap 2: Licytacja
    print("\n--- Faza 2: Licytacja (symulowana) ---")
    grajacy_idx = (rozdajacy_idx + 1) % 4
    print(f"Licytację rozpoczyna: {gracze[grajacy_idx].nazwa}")
    
    losowy_kontrakt = random.choice(list(Kontrakt))
    losowy_atut = None
    if losowy_kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA]:
        losowy_atut = random.choice(list(Kolor))
    
    print(f"Decyzja: {losowy_kontrakt.name}, Atut: {losowy_atut.name if losowy_atut else 'Brak'}")
    rozdanie.przeprowadz_licytacje(losowy_kontrakt, losowy_atut)
    
    # Etap 3: Rozdaj pozostałe 3 karty
    print("\n--- Faza 3: Rozdanie pozostałych 3 kart ---")
    rozdanie.rozdaj_karty(3)
    print("\n--- Pełne ręce graczy przed rozgrywką ---")
    for gracz in gracze:
        posortowana_reka = sorted(gracz.reka, key=lambda k: (k.kolor.name, k.ranga.value))
        print(f"Ręka gracza '{gracz.nazwa}': {', '.join(map(str, posortowana_reka))}")
    # Etap 4: Pętla rozgrywki
    print("\n--- Rozgrywka ---")
    for numer_lewy in range(1, 7):
        if rozdanie.rozdanie_zakonczone:
            break
            
        print(f"\n-- Lewa #{numer_lewy} --")
        start_idx = rozdanie.kolej_gracza_idx
        kolejnosc_graczy = [gracze[(start_idx + i) % 4] for i in range(4)]
        
        for gracz in kolejnosc_graczy:
            karta_do_zagrania = znajdz_legalny_ruch(rozdanie, gracz)
            if karta_do_zagrania:
                punkty_meldunek = rozdanie.zagraj_karte(gracz, karta_do_zagrania)
                komunikat = f"[{gracz.nazwa}] zagrywa: {karta_do_zagrania}"
                if punkty_meldunek > 0:
                    komunikat += f" (MELDUNEK! +{punkty_meldunek} pkt)"
                print(komunikat)
            else:
                print(f"BŁĄD KRYTYCZNY: Gracz {gracz.nazwa} nie ma żadnego legalnego ruchu!")
                return # Przerwij symulację w razie błędu

    # Weryfikacja końcowa
    if rozdanie.rozdanie_zakonczone and rozdanie.powod_zakonczenia:
         print(f"\n!!! Rozdanie zakończone przed czasem: {rozdanie.powod_zakonczenia} !!!")

    druzyna_wygrana, punkty_dodane, mnoznik = rozdanie.rozlicz_rozdanie()

    print("\n" + "="*25)
    print("--- WYNIK KOŃCOWY ROZDANIA ---")
    punkty_a = rozdanie.punkty_w_rozdaniu[druzyny[0].nazwa]
    punkty_b = rozdanie.punkty_w_rozdaniu[druzyny[1].nazwa]
    print(f"Punkty z kart (z bonusem): {druzyny[0].nazwa} {punkty_a} - {punkty_b} {druzyny[1].nazwa}")
    
    print(f"Rozdanie wygrywa: {druzyna_wygrana.nazwa}")
    print(f"Przyznane punkty meczowe: {punkty_dodane} (mnożnik: x{mnoznik})")
    print(f"OGÓLNY WYNIK MECZU: {druzyny[0].nazwa} {druzyny[0].punkty_meczu} - {druzyny[1].punkty_meczu} {druzyny[1].punkty_meczu}")
    print("="*25 + "\n")

if __name__ == "__main__":
    LICZBA_ITERACJI = 100
    NAZWA_PLIKU_LOGU = "log_rozdania.txt"
    
    # Inicjujemy drużyny RAZ na całą symulację, aby śledzić wynik
    druzyna_a = Druzyna(nazwa="My")
    druzyna_b = Druzyna(nazwa="Oni")
    druzyna_a.przeciwnicy = druzyna_b
    druzyna_b.przeciwnicy = druzyna_a
    
    oryginalny_stdout = sys.stdout 
    with open(NAZWA_PLIKU_LOGU, 'w', encoding='utf-8') as f:
        sys.stdout = f
        for i in range(LICZBA_ITERACJI):
            uruchom_symulacje_rozdania(i + 1, [druzyna_a, druzyna_b])
            # Sprawdź, czy ktoś wygrał cały mecz
            if druzyna_a.punkty_meczu >= 66 or druzyna_b.punkty_meczu >= 66:
                print("\n" + "#"*30)
                print("!!! KONIEC GRY !!!")
                zwyciezca_meczu = druzyna_a if druzyna_a.punkty_meczu >= 66 else druzyna_b
                print(f"Mecz wygrywa drużyna: {zwyciezca_meczu.nazwa}")
                print(f"OSTATECZNY WYNIK: {druzyna_a.nazwa} {druzyna_a.punkty_meczu} - {druzyna_b.punkty_meczu} {druzyna_b.punkty_meczu}")
                print("#"*30)
                break
                
    sys.stdout = oryginalny_stdout
    
    print(f"✅ Symulacja zakończona. Pełny log został zapisany do pliku: {NAZWA_PLIKU_LOGU}")