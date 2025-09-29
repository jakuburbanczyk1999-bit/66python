import sys
import random
from silnik_gry import Gracz, Druzyna, Rozdanie, Kontrakt, Kolor

def uruchom_symulacje_rozdania(numer_rozdania: int):
    print(f"--- ROZDANIE #{numer_rozdania} ---")

    # Setup
    druzyna_a = Druzyna(nazwa="My")
    druzyna_b = Druzyna(nazwa="Oni")
    gracze = [
        Gracz(nazwa="Jakub"), Gracz(nazwa="Przeciwnik1"),
        Gracz(nazwa="Nasz"), Gracz(nazwa="Przeciwnik2")
    ]
    for gracz in gracze:
        gracz.reka.clear(); gracz.wygrane_karty.clear()
    druzyna_a.dodaj_gracza(gracze[0]); druzyna_a.dodaj_gracza(gracze[2])
    druzyna_b.dodaj_gracza(gracze[1]); druzyna_b.dodaj_gracza(gracze[3])
    
    rozdajacy_idx = (numer_rozdania - 1) % 4
    rozdanie = Rozdanie(
        gracze=gracze, 
        druzyny=[druzyna_a, druzyna_b], 
        rozdajacy_idx=rozdajacy_idx
    )
    
    # Inicjalizacja rozdania
    rozdanie.rozdaj_karty(3)
    losowy_kontrakt = random.choice(list(Kontrakt))
    losowy_atut = None
    if losowy_kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA]:
        losowy_atut = random.choice(list(Kolor))
    rozdanie.przeprowadz_licytacje(losowy_kontrakt, losowy_atut)
    rozdanie.rozdaj_karty(3)
    
    grajacy = rozdanie.grajacy
    print(f"Rozdającym był: {rozdanie.gracze[rozdajacy_idx].nazwa}")
    print(f"Wygrał licytację: {grajacy.nazwa}")
    print(f"Ustalony kontrakt: {rozdanie.kontrakt.name}")
    print(f"Kolor atutowy: {rozdanie.atut.name if rozdanie.atut else 'Brak'}")
    
    print("\n--- Rozgrywka: Pierwsza lewa ---")
    start_idx = gracze.index(grajacy)
    kolejnosc_graczy_w_lewie = [gracze[(start_idx + i) % 4] for i in range(4)]

    for gracz_w_kolejce in kolejnosc_graczy_w_lewie:
        if gracz_w_kolejce.reka:
            karta_do_zagrania = gracz_w_kolejce.reka[0]
            print(f"[{gracz_w_kolejce.nazwa}] zagrywa: {karta_do_zagrania}")
            rozdanie.zagraj_karte(gracz_w_kolejce, karta_do_zagrania)
    
    # Weryfikacja wyniku lewy
    punkty_a = rozdanie.punkty_w_rozdaniu[druzyna_a.nazwa]
    punkty_b = rozdanie.punkty_w_rozdaniu[druzyna_b.nazwa]
    
    print("\n--- Stan po pierwszej lewie ---")
    print(f"Punkty w rozdaniu: {druzyna_a.nazwa} {punkty_a} - {punkty_b} {druzyna_b.nazwa}")
    for gracz in gracze:
        print(f"Gracz '{gracz.nazwa}' ma {len(gracz.reka)} kart w ręku i {len(gracz.wygrane_karty)} wygranych kart.")
    print(f"Następną lewę rozpoczyna: {rozdanie.gracze[rozdanie.kolej_gracza_idx].nazwa}")
    print("-" * 25 + "\n")


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