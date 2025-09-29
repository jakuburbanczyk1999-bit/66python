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

class Rozdanie:
    """Główna klasa silnika, zarządzająca stanem i logiką jednego rozdania."""

    def __init__(self, gracze: list[Gracz], druzyny: list[Druzyna], rozdajacy_idx: int):
        self.gracze = gracze
        self.druzyny = druzyny
        self.rozdajacy_idx = rozdajacy_idx
        self.talia = Talia()
        
        self.kontrakt: Optional[Kontrakt] = None
        self.grajacy: Optional[Gracz] = None
        self.atut: Optional[Kolor] = None
        self.stawka = 0
        
        self.punkty_w_rozdaniu = {druzyny[0].nazwa: 0, druzyny[1].nazwa: 0}
        
        # NOWE ATRYBUTY DO ZARZĄDZANIA ROZGRYWKĄ
        self.kolej_gracza_idx: Optional[int] = None
        self.aktualna_lewa: list[tuple[Gracz, Karta]] = [] # Lista par (gracz, zagrana karta)

    def rozdaj_karty(self, ilosc: int):
        start_idx = (self.rozdajacy_idx + 1) % 4
        for _ in range(ilosc):
            for i in range(4):
                idx = (start_idx + i) % 4
                karta = self.talia.rozdaj_karte()
                if karta:
                    self.gracze[idx].reka.append(karta)
    
    def przeprowadz_licytacje(self, wybrany_kontrakt: Kontrakt, wybrany_atut: Optional[Kolor]):
        self.grajacy = self.gracze[(self.rozdajacy_idx + 1) % 4]
        self.kontrakt = wybrany_kontrakt
        self.atut = wybrany_atut
        
        if self.kontrakt in [Kontrakt.GORSZA, Kontrakt.LEPSZA] and self.atut is not None:
            self.atut = None
            
        self.stawka = 1
        
        # Ustawienie gracza rozpoczynającego pierwszą lewę
        self.kolej_gracza_idx = self.gracze.index(self.grajacy)
        
    # --- NOWE METODY ---
    def _waliduj_ruch(self, gracz: Gracz, karta: Karta) -> bool:
        """Sprawdza, czy zagranie karty przez gracza jest legalne."""
        # Na razie bardzo prosta walidacja. Rozbudujemy ją w kolejnym kroku.
        if gracz != self.gracze[self.kolej_gracza_idx]:
            print(f"BŁĄD WALIDACJI: Nie jest kolej gracza {gracz.nazwa}!")
            return False
        if karta not in gracz.reka:
            print(f"BŁĄD WALIDACJI: Gracz {gracz.nazwa} nie ma karty {karta}!")
            return False
        
        # TODO: Dodać logikę obowiązku koloru, przebijania, grania atutem.
        return True

    def zagraj_karte(self, gracz: Gracz, karta: Karta):
        """Wykonuje ruch zagrania karty przez gracza."""
        if not self._waliduj_ruch(gracz, karta):
            return # Przerwij, jeśli ruch jest nielegalny

        gracz.reka.remove(karta)
        self.aktualna_lewa.append((gracz, karta))
        
        # Przekaż kolejkę następnemu graczowi
        self.kolej_gracza_idx = (self.kolej_gracza_idx + 1) % 4
        
        # TODO: Dodać logikę kończenia lewy po 4 zagraniach.