from bs4 import BeautifulSoup
import re
import csv

def process_itemizedlist(node):
    text = ""
    for child in node.find_all('listitem', recursive=False):
        text = text + "• " + child.get_text(strip=True) + "\n"

    return text.strip()

def extrahiere_elementare_gefaehrdungen(document):
    # Elementare-Gefährdung-Titel-Format: G
    egef_pattern = re.compile(r'^G (\d+(?:\.\d+)+)(.+)')

    rows = []
    current_text = []

    for title in soup.find_all("title"):
        t = title.get_text(strip=True)

        # Erkenne neue elementare Gefährdung
        match = egef_pattern.match(t)
        if match:
            for sibling in title.find_next_siblings():
                text = sibling.get_text(strip=True)
                if sibling.name == 'title':
                    break
                elif sibling.name == 'itemizedlist':
                    text = process_itemizedlist(sibling)
                current_text.append(text + "\n")

            nummer = match.group(1)
            current_gefaehrdung = match.group(2).strip()
            rows.append(["G", "Elementare Gefährdung (G " + nummer + ")", current_gefaehrdung, "".join(current_text).strip()])
            current_text = []
    
    return rows

def extrahiere_spezifische_gefaehrdungen(document):
    # Baustein-Titel-Format: Drei bis fünf Großbuchstaben, Punkt, restliche Zeichen
    baustein_pattern = re.compile(r'^[A-Z]{3,5}\.\d+')
    baustein_split_pattern = re.compile(r'^([A-Z]{3,5})\.(.+)')

    rows = []
    current_baustein = None
    in_gefaehrdungslage = False
    current_gefaehrdung = None
    current_text = []

    for title in soup.find_all("title"):
        t = title.get_text(strip=True)

        # Erkenne neuen Baustein
        if baustein_pattern.match(t):
            current_baustein = t
            match = baustein_split_pattern.match(t)
            if match:
                current_baustein = t
                current_prefix = match.group(1)
                current_name = match.group(2).strip()
            in_gefaehrdungslage = False

        # Gefährdungslage beginnt
        elif t == "Gefährdungslage":
            in_gefaehrdungslage = True
            current_gefaehrdung = None
            current_text = []

        # Anforderungen = Gefährdungsende
        elif t == "Anforderungen":
            if current_gefaehrdung and current_text:
                rows.append([current_baustein, current_gefaehrdung, "".join(current_text).replace("\n", " ").strip()])
            in_gefaehrdungslage = False
            current_gefaehrdung = None
            current_text = []

        # Neue Gefährdung
        elif in_gefaehrdungslage:
            for sibling in title.find_next_siblings():
                text = sibling.get_text(strip=True)
                if sibling.name == 'title':
                    break
                elif sibling.name == 'itemizedlist':
                    text = process_itemizedlist(sibling)
                current_text.append(text + "\n")

            current_gefaehrdung = t
            rows.append([current_prefix, current_name, current_gefaehrdung, "".join(current_text).strip()])
            current_text = []

    # Letzte Gefährdung sichern
    if current_gefaehrdung and current_text:
        rows.append([current_baustein, current_gefaehrdung, "".join(current_text).strip()])

    return rows

with open("XML_Kompendium_2023.xml", "r", encoding="utf-8") as file:
    soup = BeautifulSoup(file, "lxml-xml")

rows_egef = extrahiere_elementare_gefaehrdungen(soup)
rows_sgef = extrahiere_spezifische_gefaehrdungen(soup)

# Speichern als CSV
with open("gefaehrdungen.csv", "w", encoding="utf-8-sig", newline="") as csvfile:
    writer = csv.writer(
        csvfile,
        delimiter=";",
        quoting=csv.QUOTE_ALL,   # <-- alle Felder in Quotes
        quotechar='"',
        lineterminator="\n")
    writer.writerow(["Kürzel", "Baustein-Name / Typ", "Gefährdung", "Beschreibung"])
    writer.writerows(rows_egef)
    writer.writerows(rows_sgef)

print(f"{len(rows_egef) + len(rows_sgef)} Gefährdungen extrahiert und in 'gefaehrdungen.csv' gespeichert.")

