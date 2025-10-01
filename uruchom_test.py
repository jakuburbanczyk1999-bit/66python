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

def formatuj_akcje(akcje: list[dict]) -> str:
    """Pomocnicza funkcja do ładnego wyświetlania możliwych akcji."""
    opisy = []
    for akcja in akcje:
        if akcja.get('kontrakt'):
            atut_str = f" ({akcja['atut'].name})" if akcja.get('atut') else ""
            typ_akcji = akcja['typ'].replace('_', ' ').capitalize()
            if typ_akcji == 'Deklaracja': typ_akcji = akcja['kontrakt'].name
            if typ_akcji == 'Przebicie': typ_akcji = f"Przebij na {akcja['kontrakt'].name}"
            if typ_akcji == 'Zmiana kontraktu': typ_akcji = f"Zmień na {akcja['kontrakt'].name}"
            opisy.append(f"{typ_akcji}{atut_str}")
        else:
            opisy.append(akcja['typ'].replace('_', ' ').capitalize())
    return ", ".join(opisy)

def uruchom_symulacje_rozdania(numer_rozdania: int, druzyny: list[Druzyna]):
    print(f"--- ROZDANIE #{numer_rozdania} ---")
    
    # Setup
    gracze = [Gracz(nazwa="Jakub"), Gracz(nazwa="Przeciwnik1"), Gracz(nazwa="Nasz"), Gracz(nazwa="Przeciwnik2")]
    for gracz in gracze: gracz.reka.clear(); gracz.wygrane_karty.clear()
    druzyny[0].gracze.clear(); druzyny[1].gracze.clear()
    druzyny[0].dodaj_gracza(gracze[0]); druzyny[0].dodaj_gracza(gracze[2])
    druzyny[1].dodaj_gracza(gracze[1]); druzyny[1].dodaj_gracza(gracze[3])
    
    rozdajacy_idx = (numer_rozdania - 1) % 4
    rozdanie = Rozdanie(gracze=gracze, druzyny=druzyny, rozdajacy_idx=rozdajacy_idx)
    
    print(f"Rozdającym jest: {gracze[rozdajacy_idx].nazwa}")
    rozdanie.rozpocznij_nowe_rozdanie()

    # === GŁÓWNA PĘTLA LICYTACJI (aż do rozpoczęcia rozgrywki) ===
    while rozdanie.faza != FazaGry.ROZGRYWKA:
        aktualny_gracz = rozdanie.gracze[rozdanie.kolej_gracza_idx]
        mozliwe_akcje = rozdanie.get_mozliwe_akcje(aktualny_gracz)

        if not mozliwe_akcje:
            print("INFO: Brak możliwych akcji, licytacja zakończona.")
            rozdanie.faza = FazaGry.ROZGRYWKA # Wymuś koniec licytacji
            break

        # Logowanie aktualnej fazy
        if rozdanie.faza == FazaGry.DEKLARACJA_1:
            print("\n--- ETAP: Deklaracja 1 ---")
            print(f"  Deklaruje: {aktualny_gracz.nazwa}")
        elif rozdanie.faza == FazaGry.LUFA:
            print("\n--- ETAP: Faza Lufy ---")
            print(f"  Decyzję podejmuje: {aktualny_gracz.nazwa}")
        elif rozdanie.faza == FazaGry.FAZA_PYTANIA:
            print("\n--- ETAP: Faza Pytania ---")
            print(f"  Ponownie decyduje: {aktualny_gracz.nazwa}")
        elif rozdanie.faza == FazaGry.LICYTACJA:
            print("\n--- ETAP: Licytacja 2 (Przebicie) ---")
            print(f"  Licytuje: {aktualny_gracz.nazwa}")

        # Symulacja decyzji i jej logowanie
        wybrana_akcja = random.choice(mozliwe_akcje)
        print(f"  Możliwe akcje: {formatuj_akcje(mozliwe_akcje)}")
        print(f"  Decyzja: {formatuj_akcje([wybrana_akcja])}")
        
        rozdanie.wykonaj_akcje(aktualny_gracz, wybrana_akcja)
      
  # === ETAP ROZGRYWKI ===
    if rozdanie.faza == FazaGry.ROZGRYWKA:
        print("\n" + "="*25)
        print("--- ETAP: Rozgrywka ---")
        if rozdanie.nieaktywny_gracz:
            print(f"INFO: Gra 1 vs 2. Gracz '{rozdanie.nieaktywny_gracz.nazwa}' nie bierze udziału w rozgrywce.")
        
        # POPRAWKA: Liczba lew zawsze wynosi 6
        liczba_lew = 6

        for numer_lewy in range(1, liczba_lew + 1):
            if rozdanie.rozdanie_zakonczone: break
            print(f"\n-- Lewa #{numer_lewy} --")
            
            # Pętla dla jednej lewy
            for i in range(rozdanie.liczba_aktywnych_graczy):
                aktualny_gracz = rozdanie.gracze[rozdanie.kolej_gracza_idx]
                
                if i == 0:
                    print(f"  Rozpoczyna: {aktualny_gracz.nazwa}")

                karta_do_zagrania = znajdz_legalny_ruch(rozdanie, aktualny_gracz)
                if karta_do_zagrania:
                    wynik_zagrania = rozdanie.zagraj_karte(aktualny_gracz, karta_do_zagrania)
                    komunikat = f"  [{aktualny_gracz.nazwa}] zagrywa: {karta_do_zagrania}"
                    if wynik_zagrania.get('meldunek_pkt', 0) > 0:
                        komunikat += f" (MELDUNEK! +{wynik_zagrania['meldunek_pkt']} pkt)"
                    print(komunikat)
                    
                    wynik_lewy = wynik_zagrania.get('wynik_lewy')
                    if wynik_lewy:
                        zwyciezca, punkty = wynik_lewy
                        print(f"  > Lewę wygrał {zwyciezca.nazwa}, zdobywając {punkty} pkt.")
                        print(f"  > Aktualny stan punktów: My {rozdanie.punkty_w_rozdaniu['My']} - {rozdanie.punkty_w_rozdaniu['Oni']} Oni")
                else:
                    print(f"BŁĄD KRYTYCZNY: Gracz {aktualny_gracz.nazwa} nie ma żadnego legalnego ruchu!")
                    return

    # KROK 7: Podsumowanie (Weryfikacja końcowa)
    if rozdanie.rozdanie_zakonczone and rozdanie.powod_zakonczenia:
         print(f"\n!!! Rozdanie zakończone przed czasem: {rozdanie.powod_zakonczenia} !!!")

    druzyna_wygrana, punkty_dodane, mnoznik = rozdanie.rozlicz_rozdanie()

    print("\n" + "="*25)
    print("--- WYNIK KOŃCOWY ROZDANIA ---")
    print(f"  Grany kontrakt: {rozdanie.kontrakt.name}")
    punkty_a = rozdanie.punkty_w_rozdaniu[druzyny[0].nazwa]
    punkty_b = rozdanie.punkty_w_rozdaniu[druzyny[1].nazwa]
    print(f"  Punkty z kart (z bonusem): {druzyny[0].nazwa} {punkty_a} - {punkty_b} {druzyny[1].nazwa}")
    
    print(f"  Rozdanie wygrywa: {druzyna_wygrana.nazwa}")
    print(f"  Przyznane punkty meczowe: {punkty_dodane} (mnożnik: x{mnoznik})")
    print(f"  OGÓLNY WYNIK MECZU: {druzyny[0].nazwa} {druzyny[0].punkty_meczu} - {druzyny[1].nazwa} {druzyny[1].punkty_meczu}")
    print("="*25 + "\n")

if __name__ == "__main__":
    # --- NOWA KONFIGURACJA SYMULACJI ---
    LICZBA_PARTII = 20
    NAZWA_PLIKU_LOGU = "log_finalny.txt"
    
    oryginalny_stdout = sys.stdout 
    with open(NAZWA_PLIKU_LOGU, 'w', encoding='utf-8') as f:
        sys.stdout = f
        
        for i in range(1, LICZBA_PARTII + 1):
            print("\n" + "#"*40)
            print(f"### ROZPOCZYNAMY PARTIĘ #{i} ###")
            print("#"*40 + "\n")
            
            # Tworzymy nowe, świeże drużyny dla każdej partii
            druzyna_a = Druzyna(nazwa="My")
            druzyna_b = Druzyna(nazwa="Oni")
            druzyna_a.przeciwnicy = druzyna_b
            druzyna_b.przeciwnicy = druzyna_a
            
            numer_rozdania_w_partii = 1
            # Pętla wewnętrzna - graj rozdania, aż ktoś wygra partię
            while druzyna_a.punkty_meczu < 66 and druzyna_b.punkty_meczu < 66:
                uruchom_symulacje_rozdania(numer_rozdania_w_partii, [druzyna_a, druzyna_b])
                numer_rozdania_w_partii += 1

            # Logowanie końca partii
            print("\n" + "#"*30)
            print("!!! KONIEC GRY !!!")
            zwyciezca_meczu = druzyna_a if druzyna_a.punkty_meczu >= 66 else druzyna_b
            print(f"Partię wygrywa drużyna: {zwyciezca_meczu.nazwa}")
            print(f"OSTATECZNY WYNIK: {druzyna_a.nazwa} {druzyna_a.punkty_meczu} - {druzyna_b.punkty_meczu} {druzyna_b.punkty_meczu}")
            print("#"*30)

    sys.stdout = oryginalny_stdout
    
    print(f"✅ Symulacja zakończona. Pełny log z {LICZBA_PARTII} partii został zapisany do pliku: {NAZWA_PLIKU_LOGU}")