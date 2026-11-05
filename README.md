# kompresja-danych-rle

Kompresja plików metodą RLE lub Huffmana w Pythonie. Program z interfejsem Tkinter wczytuje dowolny plik jako ciąg bajtów, kompresuje go wybranym algorytmem, dekompresuje i sprawdza zgodność sumą SHA-256. Tryb bezstratny obsługuje każdy plik, a tryb stratny dźwięk WAV i obraz BMP.

Projekt na przedmiot **Złożone struktury danych**, temat 5B. Zespół: Dominika Jedynak, Kacper Kaczmarczyk, Bartosz Kaczmarczyk.

Opis teoretyczny i wyniki testów: [docs/kompresja-danych.md](docs/kompresja-danych.md).

## Uruchomienie

Wystarczy Docker. Na komputerze nie trzeba instalować Pythona ani serwera X.

```sh
docker compose up --build
```

Następnie otwórz **http://localhost:6080**. Program wypełni kartę przeglądarki i dopasuje się do jej rozmiaru. Port jest dostępny tylko z tego komputera.

Własne pliki umieść w katalogu `data/`. W kontenerze jest on widoczny jako `/data`. Wyniki trafiają do `data/output/compressed` i `data/output/restored`.

Zamknięcie karty nie zatrzymuje programu. Aby go zatrzymać, wykonaj `docker compose down`.

## Pozostałe polecenia

| Polecenie | Działanie |
|---|---|
| `docker compose run --rm --build samples` | tworzy pliki testowe w `data/samples` |
| `docker compose run --rm --build benchmark` | testuje wszystkie pliki z `data/samples` i wypisuje tabelę wyników |
| `docker compose run --rm --build tests` | uruchamia testy jednostkowe |
| `docker compose down` | zatrzymuje program i usuwa kontener |

Zakładka **Testy na różnych danych** w programie również korzysta z `data/samples`, więc przed jej użyciem wygeneruj pliki testowe. Po testach wyniki można porównywać w zakładce **Wykresy i porównania**: wybrać zestawy algorytmu i trybu, miarę, rodzaj danych, kolejność i skalę oraz przełączać słupki, mapę ciepła i tabelę.

Bez Dockera program działa na Pythonie 3.11 lub nowszym z modułem Tkinter:

```sh
python -m rle_compressor
```

## Budowa kodu

Kod jest podzielony na funkcje programu, a każda z nich ma własny model, widok i kontroler.

```
rle_compressor/
├── app.py                 składa okno i łączy funkcje
├── config.py              ścieżki katalogów
├── shared/                formatowanie, zadania w tle, wspólne widżety
└── features/
    ├── compression/       kompresja i dekompresja
    │   ├── rle_codec.py       algorytm RLE
    │   ├── huffman_codec.py   algorytm Huffmana
    │   ├── lossy_filter.py    etap stratny dla WAV i BMP
    │   ├── archive_format.py  format plików .rle i .huf
    │   ├── model.py
    │   ├── view.py
    │   └── controller.py
    ├── verification/      porównanie plików sumą SHA-256
    ├── benchmark/         test wielu plików (zakładka i wiersz poleceń)
    └── comparison/        wykresy i tabele porównujące wyniki testów
```

| Warstwa | Odpowiada za | Czego nie robi |
|---|---|---|
| Model | dane, pliki, algorytmy | nie zna Tkintera ani kontrolera |
| Widok | widżety i wyświetlanie | nie podejmuje decyzji i nie dotyka plików |
| Kontroler | reakcje na przyciski, kolejność działań | nie importuje Tkintera |

Dzięki temu rozdzieleniu testy obejmują modele i kontrolery bez otwierania okna: widok zastępuje w nich atrapa.

Algorytmy RLE i Huffmana są napisane samodzielnie, bez bibliotek kompresji. Program korzysta wyłącznie z biblioteki standardowej Pythona: `hashlib` liczy SHA-256, `heapq` to kolejka priorytetowa dla Huffmana, a `wave` odczytuje i zapisuje pliki WAV w trybie stratnym.
