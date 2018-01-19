# WEBik

# Technisch Ontwerp
#### Controllers
Verschillende functies waarbij aangegeven staat of deze GET/POST zijn:


| Route          | Omschrijving                                                     | GET / POST     |
| -------------  |:---------------------------------------------------------------  | --------------:|
| **register()** | account aanmaken                                                 |  POST          |
| **login()**    | inloggen in systeem                                              |  POST          |
| **logout()**   | uitloggen en terug naar beginpagina                              |  session kill  |
| **follow()**   | een gebruiker volgen                                             |  POST          |
| **search()**   | zoeken naar personen om hun profielpagina te bekijken            |  GET           |
| **upload()**   | foto uploaden op eigen profielpagina                             |  POST          |
| **index()**    | beginpagina waar je kan kiezen om te registreren of in te loggen |  POST          |
| **like()**     | een foto liken                                                   |  POST          |


#### Views
Schermen gegroepeerd en de links met pijlen aangegeven:
<img src ="https://i.imgur.com/GncbGVc.jpg">
<img src = "https://i.imgur.com/G3kh35f.jpg">
<img src = "https://i.imgur.com/2rW5xuC.jpg">
#### Models/Helpers
Lijst van helper functie en hun omschrijving:
* **like():** de like functie moet je op bijna elke pagina wel kunnen gebruiken. er zijn namelijk veel verschillende profielen waarvan je een foto moet kunnen like
* **apology():** Bij foutief inloggen of registreren krijg je een foutmelding.
#### Plugins/Frameworks
Een korte lijst van plugins en frameworks:
* Navigatie-bar: http://getbootstrap.com/docs/4.0/components/navbar/
* buttons: http://getbootstrap.com/docs/4.0/components/buttons/
* Avatars: https://www.w3schools.com/howto/howto_css_image_avatar.asp
* GIF’s: https://developers.giphy.com/docs/

TEST

