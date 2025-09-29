import sys
import random
from silnik_gry import Gracz, Druzyna, Rozdanie, Kontrakt, Kolor, Karta, Ranga

def znajdz_legalny_ruch(rozdanie: Rozdanie, gracz: Gracz) -> Karta | None:
    """Prosta AI: znajduje pierwszą legalną kartę do zagrania z ręki gracza."""
    for karta in gracz.reka:
        if rozdanie._waliduj_ruch(gracz, karta):
            return karta
    return None # Nie powinno się zdarzyć w legalnej grze

def uruchom_symulacje_rozdania(numer_rozdania: int, druzyny: list[Druzyna]):
    """Uruchamia i loguje pojedyncze, pełne rozdanie."""
    print(f"--- ROZDANIE #{numer_rozdania} ---")

    # Setup
    gracze = [
        Gracz(nazwa="Jakub"), Gracz(nazwa="Przeciwnik1"),
        Gracz(nazwa="Nasz"), Gracz(nazwa="Przeciwnik2")
    ]
    # Czyszczenie stanu graczy i drużyn przed nowym rozdaniem
    for gracz in gracze:
        gracz.reka.clear()
        gracz.wygrane_karty.clear()
    druzyny[0].gracze.clear()
    druzyny[1].gracze.clear()
    druzyny[0].dodaj_gracza(gracze[0])
    druzyny[0].dodaj_gracza(gracze[2])
    druzyny[1].dodaj_gracza(gracze[1])
    druzyny[1].dodaj_gracza(gracze[3])
    
    rozdajacy_idx = (numer_rozdania - 1) % 4
    rozdanie = Rozdanie(
        gracze=gracze, 
        druzyny=druzyny, 
        rozdajacy_idx=rozdajacy_idx
    )
    
    # Inicjalizacja
    rozdanie.rozdaj_karty(6)
    kontrakt = random.choice(list(Kontrakt))
    atut = random.choice(list(Kolor)) if kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA] else None
    rozdanie.przeprowadz_licytacje(kontrakt, atut)
    
    print(f"Kontrakt: {rozdanie.kontrakt.name}, Atut: {rozdanie.atut.name if atut else 'Brak'}")
    
    # Pętla rozgrywki
    print("\n--- Rozgrywka ---")
    for numer_lewy in range(1, 7):
        if rozdanie.rozdanie_zakonczone:
            break
        print(f"\n-- Lewa #{numer_lewy} --")
        start_idx = rozdanie.kolej_gracza_idx
        kolejnosc_graczy = [gracze[(start_idx + i) % 4] for i in range(4)]
        
        wynik_lewy = None
        for gracz in kolejnosc_graczy:
            karta_do_zagrania = znajdz_legalny_ruch(rozdanie, gracz)
            if karta_do_zagrania:
                punkty_meldunek = rozdanie.zagraj_karte(gracz, karta_do_zagrania)
                komunikat = f"[{gracz.nazwa}] zagrywa: {karta_do_zagrania}"
                if punkty_meldunek > 0:
                    komunikat += f" (MELDUNEK! +{punkty_meldunek} pkt)"
                print(komunikat)
                
                # Sprawdzamy, czy ostatnie zagranie zakończyło lewę
                if len(rozdanie.aktualna_lewa) == 0: # Dzieje się tak po _zakoncz_lewe
                    # Potrzebujemy sposobu, aby uzyskać wynik
                    # Na razie dodamy print w silniku, a potem to poprawimy
                    pass # Logika jest teraz w silniku

    # Weryfikacja końcowa
    if rozdanie.rozdanie_zakonczone:
         print(f"\n!!! Rozdanie zakończone przed czasem: {rozdanie.powod_zakonczenia} !!!")

    druzyna_wygrana, punkty_dodane, mnoznik = rozdanie.rozlicz_rozdanie()

    print("\n" + "="*25)
    print("--- WYNIK KOŃCOWY ROZDANIA ---")
    if rozdanie.zwyciezca_ostatniej_lewy:
        print(f"Bonus za ostatnią lewę (+12 pkt) dla drużyny: {rozdanie.zwyciezca_ostatniej_lewy.druzyna.nazwa}")
    punkty_a = rozdanie.punkty_w_rozdaniu[druzyny[0].nazwa]
    punkty_b = rozdanie.punkty_w_rozdaniu[druzyny[1].nazwa]
    print(f"Punkty z kart i meldunków: {druzyny[0].nazwa} {punkty_a} - {punkty_b} {druzyny[1].nazwa}")
    
    print(f"Rozdanie wygrywa: {druzyna_wygrana.nazwa}")
    print(f"Przyznane punkty meczowe: {punkty_dodane} (mnożnik: x{mnoznik})")
    print(f"OGÓLNY WYNIK MECZU: {druzyny[0].nazwa} {druzyny[0].punkty_meczu} - {druzyny[1].nazwa} {druzyny[1].punkty_meczu}")
    print("="*25 + "\n")


if __name__ == "__main__":
    LICZBA_ITERACJI = 100 # Zwiększmy, aby zobaczyć więcej przypadków
    NAZWA_PLIKU_LOGU = "log_rozdania.txt"
    
    druzyna_a = Druzyna(nazwa="My"); druzyna_b = Druzyna(nazwa="Oni")
    druzyna_a.przeciwnicy = druzyna_b; druzyna_b.przeciwnicy = druzyna_a
    
    oryginalny_stdout = sys.stdout 
    with open(NAZWA_PLIKU_LOGU, 'w', encoding='utf-8') as f:
        sys.stdout = f
        for i in range(LICZBA_ITERACJI):
            uruchom_symulacje_rozdania(i + 1, [druzyna_a, druzyna_b])
            
            # NOWA LOGIKA: Sprawdź, czy ktoś wygrał cały mecz
            if druzyna_a.punkty_meczu >= 66 or druzyna_b.punkty_meczu >= 66:
                print("\n" + "#"*30)
                print("!!! KONIEC GRY !!!")
                zwyciezca_meczu = druzyna_a if druzyna_a.punkty_meczu >= 66 else druzyna_b
                print(f"Mecz wygrywa drużyna: {zwyciezca_meczu.nazwa}")
                print(f"OSTATECZNY WYNIK: {druzyna_a.nazwa} {druzyna_a.punkty_meczu} - {druzyna_b.punkty_meczu} {druzyna_b.punkty_meczu}")
                print("#"*30)
                break # Przerwij pętlę symulacji
                
    sys.stdout = oryginalny_stdout
    
    print(f"✅ Symulacja zakończona. Pełny log został zapisany do pliku: {NAZWA_PLIKU_LOGU}")