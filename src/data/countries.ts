// Country, capital and main-city data used by the country switcher and city pages.
// Format per line: ISO-2 code | name | comma separated cities (first city is the capital or main hub)
const RAW = `
AF|Afghanistan|Kabul,Kandahar
AL|Albania|Tirana
DZ|Algeria|Algiers,Oran
AD|Andorra|Andorra la Vella
AO|Angola|Luanda
AG|Antigua and Barbuda|Saint John's
AR|Argentina|Buenos Aires,Cordoba,Rosario
AM|Armenia|Yerevan
AU|Australia|Sydney,Melbourne,Brisbane,Perth
AT|Austria|Vienna,Salzburg
AZ|Azerbaijan|Baku
BS|Bahamas|Nassau
BH|Bahrain|Manama
BD|Bangladesh|Dhaka,Chittagong,Sylhet
BB|Barbados|Bridgetown
BY|Belarus|Minsk
BE|Belgium|Brussels,Antwerp
BZ|Belize|Belmopan
BJ|Benin|Porto-Novo,Cotonou
BT|Bhutan|Thimphu
BO|Bolivia|La Paz,Santa Cruz
BA|Bosnia and Herzegovina|Sarajevo
BW|Botswana|Gaborone
BR|Brazil|Sao Paulo,Rio de Janeiro,Brasilia
BN|Brunei|Bandar Seri Begawan
BG|Bulgaria|Sofia
BF|Burkina Faso|Ouagadougou
BI|Burundi|Gitega,Bujumbura
CV|Cabo Verde|Praia
KH|Cambodia|Phnom Penh
CM|Cameroon|Yaounde,Douala
CA|Canada|Toronto,Vancouver,Montreal,Calgary
CF|Central African Republic|Bangui
TD|Chad|N'Djamena
CL|Chile|Santiago,Valparaiso
CN|China|Beijing,Shanghai,Shenzhen,Guangzhou
CO|Colombia|Bogota,Medellin
KM|Comoros|Moroni
CG|Congo|Brazzaville
CD|DR Congo|Kinshasa,Lubumbashi
CR|Costa Rica|San Jose
CI|Cote d'Ivoire|Abidjan,Yamoussoukro
HR|Croatia|Zagreb,Split
CU|Cuba|Havana
CY|Cyprus|Nicosia
CZ|Czechia|Prague,Brno
DK|Denmark|Copenhagen,Aarhus
DJ|Djibouti|Djibouti
DM|Dominica|Roseau
DO|Dominican Republic|Santo Domingo
EC|Ecuador|Quito,Guayaquil
EG|Egypt|Cairo,Alexandria
SV|El Salvador|San Salvador
GQ|Equatorial Guinea|Malabo
ER|Eritrea|Asmara
EE|Estonia|Tallinn
SZ|Eswatini|Mbabane
ET|Ethiopia|Addis Ababa
FJ|Fiji|Suva
FI|Finland|Helsinki
FR|France|Paris,Lyon,Marseille
GA|Gabon|Libreville
GM|Gambia|Banjul
GE|Georgia|Tbilisi
DE|Germany|Berlin,Munich,Hamburg,Frankfurt
GH|Ghana|Accra,Kumasi
GR|Greece|Athens,Thessaloniki
GD|Grenada|Saint George's
GT|Guatemala|Guatemala City
GN|Guinea|Conakry
GW|Guinea-Bissau|Bissau
GY|Guyana|Georgetown
HT|Haiti|Port-au-Prince
HN|Honduras|Tegucigalpa
HK|Hong Kong|Hong Kong
HU|Hungary|Budapest
IS|Iceland|Reykjavik
IN|India|Mumbai,Delhi,Bengaluru,Hyderabad,Chennai
ID|Indonesia|Jakarta,Surabaya,Bandung
IR|Iran|Tehran,Isfahan
IQ|Iraq|Baghdad,Erbil
IE|Ireland|Dublin,Cork
IL|Israel|Jerusalem,Tel Aviv
IT|Italy|Rome,Milan,Naples
JM|Jamaica|Kingston
JP|Japan|Tokyo,Osaka,Kyoto
JO|Jordan|Amman
KZ|Kazakhstan|Astana,Almaty
KE|Kenya|Nairobi,Mombasa
KI|Kiribati|Tarawa
XK|Kosovo|Pristina
KW|Kuwait|Kuwait City
KG|Kyrgyzstan|Bishkek
LA|Laos|Vientiane
LV|Latvia|Riga
LB|Lebanon|Beirut
LS|Lesotho|Maseru
LR|Liberia|Monrovia
LY|Libya|Tripoli
LI|Liechtenstein|Vaduz
LT|Lithuania|Vilnius
LU|Luxembourg|Luxembourg City
MG|Madagascar|Antananarivo
MW|Malawi|Lilongwe
MY|Malaysia|Kuala Lumpur,Penang,Johor Bahru
MV|Maldives|Male
ML|Mali|Bamako
MT|Malta|Valletta
MH|Marshall Islands|Majuro
MR|Mauritania|Nouakchott
MU|Mauritius|Port Louis
MX|Mexico|Mexico City,Guadalajara,Monterrey
FM|Micronesia|Palikir
MD|Moldova|Chisinau
MC|Monaco|Monaco
MN|Mongolia|Ulaanbaatar
ME|Montenegro|Podgorica
MA|Morocco|Casablanca,Rabat,Marrakech
MZ|Mozambique|Maputo
MM|Myanmar|Naypyidaw,Yangon
NA|Namibia|Windhoek
NR|Nauru|Yaren
NP|Nepal|Kathmandu,Pokhara
NL|Netherlands|Amsterdam,Rotterdam
NZ|New Zealand|Auckland,Wellington
NI|Nicaragua|Managua
NE|Niger|Niamey
NG|Nigeria|Lagos,Abuja,Kano
KP|North Korea|Pyongyang
MK|North Macedonia|Skopje
NO|Norway|Oslo,Bergen
OM|Oman|Muscat
PK|Pakistan|Karachi,Lahore,Islamabad,Rawalpindi,Faisalabad,Multan,Peshawar
PW|Palau|Ngerulmud
PS|Palestine|Ramallah,Gaza
PA|Panama|Panama City
PG|Papua New Guinea|Port Moresby
PY|Paraguay|Asuncion
PE|Peru|Lima,Cusco
PH|Philippines|Manila,Cebu,Davao
PL|Poland|Warsaw,Krakow
PT|Portugal|Lisbon,Porto
QA|Qatar|Doha
RO|Romania|Bucharest,Cluj-Napoca
RU|Russia|Moscow,Saint Petersburg
RW|Rwanda|Kigali
KN|Saint Kitts and Nevis|Basseterre
LC|Saint Lucia|Castries
VC|Saint Vincent and the Grenadines|Kingstown
WS|Samoa|Apia
SM|San Marino|San Marino
ST|Sao Tome and Principe|Sao Tome
SA|Saudi Arabia|Riyadh,Jeddah,Dammam
SN|Senegal|Dakar
RS|Serbia|Belgrade
SC|Seychelles|Victoria
SL|Sierra Leone|Freetown
SG|Singapore|Singapore
SK|Slovakia|Bratislava
SI|Slovenia|Ljubljana
SB|Solomon Islands|Honiara
SO|Somalia|Mogadishu
ZA|South Africa|Johannesburg,Cape Town,Durban
KR|South Korea|Seoul,Busan
SS|South Sudan|Juba
ES|Spain|Madrid,Barcelona,Valencia
LK|Sri Lanka|Colombo,Kandy
SD|Sudan|Khartoum
SR|Suriname|Paramaribo
SE|Sweden|Stockholm,Gothenburg
CH|Switzerland|Zurich,Geneva,Bern
SY|Syria|Damascus
TW|Taiwan|Taipei
TJ|Tajikistan|Dushanbe
TZ|Tanzania|Dodoma,Dar es Salaam
TH|Thailand|Bangkok,Phuket,Chiang Mai
TL|Timor-Leste|Dili
TG|Togo|Lome
TO|Tonga|Nukualofa
TT|Trinidad and Tobago|Port of Spain
TN|Tunisia|Tunis
TR|Turkiye|Istanbul,Ankara,Izmir
TM|Turkmenistan|Ashgabat
TV|Tuvalu|Funafuti
UG|Uganda|Kampala
UA|Ukraine|Kyiv,Lviv
AE|United Arab Emirates|Dubai,Abu Dhabi,Sharjah
GB|United Kingdom|London,Manchester,Birmingham,Edinburgh
US|United States|New York,Los Angeles,Chicago,Houston,San Francisco
UY|Uruguay|Montevideo
UZ|Uzbekistan|Tashkent
VU|Vanuatu|Port Vila
VA|Vatican City|Vatican City
VE|Venezuela|Caracas
VN|Vietnam|Hanoi,Ho Chi Minh City
YE|Yemen|Sanaa
ZM|Zambia|Lusaka
ZW|Zimbabwe|Harare
`;

export const slugify = (value: string) =>
  value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');

export type City = { name: string; slug: string };
export type Country = { code: string; name: string; cities: City[] };

export const countries: Country[] = RAW.trim()
  .split('\n')
  .map((line) => {
    const [code, name, cityList] = line.split('|');
    return {
      code,
      name,
      cities: cityList.split(',').map((city) => ({ name: city.trim(), slug: slugify(city) })),
    };
  })
  .sort((a, b) => a.name.localeCompare(b.name));

export const countryByCode = new Map(countries.map((country) => [country.code, country]));
