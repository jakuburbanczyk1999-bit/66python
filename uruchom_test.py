import sys
import random
from typing import Union
from silnik_gry import Gracz, Druzyna, Rozdanie, Kontrakt, Kolor, Karta, Ranga, FazaGry

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
        gracz.reka.clear(); gracz.wygrane_karty.clear()
    druzyny[0].gracze.clear(); druzyny[1].gracze.clear()
    druzyny[0].dodaj_gracza(gracze[0]); druzyny[0].dodaj_gracza(gracze[2])
    druzyny[1].dodaj_gracza(gracze[1]); druzyny[1].dodaj_gracza(gracze[3])
    
    rozdajacy_idx = (numer_rozdania - 1) % 4
    rozdanie = Rozdanie(
        gracze=gracze, 
        druzyny=druzyny, 
        rozdajacy_idx=rozdajacy_idx
    )
    
    print(f"Rozdającym jest: {gracze[rozdajacy_idx].nazwa}")
    rozdanie.rozpocznij_nowe_rozdanie()
    
    print("\n--- Faza 1: Rozdanie 3 kart ---")
    for gracz in gracze:
        print(f"Ręka gracza '{gracz.nazwa}': {', '.join(map(str, gracz.reka))}")

    # --- POPRAWIONA SEKCJA DEKLARACJI ---
    print("\n--- Faza 2: Deklaracja ---")
    gracz_deklarujacy = rozdanie.gracze[rozdanie.kolej_gracza_idx]
    print(f"Deklaruje: {gracz_deklarujacy.nazwa}")
    
    # Symulujemy, że gracz zawsze wybiera NORMALNA, aby przetestować Fazę Pytania
    wybrana_akcja_1 = {'typ': 'deklaracja', 'kontrakt': Kontrakt.NORMALNA, 'atut': random.choice(list(Kolor))}
    print(f"Decyzja: {wybrana_akcja_1['kontrakt'].name}, Atut: {wybrana_akcja_1['atut'].name}")
    rozdanie.wykonaj_akcje(gracz_deklarujacy, wybrana_akcja_1)

    # --- FAZA PYTANIA ---
    if rozdanie.faza == FazaGry.FAZA_PYTANIA:
        print("\n--- Faza 3: Faza Pytania ---")
        print(f"Ponownie decyduje: {gracz_deklarujacy.nazwa}")
        mozliwe_akcje_2 = rozdanie.get_mozliwe_akcje(gracz_deklarujacy)
        
        # Logujemy możliwe akcje
        akcje_str = [a.get('kontrakt', a.get('decyzja', 'pytanie')).name if hasattr(a.get('kontrakt', a.get('decyzja', 'pytanie')), 'name') else 'pytanie' for a in mozliwe_akcje_2]
        print(f"Możliwe akcje: {akcje_str}")
        
        # Symulujemy losową decyzję
        wybrana_akcja_2 = {'typ': 'pytanie'}
        print(f"Decyzja: Pytam") # Logujemy na stałe tę decyzję
            
        rozdanie.wykonaj_akcje(gracz_deklarujacy, wybrana_akcja_2)

    # --- LICYTACJA 2 (jeśli wystąpiła) ---
    if rozdanie.faza == FazaGry.LICYTACJA:
        print("\n--- Faza 4: Licytacja 2 (Przebicie) ---")
        for _ in range(3): # Pętla dla 3 pozostałych graczy
            licytujacy = rozdanie.gracze[rozdanie.kolej_gracza_idx]
            mozliwe_akcje = rozdanie.get_mozliwe_akcje(licytujacy)
            
            # Symulujemy losową decyzję
            wybrana_akcja_3 = random.choice(mozliwe_akcje)
            
            # Logowanie
            decyzja_str = "Pas"
            if wybrana_akcja_3['typ'] == 'przebicie':
                decyzja_str = f"Przebijam na {wybrana_akcja_3['kontrakt'].name}"
            print(f"Licytuje: {licytujacy.nazwa}, Decyzja: {decyzja_str}")
            
            rozdanie.wykonaj_akcje(licytujacy, wybrana_akcja_3)
    print("\n--- Faza 3: Rozdanie pozostałych 3 kart ---")
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