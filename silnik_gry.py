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
        self.kolej_gracza_idx: Optional[int] = None
        self.aktualna_lewa: list[tuple[Gracz, Karta]] = []

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
        self.kolej_gracza_idx = self.gracze.index(self.grajacy)
        
    def _waliduj_ruch(self, gracz: Gracz, karta: Karta) -> bool:
        """Sprawdza, czy zagranie karty przez gracza jest zgodne z zasadami."""
        # Podstawowe sprawdzenia
        if gracz != self.gracze[self.kolej_gracza_idx]: return False
        if karta not in gracz.reka: return False

        # Jeśli to pierwsza karta w lewie, każdy ruch jest dozwolony
        if not self.aktualna_lewa:
            return True

        # Logika dla kolejnych kart w lewie
        kolor_wiodacy = self.aktualna_lewa[0][1].kolor
        reka_gracza = gracz.reka

        # 1. Sprawdź obowiązek koloru
        karty_do_koloru = [k for k in reka_gracza if k.kolor == kolor_wiodacy]
        if karty_do_koloru:
            return karta.kolor == kolor_wiodacy

        # 2. Jeśli nie ma koloru, sprawdź obowiązek grania atutem
        # (Ta zasada nie obowiązuje w kontraktach bez atutu)
        if self.atut:
            karty_atutowe = [k for k in reka_gracza if k.kolor == self.atut]
            if karty_atutowe:
                return karta.kolor == self.atut
        
        # 3. Jeśli gracz nie ma kart do koloru ani atutów (lub nie musi ich użyć),
        # może zagrać dowolną kartą.
        return True

    def _zakoncz_lewe(self):
        """Logika kończąca lewę: wyłania zwycięzcę, liczy punkty i czyści stół."""
        if not self.aktualna_lewa:
            return

        # Ustalenie koloru wiodącego (kolor pierwszej zagranej karty)
        kolor_wiodacy = self.aktualna_lewa[0][1].kolor
        
        # Znajdź najsilniejszą kartę atutową na stole
        karty_atutowe = [(gracz, karta) for gracz, karta in self.aktualna_lewa if karta.kolor == self.atut]
        
        if karty_atutowe:
            # Jeśli są atuty, wygrywa najsilniejszy atut
            zwyciezca_pary = max(karty_atutowe, key=lambda para: para[1].ranga.value)
        else:
            # Jeśli nie ma atutów, wygrywa najsilniejsza karta w kolorze wiodącym
            karty_wiodace = [(gracz, karta) for gracz, karta in self.aktualna_lewa if karta.kolor == kolor_wiodacy]
            zwyciezca_pary = max(karty_wiodace, key=lambda para: para[1].ranga.value)

        zwyciezca_lewy = zwyciezca_pary[0]
        punkty_w_lewie = sum(karta.wartosc for _, karta in self.aktualna_lewa)
        
        self.punkty_w_rozdaniu[zwyciezca_lewy.druzyna.nazwa] += punkty_w_lewie
        zwyciezca_lewy.wygrane_karty.extend([karta for _, karta in self.aktualna_lewa])
        
        self.aktualna_lewa.clear()
        self.kolej_gracza_idx = self.gracze.index(zwyciezca_lewy)
        
        # TODO: W przyszłości dodamy tu sprawdzanie, czy rozdanie się nie zakończyło
        # (np. osiągnięcie 66 pkt, przegranie kontraktu Lepsza/Gorsza)
        
        return zwyciezca_lewy, punkty_w_lewie

    def zagraj_karte(self, gracz: Gracz, karta: Karta):
        if not self._waliduj_ruch(gracz, karta):
            # W przyszłości można tu zgłosić błąd, na razie cicho ignorujemy
            print(f"BŁĄD: Ruch gracza {gracz} kartą {karta} jest nielegalny!")
            return

        gracz.reka.remove(karta)
        self.aktualna_lewa.append((gracz, karta))
        
        if len(self.aktualna_lewa) == 4:
            self._zakoncz_lewe()
        else:
            # Przekaż kolejkę następnemu graczowi tylko jeśli lewa się nie skończyła
            self.kolej_gracza_idx = (self.kolej_gracza_idx + 1) % 4
