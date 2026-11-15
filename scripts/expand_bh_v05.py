#!/usr/bin/env python3
"""Dataset v0.5 — ljudski-autorovane situacije (60) x površinske varijante = ~180 stavki.
Svaka situacija je ručno napisana s pravim rasuđivanjem; slotovi mijenjaju samo imena/gradove.
Cilj: razbiti template-prior (o1/o2/o3 default). CC-BY-4.0.
"""
import hashlib
import json
import os
import random

R = random.Random(99)
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "..", "datasets", "expanded-v05")
os.makedirs(OUT, exist_ok=True)

IMENA = ["Goran Lukić", "Amina Hodžić", "Marko Jurić", "Lejla Softić", "Ivan Kovačević",
         "Selma Delić", "Petar Pavlović", "Emina Jahić", "Jovan Simić", "Alma Kurtić"]
GRADOVI = ["Sarajeva", "Tuzle", "Mostara", "Zenice", "Bihaća", "Banje Luke", "Brčkog", "Trebinja",
           "Foče", "Goražda", "Konjica", "Livna"]
DOK = ["pasoš", "ličnu kartu", "vozačku dozvolu", "građevinsku dozvolu", "radnu knjižicu"]
UST = ["Porezna uprava", "MUP", "Općina Centar", "Katastar", "Dom zdravlja"]

# (kat, state_template, options[(id,text)], decision, ranked, scores, risk, factors, conf, abst, rationale)
S = [
# --- choice ---
("choice", "{nm} iz {gr} stigla je ponuda za posao u inostranstvu, ali majka mu je teško bolesna i jedino on brine o njoj.",
 [("o1", "Prihvatiti posao i otići."), ("o2", "Ostati i brinuti o majci."), ("o3", "Tražiti odgodu početka rada.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.15, "o2": 0.75, "o3": 0.4}, "low", [], 0.75, None,
 "Briga o bolesnoj majci nadmašuje karijeru; odgoda je rezerva ako poslodavac pristane."),
("choice", "Firma iz {gr} nudi {nm} rad na crno uz veću platu, ili legalan ugovor uz manju platu.",
 [("o1", "Rad na crno."), ("o2", "Legalan ugovor."), ("o3", "Odbaciti obje ponude.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.1, "o2": 0.85, "o3": 0.3}, "medium", ["penzija, zdravstveno"], 0.85, None,
 "Rad na crno gubi staž i zaštitu; razlika u plati to ne pokriva."),
("choice", "{nm} ({gr}) zatekao je otvoren tuđi novčanik s većom svotom na klupi u parku.",
 [("o1", "Uzmi novac."), ("o2", "Odnesi u najbližu policijsku stanicu."), ("o3", "Ostavi gdje jeste.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.02, "o2": 0.9, "o3": 0.3}, "low", [], 0.9, None,
 "Nađena stvar se predaje policiji; uzimanje je krađa, ostavljanje rizikuje gubitak."),
("choice", "Student {nm} iz {gr} pao je ispit koji mu je uslov za stipendiju; profesor nudi da mu 'sredi' prolaz za uslugu.",
 [("o1", "Prihvatiti namješten prolaz."), ("o2", "Odbiti i učiti za popravni."), ("o3", "Prijaviti profesora.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.7, "o3": 0.6}, "medium", ["izbacivanje"], 0.7, None,
 "Namješten prolaz je korupcija s rizikom izbacivanja; popravni je čist put. Prijava je hrabra ali nosi rizik odmazde."),
("choice", "{nm} iz {gr} svjedočio je saobraćajnoj nesreći; vozač koji je izazvao nudi mu novac da šuti.",
 [("o1", "Uzmi novac i šuti."), ("o2", "Svjedoči istinito policiji."), ("o3", "Ne miješaj se uopšte.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.9, "o3": 0.4}, "medium", ["krivična odgovornost"], 0.9, None,
 "Podmićivanje svjedoka je krivično djelo; istinito svjedočenje je obaveza."),
# --- risk ---
("risk", "{nm} iz {gr} razmišlja da podigne brzi kredit s kamatom od 40% da pokrije kockarski dug.",
 [("o1", "Podigni kredit."), ("o2", "Potraži savjetovalište za kockanje i reprogram."), ("o3", "Prodaj stan.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.85, "o3": 0.2}, "high", ["dužnička spirala"], 0.85, None,
 "Skupi kredit na kockarski dug je spirala; stručna pomoć i reprogram su izlaz."),
("risk", "Turista {nm} u {gr} nudi mještaninu vožnju neosiguranim čamcem po nabujaloj rijeci {br} za dobru cijenu.",
 [("o1", "Prihvati vožnju."), ("o2", "Odbij i prijavi opasnu ponudu."), ("o3", "Cjenkaj se za nižu cijenu.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.9, "o3": 0.1}, "high", ["utapanje"], 0.9, None,
 "Nabujala rijeka + neosiguran čamac = životni rizik; cijena je nebitna."),
("risk", "{nm} ({gr}) dobija poslovni e-mail s linkom od nepoznatog pošiljaoca koji traži hitnu uplatu dobavljaču.",
 [("o1", "Klikni i uplati odmah."), ("o2", "Provjeri pošiljaoca telefonom pa odluči."), ("o3", "Ignoriši sve e-mailove.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.85, "o3": 0.4}, "high", ["phishing, krađa"], 0.85, None,
 "Hitnost + nepoznat pošiljalac je klasičan phishing obrazac; provjera kanalom van e-maila."),
("risk", "Poljoprivrednik {nm} iz {gr} prska voćnjak ({br}) hemikalijom kojoj je istekao rok, jer je jeftinija.",
 [("o1", "Prskaj isteklog."), ("o2", "Kupi ispravno sredstvo."), ("o3", "Ne prskaj ništa ove godine.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.15, "o2": 0.8, "o3": 0.4}, "medium", ["zdravlje, rod"], 0.8, None,
 "Istekla hemija je neprovjerenaeyes; ispravno sredstvo štiti i rod i kupce."),
# --- scoring ---
("scoring", "Prijava stranke {nm} ({us}) za subvenciju: priloženi su svi papiri osim potvrde o prihodima.",
 [("o1", "Potpuna."), ("o2", "Nepotpuna.")],
 "o2", ["o2", "o1"], {"o1": 0.25, "o2": 0.8}, "low", [], 0.8, None,
 "Subvencija se ne može obračunati bez potvrde o prihodima."),
("scoring", "Tehnički pregled vozila {nm} ({gr}, {br}): kočnice ispravne, svjetla neispravna, gume na granici.",
 [("o1", "Prolazi."), ("o2", "Ne prolazi.")],
 "o2", ["o2", "o1"], {"o1": 0.2, "o2": 0.85}, "medium", ["sigurnost u saobraćaju"], 0.85, None,
 "Neispravna svjetla + gume na granici znače pad na pregledu."),
("scoring", "Školski zadatak učenika {nm} ({us}): tačan rezultat, ali bez postupka i bez jedinica.",
 [("o1", "Odličan."), ("o2", "Djelimičan.")],
 "o2", ["o2", "o1"], {"o1": 0.3, "o2": 0.8}, "low", [], 0.8, None,
 "Bez postupka nema dokaza razumijevanja; rezultat sam nije dovoljan."),
# --- benchmark ---
("benchmark", "{nm} iz {gr} podnosi zahtjev za penziju ({us}), ali mu fali 6 mjeseci staža do uslova.",
 [("o1", "Odobriti penziju."), ("o2", "Odbaciti — ne ispunjava uslov.")],
 "o2", ["o2", "o1"], {"o1": 0.15, "o2": 0.85}, "medium", ["zloupotreba fonda"], 0.85, None,
 "Uslov staža je zakonski prag; manjak se ne može zaobići odlukom službenika."),
("benchmark", "Vlasnik iz {gr} traži legalizaciju ({br}) objekta izgrađenog na klizištu, {nm} je referent.",
 [("o1", "Legaliziovati."), ("o2", "Odbaciti uz obrazloženje.")],
 "o2", ["o2", "o1"], {"o1": 0.1, "o2": 0.9}, "high", ["sigurnost"], 0.9, None,
 "Klizište isključuje legalizaciju bez obzira na pritisak."),
# --- confidence ---
("confidence", "Ugovor stranke {nm} ({us}) ima potpis, ali nedostaje pečat firme i datum.",
 [("o1", "Uredan ugovor."), ("o2", "Neuredan ugovor.")],
 "o2", ["o2", "o1"], {"o1": 0.2, "o2": 0.85}, "medium", ["pravna valjanost"], 0.85, None,
 "Bez pečata i datuma ugovor je formalno manjkav."),
("confidence", "Svjedok {nm} ({gr}) tvrdi da je vidio događaj, ali je bio 200 metara daleko noću.",
 [("o1", "Pouzdan iskaz."), ("o2", "Nepouzdan iskaz.")],
 "o2", ["o2", "o1"], {"o1": 0.15, "o2": 0.85}, "medium", ["pogrešna presuda"], 0.85, None,
 "Noć + 200 metara onemogućavaju pouzdano prepoznavanje."),
# --- multicriteria ---
("multicriteria", "{nm} iz {gr} bira vrtić za dijete ({br}): jeftiniji blizu posla ali s lošim ocjenama, ili skuplji dalje s odličnim.",
 [("o1", "Jeftiniji blizu."), ("o2", "Skuplji dalje s ocjenama."), ("o3", "Čuvati dijete kod kuće bez posla.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.4, "o2": 0.75, "o3": 0.2}, "medium", ["razvoj djeteta"], 0.75, None,
 "Kvalitet brige o djetetu nadmašuje i cijenu i udaljenost."),
("multicriteria", "Porodica {nm} ({gr}) bira grijanje ({us}): jeftina peć na ugalj ili skuplja toplotna pumpa uz subvenciju.",
 [("o1", "Peć na ugalj."), ("o2", "Toplotna pumpa uz subvenciju."), ("o3", "Ne grijati se.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.35, "o2": 0.8, "o3": 0.05}, "medium", ["zdravlje, troškovi"], 0.8, None,
 "Subvencija poništava razliku u cijeni, a zdravlje i dugoročni trošak odlučuju."),
("multicriteria", "{nm} ({us}) kupuje polovan auto: jeftiniji s velikom kilometražom ili skuplji s garancijom kuće.",
 [("o1", "Jeftiniji s kilometražom."), ("o2", "Skuplji s garancijom."), ("o3", "Odustati od kupovine.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.25, "o2": 0.8, "o3": 0.4}, "medium", ["kvarovi"], 0.8, None,
 "Garancija kuće pokriva rizik koji kilometraža samo najavljuje."),
# --- ranking ---
("ranking", "{nm} iz {gr} hitno treba izvod iz matične knjige za sutrašnji konkurs; portal radi, ali izvod stiže poštom za 5 dana.",
 [("e-uprava", "Portal."), ("salter", "Šalter uživo."), ("posta", "Pošta.")],
 "salter", ["salter", "posta", "e-uprava"], {"e-uprava": 0.2, "salter": 0.9, "posta": 0.3}, "medium", ["rok konkursa"], 0.9, None,
 "Samo šalter daje papir odmah; portal kasni poštom."),
("ranking", "{nm} šalje žalbu kojoj zakon traži dokaz o datumu predaje, a rok ističe danas u ponoć.",
 [("e-uprava", "Portal."), ("salter", "Šalter (zatvoren)."), ("posta", "Pošta s povratnicom.")],
 "posta", ["posta", "e-uprava", "salter"], {"e-uprava": 0.5, "salter": 0.05, "posta": 0.9}, "high", ["propušten rok"], 0.9, None,
 "Povratnica je jedini dokaz datuma kad je šalter zatvoren."),
# --- abstention / ambiguous ---
("abstention", "Podnesak {br} sadrži samo jednu rečenicu: 'Molim da se riješi.' Bez imena, predmeta i priloga.",
 [("o1", "Odobriti."), ("o2", "Odbiti."), ("o3", "Tražiti dopunu.")],
 "abstain", [], {}, "medium", ["nema podataka"], 0.2, "nerazumljiv podnesak",
 "Jedna rečenica bez ikakvih podataka ne nosi odluku."),
("abstention", "Dva vještaka ({gr}) dala su suprotna mišljenja o istom kvaru ({br}), oba s pečatom i obrazloženjem.",
 [("o1", "Prihvatiti prvo mišljenje."), ("o2", "Prihvatiti drugo mišljenje."), ("o3", "Tražiti treće vještačenje.")],
 "o3", ["o3", "o1", "o2"], {"o1": 0.3, "o2": 0.3, "o3": 0.6}, "medium", ["pogrešna odluka"], 0.55, None,
 "Dva jednaka suprotna mišljenja traže treće; povjerenje ostaje nisko."),
("abstention", "Zahtjev ({br}) je napisan mješavinom tri jezika i niko u ustanovi {us} ga ne razumije u cijelosti.",
 [("o1", "Odobriti."), ("o2", "Odbiti."), ("o3", "Tražiti prevod.")],
 "o3", ["o3", "o1", "o2"], {"o1": 0.1, "o2": 0.1, "o3": 0.85}, "medium", ["nesporazum"], 0.85, None,
 "Nerazumljiv zahtjev se ne odobrava niti odbija — traži se prevod."),
]

S2 = [
("choice", "{nm} iz {gr} može kupiti stan na kredit s kamatom 3% fiksno ili čekati pad cijena uz rizik rasta kamata.",
 [("o1", "Kupiti sada na fiksni kredit."), ("o2", "Čekati pad cijena."), ("o3", "Odustati od kupovine.")],
 "o1", ["o1", "o2", "o3"], {"o1": 0.7, "o2": 0.4, "o3": 0.1}, "medium", ["kamatni rizik"], 0.7, None,
 "Fiksna niska kamata zaključava trošak; čekanje nosi dvostruki rizik."),
("choice", "Poslodavac iz {gr} traži od {nm} da potpiše otkaz sporazumno uz otpremninu, iako ima pravo na redovan otkazni rok.",
 [("o1", "Potpisati sporazumni."), ("o2", "Tražiti redovan otkazni rok."), ("o3", "Dati otkaz sam.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.4, "o2": 0.75, "o3": 0.1}, "medium", ["prava radnika"], 0.75, None,
 "Sporazumni otkaz gubi prava iz redovnog roka; otpremnina to rijetko pokriva."),
("choice", "{nm} ({gr}) našao je novčanik s dokumentima ali bez novca.",
 [("o1", "Zadržati dokumente."), ("o2", "Predati policiji."), ("o3", "Baciti u smeće.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.1, "o2": 0.9, "o3": 0.05}, "low", [], 0.9, None,
 "Dokumenti se vraćaju vlasniku preko policije."),
("choice", "Ljekar predlaže {nm} iz {gr} skupu privatnu operaciju koja nije hitna, a isti zahvat radi se besplatno u javnoj bolnici uz čekanje.",
 [("o1", "Privatno odmah."), ("o2", "Javna bolnica uz čekanje."), ("o3", "Odbiti operaciju.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.4, "o2": 0.8, "o3": 0.1}, "medium", ["trošak"], 0.8, None,
 "Nehitni zahvat ne opravdava privatni trošak kad javna opcija postoji."),
("choice", "{nm} iz {gr} dobija nasljedstvo, a rođak traži da mu prepiše dio 'na riječ', bez papira.",
 [("o1", "Prepisati na riječ."), ("o2", "Sve preko notara i ugovora."), ("o3", "Odbiti rođaka bez obrazloženja.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.9, "o3": 0.3}, "high", ["prevara, gubitak"], 0.9, None,
 "Imovina bez papira je poklon prevarantu; notar štiti obje strane."),
("risk", "{nm} iz {gr} ulaže cijelu ušteđevinu u jedan kripto-token koji preporučuje influenser.",
 [("o1", "Uloži sve."), ("o2", "Uloži mali dio koji može izgubiti."), ("o3", "Ne ulaži ništa.")],
 "o3", ["o3", "o2", "o1"], {"o1": 0.03, "o2": 0.3, "o3": 0.9}, "high", ["totalni gubitak"], 0.9, None,
 "Influenserove preporuke + cijela ušteđevina je recept za totalni gubitak."),
("risk", "Vozač {nm} iz {gr} vozi starim gumama po poledici jer 'nema para za zimske'.",
 [("o1", "Voziti dalje."), ("o2", "Kupiti polovne zimske."), ("o3", "Ne voziti dok se ne riješi.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.1, "o2": 0.8, "o3": 0.6}, "high", ["nesreća"], 0.8, None,
 "Polovne zimske su jeftin kompromis; vožnja na ljetnim po ledu je ruski rulet."),
("risk", "{nm} ({gr}) ostavlja djecu samu kod kuće preko noći radi smjene.",
 [("o1", "Ostaviti ih same."), ("o2", "Naći čuvanje kod rodbine."), ("o3", "Voditi djecu na smjenu.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.05, "o2": 0.9, "o3": 0.3}, "high", ["sigurnost djece"], 0.9, None,
 "Djeca sama preko noći su neprihvatljiv rizik; rodbina je rješenje."),
("risk", "Firma {nm} iz {gr} skladišti zapaljive materije u podrumu stambene zgrade.",
 [("o1", "Nastaviti skladištenje."), ("o2", "Izmjestiti u atestirano skladište."), ("o3", "Prestati s poslom.")],
 "o2", ["o2", "o3", "o1"], {"o1": 0.02, "o2": 0.9, "o3": 0.5}, "high", ["požar, ljudski životi"], 0.9, None,
 "Zapaljivo u stambenoj zgradi je potencijalna katastrofa; atestirano skladište je obaveza."),
("scoring", "Zahtjev stranke {nm} ({us}): svi papiri tu, ali je podnesen nakon roka.",
 [("o1", "Potpun."), ("o2", "Nepotpun/neblagovremen.")],
 "o2", ["o2", "o1"], {"o1": 0.2, "o2": 0.85}, "medium", ["propušten rok"], 0.85, None,
 "Zakašnjeli zahtjev ne može biti potpun bez obzira na sadržaj."),
("scoring", "Prijava {nm} za konkurs: diploma priložena, ali nedostaje dokaz o radnom iskustvu koji je eliminatoran.",
 [("o1", "Potpuna."), ("o2", "Nepotpuna.")],
 "o2", ["o2", "o1"], {"o1": 0.15, "o2": 0.88}, "medium", ["diskvalifikacija"], 0.88, None,
 "Eliminatoran uslov bez dokaza znači nepotpunu prijavu."),
("benchmark", "{nm} iz {gr} traži penziju, staž uredan, ali nema dokaz o državljanstvu.",
 [("o1", "Odobriti."), ("o2", "Odbaciti dok ne dostavi dokaz.")],
 "o2", ["o2", "o1"], {"o1": 0.15, "o2": 0.85}, "medium", ["isplata bez osnova"], 0.85, None,
 "Bez dokaza državljanstva nema osnova za isplatu."),
("benchmark", "Zahtjev za subvenciju ({us}): prihod domaćinstva iznad cenzusa, sve ostalo uredno.",
 [("o1", "Odobriti iz sažaljenja."), ("o2", "Odbaciti — iznad cenzusa.")],
 "o2", ["o2", "o1"], {"o1": 0.1, "o2": 0.9}, "medium", ["zloupotreba"], 0.9, None,
 "Cenzus je prag; sažaljenje ga ne pomiče."),
("confidence", "Ugovor stranke {nm} ima sve: potpis, pečat, datum i klauzule.",
 [("o1", "Uredan."), ("o2", "Neuredan.")],
 "o1", ["o1", "o2"], {"o1": 0.92, "o2": 0.08}, "low", [], 0.92, None,
 "Svi formalni elementi su prisutni."),
("confidence", "Iskaz svjedoka {nm} potvrđen je snimkom nadzorne kamere.",
 [("o1", "Pouzdan."), ("o2", "Nepouzdan.")],
 "o1", ["o1", "o2"], {"o1": 0.9, "o2": 0.1}, "low", [], 0.9, None,
 "Snimak potvrđuje iskaz."),
("multicriteria", "{nm} iz {gr} bira između posla s većom platom ali noćnim smjenama i manje plaćenog dnevnog posla; ima malo dijete.",
 [("o1", "Veća plata, noćne smjene."), ("o2", "Manja plata, dnevni posao."), ("o3", "Ne raditi.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.4, "o2": 0.75, "o3": 0.15}, "medium", ["porodica, zdravlje"], 0.75, None,
 "Noćne smjene s malim djetetom koštaju više nego što plata donosi."),
("multicriteria", "Student {nm} ({gr}) bira: težak fakultet s perspektivom ili lakši bez perspektive, uz stipendiju koja traje 4 godine.",
 [("o1", "Lakši fakultet."), ("o2", "Teži s perspektivom."), ("o3", "Odustati od studija.")],
 "o2", ["o2", "o1", "o3"], {"o1": 0.3, "o2": 0.8, "o3": 0.1}, "medium", ["budućnost"], 0.8, None,
 "Stipendija pokriva 4 godine — dovoljno za teži put koji se isplati."),
("ranking", "{nm} iz {gr} šalje hitan dopis koji mora stići danas do 15h; pošta zatvara u 14h, šalter radi do 16h.",
 [("e-uprava", "Portal."), ("salter", "Šalter."), ("posta", "Pošta.")],
 "salter", ["salter", "e-uprava", "posta"], {"e-uprava": 0.4, "salter": 0.9, "posta": 0.1}, "high", ["rok"], 0.9, None,
 "Pošta zatvara prije roka; šalter je jedina sigurna opcija."),
("ranking", "Žalba stranke {nm} mora imati dokaz o datumu; portal izdaje potvrdu odmah, pošta putuje 3 dana.",
 [("e-uprava", "Portal s potvrdom."), ("salter", "Šalter."), ("posta", "Pošta.")],
 "e-uprava", ["e-uprava", "salter", "posta"], {"e-uprava": 0.9, "posta": 0.3, "salter": 0.5}, "medium", ["dokaz"], 0.9, None,
 "Trenutna potvrda s portala je najjači dokaz datuma."),
("abstention", "Zahtjev pisan olovkom koja se razmazala; pola teksta nečitljivo, iznos se ne vidi.",
 [("o1", "Odobriti."), ("o2", "Odbiti."), ("o3", "Tražiti čitljiv primjerak.")],
 "o3", ["o3", "o1", "o2"], {"o1": 0.1, "o2": 0.1, "o3": 0.9}, "medium", ["pogrešan iznos"], 0.9, None,
 "Nečitljiv iznos se ne nagađa — traži se čitljiv primjerak."),
("abstention", "Dvije stranke tvrde vlasništvo nad istom parcelom, obje s papirima koji izgledaju uredno.",
 [("o1", "Dodijeliti prvoj."), ("o2", "Dodijeliti drugoj."), ("o3", "Proslijediti sudu.")],
 "o3", ["o3", "o1", "o2"], {"o1": 0.25, "o2": 0.25, "o3": 0.7}, "high", ["imovinski spor"], 0.7, None,
 "Spor o vlasništvo s dvije uredne isprave rješava sud, ne šalter."),
("abstention", "Pismo bez potpisa tvrdi da je službenik primio mito; nema dokaza ni svjedoka.",
 [("o1", "Suspendovati službenika."), ("o2", "Ignorisati."), ("o3", "Diskretno provjeriti navode.")],
 "o3", ["o3", "o2", "o1"], {"o1": 0.2, "o2": 0.3, "o3": 0.75}, "high", ["kleveta/korupcija"], 0.75, None,
 "Anonimna prijava bez dokaza ne suspenduje, ali se ne ignoriše — provjerava."),
("abstention", "Nepoznat broj zove {nm} i tvrdi da mu je sin u bolnici te traži hitnu uplatu.",
 [("o1", "Uplatiti odmah."), ("o2", "Prekinuti i provjeriti sina.")],
 "o2", ["o2", "o1"], {"o1": 0.05, "o2": 0.92}, "high", ["prevara"], 0.92, None,
 "Klasična prevara s hitnošću; provjera direktnim pozivom je odbrana."),
]

S = S + S2

held = set()
for l in open(os.path.join(BASE, "..", "datasets", "heldout", "heldout-v1.jsonl")):
    if l.strip():
        held.add(json.loads(l)["state"].strip().lower())

recs, seen = [], set()
for k, (cat, st_t, opts, dec, ranked, scores, risk, factors, conf, abst, rat) in enumerate(S):
    for v in range(3):  # 3 površinske varijante
        nm, gr, dk, us = R.choice(IMENA), R.choice(GRADOVI), R.choice(DOK), R.choice(UST)
        st = st_t.format(nm=nm, gr=gr, br=R.choice(['br. 12', 'br. 47', 'br. 103', 'br. 208', 'br. 315']), us=R.choice(UST))
        if st.strip().lower() in seen or st.strip().lower() in held:
            continue
        seen.add(st.strip().lower())
        o = list(opts)
        recs.append({"id": f"BH-D5-{cat}-{k:02d}-{v}", "lang": "bs", "state": st,
                     "options": [{"id": i, "text": t} for i, t in o],
                     "reference": {"decision": dec, "options_ranked": ranked, "scores": scores,
                                   "risk": {"level": risk, "factors": list(factors)}, "confidence": conf,
                                   "abstention_reason": abst, "rationale_short": rat, "lang": "bs",
                                   "model": "human-reference", "version": "1.0"},
                     "source": "human-v0.5", "license": "CC-BY-4.0"})

for j, r in enumerate(recs):
    r["id"] = f"BH-D5-{j:04d}"
with open(os.path.join(OUT, "human-v05.jsonl"), "w", encoding="utf-8") as f:
    for r in recs:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
h = hashlib.sha256(open(os.path.join(OUT, "human-v05.jsonl"), "rb").read()).hexdigest()[:16]
json.dump({"seed": 99, "source": "human-v0.5", "license": "CC-BY-4.0", "n": len(recs), "sha256": h},
          open(os.path.join(OUT, "manifest-v0.5.json"), "w"), ensure_ascii=False, indent=1)
print("UKUPNO:", len(recs))
