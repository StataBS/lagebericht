SERVER = 'pdstatasvsql04'
DATABASE = 'lagebericht_app'
ROUNDED_MINUTES = 10                # rundet Minuten in meldezeit-Text
# Menu Optionen dürfen nicht geändert werden, da sie so geschrieben im Code und dictionaries verwendet werden.
MENU_OPTIONS = ['Info',
    'Datei hochladen',
    'Prozesssteuerung manuell',
    'Werte erfassen',
    'Werte überprüfen',
    'Versand Lagebericht',
    'Konfiguration zeigen',
    'Konfiguration editieren',
    'Verteiler verwalten',    
    'Passwort ändern'
    ]
MENU_DESC = {
    'Info': """Die Export Datei Sample-Export.xlsx wird über den Menubefehl `Datei hochladen` in das Datenaustauschverzeichnis MD kopiert. 
Ist die Option `Import nach upload starten` so werden alle Prozessschritte, ausser dem Versand des Mails, durchgeführt. Ist die Option
nicht aktiv, so können auch mit dem Menupunkt `Prozesssteuerung manuell` einzelne oder alle Schritte durchgeführt werden. 
Einige Vergleichsdaten müssen vor dem Export manuell erfasst werden: 
* Isolierte in APHs BS
* Inzidenzen für den Landeskreis Lörrach 
* Inzidenzen für das Département du Haut-Rhin.

Im Mail wird jeweils der neuste Wert dieser Felder übernommen.

In den beiden Tabellen werden die Log-Einträge der letzten Prozesse sowie die zuletzt eingelesenen Werte angezeigt.
""",
    'Datei hochladen': """Die Excel Datei kann über das Cockpit mit drag & drop hochgeladen werden. Sie wird automatisch in das 
    Datenaustauschverzeichnis MD gespeichert, und von hier in die Datenbank eingelesen. Nach dem Einlesen-Vorgang wird die Datei gelöscht.
    Die Importierten Spalten werden als csv-Datei im Verzeichnis archiv archiviert.
    """,
    'Prozesssteuerung manuell': """Auf dieser Seite kannst du die einzelnen Prozessschritte manuell ausgelöst werden. Alle Schritte setzen voraus, dass die Importdatei bereits 
    hochgeladen wurde.
* Import Excel Datei in Datenbank: importiert die unter dem Datenaustausch-Verzeichnis MD abgelegte Excel Datei mit Einzelfällen in die Datenbank
* Zeitreihe erstellen: Extrahiert die Informationen zum Stand des gestrigen Tages und speichert sie in der Tabelle Zeitreihe (Eine Zeile pro Tag) ab. Hier werden 
auch die Inzidenzen berechnet.  Diese Tabelle enthält alle Werte welche im Lagebericht publiziert werden. 
* OGD Dateien Exportieren: Ausgewählte Felder der Zeitreihe werden in die Datei MD\\uplaod\\covid_faelle.csv-, Altersklasse und Geschlecht der positiv Getesteten pro Tag werden 
in die Datei covid_faelle_detail.csv  exportiert.
* Grafiken erzeugen: Die Grafik der Lagebericht-Mail Beilage wird basierend auf dem Stand der Datei MD\\uplaod\\covid_faelle.csv erzeugt. 
    - Figur 1: Neue Fälle pro Tag und Mittel der letzten 7 Tage.  
    - Figur 2: Kumulierte Fälle
* Test Mail verschicken: Der Lagebericht wird erzeugt und als Testversion-Mail an den eigenen Benutzer verschickt, ein cc wird an den Verteiler Text_mail_cc verschickt. Der Testcharakter ist im Betreff 
der Mail vermerkt.
* Test SMS verschicken: Das Lagebericht SMS wird erzeugt und als Testversion-SMS an den eigenen Benutzer verschickt, ein cc wird an den Verteiler Text_mail_cc verschickt. Der Testcharakter ist im Betreff 
des SMS vermerkt.
* Die Option `Für Hospitialisierte-BS-Werte vom Vortag verwenden` wird verwendet, wenn die heutig publizierten Spitaldaten noch nicht komplett sind.
Das Feld `Begleittext für den Mailversand` kann für beliebige Infos verwendet werden, die in den Mailtext integriert werden sollen. 

Wählen sie mindestens einen Prozess aus und drücken sie die `Ausführen` Schaltfläche.  
    """,
    'Versand Lagebericht': """Der Covid-19 Lagebericht wird als Mail oder SMS an den jeweiliegen Verteiler verschickt. Der Verteiler kann unter Menupunkt `Verteiler verwalten` ergänzt und 
    editiert werden. Wählen sie einen oder mehrere Versandtypen aus und drücken sie `Ausführen` Schaltfläche um den Prozess zu starten.
    """,
    'Konfiguration zeigen':"""Alle Variablen, die intern für die Ablage von Daten, Import von Daten oder für Berechnungen verwendet werden, sind 
    über die Konfiguration gesteuert. Alle Einstellungen können hier eingesehen und überprüft werden. Verwenden sie die Menuoption `Konfiguration editieren` 
    um die Werte zu ändern.
    """,

    'Konfiguration editieren': """Hier können sie die einzelnen Variablen der Konfiguration ändern. Achtung, das Ändern von Werten auf dieser Seite kann dazu führen, 
    dass der Import Prozess nicht mehr korrekt abläuft, z.B. wenn Verzeichnisse angegeben werden, welche nicht existieren. Seien sie sehr vorsichtig beim Speichern von
    Änderungen und testen sie diese nach Möglichkeit sofort aus. Vorgehen:
* suchen sie den Schlüssen in der Parameter-Auswahlliste
* überprüfen sie in der Feldbeschreibung (unter dem Texteingabefeld), dass der richtige Parameter gewählt ist
* überschreiben sie den Parameter-Wert im Texteingabefeld
* drücken sie die `Speichern` Schaltfläche und achten sie darauf, dass eine Erfolgsmeldung angezeigt wird.
    """,
    'Werte erfassen':"""Die Felder `Fälle Haut-Rhin`, `Fälle Lörrach` sowie die Patienten in Langzeitpflege müssen manuell erfasst werden. Wähle ein Datum erfasse oder editiere den Wert im
entsprechenden Feld und drücke die `Speichern` Schaltfläche. Die Daten sind hier publiziert:
* [Landeskreis Lörrach](https://lraloe.maps.arcgis.com/apps/opsdashboard/index.html#/a9ac81343b9d426881fa386ce7bb71dd). 7-Tage-Inzidenz Wert aus 
Dashborad kopieren.
* [Département du Haut Rhin](https://www.grand-est.ars.sante.fr/liste-communiques-presse?archive=0) Auf das aktuellste Tabeau de bord Dokument klicken, 
pdf öffnen und unter Tabelle Population générale tous âges, für die Zeile Haut-Rhin/Spalte Taux d’incidence kopieren.
* Isolierte APH: Diese Werte werden von der Datenbank der Langzeitpflegepatienten übernommen und jeweils am Montag mittels dieser Seite in 
die Lagebericht-DB eingepflegt.
""",
'Passwort ändern': """
Auf dieser Seite kannst du dein Passwort ändern.
""",
'Verteiler verwalten': """Auf dieser Seite können Personen erfasst und in eine Mail oder SMS-Verteiler aufgenommen werden.

1. Unter `Liste der erfassten Personen` können bestehende Personen editiert oder gelöscht sowie neue Personen angelegt werden. 
Die `Mobile` Nummer wird für den Versand von SMS benötigt, im Feld `Hat Konto` steht ein `ja` für Operatoren mit Login 
für die Applikation und `nein` für Personen, die nur für den Versand benötigt werden.

2. Unter Verteiler wird zunächst aus den verschiedenen Verteilern ausgewählt, wobei die Liste der für den gewählten Verteiler 
im Listen Feld `Personen zuweisen zu Verteiler...` mit der aktuellen Einstellung in der Datebank aktualisiert wird. Um 
die Liste zu ändern können Personen zugefügt oder entfernt werden. Zum Speicher der Änderungen wird der `Speichern`-Knopf
gedrückt. Personen können auch als Excel Liste geladen werden. Der aktuelle Stand ist unter 
`\\\\bs.ch\\dfs\\bs\PD\PD-StatA-FST-OGD-DataExch\\MD\\admin\\Verteiler_Lagebericht.xlsx` abgelegt. Bereits im System vorhandene 
Personen werden beim Einlesesprozess aktualisiert.""",
'Werte überprüfen': """Auf dieser Seite können Werte überprüft werden. Wählen sie eine oder mehrere Spalten aus der Listenbox aus. 
Die entsprechenden Werte werden anschliessend als Tabelle und als Zeitreihe dargestellt.
"""
}
FELDER_GRUPPEN=['Fälle Basel', 'Inzidenzen Kanton Basel', 'Inzidenzen Stadt Basel', 'Inzidenzen Stadt Basel', 'Inzidenzen Riehen'
    , 'Indzidenzen Bettingen', 'Todesfälle']
#sql commands
SERVER_NAME = 'select @@servername as server_name'
KONTAKT_TECH = 'mailto:lukas.calmbach@bs.ch'
KONTAKT_FACH = 'mailto:simon.fuchs@bs.ch'
FELDER_ZEITREIHE = ['publizierte_neue_faelle'
      ,'publizierte_neue_faelle_kum'
      ,'hospitalisierte_bs'
      ,'hospitalisierte_total'
      ,'hospitalisierte_icu'
      ,'faelle_bs'
      ,'faelle_bs_kum'
      ,'erholt_bs'
      ,'gestorbene_bs'
      ,'isoliert_bs'
      ,'isoliert_gestern_kontakt_bs'
      ,'isoliert_zu_hause_bs'
      ,'isoliert_aph_bs'
      ,'isoliert_andere_bs'
      ,'isoliert_ohne_angaben_bs'
      ,'quarantaene_bs'
      ,'quarantaene_reise_bs'
      ,'quarantaene_kontakt_bs'
      ,'diff_faelle_bs'
      ,'diff_erholt_bs'
      ,'diff_verstorben_bs'
      ,'diff_quarantaene_rueckkehrende_bs'
      ,'diff_quarantaene_kontaktpersonen_bs'
      ,'inzidenz07_bs'
      ,'inzidenz14_bs'
      ,'inzidenz07_bl'
      ,'inzidenz14_bl'
      ,'summe_07_tage'
      ,'summe_14_tage'
      ,'faelle_bl'
      ,'faelle_bl_kum'
      ,'faelle_ch_kum'
      ,'faelle_loerrach_kum'
      ,'faelle_haut_rhin_kum'
      ,'faelle_bl_summe_07'
      ,'faelle_bl_summe_14'
      ,'inzidenz07_loerrach'
      ,'inzidenz07_haut_rhin'
      ,'inzidenz14_ch'
      ,'inzidenz07_ch'
      ,'faelle_riehen'
      ,'faelle_bettingen'
      ,'faelle_basel'
      ,'faelle_riehen_kum'
      ,'faelle_bettingen_kum'
      ,'faelle_basel_kum'
      ,'inzidenz07_riehen'
      ,'inzidenz14_riehen'
      ,'inzidenz07_bettingen'
      ,'inzidenz14_bettingen'
      ,'inzidenz07_basel'
      ,'inzidenz14_basel']
FELDER_INZIDENZEN = ['faelle_bs_kum'
      ,'faelle_bs_1W'
      ,'faelle_bs_2W'
      ,'faelle_bs_summe_07'
      ,'faelle_bs_summe_14'
      ,'inzidenz_bs_07'
      ,'inzidenz_bs_14'
      ,'bev_bs'
      ,'faelle_bl_kum'
      ,'faelle_bl_1W'
      ,'faelle_bl_2W'
      ,'faelle_bl_summe_07'
      ,'faelle_bl_summe_14'
      ,'inzidenz_bl_07'
      ,'inzidenz_bl_14'
      ,'bev_bl'
      ,'faelle_ch_kum'
      ,'faelle_ch_1W'
      ,'faelle_ch_2W'
      ,'faelle_ch_summe_07'
      ,'faelle_ch_summe_14'
      ,'inzidenz_ch_07'
      ,'inzidenz_ch_14'
      ,'bev_ch'
      ,'faelle_loerrach_kum'
      ,'faelle_loerrach_1W'
      ,'faelle_loerrach_2W'
      ,'faelle_loerrach_summe_07'
      ,'faelle_loerrach_summe_14'
      ,'inzidenz_loerrach_07'
      ,'inzidenz_loerrach_14'
      ,'bev_loerrach'
      ,'faelle_haut_rhin_kum'
      ,'faelle_haut_rhin_1W'
      ,'faelle_haut_rhin_2W'
      ,'faelle_haut_rhin_summe_07'
      ,'faelle_haut_rhin_summe_14'
      ,'inzidenz_haut_rhin_07'
      ,'inzidenz_haut_rhin_14'
      ,'bev_haut_rhin'
      ,'faelle_riehen_kum'
      ,'faelle_riehen_1W'
      ,'faelle_riehen_2W'
      ,'faelle_riehen_summe_07'
      ,'faelle_riehen_summe_14'
      ,'inzidenz_riehen_07'
      ,'inzidenz_riehen_14'
      ,'bev_riehen'
      ,'faelle_bettingen_kum'
      ,'faelle_bettingen_1W'
      ,'faelle_bettingen_2W'
      ,'faelle_bettingen_summe_07'
      ,'faelle_bettingen_summe_14'
      ,'inzidenz_bettingen_07'
      ,'inzidenz_bettingen_14'
      ,'bev_bettingen'
      ,'faelle_basel_kum'
      ,'faelle_basel_1W'
      ,'faelle_basel_2W'
      ,'faelle_basel_summe_07'
      ,'faelle_basel_summe_14'
      ,'inzidenz_basel_07'
      ,'inzidenz_basel_14'
      ,'bev_basel']
RESULT_SUCCESS = 5
RESULT_ERROR = 6
PROCESS = {'import': 1, 'update': 3, 'mail_test':6, 'mail_prod': 7, 'export_ogd': 5, 'synch_external': 2, 'sms': 8, 
    'login': 25, 'plots': 4, 'sms_test': 27}

URL_ANLEITUNG = "http://pdstatasvtweb03/docs/data/covid-lagebericht/Anleitung_0.1.9.pdf"