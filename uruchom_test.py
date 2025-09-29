import sys
import random
from silnik_gry import Gracz, Druzyna, Rozdanie, Kontrakt, Kolor, Karta

def znajdz_legalny_ruch(rozdanie: Rozdanie, gracz: Gracz) -> Karta | None:
    for karta in gracz.reka:
        if rozdanie._waliduj_ruch(gracz, karta):
            return karta
    return None

def uruchom_symulacje_rozdania(numer_rozdania: int):
    print(f"--- ROZDANIE #{numer_rozdania} ---")

    # Setup
    druzyna_a = Druzyna(nazwa="My"); druzyna_b = Druzyna(nazwa="Oni")
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
    rozdanie.rozdaj_karty(6)
    kontrakt = random.choice(list(Kontrakt))
    atut = random.choice(list(Kolor)) if kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA] else None
    rozdanie.przeprowadz_licytacje(kontrakt, atut)
    
    print(f"Kontrakt: {rozdanie.kontrakt.name}, Atut: {rozdanie.atut.name if atut else 'Brak'}")
    
    print("\n--- Rozgrywka ---")
    for numer_lewy in range(1, 7):
        print(f"\n-- Lewa #{numer_lewy} --")
        start_idx = rozdanie.kolej_gracza_idx
        kolejnosc_graczy = [gracze[(start_idx + i) % 4] for i in range(4)]
        
        for gracz in kolejnosc_graczy:
            karta_do_zagrania = znajdz_legalny_ruch(rozdanie, gracz)
            if karta_do_zagrania:
                # Wykonaj ruch i sprawdź, czy dał punkty z meldunku
                punkty_meldunek = rozdanie.zagraj_karte(gracz, karta_do_zagrania)
                komunikat = f"[{gracz.nazwa}] zagrywa: {karta_do_zagrania}"
                if punkty_meldunek > 0:
                    komunikat += f" (MELDUNEK! +{punkty_meldunek} pkt)"
                print(komunikat)

    # Weryfikacja końcowa
    punkty_a = rozdanie.punkty_w_rozdaniu[druzyna_a.nazwa]
    punkty_b = rozdanie.punkty_w_rozdaniu[druzyna_b.nazwa]
    print("\n" + "="*25); print("--- WYNIK KOŃCOWY ROZDANIA ---")
    print(f"Punkty: {druzyna_a.nazwa} {punkty_a} - {punkty_b} {druzyna_b.nazwa}")
    print("="*25 + "\n")


if __name__ == "__main__":
    LICZBA_ITERACJI = 120
    NAZWA_PLIKU_LOGU = "log_rozdania.txt"
    oryginalny_stdout = sys.stdout 
    with open(NAZWA_PLIKU_LOGU, 'w', encoding='utf-8') as f:
        sys.stdout = f;
        for i in range(LICZBA_ITERACJI): uruchom_symulacje_rozdania(i + 1)
    sys.stdout = oryginalny_stdout
    print(f"✅ Symulacja zakończona. Pełny log z {LICZBA_ITERACJI} rozdań został zapisany do pliku: {NAZWA_PLIKU_LOGU}")