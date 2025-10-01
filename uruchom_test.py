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

    # Setup (bez zmian)
    gracze = [
        Gracz(nazwa="Jakub"), Gracz(nazwa="Przeciwnik1"),
        Gracz(nazwa="Nasz"), Gracz(nazwa="Przeciwnik2")
    ]
    for gracz in gracze: gracz.reka.clear(); gracz.wygrane_karty.clear()
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
    
    # KROK 1: Rozdanie 3 kart
    rozdanie.rozpocznij_nowe_rozdanie()
    print("\n--- ETAP: Rozdanie 3 kart ---")
    for gracz in gracze:
        print(f"  Ręka gracza '{gracz.nazwa}': {', '.join(map(str, gracz.reka))}")

    # KROK 2: Deklaracja 1
    if rozdanie.faza == FazaGry.DEKLARACJA_1:
        print("\n--- ETAP: Deklaracja 1 ---")
        gracz_deklarujacy = rozdanie.gracze[rozdanie.kolej_gracza_idx]
        print(f"  Deklaruje: {gracz_deklarujacy.nazwa}")
        mozliwe_akcje = rozdanie.get_mozliwe_akcje(gracz_deklarujacy)
        print(f"  Możliwe akcje: {formatuj_akcje(mozliwe_akcje)}")
        wybrana_akcja = random.choice(mozliwe_akcje)
        kontrakt_info = wybrana_akcja['kontrakt'].name
        atut_str = wybrana_akcja.get('atut', {}).name if wybrana_akcja.get('atut') else "Brak"
        print(f"  Decyzja: {kontrakt_info}, Atut: {atut_str}")
        rozdanie.wykonaj_akcje(gracz_deklarujacy, wybrana_akcja)

    # KROK 3: Faza Lufy 1 (na razie tylko szkielet)
    if rozdanie.faza == FazaGry.LUFA:
        print("\n--- ETAP: Faza Lufy 1 ---")
        gracz_odpowiadajacy = rozdanie.gracze[rozdanie.kolej_gracza_idx]
        print(f"  Decyzję podejmuje: {gracz_odpowiadajacy.nazwa}")
        # Na razie symulujemy pas
        akcja_lufa = {'typ': 'pas_lufa'}
        print("  Decyzja: Pas")
        rozdanie.wykonaj_akcje(gracz_odpowiadajacy, akcja_lufa)


    # KROK 4: Faza Pytania
    if rozdanie.faza == FazaGry.FAZA_PYTANIA:
        print("\n--- ETAP: Faza Pytania ---")
        gracz_pytajacy = rozdanie.gracze[rozdanie.kolej_gracza_idx]
        print(f"  Ponownie decyduje: {gracz_pytajacy.nazwa}")
        mozliwe_akcje_2 = rozdanie.get_mozliwe_akcje(gracz_pytajacy)
        print(f"  Możliwe akcje: {formatuj_akcje(mozliwe_akcje_2)}")
        wybrana_akcja_2 = random.choice(mozliwe_akcje_2)
        decyzja_str = f"Zmień na {wybrana_akcja_2['kontrakt'].name}" if wybrana_akcja_2['typ'] == 'zmiana_kontraktu' else "Pytam"
        print(f"  Decyzja: {decyzja_str}")
        rozdanie.wykonaj_akcje(gracz_pytajacy, wybrana_akcja_2)

    # KROK 5: Licytacja 2 (Przebicie)
    if rozdanie.faza == FazaGry.LICYTACJA:
        print("\n--- ETAP: Licytacja 2 (Przebicie) ---")
        for _ in range(3):
            if rozdanie.faza != FazaGry.LICYTACJA: break
            licytujacy = rozdanie.gracze[rozdanie.kolej_gracza_idx]
            mozliwe_akcje = rozdanie.get_mozliwe_akcje(licytujacy)
            if not mozliwe_akcje: continue
            print(f"  Licytuje: {licytujacy.nazwa}")
            print(f"  Możliwe akcje: {formatuj_akcje(mozliwe_akcje)}")
            wybrana_akcja_3 = random.choice(mozliwe_akcje)
            decyzja_str = "Pas"
            if wybrana_akcja_3['typ'] == 'przebicie':
                decyzja_str = f"Przebijam na {wybrana_akcja_3['kontrakt'].name}"
            print(f"  Decyzja: {decyzja_str}")
            rozdanie.wykonaj_akcje(licytujacy, wybrana_akcja_3)
      
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
                print(f"OSTATECZNY WYNIK: {druzyna_a.nazwa} {druzyna_a.punkty_meczu} - {druzyna_b.nazwa} {druzyna_b.punkty_meczu}")
                print("#"*30)
                break
                
    sys.stdout = oryginalny_stdout
    
    print(f"✅ Symulacja zakończona. Pełny log został zapisany do pliku: {NAZWA_PLIKU_LOGU}")