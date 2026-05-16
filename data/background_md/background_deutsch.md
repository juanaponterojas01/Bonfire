# Hintergrundzusammenfassung – Juan Manuel Aponte Rojas

## Teil 1: Werdegang (chronologisch)

- **2013 – 2019: Bachelorstudium Maschinenbau an der Universidad Nacional de Colombia, Bogotá**
  - Studium der allgemeinen Maschinenbau-Grundlagen mit Schwerpunkten in Strömungsmechanik, Thermodynamik, Wärmeübertragung, numerischen Methoden, FEM, CFD, Regelungstechnik und Programmierung.
  - **2018**: Projektarbeit – Entwicklung und Bau einer orbitalen Kartonverpackungsmaschine für die Firma Cartonería Mosquera S.A., inklusive Konstruktion, Fertigungsplanung, Finite-Elemente-Analyse und Kostenkalkulation.
  - **2019**: Bachelorarbeit – Entwicklung eines proprietären inkompressiblen Strömungslösers als Lehr- und Forschungswerkzeug; Implementierung mit kompakten finiten Differenzen (4.–10. Ordnung), ADI-Zeitschrittverfahren und Fractional-Step-Methode zur Druck-Geschwindigkeits-Kopplung; Validierung am Backward-Face-Step-Benchmark.
  - Abschluss als *Ingeniero Mecánico* mit einer Durchschnittsnote von 4,0/5,0.

- **Oktober 2023 – Januar 2024: Pflichtpraktikum bei TLK-Thermo GmbH, Braunschweig**
  - Einarbeitung in Python und das Qt-Framework.
  - Weiterentwicklung einer Backend-Software zur Konvertierung und Bearbeitung von Daten zwischen JSON-Dateien und Python-Klassen.
  - Implementierung einer grafischen Benutzeroberfläche (GUI) zur Datenbearbeitung und -speicherung.
  - Dokumentation mit Sphinx und reStructuredText.

- **2022 – 2024: Masterstudium Maschinenbau an der Technischen Universität Braunschweig**
  - Schwerpunkt: Energie- und Verfahrenstechnik.
  - **November 2022 – März 2023**: Studienarbeit am Institut für Flugantriebe und Strömungsmaschinen (IFAS) – Implementierung einer neuartigen Rückplattenmesstechnik zur Analyse des Kippverhaltens von Kohlenschwimmringdichtungen; Durchführung von Versuchen, Datenauswertung in MATLAB, Fehleranalyse und Interpretation komplexer Druckprofile.
  - **April – Oktober 2024**: Masterarbeit am Institut für Thermodynamik – Entwicklung einer optimalen Ladestrategie für ein Batteriesystem mittels numerischer Optimalsteuerung (Direct Multiple Shooting, CasADi); Modellierung in Modelica/TIL_AddOn_Battery mit einem 2RC-Ersatzschaltbild und thermischem Lumping.
  - Abschluss als **Master of Science** am 19. November 2024 mit der Gesamtnote **gut (2,5)**.

- **März 2026: Weiterbildung im Bereich Deep Learning**
  - Abschluss des Udemy-Kurses *PyTorch for Deep Learning Bootcamp* (52 Stunden).

- **Programmierprojekte (laufend)**
  - Entwicklung eines *Digital Twin* für die Ladezustands-Schätzung (SOC) von Lithium-Ionen-Batterien mittels Physics-informed LSTM.
  - Entwicklung eines Python-Tools zur automatisierten Generierung von Bewerbungsunterlagen (Motivationsschreiben, Lebenslauf, E-Mails) mit PyQt6-GUI, mehrsprachiger Unterstützung und PDF-Vorschau.
  - Entwicklung der *Bonfire App* – KI-gestützte Automatisierung von Stellenbewerbungen unter Nutzung von LLMs.

---

## Teil 2: Fähigkeiten und Kompetenzen

### Kernkompetenzen (stärkste Fähigkeiten)

**1. Thermische Energietechnik und Batteriemodellierung**
Durch die Masterarbeit und das Praktikum bei TLK-Thermo verfügt Juan über fundierte Kenntnisse in der thermodynamischen Modellierung von Batteriesystemen. Er beherrscht die Erstellung von elektro-thermischen Ersatzschaltbildern (Thevenin, 2RC-Modell), die Berücksichtigung von reversiblem und irreversiblem Wärmeverhalten sowie die Implementierung von Derating-Strategien basierend auf SOC und Temperatur. Seine Arbeit mit Modelica und der TIL-Batteriebibliothek ermöglicht ihm die ganzheitliche Simulation komplexer gekoppelter Systeme aus Batterie, Kühlkreislauf und Leistungselektronik.

**2. Numerische Simulation und Optimierung**
Sein ingenieurwissenschaftlicher Hintergrund ist geprägt von intensiver Arbeit mit numerischen Methoden. In der Bachelorarbeit entwickelte er einen eigenen CFD-Solver für inkompressible Strömungen mit hochgenauen kompakten finiten Differenzen und ADI-Zeitschrittverfahren. In der Masterarbeit wandte er diese analytische Stärke auf die Optimierung an: Er formulierte und löste ein Optimalsteuerungsproblem (OCP) mit Direktem Multiple Shooting unter Verwendung von CasADi und IPOPT. Diese Kombination aus physikalischer Modellierung und mathematischer Optimierung ist eine seiner herausragendsten Kompetenzen.

**3. Python-Softwareentwicklung und Automatisierung**
Während des Praktikums bei TLK-Thermo und in seinen eigenen Projekten hat Juan umfangreiche Erfahrung in der Python-Entwicklung gesammelt. Er entwickelte Backend-Software zur Datenkonvertierung zwischen JSON und Python-Klassen, implementierte grafische Oberflächen mit PyQt6 und dokumentierte Projekte professionell mit Sphinx. Seine Fähigkeit, ingenieurwissenschaftliche Probleme in robuste, wartbare Software zu übersetzen, zeigt sich auch in seinen eigenen Tools wie dem Bewerbungsgenerator und der Battery-Digital-Twin-Anwendung.

**4. Messtechnik und experimentelle Datenanalyse**
Die Studienarbeit am IFAS beweist seine Kompetenz im experimentellen Bereich: Er instrumentierte komplexe Prüfstände mit Miniatur-Kulite-Drucksensoren, führte Kalibrierungen mit hydraulischen Totlastprüfern durch und wertete hochfrequente Messsignale (1024 Samples/Umdrehung) mit MATLAB aus. Er beherrscht die statistische Fehleranalyse (systematische und zufällige Fehler, Student-t-Verteilung) sowie die Interpretation komplexer phänomenologischer Zusammenhänge (Lomakin-Effekt, Lock-Up-Zustand, Kippbewegungen).

### Weitere technische Fähigkeiten

- **Strömungsmechanik & CFD**: Grundlagen der inkompressiblen und kompressiblen Strömung, Erfahrung mit der Entwicklung eigener Solver, Validierung anhand von Benchmark-Daten.
- **FEM und Strukturanalyse**: Anwendung der Finite-Elemente-Methode in Inventor für statische Strukturanalysen (Maschinenbau-Projekt).
- **Maschinelles Lernen**: Grundlagen in PyTorch, insbesondere LSTM-basierte Zeitreihenvorhersage und Physics-Informed Neural Networks (PINNs) für batterietechnische Anwendungen.
- **Regelungstechnik**: Kenntnisse in der modellprädiktiven Regelung (MPC), Zustandsschätzung und klassischen Regelungskonzepten.
- **CAD und Konstruktion**: Erfahrung in der mechanischen Konstruktion, Fertigungsplanung und Kostenabschätzung aus dem Maschinenbau-Projekt.
- **Sprachen**: Spanisch (Muttersprache), Deutsch (fließend in Wort und Schrift, Studium und Praktikum in Deutschland), Englisch (fachsprachlich sicher).

### Soft Skills und methodische Kompetenzen

- **Projektmanagement**: Nachweisbare Erfahrung in der Projektleitung und -planung (Note 5,0/5,0 im Fach „Gerencia y gestión de proyectos").
- **Selbstständige Arbeitsweise**: Entwicklung komplexer Software- und Simulationsprojekte eigenständig von der Idee bis zur Dokumentation.
- **Analytisches Denken**: Systematische Herangehensweise an komplexe physikalische und technische Probleme, belegt durch die wissenschaftlichen Arbeiten.
- **Interkulturelle Kompetenz**: Erfolgreiches Studium und Berufspraxis in Kolumbien und Deutschland.
