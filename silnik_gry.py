import random
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Union, Optional

# Krok 1: Definiujemy "atomy" gry
class Kolor(Enum):
    CZERWIEN = auto()
    DZWONEK = auto()
    ZOLADZ = auto()
    WINO = auto()

class Ranga(Enum):
    DZIEWIATKA = auto()
    WALET = auto()
    DAMA = auto()
    KROL = auto()
    DZIESIATKA = auto()
    AS = auto()

WARTOSCI_KART = {
    Ranga.AS: 11, Ranga.DZIESIATKA: 10, Ranga.KROL: 4,
    Ranga.DAMA: 3, Ranga.WALET: 2, Ranga.DZIEWIATKA: 0,
}

@dataclass(frozen=True)
class Karta:
    ranga: Ranga
    kolor: Kolor

    @property
    def wartosc(self) -> int:
        return WARTOSCI_KART[self.ranga]

    def __str__(self) -> str:
        return f"{self.ranga.name.capitalize()} {self.kolor.name.capitalize()}"

class Talia:
    def __init__(self):
        self.karty = self._stworz_pelna_talie()
        self.tasuj()

    def _stworz_pelna_talie(self) -> list['Karta']:
        return [Karta(ranga, kolor) for kolor in Kolor for ranga in Ranga]

    def tasuj(self):
        random.shuffle(self.karty)

    def rozdaj_karte(self) -> Union['Karta', None]:
        if self.karty:
            return self.karty.pop()
        return None

    def __len__(self) -> int:
        return len(self.karty)

@dataclass
class Gracz:
    """Reprezentuje pojedynczego gracza."""
    nazwa: str
    reka: list[Karta] = field(default_factory=list)
    druzyna: Optional['Druzyna'] = None
    wygrane_karty: list[Karta] = field(default_factory=list) # <-- NOWY ATRYBUT

    def __str__(self) -> str:
        return self.nazwa

@dataclass
class Druzyna:
    """Reprezentuje drużynę złożoną z dwóch graczy."""
    nazwa: str
    gracze: list[Gracz] = field(default_factory=list)
    punkty_meczu: int = 0
    przeciwnicy: 'Druzyna' = None 
    def dodaj_gracza(self, gracz: Gracz):
        """Dodaje gracza do drużyny i ustawia mu referencję do tej drużyny."""
        if len(self.gracze) < 2:
            self.gracze.append(gracz)
            gracz.druzyna = self

class Kontrakt(Enum):
    """Definiuje możliwe typy kontraktów w grze."""
    NORMALNA = auto()
    BEZ_PYTANIA = auto()
    GORSZA = auto()
    LEPSZA = auto()

STAWKI_KONTRAKTOW = {
    Kontrakt.NORMALNA: 1, # Bazowa stawka, później mnożona przez 1, 2 lub 3
    Kontrakt.BEZ_PYTANIA: 6,
    Kontrakt.GORSZA: 6,
    Kontrakt.LEPSZA: 12,
}

class Rozdanie:
    def __init__(self, gracze: list[Gracz], druzyny: list[Druzyna], rozdajacy_idx: int):
        self.gracze = gracze; self.druzyny = druzyny; self.rozdajacy_idx = rozdajacy_idx
        self.talia = Talia()
        self.kontrakt: Optional[Kontrakt] = None; self.grajacy: Optional[Gracz] = None
        self.atut: Optional[Kolor] = None; self.stawka = 0
        self.punkty_w_rozdaniu = {druzyny[0].nazwa: 0, druzyny[1].nazwa: 0}
        self.kolej_gracza_idx: Optional[int] = None
        self.aktualna_lewa: list[tuple[Gracz, Karta]] = []
        self.zadeklarowane_meldunki: list[tuple[Gracz, Kolor]] = []
        
        self.rozdanie_zakonczone: bool = False
        self.zwyciezca_rozdania: Optional[Druzyna] = None
        self.powod_zakonczenia: str = ""
        self.zwyciezca_ostatniej_lewy: Optional[Gracz] = None
    def rozdaj_karty(self, ilosc: int):
        start_idx = (self.rozdajacy_idx + 1) % 4
        for _ in range(ilosc):
            for i in range(4):
                idx = (start_idx + i) % 4
                karta = self.talia.rozdaj_karte()
                if karta: self.gracze[idx].reka.append(karta)
    
    def rozlicz_rozdanie(self) -> tuple[Druzyna, int, int]:
        """FINALNA WERSJA: Prawidłowo oblicza i przyznaje punkty meczowe."""
        druzyna_grajacego = self.grajacy.druzyna
        
        # Krok 1: Ustal ostatecznego zwycięzcę rozdania
        if self.rozdanie_zakonczone and self.zwyciezca_rozdania:
            # Jeśli rozdanie zakończyło się wcześniej, zwycięzca jest już znany. To jest najważniejszy warunek.
            druzyna_wygrana = self.zwyciezca_rozdania
        else:
            # Jeśli rozdanie trwało do końca (6 lew), rozstrzygamy na podstawie punktów
            if self.zwyciezca_ostatniej_lewy:
                druzyna_bonus = self.zwyciezca_ostatniej_lewy.druzyna
                self.punkty_w_rozdaniu[druzyna_bonus.nazwa] += 12
            
            punkty_grajacego = self.punkty_w_rozdaniu[druzyna_grajacego.nazwa]
            punkty_przeciwnikow = self.punkty_w_rozdaniu[druzyna_grajacego.przeciwnicy.nazwa]

            # TODO: Dodać logikę dla wygranej w Gorsza/Lepsza do końca
            if punkty_grajacego > punkty_przeciwnikow:
                druzyna_wygrana = druzyna_grajacego
            else: # W przypadku remisu lub mniejszej liczby punktów, grający przegrywa
                druzyna_wygrana = druzyna_grajacego.przeciwnicy
        
        druzyna_przegrana = druzyna_wygrana.przeciwnicy
        punkty_przegranego = self.punkty_w_rozdaniu[druzyna_przegrana.nazwa]
        
        # Krok 2: Oblicz punkty meczowe
        mnoznik = 1
        punkty_meczu = STAWKI_KONTRAKTOW.get(self.kontrakt, 0)

        if self.kontrakt == Kontrakt.NORMALNA:
            if punkty_przegranego < 33:
                mnoznik = 2 # Schneider
                if not any(len(gracz.wygrane_karty) > 0 for gracz in druzyna_przegrana.gracze):
                    mnoznik = 3 # Schwarz
            punkty_meczu *= mnoznik
        
        druzyna_wygrana.punkty_meczu += punkty_meczu
        return druzyna_wygrana, punkty_meczu, mnoznik
    def przeprowadz_licytacje(self, wybrany_kontrakt: Kontrakt, wybrany_atut: Optional[Kolor]):
        """Ustawia stan gry na podstawie ZEWNĘTRZNEJ decyzji licytacyjnej."""
        # Ta metoda już niczego nie losuje - jest tylko wykonawcą.
        self.grajacy = self.gracze[(self.rozdajacy_idx + 1) % 4]
        
        self.kontrakt = wybrany_kontrakt
        self.atut = wybrany_atut
        
        if self.kontrakt in [Kontrakt.GORSZA, Kontrakt.LEPSZA] and self.atut is not None:
            self.atut = None
            
        self.stawka = 1 # Na razie uproszczone
        self.kolej_gracza_idx = self.gracze.index(self.grajacy)
        
    def _waliduj_ruch(self, gracz: Gracz, karta: Karta) -> bool:
        if gracz != self.gracze[self.kolej_gracza_idx]: return False
        if karta not in gracz.reka: return False
        if not self.aktualna_lewa: return True
        kolor_wiodacy = self.aktualna_lewa[0][1].kolor
        reka_gracza = gracz.reka
        karty_do_koloru = [k for k in reka_gracza if k.kolor == kolor_wiodacy]
        if karty_do_koloru: return karta.kolor == kolor_wiodacy
        if self.atut:
            karty_atutowe = [k for k in reka_gracza if k.kolor == self.atut]
            if karty_atutowe: return karta.kolor == self.atut
        return True

    def _zakoncz_lewe(self):
        
        kolor_wiodacy = self.aktualna_lewa[0][1].kolor
        karty_atutowe = [(g, k) for g, k in self.aktualna_lewa if k.kolor == self.atut]
        if karty_atutowe: zwyciezca_pary = max(karty_atutowe, key=lambda p: p[1].ranga.value)
        else:
            karty_wiodace = [(g, k) for g, k in self.aktualna_lewa if k.kolor == kolor_wiodacy]
            zwyciezca_pary = max(karty_wiodace, key=lambda p: p[1].ranga.value)
        zwyciezca_lewy = zwyciezca_pary[0]
        punkty_w_lewie = sum(karta.wartosc for _, karta in self.aktualna_lewa)
        
        druzyna_zwyciezcy = zwyciezca_lewy.druzyna
        self.punkty_w_rozdaniu[druzyna_zwyciezcy.nazwa] += punkty_w_lewie
        zwyciezca_lewy.wygrane_karty.extend([karta for _, karta in self.aktualna_lewa])
        liczba_wygranych_kart = sum(len(g.wygrane_karty) for g in self.gracze)
        if liczba_wygranych_kart == 24:
            self.zwyciezca_ostatniej_lewy = zwyciezca_lewy

        
        # --- NOWA LOGIKA SPRAWDZANIA KOŃCA ROZDANIA ---
        if self.kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA]:
            if self.punkty_w_rozdaniu[druzyna_zwyciezcy.nazwa] >= 66:
                self.rozdanie_zakonczone = True
                self.zwyciezca_rozdania = druzyna_zwyciezcy
                self.powod_zakonczenia = f"osiągnięcie {self.punkty_w_rozdaniu[druzyna_zwyciezcy.nazwa]} punktów"

        if not self.rozdanie_zakonczone:
            if self.kontrakt == Kontrakt.BEZ_PYTANIA and zwyciezca_lewy != self.grajacy:
                self.rozdanie_zakonczone = True
                self.zwyciezca_rozdania = druzyna_zwyciezcy # Przeciwnicy wygrywają
                self.powod_zakonczenia = f"przejęcie lewy przez gracza {zwyciezca_lewy.nazwa}"
            elif self.kontrakt == Kontrakt.LEPSZA and zwyciezca_lewy.druzyna != self.grajacy.druzyna:
                self.rozdanie_zakonczone = True
                self.zwyciezca_rozdania = zwyciezca_lewy.druzyna
                self.powod_zakonczenia = "przejęcie lewy przez przeciwnika"
            elif self.kontrakt == Kontrakt.GORSZA and zwyciezca_lewy == self.grajacy:
                self.rozdanie_zakonczone = True
                self.zwyciezca_rozdania = zwyciezca_lewy.druzyna.przeciwnicy # UWAGA: to musimy dodać
                self.powod_zakonczenia = f"wzięcie lewy przez gracza {self.grajacy.nazwa}"

        self.aktualna_lewa.clear()
        self.kolej_gracza_idx = self.gracze.index(zwyciezca_lewy)
        
    def zagraj_karte(self, gracz: Gracz, karta: Karta) -> int:
        """Wykonuje ruch, sprawdza meldunek i zwraca punkty z meldunku."""
        if not self._waliduj_ruch(gracz, karta):
            print(f"BŁĄD: Ruch gracza {gracz} kartą {karta} jest nielegalny!")
            return 0

        punkty_z_meldunku = 0
        # --- NOWA LOGIKA MELDUNKU ---
        # Sprawdź meldunek tylko jeśli to pierwsza karta w lewie i odpowiedni kontrakt
        if not self.aktualna_lewa and self.kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA]:
            if karta.ranga == Ranga.KROL or karta.ranga == Ranga.DAMA:
                # Sprawdź, czy gracz ma drugą kartę do pary
                szukana_ranga = Ranga.DAMA if karta.ranga == Ranga.KROL else Ranga.KROL
                if any(k.ranga == szukana_ranga and k.kolor == karta.kolor for k in gracz.reka):
                    # Sprawdź, czy ten meldunek nie był już zgłoszony
                    if (gracz, karta.kolor) not in self.zadeklarowane_meldunki:
                        punkty_z_meldunku = 40 if karta.kolor == self.atut else 20
                        self.punkty_w_rozdaniu[gracz.druzyna.nazwa] += punkty_z_meldunku
                        self.zadeklarowane_meldunki.append((gracz, karta.kolor))

        gracz.reka.remove(karta)
        self.aktualna_lewa.append((gracz, karta))
        
        if len(self.aktualna_lewa) == 4:
            self._zakoncz_lewe()
        else:
            self.kolej_gracza_idx = (self.kolej_gracza_idx + 1) % 4
            
        return punkty_z_meldunku
