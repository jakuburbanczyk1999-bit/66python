import random
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Union, Optional

logger = logging.getLogger('szesc_szesc_logger')

class Kolor(Enum):
    CZERWIEN, DZWONEK, ZOLADZ, WINO = auto(), auto(), auto(), auto()

class Ranga(Enum):
    DZIEWIATKA, WALET, DAMA, KROL, DZIESIATKA, AS = auto(), auto(), auto(), auto(), auto(), auto()

WARTOSCI_KART = { Ranga.AS: 11, Ranga.DZIESIATKA: 10, Ranga.KROL: 4, Ranga.DAMA: 3, Ranga.WALET: 2, Ranga.DZIEWIATKA: 0 }

@dataclass(frozen=True)
class Karta:
    ranga: Ranga
    kolor: Kolor
    @property
    def wartosc(self) -> int: return WARTOSCI_KART[self.ranga]
    def __str__(self) -> str: return f"{self.ranga.name.capitalize()} {self.kolor.name.capitalize()}"
    @property
    def nazwa_pliku(self) -> str: return f"{self.ranga.name.capitalize()}{self.kolor.name.capitalize()}.png"

class Talia:
    def __init__(self):
        self.karty = [Karta(r, k) for k in Kolor for r in Ranga]
        self.tasuj()
    def tasuj(self): random.shuffle(self.karty)
    def rozdaj_karte(self) -> Optional['Karta']: return self.karty.pop() if self.karty else None

@dataclass
class Gracz:
    nazwa: str
    reka: list[Karta] = field(default_factory=list)
    druzyna: Optional['Druzyna'] = None
    wygrane_karty: list[Karta] = field(default_factory=list)
    def __str__(self) -> str: return self.nazwa

@dataclass
class Druzyna:
    nazwa: str
    gracze: list[Gracz] = field(default_factory=list)
    punkty_meczu: int = 0
    przeciwnicy: 'Druzyna' = None
    def dodaj_gracza(self, gracz: Gracz):
        if len(self.gracze) < 2:
            self.gracze.append(gracz)
            gracz.druzyna = self

class Kontrakt(Enum):
    NORMALNA, BEZ_PYTANIA, GORSZA, LEPSZA = auto(), auto(), auto(), auto()

class FazaGry(Enum):
    PRZED_ROZDANIEM, DEKLARACJA_1, LICYTACJA, LUFA, ROZGRYWKA, ZAKONCZONE, FAZA_PYTANIA = auto(), auto(), auto(), auto(), auto(), auto(), auto()

STAWKI_KONTRAKTOW = { Kontrakt.NORMALNA: 1, Kontrakt.BEZ_PYTANIA: 6, Kontrakt.GORSZA: 6, Kontrakt.LEPSZA: 12 }

class Rozdanie:
    def __init__(self, gracze: list[Gracz], druzyny: list[Druzyna], rozdajacy_idx: int):
        self.gracze = gracze
        for gracz in self.gracze:
            gracz.reka.clear()
            gracz.wygrane_karty.clear()
        self.druzyny = druzyny; self.rozdajacy_idx = rozdajacy_idx
        self.talia = Talia(); self.kontrakt: Optional[Kontrakt] = None; self.grajacy: Optional[Gracz] = None
        self.atut: Optional[Kolor] = None; self.mnoznik_lufy: int = 1; self.czy_byla_lufa: bool = False
        self.punkty_w_rozdaniu = {d.nazwa: 0 for d in druzyny}; self.kolej_gracza_idx: Optional[int] = None
        self.aktualna_lewa: list[tuple[Gracz, Karta]] = []; self.zadeklarowane_meldunki: list[tuple[Gracz, Kolor]] = []
        self.rozdanie_zakonczone: bool = False; self.powod_zakonczenia: str = ""
        self.zwyciezca_rozdania: Optional[Druzyna] = None; self.zwyciezca_ostatniej_lewy: Optional[Gracz] = None
        self.faza: FazaGry = FazaGry.PRZED_ROZDANIEM
        self.historia_licytacji: list[tuple[Gracz, dict]] = []; self.historia_akcji: list[str] = []
        self.pasujacy_gracze: list[Gracz] = []; self.oferty_przebicia: list[tuple[Gracz, dict]] = []
        self.nieaktywny_gracz: Optional[Gracz] = None; self.liczba_aktywnych_graczy = 4; self.numer_lewy = 0
        self.ostatni_podbijajacy: Optional[Gracz] = None

    def _nastepna_tura(self):
        if self.kolej_gracza_idx is None: return
        for _ in range(4):
            self.kolej_gracza_idx = (self.kolej_gracza_idx + 1) % 4
            aktualny_gracz = self.gracze[self.kolej_gracza_idx]
            
            # Warunek 1: Pomiń gracza nieaktywnego (w 'Gorsza'/'Lepsza')
            if aktualny_gracz == self.nieaktywny_gracz:
                continue
            
            # Warunek 2: Pomiń partnera grającego ZAWSZE w fazie LUFA
            is_partner_of_declarer = self.grajacy and \
                                     aktualny_gracz.druzyna == self.grajacy.druzyna and \
                                     aktualny_gracz != self.grajacy
            if self.faza == FazaGry.LUFA and is_partner_of_declarer:
                continue
            
            # Jeśli gracz jest aktywny, zakończ
            return

    def _ustaw_kontrakt(self, gracz_grajacy: Gracz, kontrakt: Kontrakt, atut: Optional[Kolor]):
        self.grajacy, self.kontrakt, self.atut = gracz_grajacy, kontrakt, atut
        self.nieaktywny_gracz, self.liczba_aktywnych_graczy = None, 4
        if self.kontrakt in [Kontrakt.LEPSZA, Kontrakt.GORSZA]:
            self.atut, self.liczba_aktywnych_graczy = None, 3
            self.nieaktywny_gracz = next(p for p in self.grajacy.druzyna.gracze if p != self.grajacy)
        atut_str = f"w {self.atut.name.capitalize()}" if self.atut else "bez atu"
        logger.info(f"  * [KONTRAKT] {self.grajacy.nazwa} gra {self.kontrakt.name} ({atut_str})")
        self.historia_akcji.append(f"INFO:{self.grajacy.nazwa} gra {self.kontrakt.name} ({atut_str})")

    def _oblicz_limit_stawki(self) -> int:
        punkty_a, punkty_b = self.druzyny[0].punkty_meczu, self.druzyny[1].punkty_meczu
        return 66 - min(punkty_a, punkty_b)

    def _czy_lufa_mozliwa(self) -> bool:
        stawka_bazowa = STAWKI_KONTRAKTOW.get(self.kontrakt, 1)
        return stawka_bazowa * (self.mnoznik_lufy * 2) <= self._oblicz_limit_stawki()

    def rozpocznij_nowe_rozdanie(self):
        self.rozdaj_karty(3); self.faza = FazaGry.DEKLARACJA_1; self.kolej_gracza_idx = (self.rozdajacy_idx + 1) % 4

    def get_mozliwe_akcje(self, gracz: Gracz) -> list[dict]:
        if gracz != self.gracze[self.kolej_gracza_idx]: return []

        if self.faza == FazaGry.LUFA:
            is_partner_of_declarer = self.grajacy and gracz.druzyna == self.grajacy.druzyna and gracz != self.grajacy
            if is_partner_of_declarer:
                return [] # Partner grającego nigdy nie bierze udziału w lufie
            if self.ostatni_podbijajacy and gracz.druzyna == self.ostatni_podbijajacy.druzyna:
                return [{'typ': 'pas_lufa'}]
            akcja_podbicia = {'typ': 'kontra'} if gracz == self.grajacy else {'typ': 'lufa'}
            if self._czy_lufa_mozliwa():
                return [akcja_podbicia, {'typ': 'pas_lufa'}]
            else:
                return [{'typ': 'pas_lufa'}]

        if self.faza == FazaGry.DEKLARACJA_1:
            akcje = [{'typ': 'deklaracja', 'kontrakt': k, 'atut': c} for k in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA] for c in Kolor]
            akcje.extend([{'typ': 'deklaracja', 'kontrakt': k, 'atut': None} for k in [Kontrakt.GORSZA, Kontrakt.LEPSZA]])
            return akcje

        if self.faza == FazaGry.FAZA_PYTANIA:
            return [{'typ': 'zmiana_kontraktu', 'kontrakt': k} for k in [Kontrakt.LEPSZA, Kontrakt.GORSZA, Kontrakt.BEZ_PYTANIA]] + [{'typ': 'pytanie'}]

        if self.faza == FazaGry.LICYTACJA:
            is_opponent = self.grajacy and gracz.druzyna != self.grajacy.druzyna
            if not is_opponent: # Partner grającego może tylko spasować
                return [{'typ': 'pas'}]
            else: # Przeciwnicy mogą przebić, spasować lub dać lufę
                akcje = [{'typ': 'pas'}, {'typ': 'przebicie', 'kontrakt': Kontrakt.LEPSZA}, {'typ': 'przebicie', 'kontrakt': Kontrakt.GORSZA}]
                if self._czy_lufa_mozliwa():
                    akcje.append({'typ': 'lufa'})
                return akcje

        return []

    def _zakoncz_licytacje(self):
        self.faza = FazaGry.ROZGRYWKA
        self.kolej_gracza_idx = self.gracze.index(self.grajacy)
        if len(self.gracze[0].reka) < 6:
            self.rozdaj_karty(3)
        logger.info("  - [LICYTACJA] Licytacja zakończona, początek rozgrywki.")
        self.historia_akcji.append("INFO:Licytacja zakończona")

    # ✅ === POCZĄTEK ZMIANY: Całkowicie nowa logika fazy LUFA ===
    def wykonaj_akcje(self, gracz: Gracz, akcja: dict):
        self.historia_licytacji.append((gracz, akcja))
        opis_akcji = akcja['typ'].upper()
        if 'kontrakt' in akcja: opis_akcji += f" {akcja['kontrakt'].name}"
        if 'atut' in akcja and akcja['atut']: opis_akcji += f" w {akcja['atut'].name}"
        logger.info(f"    [AKCJA] {gracz.nazwa}: {opis_akcji}")
        self.historia_akcji.append(f"INFO:{gracz.nazwa}:{opis_akcji}")

        if self.faza == FazaGry.DEKLARACJA_1 and akcja['typ'] == 'deklaracja':
            self._ustaw_kontrakt(gracz, akcja['kontrakt'], akcja.get('atut'))
            self.faza = FazaGry.LUFA
            self.kolej_gracza_idx = self.gracze.index(self.grajacy)
            self._nastepna_tura()

        # ✅ === POCZĄTEK ZMIANY: Poprawiona logika przekazywania tury po lufie/kontrze ===
        elif self.faza == FazaGry.LUFA:
            if akcja['typ'] in ['lufa', 'kontra']:
                self.mnoznik_lufy *= 2
                self.czy_byla_lufa = True
                self.ostatni_podbijajacy = gracz
                self.pasujacy_gracze.clear()
                
                if gracz == self.grajacy:
                    # Grający dał 'kontrę', tura wraca do aktywnego przeciwnika
                    przeciwnik = next(p for p in gracz.druzyna.przeciwnicy.gracze if p != self.nieaktywny_gracz and p not in self.pasujacy_gracze)
                    self.kolej_gracza_idx = self.gracze.index(przeciwnik)
                else:
                    # Przeciwnik dał 'lufę', tura ZAWSZE wraca do grającego
                    self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                return

            elif akcja['typ'] == 'pas_lufa':
                self.pasujacy_gracze.append(gracz)
                
                przeciwnicy_grajacego = [p for p in self.grajacy.druzyna.przeciwnicy.gracze if p != self.nieaktywny_gracz]
                if len(self.gracze[0].reka) < 6 and all(p in self.pasujacy_gracze for p in przeciwnicy_grajacego):
                    logger.info("  - [LICYTACJA] Koniec pierwszej tury lufy, dobieranie kart.")
                    self.rozdaj_karty(3)
                    if self.czy_byla_lufa or self.kontrakt != Kontrakt.NORMALNA:
                        self._zakoncz_licytacje()
                    else:
                        self.faza = FazaGry.FAZA_PYTANIA
                        self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                    return

                if self.ostatni_podbijajacy:
                    druzyna_odpowiadajaca = self.ostatni_podbijajacy.druzyna.przeciwnicy
                    if gracz.druzyna == druzyna_odpowiadajaca:
                        logger.info(f"  - [LICYTACJA] {gracz.nazwa} pasuje, kończąc lufę.")
                        self._zakoncz_licytacje()
                    else:
                        self._nastepna_tura()
                else:
                    self._nastepna_tura()
        # ✅ === KONIEC ZMIANY ===

        elif self.faza == FazaGry.FAZA_PYTANIA:
            if akcja['typ'] == 'zmiana_kontraktu':
                self._ustaw_kontrakt(self.grajacy, akcja['kontrakt'], self.atut)
                self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = self.grajacy
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()
            elif akcja['typ'] == 'pytanie':
                self.faza = FazaGry.LICYTACJA
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()

        elif self.faza == FazaGry.LICYTACJA:
            if akcja['typ'] == 'lufa':
                self.czy_byla_lufa = True; self.mnoznik_lufy *= 2; self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = gracz
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                return
            if akcja['typ'] == 'pas':
                self.pasujacy_gracze.append(gracz)
            elif akcja['typ'] == 'przebicie':
                self.oferty_przebicia.append((gracz, akcja))
            if len(self.pasujacy_gracze) + len(self.oferty_przebicia) >= 3:
                self._rozstrzygnij_licytacje_2()
            else:
                self._nastepna_tura()

        elif self.faza == FazaGry.FAZA_PYTANIA:
            if akcja['typ'] == 'zmiana_kontraktu':
                self._ustaw_kontrakt(self.grajacy, akcja['kontrakt'], self.atut)
                self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = self.grajacy
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()
            elif akcja['typ'] == 'pytanie':
                self.faza = FazaGry.LICYTACJA
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()

        elif self.faza == FazaGry.LICYTACJA:
            if akcja['typ'] == 'lufa':
                self.czy_byla_lufa = True; self.mnoznik_lufy *= 2; self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = gracz
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                return
            if akcja['typ'] == 'pas':
                self.pasujacy_gracze.append(gracz)
            elif akcja['typ'] == 'przebicie':
                self.oferty_przebicia.append((gracz, akcja))
            if len(self.pasujacy_gracze) + len(self.oferty_przebicia) >= 3:
                self._rozstrzygnij_licytacje_2()
            else:
                self._nastepna_tura()

        elif self.faza == FazaGry.FAZA_PYTANIA:
            if akcja['typ'] == 'zmiana_kontraktu':
                self._ustaw_kontrakt(self.grajacy, akcja['kontrakt'], self.atut)
                self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = self.grajacy
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()
            elif akcja['typ'] == 'pytanie':
                self.faza = FazaGry.LICYTACJA
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()

        elif self.faza == FazaGry.LICYTACJA:
            if akcja['typ'] == 'lufa':
                self.czy_byla_lufa = True; self.mnoznik_lufy *= 2; self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = gracz
                self.kolej_gracza_idx = self.gracze.index(self.grajacy) # Tura wraca do grającego
                return
            if akcja['typ'] == 'pas':
                self.pasujacy_gracze.append(gracz)
            elif akcja['typ'] == 'przebicie':
                self.oferty_przebicia.append((gracz, akcja))
            if len(self.pasujacy_gracze) + len(self.oferty_przebicia) >= 3:
                self._rozstrzygnij_licytacje_2()
            else:
                self._nastepna_tura()

        elif self.faza == FazaGry.FAZA_PYTANIA:
            if akcja['typ'] == 'zmiana_kontraktu':
                self._ustaw_kontrakt(self.grajacy, akcja['kontrakt'], self.atut)
                self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = self.grajacy
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()
            elif akcja['typ'] == 'pytanie':
                self.faza = FazaGry.LICYTACJA
                self.kolej_gracza_idx = self.gracze.index(self.grajacy)
                self._nastepna_tura()

        elif self.faza == FazaGry.LICYTACJA:
            if akcja['typ'] == 'lufa':
                self.czy_byla_lufa = True; self.mnoznik_lufy *= 2; self.faza = FazaGry.LUFA
                self.ostatni_podbijajacy = gracz
                self.kolej_gracza_idx = self.gracze.index(next(p for p in gracz.druzyna.przeciwnicy.gracze if p != self.nieaktywny_gracz))
                return
            if akcja['typ'] == 'pas': self.pasujacy_gracze.append(gracz)
            elif akcja['typ'] == 'przebicie': self.oferty_przebicia.append((gracz, akcja))
            if len(self.pasujacy_gracze) + len(self.oferty_przebicia) >= 3:
                self._rozstrzygnij_licytacje_2()
            else:
                self._nastepna_tura()
    # ✅ === KONIEC ZMIANY ===
    
    def rozdaj_karty(self, ilosc: int):
        start_idx = (self.rozdajacy_idx + 1) % 4
        for _ in range(ilosc):
            for i in range(4):
                karta = self.talia.rozdaj_karte()
                if karta: self.gracze[(start_idx + i) % 4].reka.append(karta)
    
    def rozlicz_rozdanie(self) -> tuple[Druzyna, int, int]:
        druzyna_wygrana = self.zwyciezca_rozdania
        if not druzyna_wygrana:
            aktywni_gracze = [p for p in self.gracze if p != self.nieaktywny_gracz]
            if self.kontrakt in [Kontrakt.GORSZA, Kontrakt.LEPSZA] and not any(p.reka for p in aktywni_gracze):
                druzyna_wygrana = self.grajacy.druzyna
            elif self.zwyciezca_ostatniej_lewy:
                 druzyna_wygrana = self.zwyciezca_ostatniej_lewy.druzyna
            else:
                punkty_grajacego = self.punkty_w_rozdaniu.get(self.grajacy.druzyna.nazwa, 0)
                punkty_przeciwnikow = self.punkty_w_rozdaniu.get(self.grajacy.druzyna.przeciwnicy.nazwa, 0)
                druzyna_wygrana = self.grajacy.druzyna if punkty_grajacego >= punkty_przeciwnikow else self.grajacy.druzyna.przeciwnicy
        
        punkty_meczu = STAWKI_KONTRAKTOW.get(self.kontrakt, 0)
        mnoznik = 1
        
        if self.kontrakt == Kontrakt.NORMALNA and druzyna_wygrana == self.grajacy.druzyna:
            punkty_przegranego = self.punkty_w_rozdaniu[druzyna_wygrana.przeciwnicy.nazwa]
            if not any(gracz.wygrane_karty for gracz in druzyna_wygrana.przeciwnicy.gracze):
                mnoznik = 3
            elif punkty_przegranego < 33:
                mnoznik = 2
            punkty_meczu *= mnoznik
            
        punkty_meczu *= self.mnoznik_lufy
        druzyna_wygrana.punkty_meczu += punkty_meczu
        return druzyna_wygrana, punkty_meczu, mnoznik
    
    def _waliduj_ruch(self, gracz: Gracz, karta: Karta) -> bool:
        if gracz != self.gracze[self.kolej_gracza_idx] or karta not in gracz.reka:
            return False
        if not self.aktualna_lewa:
            return True
        kolor_wiodacy = self.aktualna_lewa[0][1].kolor
        reka_gracza = gracz.reka
        
        karty_do_koloru = [k for k in reka_gracza if k.kolor == kolor_wiodacy]
        
        if karty_do_koloru:
            najwyzsza_karta_wiodaca_na_stole = max(
                (k for _, k in self.aktualna_lewa if k.kolor == kolor_wiodacy),
                key=lambda k: k.ranga.value
            )
            wyzsze_karty_w_rece = [
                k for k in karty_do_koloru 
                if k.ranga.value > najwyzsza_karta_wiodaca_na_stole.ranga.value
            ]
            if wyzsze_karty_w_rece:
                return karta in wyzsze_karty_w_rece
            else:
                return karta.kolor == kolor_wiodacy
        else:
            if self.atut:
                karty_atutowe_w_rece = [k for k in reka_gracza if k.kolor == self.atut]
                if karty_atutowe_w_rece:
                    atuty_na_stole = [k for _, k in self.aktualna_lewa if k.kolor == self.atut]
                    if atuty_na_stole:
                        najwyzszy_atut_na_stole = max(atuty_na_stole, key=lambda k: k.ranga.value)
                        wyzsze_atuty_w_rece = [k for k in karty_atutowe_w_rece if k.ranga.value > najwyzszy_atut_na_stole.ranga.value]
                        if wyzsze_atuty_w_rece:
                            return karta in wyzsze_atuty_w_rece
                    return karta.kolor == self.atut
            return True
    
    def _zakoncz_lewe(self):
        if not self.aktualna_lewa: return None
        kolor_wiodacy = self.aktualna_lewa[0][1].kolor
        karty_atutowe = [(g, k) for g, k in self.aktualna_lewa if k.kolor == self.atut]
        
        if karty_atutowe:
            zwyciezca_pary = max(karty_atutowe, key=lambda p: p[1].ranga.value)
        else:
            karty_wiodace = [(g, k) for g, k in self.aktualna_lewa if k.kolor == kolor_wiodacy]
            zwyciezca_pary = max(karty_wiodace, key=lambda p: p[1].ranga.value)
            
        zwyciezca_lewy, _ = zwyciezca_pary
        punkty_w_lewie = sum(k.wartosc for _, k in self.aktualna_lewa)
        druzyna_zwyciezcy = zwyciezca_lewy.druzyna
        self.punkty_w_rozdaniu[druzyna_zwyciezcy.nazwa] += punkty_w_lewie
        zwyciezca_lewy.wygrane_karty.extend([k for _, k in self.aktualna_lewa])
        druzyna_grajacego = self.grajacy.druzyna
        
        if self.kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA] and self.punkty_w_rozdaniu[druzyna_zwyciezcy.nazwa] >= 66:
            self.rozdanie_zakonczone, self.zwyciezca_rozdania, self.powod_zakonczenia = True, druzyna_zwyciezcy, f"osiągnięcie {self.punkty_w_rozdaniu[druzyna_zwyciezcy.nazwa]} punktów"
        
        if not self.rozdanie_zakonczone:
            if self.kontrakt == Kontrakt.BEZ_PYTANIA and zwyciezca_lewy != self.grajacy: 
                self.rozdanie_zakonczone, self.zwyciezca_rozdania, self.powod_zakonczenia = True, druzyna_grajacego.przeciwnicy, f"przejęcie lewy przez {zwyciezca_lewy.nazwa}"
            elif self.kontrakt == Kontrakt.LEPSZA and druzyna_zwyciezcy != druzyna_grajacego: 
                self.rozdanie_zakonczone, self.zwyciezca_rozdania, self.powod_zakonczenia = True, druzyna_grajacego.przeciwnicy, "przejęcie lewy przez przeciwnika"
            elif self.kontrakt == Kontrakt.GORSZA and zwyciezca_lewy == self.grajacy: 
                self.rozdanie_zakonczone, self.zwyciezca_rozdania, self.powod_zakonczenia = True, druzyna_grajacego.przeciwnicy, f"wzięcie lewy przez gracza {self.grajacy.nazwa}"
        
        aktywni_gracze = [p for p in self.gracze if p != self.nieaktywny_gracz]
        if not any(p.reka for p in aktywni_gracze) and not self.rozdanie_zakonczone:
            self.zwyciezca_ostatniej_lewy = zwyciezca_lewy
            self.rozdanie_zakonczone = True
            self.powod_zakonczenia = "koniec kart"

        log_msg_lewa = f"  > [LEWA] Wygrywa {zwyciezca_lewy.nazwa} (+{punkty_w_lewie} pkt). Stół: {', '.join([str(k) for _, k in self.aktualna_lewa])}"
        self.historia_akcji.append(f"LEWA:{zwyciezca_lewy.nazwa}:{punkty_w_lewie}")
        logger.info(log_msg_lewa)

        self.aktualna_lewa.clear()
        if not self.rozdanie_zakonczone: self.kolej_gracza_idx = self.gracze.index(zwyciezca_lewy)
        return (zwyciezca_lewy, punkty_w_lewie)
        
    def zagraj_karte(self, gracz: Gracz, karta: Karta):
        if not self._waliduj_ruch(gracz, karta): 
            logger.warning(f"NIELEGALNY RUCH ODRZUCONY: {gracz.nazwa} próbuje zagrać {karta}")
            return
        
        if not self.aktualna_lewa: self.numer_lewy += 1
        
        punkty_z_meldunku = 0
        if not self.aktualna_lewa and self.kontrakt in [Kontrakt.NORMALNA, Kontrakt.BEZ_PYTANIA] and karta.ranga in [Ranga.KROL, Ranga.DAMA]:
            szukana_ranga = Ranga.DAMA if karta.ranga == Ranga.KROL else Ranga.KROL
            if any(k.ranga == szukana_ranga and k.kolor == karta.kolor for k in gracz.reka) and (gracz, karta.kolor) not in self.zadeklarowane_meldunki:
                punkty_z_meldunku = 40 if karta.kolor == self.atut else 20
                self.punkty_w_rozdaniu[gracz.druzyna.nazwa] += punkty_z_meldunku
                self.zadeklarowane_meldunki.append((gracz, karta.kolor))
        
        if punkty_z_meldunku > 0:
            log_msg_meldunek = f"  ! [MELDUNEK] {gracz.nazwa} zgłasza {punkty_z_meldunku} punktów w {karta.kolor.name.capitalize()}"
            self.historia_akcji.append(f"MELDUNEK:{gracz.nazwa}: zgłasza {punkty_z_meldunku} punktów w kolorze {karta.kolor.name.capitalize()}")
            logger.info(log_msg_meldunek)
        
        log_msg_karta = f"    [KARTA] {gracz.nazwa} zagrywa: {karta}"
        self.historia_akcji.append(f"KARTA:{gracz.nazwa}:{str(karta)}")
        logger.info(log_msg_karta)
        
        gracz.reka.remove(karta)
        self.aktualna_lewa.append((gracz, karta))
        
        if len(self.aktualna_lewa) == self.liczba_aktywnych_graczy:
            self._zakoncz_lewe()
        elif not self.rozdanie_zakonczone:
            self._nastepna_tura()
            
    def _rozstrzygnij_licytacje_2(self):
        nowy_grajacy, nowa_akcja = None, None
        oferty_lepsza = [o for o in self.oferty_przebicia if o[1]['kontrakt'] == Kontrakt.LEPSZA]
        if oferty_lepsza: nowy_grajacy, nowa_akcja = oferty_lepsza[0]
        else:
            oferty_gorsza = [o for o in self.oferty_przebicia if o[1]['kontrakt'] == Kontrakt.GORSZA]
            if oferty_gorsza: nowy_grajacy, nowa_akcja = oferty_gorsza[0]
        
        if nowy_grajacy and nowa_akcja:
            self.historia_akcji.append(f"INFO:{nowy_grajacy.nazwa} przebił na {nowa_akcja['kontrakt'].name}.")
            logger.info(f"  INFO: Licytację przebił {nowy_grajacy.nazwa} z kontraktem {nowa_akcja['kontrakt'].name}.")
            self._ustaw_kontrakt(nowy_grajacy, nowa_akcja['kontrakt'], None)
        else: 
            self.historia_akcji.append("INFO:Wszyscy spasowali, kontrakt zostaje.")
            logger.info("  INFO: Wszyscy spasowali, pierwotny kontrakt zostaje.")
        
        if len(self.gracze[0].reka) < 6:
            self.rozdaj_karty(3)
        
        self.faza = FazaGry.ROZGRYWKA
        self.kolej_gracza_idx = self.gracze.index(self.grajacy)

    def get_legalne_karty(self, gracz: Gracz) -> list[Karta]:
        if gracz != self.gracze[self.kolej_gracza_idx] or not gracz.reka: return []
        return [karta for karta in gracz.reka if self._waliduj_ruch(gracz, karta)]
        
    def get_aktualna_stawka(self) -> int:
        if not self.kontrakt: return 0
        stawka_bazowa = STAWKI_KONTRAKTOW.get(self.kontrakt, 1)
        if self.kontrakt != Kontrakt.NORMALNA or not self.grajacy:
            return stawka_bazowa * self.mnoznik_lufy
        druzyna_przeciwnikow = self.grajacy.druzyna.przeciwnicy
        punkty_przeciwnika = self.punkty_w_rozdaniu[druzyna_przeciwnikow.nazwa]
        przeciwnik_wzial_lewe = any(gracz.wygrane_karty for gracz in druzyna_przeciwnikow.gracze)
        mnoznik_punktowy = 1
        if not przeciwnik_wzial_lewe: mnoznik_punktowy = 3
        elif punkty_przeciwnika < 33: mnoznik_punktowy = 2
        return mnoznik_punktowy * self.mnoznik_lufy

class Mecz:
    def __init__(self, nazwy_graczy: list[str]):
        self.druzyna_a = Druzyna(nazwa="My")
        self.druzyna_b = Druzyna(nazwa="Oni")
        self.gracze = [Gracz(nazwa=n) for n in nazwy_graczy]
        self.druzyna_a.dodaj_gracza(self.gracze[0])
        self.druzyna_a.dodaj_gracza(self.gracze[2])
        self.druzyna_b.dodaj_gracza(self.gracze[1])
        self.druzyna_b.dodaj_gracza(self.gracze[3])
        self.druzyna_a.przeciwnicy = self.druzyna_b
        self.druzyna_b.przeciwnicy = self.druzyna_a
        self.rozdajacy_idx = 3 
        self.rozdanie: Optional[Rozdanie] = None
        self.zwyciezca_meczu: Optional[Druzyna] = None

    def rozpocznij_mecz(self):
        self.przygotuj_nastepne_rozdanie()

    def przygotuj_nastepne_rozdanie(self):
        self.rozdajacy_idx = (self.rozdajacy_idx + 1) % 4
        logger.info(f"===\n### NOWE ROZDANIE (rozdaje: {self.gracze[self.rozdajacy_idx].nazwa}) ###")
        self.rozdanie = Rozdanie(gracze=self.gracze, druzyny=[self.druzyna_a, self.druzyna_b], rozdajacy_idx=self.rozdajacy_idx)
        self.rozdanie.rozpocznij_nowe_rozdanie()

    def sprawdz_koniec_meczu(self, limit_punktow: int = 66):
        if self.druzyna_a.punkty_meczu >= limit_punktow:
            self.zwyciezca_meczu = self.druzyna_a
        elif self.druzyna_b.punkty_meczu >= limit_punktow:
            self.zwyciezca_meczu = self.druzyna_b