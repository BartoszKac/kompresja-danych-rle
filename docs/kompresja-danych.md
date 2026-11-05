# Kompresja danych

## Kompresja stratna i bezstratna

**Kompresja bezstratna** pozwala odtworzyć dane co do bitu. Stosuje się ją wszędzie tam, gdzie każda zmiana byłaby błędem: w tekstach, programach i archiwach. Przykłady to RLE, kodowanie Huffmana, LZ77 oraz formaty ZIP i PNG.

**Kompresja stratna** trwale usuwa informacje, których człowiek prawie nie zauważa, np. bardzo ciche dźwięki lub drobne szczegóły obrazu. Daje zwykle znacznie mniejsze pliki, ale oryginału nie da się już odzyskać. Przykłady to JPG i MP3.

| Cecha | Bezstratna | Stratna |
|---|---|---|
| Odtworzenie oryginału | dokładne | tylko przybliżone |
| Typowe zastosowania | tekst, programy, archiwa | zdjęcia, muzyka, wideo |
| Sprawdzenie SHA-256 oryginału i wyniku | sumy są równe | sumy zwykle się różnią |

## RLE (Run-Length Encoding)

RLE zastępuje serię jednakowych symboli informacją: ile razy symbol się powtarza i jaki to symbol.

Nasz program działa na bajtach i zapisuje każdą serię jako dwa bajty: `liczność, wartość`.

```
Wejście:  A A A A B C C     (7 bajtów)
Wynik:    4 A   1 B   2 C   (6 bajtów)
```

Liczność mieści się w jednym bajcie, więc jedna para opisuje najwyżej 255 bajtów. Dłuższa seria jest dzielona: 1000 razy `a` to pary `255 a`, `255 a`, `255 a`, `235 a`.

Dekompresja wykonuje działanie odwrotne: każdą parę zamienia na odpowiednią liczbę powtórzeń bajtu.

Skuteczność zależy wyłącznie od długości serii:

- **Najlepszy przypadek:** seria 255 bajtów zajmuje 2 bajty, więc współczynnik dąży do 127,5.
- **Najgorszy przypadek:** gdy sąsiednie bajty się różnią, każdy bajt zajmuje 2 bajty, a plik rośnie dwukrotnie (współczynnik 0,5).

### Format plików `.rle` i `.huf`

| Pole | Rozmiar | Znaczenie |
|---|---|---|
| znacznik `RLE1` lub `HUF1` | 4 B | rozpoznanie algorytmu |
| rozmiar oryginału | 8 B | wykrycie pliku uszkodzonego lub uciętego |
| dane skompresowane | zależy od danych | pary RLE albo tabela i kody Huffmana |

## Kodowanie Huffmana

Kodowanie Huffmana nadaje częstym symbolom krótkie kody, a rzadkim długie. Nie wymaga, aby jednakowe symbole leżały obok siebie, liczy się tylko częstość ich występowania.

Algorytm:

1. Policz wystąpienia każdego symbolu.
2. Utwórz z każdego symbolu osobny węzeł o wadze równej liczbie wystąpień.
3. Połącz dwa węzły o najmniejszej wadze w nowy węzeł o wadze równej ich sumie.
4. Powtarzaj krok 3, aż zostanie jeden węzeł, czyli korzeń drzewa.
5. Odczytaj kody ze ścieżek od korzenia do liści: gałąź w lewo to `0`, w prawo to `1`.

Żaden kod nie jest początkiem innego, dlatego dekoder wie, gdzie kończy się każdy symbol, mimo że kody mają różną długość.

Przykład dla słowa `ABRAKADABRA` (11 znaków, w ASCII 88 bitów):

| Symbol | Liczba wystąpień | Kod | Razem bitów |
|---|---:|---|---:|
| A | 5 | `0` | 5 |
| R | 2 | `10` | 4 |
| B | 2 | `110` | 6 |
| K | 1 | `1110` | 4 |
| D | 1 | `1111` | 4 |
| **Suma** | **11** | | **23** |

Dane zajmują 23 bity zamiast 88. Do pliku trzeba jednak dopisać także drzewo lub tablicę kodów, potrzebne przy dekompresji, co przy krótkich danych może zniwelować zysk.

### Porównanie z RLE

| | RLE | Huffman |
|---|---|---|
| Co wykorzystuje | sąsiednie powtórzenia | nierówną częstość symboli |
| Dane dodatkowe | brak | drzewo lub tablica kodów |
| Złożoność implementacji | bardzo mała | większa (drzewo, kolejka priorytetowa, zapis bitów) |
| Słowo `ABRAKADABRA` | brak serii, plik rośnie dwukrotnie | wyraźny zysk |

W programie zaimplementowano oba algorytmy i można wybrać jeden z nich przed kompresją. Program zapisuje wybrany algorytm w nagłówku pliku, więc przy dekompresji rozpoznaje go sam.

### Implementacja Huffmana w programie

Kod znajduje się w `huffman_codec.py`. Do wybierania dwóch najrzadszych grup służy kolejka priorytetowa (`heapq`). Pozostałą część algorytmu program realizuje samodzielnie.

Wynik zawiera tabelę 256 bajtów z długością kodu każdej wartości bajtu oraz ciąg kodów dopełniony zerami do pełnego bajtu. Program stosuje **kody kanoniczne**: koder i dekoder wyznaczają je z samych długości w tej samej kolejności, więc nie trzeba zapisywać całego drzewa. Dekoder odbudowuje z kodów drzewo binarne i dla każdego bitu schodzi o jeden poziom, a po dojściu do liścia zapisuje bajt i wraca do korzenia.

Tabela zajmuje stałe 256 bajtów, dlatego przy bardzo małych plikach Huffman może je powiększyć.

## Tryb stratny w programie

Program pozwala wybrać tryb **bezstratny** albo **stratny**, niezależnie od algorytmu. RLE i Huffman same zawsze są bezstratne, dlatego tryb stratny dodaje przed nimi etap upraszczania danych (`lossy_filter.py`). Etap ten trwale usuwa szczegóły, tak aby powstały długie serie jednakowych bajtów:

- **Dźwięk WAV:** zostaje jeden kanał w 8 bitach zamiast 16. Wartości są zaokrąglane do wielokrotności 4, a każda czwarta próbka zastępuje trzy kolejne.
- **Obraz BMP (24 bity):** kolor zostaje zamieniony na jasność, czyli odcień szarości. Wartości są zaokrąglane do wielokrotności 16, a każdy czwarty piksel w wierszu zastępuje trzy kolejne. Rozmiar obrazu w pikselach się nie zmienia.

Po dekompresji powstaje poprawny plik WAV lub BMP o wyraźnie gorszej jakości, a SHA-256 zwykle wykazuje różnicę z oryginałem. Wyjątkiem jest obraz czysto czarno-biały, w którym uproszczenie może nic nie zmienić.

Tryb stratny odrzuca pozostałe pliki. W tekście i programach zmiana bajtów oznaczałaby zmianę treści. Bajty PNG, JPG i MP3 są już zakodowane, więc ich zaokrąglanie uszkodziłoby plik zamiast pogorszyć jakość. Aby kompresować je stratnie, trzeba by najpierw je zdekodować.

Prawdziwe formaty stratne działają mądrzej: JPG i MP3 usuwają przede wszystkim to, czego człowiek prawie nie zauważa. Nasz etap jest celowo prosty i służy pokazaniu zasady: im więcej informacji usuniemy, tym mniejszy plik i tym gorsza jakość.

## Wyniki testów

Współczynnik kompresji to **rozmiar przed / rozmiar po**. Wartość powyżej 1 oznacza zmniejszenie pliku, a poniżej 1 jego powiększenie. Rozmiar po kompresji obejmuje 12-bajtowy nagłówek.

### Tryb bezstratny

SHA-256 potwierdziło zgodność z oryginałem we wszystkich wierszach tej tabeli.

| Plik | Rodzaj danych | Przed | RLE: po | RLE: współczynnik | Huffman: po | Huffman: współczynnik |
|---|---|---:|---:|---:|---:|---:|
| `skan_dokumentu.bmp` | czarne wiersze na białej stronie | 2,64 MiB | 21,66 KiB | 124,644 | 427,96 KiB | 6,309 |
| `tekst_serie_znakow.txt` | tekst z seriami po 200 znaków | 1020,70 KiB | 10,22 KiB | 99,885 | 608,76 KiB | 1,677 |
| `dane_z_zerami.bin` | krótkie rekordy i długie obszary zer | 1,00 MiB | 23,97 KiB | 42,722 | 136,22 KiB | 7,517 |
| `tekst_tabela_wyrownana.txt` | tabela z długimi wyrównaniami spacjami | 1,73 MiB | 142,51 KiB | 12,418 | 356,77 KiB | 4,960 |
| `dzwiek_z_cisza.wav` | krótkie tony i długa cisza | 2,52 MiB | 703,79 KiB | 3,672 | 652,60 KiB | 3,960 |
| `tekst_powtarzana_fraza.txt` | powtarzane zdanie | 1023,99 KiB | 2,00 MiB | 0,500 | 517,71 KiB | 1,978 |
| `tekst_losowy.txt` | losowe litery i cyfry | 1,00 MiB | 1,97 MiB | 0,508 | 764,06 KiB | 1,340 |
| `obraz_kolorowy.bmp` | kolorowy obraz z płynnymi przejściami | 2,64 MiB | 5,25 MiB | 0,503 | 2,22 MiB | 1,189 |
| `dzwiek.wav` | dźwięk WAV (szum z tonem) | 2,52 MiB | 5,03 MiB | 0,502 | 2,25 MiB | 1,120 |
| `muzyka.mp3` | dźwięk MP3 | 704,74 KiB | 1,37 MiB | 0,503 | 702,14 KiB | 1,004 |
| `zdjecie.jpg` | obraz JPG z szumem | 676,89 KiB | 1,32 MiB | 0,502 | 674,77 KiB | 1,003 |
| `obraz.png` | obraz PNG | 104,34 KiB | 207,85 KiB | 0,502 | 104,51 KiB | 0,998 |

### Tryb stratny

Tryb stratny dotyczy tylko plików WAV i BMP. W kolumnie SHA-256 widać, czy plik po dekompresji jest identyczny z oryginałem.

| Plik | Przed | RLE: po | RLE: współczynnik | Huffman: po | Huffman: współczynnik | SHA-256 |
|---|---:|---:|---:|---:|---:|---|
| `skan_dokumentu.bmp` | 2,64 MiB | 21,66 KiB | 124,644 | 427,96 KiB | 6,309 | zgodne |
| `obraz_kolorowy.bmp` | 2,64 MiB | 67,63 KiB | 39,923 | 895,40 KiB | 3,015 | różne |
| `dzwiek_z_cisza.wav` | 2,52 MiB | 86,51 KiB | 29,871 | 263,26 KiB | 9,816 | różne |
| `dzwiek.wav` | 2,52 MiB | 352,31 KiB | 7,335 | 450,27 KiB | 5,739 | różne |

Wyniki można odtworzyć poleceniami `docker compose run --rm --build samples` oraz `docker compose run --rm --build benchmark`. Pliki są tworzone syntetycznie przez `scripts/generate_samples.py`: obrazy to wzory testowe generatora ffmpeg, a dźwięk to szum lub tony. Nie są to prawdziwe zdjęcia ani nagrania muzyki, więc inne pliki tego samego typu mogą dać nieco inny wynik.

## Dlaczego wynik zależy od danych

W trybie bezstratnym SHA-256 potwierdziło w każdym teście, że dane po dekompresji są identyczne z oryginałem. Bezstratność nie zależy więc od rodzaju danych, zależy od niego tylko uzyskany rozmiar.

Porównanie algorytmów pokazuje, że każdy korzysta z innej regularności:

- **RLE wygrywa przy długich seriach.** W skanie dokumentu współczynnik wynosi 124,6, a u Huffmana tylko 6,3. Huffman musi zapisać co najmniej 1 bit na każdy bajt, więc nie może przekroczyć współczynnika około 8. RLE zapisuje całą serię w 2 bajtach.
- **Huffman wygrywa, gdy serii nie ma, ale częstość znaków jest nierówna.** Powtarzana fraza przy RLE rośnie dwukrotnie, a u Huffmana maleje prawie dwukrotnie. Podobnie losowy tekst: 62 równie częste znaki wymagają około 6 bitów zamiast 8, stąd współczynnik około 1,34.
- **Huffman nie szkodzi tak jak RLE.** Na danych bez regularności RLE podwaja rozmiar, a Huffman zostawia go prawie bez zmian.
- **Danych już skompresowanych nie poprawia żaden z nich.** Dla PNG, JPG i MP3 częstości bajtów są niemal równe, więc Huffman daje współczynnik około 1. PNG nawet nieznacznie urósł przez tabelę i nagłówek.

Poniżej wyjaśnienie dla poszczególnych danych z punktu widzenia RLE:

- **Skan, tekst z seriami, dane z zerami, wyrównana tabela:** zawierają długie serie jednakowych bajtów. Na przykład seria 200 bajtów zajmuje 2 bajty, stąd współczynnik bliski 100 dla tekstu z seriami.
- **Dźwięk z ciszą:** cisza to same bajty zerowe, więc mocno się kompresuje, a fragmenty z tonem nie.
- **Kolorowy obraz BMP:** dane nie są skompresowane, ale kolor piksela zapisują kolejno trzy różne bajty, więc nawet jednolity obszar nie tworzy serii jednakowych bajtów. Ten sam obszar po zamianie na odcienie szarości tworzy już długie serie, co pokazuje tryb stratny.
- **Powtarzana fraza:** tekst powtarza się, ale jako całe zdanie, a sąsiednie znaki są różne. RLE porównuje tylko sąsiednie bajty, więc nie widzi tej regularności. Wykorzystałyby ją metody słownikowe, takie jak LZ77 czy LZW. Ten przypadek pokazuje, że „dane z powtórzeniami” nie zawsze oznaczają dane dobre dla RLE.
- **Losowy tekst:** prawdopodobieństwo, że dwa sąsiednie znaki są takie same, wynosi tylko 1/62, więc serii prawie nie ma.
- **PNG, JPG, MP3:** te formaty są już skompresowane. Ich bajty przypominają dane losowe, ponieważ wcześniejsza kompresja usunęła z nich regularności.
- **WAV:** dane nie są skompresowane, ale kolejne 16-bitowe próbki dźwięku z szumem prawie nigdy nie tworzą serii jednakowych bajtów. Wynik może być znacznie lepszy przy długiej ciszy.

Ogólna zasada: żaden algorytm bezstratny nie zmniejszy wszystkich możliwych plików, ponieważ krótszych plików jest za mało, by każdemu dłuższemu przypisać inny. Każda metoda opiera się na określonej regularności danych, a gdy jej nie ma, plik nie maleje, a nawet może urosnąć. Dla RLE tą regularnością są serie sąsiednich jednakowych bajtów.
