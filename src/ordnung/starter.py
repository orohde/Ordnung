"""The rule set Ordnung! ships with.

Generic rules for a German household, written for the starter folders
(``folders.STARTER_HOUSEHOLD``). Each entry is (folder, [alternatives]); every
alternative is one rule whose words must ALL appear in the document text.

A fresh installation gets these rules as they are. An archive that already
has its own structure can *adapt* them instead: each rule is measured against
the filed documents and moved to the folder where it actually finds them –
or left out when it fits nowhere well enough.
"""

from __future__ import annotations

STARTER_RULES: list[tuple[str, list[list[str]]]] = [
    ("Arbeit/Gehaltsabrechnungen", [["gehaltsabrechnung"], ["entgeltabrechnung"], ["verdienstabrechnung"],
                                    ["lohnabrechnung"], ["bezügemitteilung"]]),
    ("Arbeit/Verträge", [["arbeitsvertrag"]]),
    ("Arbeit/Zeugnisse", [["arbeitszeugnis"], ["zwischenzeugnis"]]),
    ("Auto/Versicherung", [["kraftfahrtversicherung"], ["kfz-versicherung"], ["kfz-haftpflicht"]]),
    ("Auto/Steuer", [["kraftfahrzeugsteuer"]]),
    ("Auto/Werkstatt", [["hauptuntersuchung"], ["inspektion", "kilometerstand"]]),
    ("Auto/Kaufvertrag", [["kaufvertrag", "fahrzeug-ident"], ["zulassungsbescheinigung teil ii"]]),
    ("Banken/Girokonto", [["kontoauszug"], ["rechnungsabschluss", "girokonto"]]),
    ("Banken/Kreditkarte", [["kreditkartenabrechnung"], ["kreditkarte", "umsatzaufstellung"]]),
    ("Banken/Depot", [["depotauszug"], ["wertpapierabrechnung"], ["jahressteuerbescheinigung"]]),
    ("Banken/Kredite", [["darlehensvertrag"], ["darlehenskonto"], ["tilgungsplan"]]),
    ("Behörden/Rundfunkbeitrag", [["rundfunkbeitrag"]]),
    ("Behörden/Meldewesen", [["meldebescheinigung"], ["bürgeramt", "anmeldung"]]),
    ("Behörden/Ausweise", [["reisepass", "antrag"], ["personalausweis", "antrag"]]),
    ("Finanzamt/Bescheide", [["steuerbescheid"], ["bescheid für", "einkommensteuer"]]),
    ("Finanzamt/Steuererklärung", [["einkommensteuererklärung", "anlage"], ["elster", "übertragungsprotokoll"]]),
    ("Finanzamt/Belege", [["lohnsteuerbescheinigung"], ["zuwendungsbestätigung"], ["spendenbescheinigung"]]),
    ("Gesundheit/Arztbriefe", [["arztbrief"], ["entlassungsbericht"], ["sehr geehrte frau kollegin"],
                               ["sehr geehrter herr kollege"]]),
    ("Gesundheit/Befunde", [["befundbericht"], ["laborbefund"]]),
    ("Gesundheit/Rechnungen", [["gebührenordnung für ärzte"], ["gebührenordnung für zahnärzte"],
                               ["goä", "rechnung"]]),
    ("Gesundheit/Rezepte", [["e-rezept"], ["arzneiverordnungsblatt"]]),
    ("Gesundheit/Krankenversicherung", [["krankenversicherung", "beitragsanpassung"],
                                        ["krankenkasse", "mitgliedsbescheinigung"],
                                        ["leistungsabrechnung", "krankenversicherung"]]),
    ("Versicherungen/Haftpflicht", [["privathaftpflicht"], ["haftpflichtversicherung", "versicherungsschein"]]),
    ("Versicherungen/Hausrat", [["hausratversicherung"]]),
    ("Versicherungen/Rechtsschutz", [["rechtsschutzversicherung"]]),
    ("Versicherungen/Wohngebäude", [["wohngebäudeversicherung"]]),
    ("Versicherungen/Leben und Rente", [["renteninformation"], ["lebensversicherung"], ["rentenversicherung", "standmitteilung"]]),
    ("Verträge/Mobilfunk", [["mobilfunkrechnung"], ["mobilfunkvertrag"]]),
    ("Verträge/Internet und Telefon", [["festnetz", "rechnung"], ["glasfaser", "rechnung"], ["internetanschluss"]]),
    ("Verträge/Strom und Gas", [["stromrechnung"], ["jahresabrechnung", "strom"], ["abschlag", "strom"],
                                ["erdgas", "abrechnung"]]),
    ("Wohnen/Nebenkosten", [["nebenkostenabrechnung"], ["betriebskostenabrechnung"], ["grundsteuer"],
                            ["abwassergebühr"]]),
    ("Wohnen/Miete oder Eigentum", [["mietvertrag"], ["kaufvertrag", "grundbuch"], ["grundbuchauszug"]]),
    ("Bedienungsanleitungen", [["bedienungsanleitung"], ["gebrauchsanweisung"], ["betriebsanleitung"]]),
]


def starter_rules() -> list[tuple[str, list[dict]]]:
    """(folder, conditions) for every shipped rule."""
    return [(folder, [{"type": "contains", "value": word} for word in words])
            for folder, alternatives in STARTER_RULES for words in alternatives]
