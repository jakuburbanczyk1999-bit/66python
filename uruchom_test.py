import sys
import random
from silnik_gry import Gracz, Druzyna, Rozdanie, Kontrakt, Kolor, Karta

def znajdz_legalny_ruch(rozdanie: Rozdanie, gracz: Gracz) -> Karta | None:
    """Prosta AI: znajduje pierwszą legalną kartę do zagrania z ręki gracza."""
    for karta in gracz.reka:
        if rozdanie._waliduj_ruch(gracz, karta):
            return karta
    return None

def uruchom_symulacje_rozdania(numer_rozdania: int):
    print(f"--- ROZDANIE #{numer_rozdania} ---")

    # Setup
    druzyna_a = Druzyna(nazwa="My")
    druzyna_b = Druzyna(nazwa="Oni")
    gracze = [
        Gracz(nazwa="Jakub"), Gracz(nazwa="Przeciwnik1"),
        Gracz(nazwa="Nasz"), Gracz(nazwa="Przeciwnik2")
    ]
    for gracz in gracze: gracz.reka.clear(); gracz.wygrane_karty.clear()
    druzyna_a.dodaj_gracza(gracze[0]); druzyna_a.dodaj_gracza(gracze[2])
    druzyna_b.dodaj_gracza(gracze[1]); druzyna_b.dodaj_gracza(gracze[3])
    
    rozdajacy_idx = (numer_rozdania - 1) % 4
    rozdanie = Rozdanie(gracze=gracze, druzyny=[druzyna_a, druzyna_b], rozdajacy_idx=rozdajacy_idx)
    
    # Inicjalizacja
    rozdanie.rozdaj_karty(6) # Rozdajemy od razu wszystkie 6, bo licytacja jest symulowana
    kontrakt = random.choice(list(Kontrakt))
    atut = random.choice(list(Kolor)) if kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA] else None
    rozdanie.przeprowadz_licytacje(kontrakt, atut)
    
    grajacy = rozdanie.grajacy
    print(f"Rozdającym był: {rozdanie.gracze[rozdajacy_idx].nazwa}, Wygrał licytację: {grajacy.nazwa}")
    print(f"Kontrakt: {rozdanie.kontrakt.name}, Atut: {rozdanie.atut.name if rozdanie.atut else 'Brak'}")
    
    # --- NOWA CZĘŚĆ: Pętla rozgrywająca wszystkie 6 lew ---
    print("\n--- Rozgrywka ---")
    for numer_lewy in range(1, 7):
        print(f"\n-- Lewa #{numer_lewy} --")
        start_idx = rozdanie.kolej_gracza_idx
        kolejnosc_graczy = [gracze[(start_idx + i) % 4] for i in range(4)]

        for gracz in kolejnosc_graczy:
            karta_do_zagrania = znajdz_legalny_ruch(rozdanie, gracz)
            if karta_do_zagrania:
                print(f"[{gracz.nazwa}] zagrywa: {karta_do_zagrania}")
                rozdanie.zagraj_karte(gracz, karta_do_zagrania)
        
        # Logika podsumowująca lewę jest teraz wewnątrz silnika, więc nie musimy nic więcej robić

    # --- Weryfikacja końcowa ---
    punkty_a = rozdanie.punkty_w_rozdaniu[druzyna_a.nazwa]
    punkty_b = rozdanie.punkty_w_rozdaniu[druzyna_b.nazwa]
    print("\n" + "="*25)
    print("--- WYNIK KOŃCOWY ROZDANIA ---")
    print(f"Punkty: {druzyna_a.nazwa} {punkty_a} - {punkty_b} {druzyna_b.nazwa}")
    print(f"Suma punktów w rozdaniu: {punkty_a + punkty_b} (powinno być 120)")
    print("="*25 + "\n")


if __name__ == "__main__":
    LICZBA_ITERACJI = 5
    NAZWA_PLIKU_LOGU = "log_rozdania.txt"
    oryginalny_stdout = sys.stdout 
    with open(NAZWA_PLIKU_LOGU, 'w', encoding='utf-8') as f:
        sys.stdout = f
        for i in range(LICZBA_ITERACJI):
            uruchom_symulacje_rozdania(i + 1)
    sys.stdout = oryginalny_stdout
    
    print(f"✅ Symulacja zakończona. Pełny log z {LICZBA_ITERACJI} rozdań został zapisany do pliku: {NAZWA_PLIKU_LOGU}")