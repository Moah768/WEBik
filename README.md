# WEBik

# Technisch Ontwerp
#### Controllers
Verschillende functies waarbij aangegeven staat of deze GET/POST zijn:


| Route                     | Omschrijving                                                                                  | GET / POST     |
| ------------------------- |:-------------------------------------------------------------------------------------------   | --------------:|
| **register()**            | Account aanmaken                                                                              |  POST          |
| **login()**               | Inloggen in systeem                                                                           |  POST          |
| **logout()**              | Uitloggen en terug naar beginpagina                                                           |  session kill  |
| **search()**              | Zoeken naar personen om hun profielpagina te bekijken en hen daar ook te volgen               |  GET           |
| **uploaden()**            | Foto uploaden op eigen profielpagina                                                          |  POST          |
| **index()**               | Geeft profiel weer van de huidige gebruiker                                                   |  POST          |
| **change_password()**     | Wachtwoord wijzigen                                                                           |  POST          |
| **followers()**           | Laat per gebruiker een lijst zien met al zijn volgers                                         |  POST          |
| **following()**           | Laat per gebruiker een lijst zien met iedereen die hij volgt                                  |  POST          |
| **add_following()**       | Voegt de gebruiker die jij net hebt gevolgd toe aan jou volgers                               |  POST          |
| **profile()**             | Weergeeft profiel van een andere gebruiker                                                    |  POST          |
| **gif()**                 | Haal een gif uit de Giphy API                                                                 |  POST          |
| **gif_uploaden()**        | Upload gif naar het profiel van de gebruiker                                                  |  POST          |
| **upload_file()**         | Een link voor het makkelijk terughalen van fotos                                              |  POST          |
| **like()**                | Met deze functie kan een gif of foto leuk gevonden worden                                     |  POST          |
| **dislike()**             | Met deze functie kan je je like terugtrekken                                                  |  POST          |
| **timeline()**            | Laat alle uploads van de mensen die jij volgt zien                                            |  POST          |
| **settings()**            | Ga naar instellingen waar je je bio/profiel foto kan veranderen                               |  POST          |
| **trending()**            | Laat van alle gebruikers de uploads zien gesorteerd op meeste likes                           |  POST          |
| **delete()**              | Verwijder een geuploade foto of gif van je profiel                                            |  POST          |
| **profile_picture()**     | Upload een profiel foto                                                                       |  POST          |
| **Unfollow()**            | Ontvolg een account                                                                           |  POST          |
| **bio()**                 | Voeg een bio toe aan je profiel                                                               |  POST          |
| **add_comment()**         | Voeg een comment toe aan een foto                                                             |  POST          |
| **show_comment()**        | Laat comment van een foto zien en bekijk foto beter                                           |  POST          |





#### Views
Test
Schermen gegroepeerd en de links met pijlen aangegeven:
<img src ="https://i.imgur.com/GncbGVc.jpg">
<img src = "https://i.imgur.com/G3kh35f.jpg">
<img src = "https://i.imgur.com/2rW5xuC.jpg">

#### Models/Helpers
Lijst van helper functie en hun omschrijving:
* **apology():** Bij fouten op de webapplicatie krijg je een foutmelding.
* **login_required():** Maakt route waarbij inloggen verplicht is
* **allowed_file():** Controleer of file toegestaan is
* **get_id():** Geeft de huidige gebruikers id
* **following_users():** Geeft gebruikers die de huidige gebruiker volgen
* **liked_photos():** Geeft gelikete fotos terug.




#### Plugins/Frameworks
Een korte lijst van plugins en frameworks:
* Navigatie-bar: http://getbootstrap.com/docs/4.0/components/navbar/
* buttons: http://getbootstrap.com/docs/4.0/components/buttons/
* GIF’s: https://developers.giphy.com/docs/

