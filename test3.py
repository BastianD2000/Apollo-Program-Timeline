import json
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS

# Namespaces
EX = Namespace("http://apollo.org/resource/")
TL = Namespace("http://yoda.media.h-da.de/thull/vocab/tl#")

# RDF-Graph initialisieren
g = Graph()
g.bind("ex", EX)
g.bind("tl", TL)
g.bind("rdfs", RDFS)

# Timeline erstellen
g.add((EX.timeline, RDF.type, TL.Timeline))
g.add((EX.timeline, RDFS.label, Literal("Apollo Missions Timeline")))

# Öffnen der JSON-Daten
with open("7/sparql_apollo.json", "r", encoding="utf-8") as file:
    data = json.load(file)

slide_counter = 1
media_counter = 1

# Funktion zur Erstellung des Texts mit HTML-Zeilenumbrüchen und eingebetteten Links
def create_text(description, crew_data, role_data, launch_rocket, spacecraft, launch_site):
    text = description.replace("\n", "<br>")
    
    # Crew-Daten mit Links formatieren
    crew_text = ""
    if crew_data and role_data:
        crew_members = crew_data.split(" | ")
        roles = role_data.split(" | ")
        crew_text = "<br>".join([
            f'<a href="{astronaut}" target="_blank">{astronaut.split("/")[-1].replace("_", " ")}</a> - {role}' 
            for astronaut, role in zip(crew_members, roles)
        ])
    
    if crew_text:
        text += f"<br><b>Crew:</b><br>{crew_text}"

    # Rakete mit Links formatieren (Name wird immer angezeigt, Link nur wenn vorhanden)
    if launch_rocket:
        rocket_links = launch_rocket.split(" | ")
        rocket_text = "<br>".join([
            f'<a href="{rocket}" target="_blank">{rocket.split("/")[-1].replace("_", " ")}</a>' 
            if "http" in rocket else rocket.split("/")[-1].replace("_", " ") 
            for rocket in rocket_links
        ])
        if rocket_text:
            text += f"<br><b>Rocket:</b><br>{rocket_text}"

    # Spacecraft mit Links formatieren
    if spacecraft:
        spacecraft_links = spacecraft.split(" | ")
        spacecraft_text = "<br>".join([
            f'<a href="{craft}" target="_blank">{craft.split("/")[-1].replace("_", " ")}</a>' 
            for craft in spacecraft_links
        ])
        text += f"<br><b>Spacecraft:</b><br>{spacecraft_text}"

    # Launch Site mit Links formatieren
    if launch_site:
        launch_site_links = launch_site.split(" | ")
        launch_site_text = "<br>".join([
            f'<a href="{site}" target="_blank">{site.split("/")[-1].replace("_", " ")}</a>' 
            for site in launch_site_links
        ])
        text += f"<br><b>Launch Site:</b><br>{launch_site_text}"
        
    return text

# Funktion zur Auswahl des richtigen Bildes basierend auf der Missionsname
def select_image_url(mission_name, image_urls):
    if mission_name == "Apollo 11":
        return image_urls[8] if len(image_urls) > 8 else image_urls[0]
    elif mission_name == "Apollo 12":
        return image_urls[1] if len(image_urls) > 1 else image_urls[0]
    elif mission_name == "Apollo 14":
        return image_urls[3] if len(image_urls) > 3 else image_urls[0]
    else:
        return image_urls[0]

# Verarbeitung der Missionsdaten
for binding in data["results"]["bindings"]:
    try:
        mission_name = binding["name"]["value"]
        mission_uri = URIRef(EX + mission_name.replace(" ", "_"))

        # Erstellen der Slide-URI
        slide_uri = URIRef(EX + "slide" + str(slide_counter))
        g.add((slide_uri, RDF.type, TL.Slide))

        # Erstellen des Textes für die Mission
        text_uri = URIRef(EX + "text" + str(slide_counter))
        g.add((text_uri, RDF.type, TL.Text))
        g.add((text_uri, TL.headline, Literal(mission_name)))
        
        # Mission Details
        description = binding.get("description", {}).get("value", "")
        crew_data = binding.get("crew", {}).get("value", "")
        role_data = binding.get("role", {}).get("value", "")
        launch_rocket = binding.get("launchRocket", {}).get("value", "")
        spacecraft = binding.get("spacecraft", {}).get("value", "")
        launch_site = binding.get("launchSite", {}).get("value", "")
        
        # Text erstellen
        text = create_text(description, crew_data, role_data, launch_rocket, spacecraft, launch_site)
        
        # Start- und Enddatum hinzufügen
        start_date = binding.get("startDate", {}).get("value", "")
        end_dates = binding.get("endDate", {}).get("value", "").split(" | ")
        
        if start_date:
            g.add((slide_uri, TL.startDate, Literal(start_date)))
        
        # Nur das erste Enddatum verwenden für Apollo 9
        if mission_name == "Apollo 9" and end_dates:
            g.add((slide_uri, TL.endDate, Literal(end_dates[0])))
        elif end_dates:
            g.add((slide_uri, TL.endDate, Literal(end_dates[0])))
        
        # Text in das Slide-Element einfügen
        g.add((text_uri, TL.text, Literal(text.strip())))
        g.add((slide_uri, TL.text, text_uri))

        # Bild-URL (passendes Bild auswählen)
        image_urls = binding.get("image", {}).get("value", "").split(" | ")
        selected_image_url = select_image_url(mission_name, image_urls)
        media_uri = URIRef(EX + "media" + str(media_counter))
        if selected_image_url:
            # Bildunterschrift aus der URL extrahieren
            image_caption = selected_image_url.split("/")[-1].split(".")[0].replace("_", " ")
            g.add((media_uri, RDF.type, TL.Media))
            g.add((media_uri, TL.url, URIRef(selected_image_url)))
            g.add((media_uri, TL.caption, Literal(image_caption)))

            g.add((slide_uri, TL.media, media_uri))
            media_counter += 1

        # Verbindung der Mission zum Slide
        g.add((EX.timeline, TL.event, slide_uri))
        slide_counter += 1

    except Exception as e:
        print(f"Fehler bei der Verarbeitung der Mission '{binding['name']['value']}': {e}")
        print(f"Details: {binding}")

# Finaler Export nach der letzten Mission
output_file = "7/apollo_missions.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"RDF-Daten mit Mapping wurden in {output_file} gespeichert.")
