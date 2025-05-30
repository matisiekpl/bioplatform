# BioPlatform

Platforma oparta na Django do zarządzania i analizy danych biologicznych, zaprojektowana specjalnie dla eksperymentów z hodowlami komórkowymi.

Link: https://labolatorium.mateuszwozniak.com/
Część kodu pochodzi z projektu inżynierskiego Mateusza Woźniaka: http://github.com/matisiekpl/cell-detector

## Przegląd

BioPlatform to aplikacja internetowa, która umożliwia naukowcom:

- Organizację badań w zespoły z wieloma członkami i różnymi poziomami uprawnień
- Tworzenie i zarządzanie eksperymentami z liniami komórkowymi
- Rejestrowanie pomiarów, w tym liczby komórek i wskaźników adhezji
- Analizę obrazów komórek przy użyciu widzenia komputerowego do automatycznego liczenia komórek
- Wizualizację i śledzenie danych eksperymentalnych w czasie

## Funkcje

### Zarządzanie użytkownikami
- Rejestracja i uwierzytelnianie użytkowników
- Współpraca w ramach zespołów
- Kontrola dostępu oparta na rolach (Obserwator, Edytor, Administrator)

### Zarządzanie eksperymentami
- Tworzenie, przeglądanie, aktualizowanie i usuwanie eksperymentów
- Kategoryzacja eksperymentów według typu (obecnie obsługiwane są eksperymenty z liniami komórkowymi)
- Organizacja eksperymentów w ramach zespołów

### Pomiary
- Rejestrowanie różnych typów pomiarów:
  - Liczba komórek
  - Wskaźniki adhezji
- Przesyłanie i przypisywanie obrazów do pomiarów
- Znakowanie czasowe i śledzenie historii pomiarów

### Analiza obrazów
- Automatyczne wykrywanie i liczenie komórek przy użyciu widzenia komputerowego
- Przetwarzanie obrazów za pomocą OpenCV
- Wizualna weryfikacja wykrytych komórek
- Ręczna korekta automatycznie policzonych komórek

## Szczegóły techniczne

### Wykorzystane technologie
- **Backend**: Django (Python)
- **Baza danych**: SQLite (domyślnie)
- **Frontend**: TailwindCSS
- **Przetwarzanie obrazów**: OpenCV, NumPy, PIL
- **Wizualizacja**: Matplotlib

### Struktura projektu
- `core/`: Główna aplikacja
  - `models.py`: Modele danych (Użytkownik, Zespół, Członkostwo, Eksperyment, Pomiar)
  - `views/`: Kontrolery dla różnych sekcji
  - `templates/`: Szablony HTML
  - `forms/`: Definicje formularzy
  - `utils.py`: Funkcje narzędziowe, w tym algorytm wykrywania komórek

### Modele danych
- **User**: Rozszerzony model użytkownika Django z niestandardowymi polami
- **Team**: Grupa użytkowników, którzy mogą współpracować
- **Membership**: Łączy użytkowników z zespołami z określonymi rolami
- **Experiment**: Eksperyment badawczy z metadanymi
- **Measurement**: Punkt danych zebrany dla eksperymentu
