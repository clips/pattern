#### PATTERN | WEB | LOCALE ########################################################################
# -*- coding: utf-8 -*-
# Copyright (c) 2010 University of Antwerp, Belgium
# Author: Tom De Smedt <tom@organisms.be>
# License: BSD (see LICENSE.txt for details).
# http://www.clips.ua.ac.be/pages/pattern

from __future__ import unicode_literals

from builtins import str, bytes, dict, int
from builtins import map, zip, filter
from builtins import object, range

#### LANGUAGE & REGION #############################################################################
# IETF BCP 47 language-region code => (language, region, ISO-639 language code, ISO-3166 region code).
# Note: the list is incomplete (especially for African languages).
# Please help out by correcting errors and omissions.

LANGUAGE_REGION = {
    'aa-ET': ('Afar', 'Ethiopia', 'aa', 'ET'),
    'af-ZA': ('Afrikaans', 'South Africa', 'af', 'ZA'),
    'ar-AE': ('Arabic', 'United Arab Emirates', 'ar', 'AE'),
    'ar-BH': ('Arabic', 'Bahrain', 'ar', 'BH'),
    'ar-DZ': ('Arabic', 'Algeria', 'ar', 'DZ'),
    'ar-EG': ('Arabic', 'Egypt', 'ar', 'EG'),
    'ar-IQ': ('Arabic', 'Iraq', 'ar', 'IQ'),
    'ar-JO': ('Arabic', 'Jordan', 'ar', 'JO'),
    'ar-KW': ('Arabic', 'Kuwait', 'ar', 'KW'),
    'ar-LB': ('Arabic', 'Lebanon', 'ar', 'LB'),
    'ar-LY': ('Arabic', 'Libya', 'ar', 'LY'),
    'ar-MA': ('Arabic', 'Morocco', 'ar', 'MA'),
    'ar-OM': ('Arabic', 'Oman', 'ar', 'OM'),
    'ar-QA': ('Arabic', 'Qatar', 'ar', 'QA'),
    'ar-SA': ('Arabic', 'Saudi Arabia', 'ar', 'SA'),
    'ar-SD': ('Arabic', 'Sudan', 'ar', 'SD'),
    'ar-SY': ('Arabic', 'Syria', 'ar', 'SY'),
    'ar-TN': ('Arabic', 'Tunisia', 'ar', 'TN'),
    'ar-YE': ('Arabic', 'Yemen', 'ar', 'YE'),
    'be-BY': ('Belarusian', 'Belarus', 'be', 'BY'),
    'bg-BG': ('Bulgarian', 'Bulgaria', 'bg', 'BG'),
    'ca-AD': ('Catalan', 'Andorra', 'ca', 'AD'),
    'cs-CZ': ('Czech', 'Czech Republic', 'cs', 'CZ'),
    'da-DK': ('Danish', 'Denmark', 'da', 'DK'),
    'de-DE': ('German', 'Germany', 'de', 'DE'),
    'de-AT': ('German', 'Austria', 'de', 'AT'),
    'de-CH': ('German', 'Switzerland', 'de', 'CH'),
    'de-LI': ('German', 'Liechtenstein', 'de', 'LI'),
    'de-LU': ('German', 'Luxembourg', 'de', 'LU'),
    'el-GR': ('Greek', 'Greece', 'el', 'GR'),
    'en-AU': ('English', 'Australia', 'en', 'AU'),
    'en-BZ': ('English', 'Belize', 'en', 'BZ'),
    'en-CA': ('English', 'Canada', 'en', 'CA'),
    'en-GB': ('English', 'United Kingdom', 'en', 'GB'),
    'en-IE': ('English', 'Ireland', 'en', 'IE'),
    'en-JM': ('English', 'Jamaica', 'en', 'JM'),
    'en-KE': ('English', 'Kenya', 'en', 'KE'),
    'en-NZ': ('English', 'New Zealand', 'en', 'NZ'),
    'en-TT': ('English', 'Trinidad', 'en', 'TT'),
    'en-US': ('English', 'United States', 'en', 'US'),
    'en-ZA': ('English', 'South Africa', 'en', 'ZA'),
    'es-ES': ('Spanish', 'Spain', 'es', 'ES'),
    'es-AR': ('Spanish', 'Argentina', 'es', 'AQ'),
    'es-BO': ('Spanish', 'Bolivia', 'es', 'BO'),
    'es-CL': ('Spanish', 'Chile', 'es', 'CL'),
    'es-CO': ('Spanish', 'Colombia', 'es', 'CO'),
    'es-CR': ('Spanish', 'Costa Rica', 'es', 'CR'),
    'es-DO': ('Spanish', 'Dominican Republic', 'es', 'DO'),
    'es-EC': ('Spanish', 'Ecuador', 'es', 'EC'),
    'es-GT': ('Spanish', 'Guatemala', 'es', 'GT'),
    'es-HN': ('Spanish', 'Honduras', 'es', 'HN'),
    'es-MX': ('Spanish', 'Mexico', 'es', 'MX'),
    'es-NI': ('Spanish', 'Nicaragua', 'es', 'NI'),
    'es-PA': ('Spanish', 'Panama', 'es', 'PA'),
    'es-PE': ('Spanish', 'Peru', 'es', 'PE'),
    'es-PR': ('Spanish', 'Puerto Rico', 'es', 'PR'),
    'es-PY': ('Spanish', 'Paraguay', 'es', 'PY'),
    'es-SV': ('Spanish', 'El Salvador', 'es', 'SV'),
    'es-UY': ('Spanish', 'Uruguay', 'es', 'UY'),
    'es-VE': ('Spanish', 'Venezuela', 'es', 'VE'),
    'et-EE': ('Estonian', 'Estonia', 'et', 'EE'),
    'eu-PV': ('Basque', 'Basque Country', 'eu', 'PV'),
    'fa-IR': ('Farsi', 'Iran', 'fa', 'IR'),
    'fi-FI': ('Finnish', 'Finland', 'fi', 'FI'),
    'fo-FO': ('Faeroese', 'Faroe Islands', 'fo', 'FO'),
    'fr-CG': ('French', 'Congo', 'fr', 'CG'),
    'fr-FR': ('French', 'France', 'fr', 'FR'),
    'fr-BE': ('French', 'Belgium', 'fr', 'BE'),
    'fr-CA': ('French', 'Canada', 'fr', 'CA'),
    'fr-CH': ('French', 'Switzerland', 'fr', 'CH'),
    'fr-LU': ('French', 'Luxembourg', 'fr', 'LU'),
    'ga-IE': ('Irish', 'Ireland', 'ga', 'IE'),
    'gd-UK': ('Gaelic', 'Scotland', 'gd', 'UK'),
    'he-IL': ('Hebrew', 'Israel', 'he', 'IL'),
    'hi-IN': ('Hindi', 'India', 'hi', 'IN'),
    'hr-HR': ('Croatian', 'Croatia', 'hr', 'HR'),
    'hu-HU': ('Hungarian', 'Hungary', 'hu', 'HU'),
    'id-ID': ('Indonesian', 'Indonesia', 'id', 'ID'),
    'is-IS': ('Icelandic', 'Iceland', 'is', 'IS'),
    'it-IT': ('Italian', 'Italy', 'it', 'IT'),
    'it-CH': ('Italian', 'Switzerland', 'it', 'CH'),
    'ja-JA': ('Japanese', 'Japan', 'ja', 'JA'),
    'ka-GE': ('Georgian', 'Georgia', 'ka', 'GE'),
    'kg-CG': ('Kongo', 'Congo', 'kg', 'CG'),
    'kl-GL': ('Kalaallisut', 'Greenland', 'kl', 'GL'),
    'ko-KP': ('Korean', 'Johab', 'ko', 'KP'),
    'ln-CG': ('Lingala', 'Congo', 'ln', 'CG'),
    'lo-LA': ('Lao', 'Lao', 'lo', 'LA'),
    'lt-LT': ('Lithuanian', 'Lithuania', 'lt', 'LT'),
    'lv-LV': ('Latvian', 'Latvia', 'lv', 'LV'),
    'mk-ML': ('Macedonian', 'Macedonia', 'mk', 'MK'),
    'ms-MY': ('Malay', 'Malaysia', 'ms', 'MY'),
    'mt-MT': ('Maltese', 'Malta', 'mt', 'MT'),
    'nd-ZW': ('Ndebele', 'Zimbabwe', 'nd', 'ZW'),
    'nl-NL': ('Dutch', 'Netherlands', 'nl', 'NL'),
    'nl-BE': ('Dutch', 'Belgium', 'nl', 'BE'),
    'no-NO': ('Norwegian', 'Nynorsk', 'no', 'NO'),
    'om-ET': ('Oromo', 'Ethiopia', 'om', 'ET'),
    'om-KE': ('Oromo', 'Kenya', 'om', 'KE'),
    'pl-PL': ('Polish', 'Poland', 'pl', 'PL'),
    'pt-MZ': ('Portuguese', 'Mozambique', 'pt', 'PT'),
    'pt-PT': ('Portuguese', 'Portugal', 'pt', 'PT'),
    'pt-BR': ('Portuguese', 'Brazil', 'pt', 'BR'),
    'rm-IT': ('Rhaeto-Romanic', 'Italy', 'rm', 'IT'),
    'ro-RO': ('Romanian', 'Romania', 'ro', 'RO'),
    'ro-MO': ('Romanian', 'Republic of Moldova', 'ro', 'MO'),
    'ru-RU': ('Russian', 'Russia', 'ru', 'RU'),
    'rw-RW': ('Kinyarwanda', 'Rwanda', 'rw', 'RW'),
    'sk-SK': ('Slovak', 'Slovakia', 'sk', 'SK'),
    'sl-SI': ('Slovenian', 'Slovenia', 'sl', 'SI'),
    'sm-SM': ('Samoan', 'Samoa', 'sm', 'SM'),
    'so-KE': ('Somali', 'Kenya', 'so', 'KE'),
    'so-SO': ('Somali', 'Somalia', 'so', 'SO'),
    'sq-AL': ('Albanian', 'Albania', 'sq', 'AL'),
    'sr-RS': ('Serbian', 'Serbia', 'sr', 'RS'),
    'sv-SE': ('Swedish', 'Sweden', 'sv', 'SE'),
    'sw-SW': ('Swahili', 'Kenya', 'sw', 'KE'),
    'sw-TZ': ('Swahili', 'Tanzania', 'sw', 'TZ'),
    'sv-FI': ('Swedish', 'Finland', 'sv', 'FI'),
    'sx-ZA': ('Sotho', 'South Africa', 'sx', 'ZA'),
    'sz-FI': ('Sami', 'Sapmi', 'sz', 'FI'),
    'th-TH': ('Thai', 'Thailand', 'th', 'TH'),
    'tn-BW': ('Tswana', 'Botswana', 'tn', 'BW'),
    'to-TO': ('Tonga', 'Tonga', 'to', 'TO'),
    'tr-TR': ('Turkish', 'Turkey', 'tr', 'TR'),
    'ts-ZA': ('Tsonga', 'South Africa', 'ts', 'ZA'),
    'uk-UA': ('Ukrainian', 'Ukraine', 'uk', 'UA'),
    'ur-PK': ('Urdu', 'Pakistan', 'ur', 'PK'),
    'uz-UZ': ('Uzbek', 'Uzbekistan', 'uz', 'UZ'),
    've-ZA': ('Venda', 'South Africa', 've', 'ZA'),
    'vi-VN': ('Vietnamese', 'Vietnam', 'vi', 'VN'),
    'xh-ZA': ('Xhosa', 'South Africa', 'xh', 'ZA'),
    'zh-CN': ('Chinese', 'China', 'zh', 'CN'),
    'zh-HK': ('Chinese', 'Hong Kong', 'zh', 'HK'),
    'zh-SG': ('Chinese', 'Singapore', 'zh', 'SG'),
    'zh-TW': ('Chinese', 'Taiwan', 'zh', 'TW'),
    'zu-ZA': ('Zulu', 'South Africa', 'zu', 'ZA'),
    'zu-ZW': ('Zulu', 'Zimbabwe', 'zu', 'ZW')
}


def encode_language(name):
    """ Returns the language code for the given language name.
        For example: encode_language("dutch") => "nl".
    """
    for tag, (language, region, iso639, iso3166) in LANGUAGE_REGION.items():
        if language == name.capitalize():
            return iso639


def decode_language(code):
    """ Returns the language name for the given language code.
        For example: decode_language("nl") => "Dutch".
    """
    for tag, (language, region, iso639, iso3166) in LANGUAGE_REGION.items():
        if iso639 == code.lower():
            return language


def encode_region(name):
    """ Returns the region code for the given region name.
        For example: encode_region("belgium") => "BE".
    """
    for tag, (language, region, iso639, iso3166) in LANGUAGE_REGION.items():
        if region == name.capitalize():
            return iso3166


def decode_region(code):
    """ Returns the region name for the given region code.
        For example: decode_region("be") => "Belgium".
    """
    for tag, (language, region, iso639, iso3166) in LANGUAGE_REGION.items():
        if iso3166 == code.upper():
            return region


def languages(region):
    """ Returns a list of language codes for the given region code.
        For example: languages(encode_region("belgium")) => ["fr", "nl"]
    """
    v, a = region.upper(), []
    for tag, (language, region, iso639, iso3166) in LANGUAGE_REGION.items():
        if iso3166 == v:
            a.append(iso639)
    return sorted(a)


def regions(language):
    """ Returns a list of region codes for the given language code.
        For example: regions(encode_language("dutch")) => ["NL", "BE"]
    """
    x, a = language.lower(), []
    for tag, (language, region, iso639, iso3166) in LANGUAGE_REGION.items():
        if iso639 == x:
            a.append(iso3166)
    return sorted(a, key=lambda tag: tag.lower() != x and tag or "")


def regionalize(language):
    """ Returns a list of RFC-5646 language-region codes for the given language code.
        For example: regionalize("nl") => ["nl-nl", "nl-be"]
    """
    if not isinstance(language, str):
        return []
    if "-" in language:
        language, region = language.split("-")
        return [language.lower() + "-" + region.upper()]  # nl-nl => nl-NL
    main = lambda tag: tag in ("ar-AE", "en-US", "zh-CN") or tag[:2] == tag[3:].lower() # nl-NL
    a = [language + "-" + r for r in regions(language.lower())]
    a = sorted(a, key=main, reverse=True)
    return a


def market(language):
    """ Returns the first item from regionalize(language).
    """
    a = regionalize(language)
    a = len(a) > 0 and a[0] or None
    return a

#print(encode_language("dutch")) # nl
#print(decode_language("nl"))    # Dutch
#print(encode_region("belgium")) # BE
#print(decode_region("be"))      # Belgium
#print(languages("be"))          # ["fr", "nl"]
#print(regions("nl"))            # ["NL", "BE"]
#print(regionalize("nl"))        # ["nl-NL", "nl-BE"]

### GEOCODE ########################################################################################
# capital => (latitude, longitude, ISO-639 language code, region)

GEOCODE = {
         'Abu Dhabi': ( 24.467,  54.367, "ar", "United Arab Emirates"),
             'Abuja': (  9.083,   7.533, "en", "Nigeria"),
             'Accra': (  5.550,  -0.217, "en", "Ghana"),
           'Algiers': ( 36.750,   3.050, "ar", "Algeria"),
             'Amman': ( 31.950,  35.933, "ar", "Jordan"),
         'Amsterdam': ( 52.383,   4.900, "nl", "Netherlands"),
            'Ankara': ( 39.933,  32.867, "tr", "Turkey"),
            'Astana': ( 51.167,  71.417, "ru", "Kazakhstan"),
          'Asuncion': (-25.267, -57.667, "es", "Paraguay"),
            'Athens': ( 37.983,  23.733, "el", "Greece"),
           'Baghdad': ( 33.333,  44.383, "ar", "Iraq"),
            'Bamako': ( 12.650,  -8.000, "fr", "Mali"),
           'Bangkok': ( 13.750, 100.517, "th", "Thailand"),
            'Bangui': (  4.367,  18.583, "fr", "Central African Republic"),
           'Beijing': ( 39.917, 116.383, "zh", "China"),
            'Beirut': ( 33.867,  35.500, "ar", "Lebanon"),
          'Belgrade': ( 44.833,  20.500, "sr", "Serbia"),
            'Berlin': ( 52.517,  13.400, "de", "Germany"),
              'Bern': ( 46.950,   7.433, "de", "Switzerland"),
            'Bissau': ( 11.850, -15.583, "pt", "Guinea"),
            'Bogota': (  4.600, -74.083, "es", "Colombia"),
          'Brasilia': (-15.783, -47.917, "pt", "Brazil"),
        'Bratislava': ( 48.150,  17.117, "sk", "Slovakia"),
       'Brazzaville': ( -4.250,  15.283, "fr", "Congo"),
          'Brussels': ( 50.833,   4.333, "nl", "Belgium"),
         'Bucharest': ( 44.433,  26.100, "ro", "Romania"),
          'Budapest': ( 47.500,  19.083, "hu", "Hungary"),
      'Buenos Aires': (-34.600, -58.667, "es", "Argentina"),
         'Bujumbura': ( -3.367,  29.350, "rn", "Burundi"),
             'Cairo': ( 30.050,  31.250, "ar", "Egypt"),
          'Canberra': (-35.283, 149.217, "en", "Australia"),
           'Caracas': ( 10.500, -66.933, "es", "Venezuela"),
          'Chisinau': ( 47.000,  28.850, "ro", "Moldova"),
           'Colombo': (  6.933,  79.850, "si", "Sri Lanka"),
           'Conakry': (  9.550, -13.700, "fr", "Guinea"),
        'Copenhagen': ( 55.667,  12.583, "da", "Denmark"),
             'Dakar': ( 24.633,  46.717, "fr", "Senegal"),
          'Damascus': ( 33.500,  36.300, "ar", "Syria"),
     'Dar es Salaam': ( -6.800,  39.283, "sw", "Tanzania"),
             'Dhaka': ( 23.717,  90.400, "bn", "Bangladesh"),
            'Dublin': ( 53.317,  -6.233, "en", "Ireland"),
          'Freetown': (  8.500, -13.250, "en", "Sierra Leone"),
       'George Town': ( 19.300, -81.383, "en", "Malaysia"),
        'Georgetown': (  6.800, -58.167, "en", "Guyana"),
    'Guatemala City': ( 14.617, -90.517, "es", "Guatemala"),
             'Hanoi': ( 21.033, 105.850, "vi", "Vietnam"),
            'Harare': (-17.833,  31.050, "en", "Zimbabwe"),
            'Havana': ( 23.117, -82.350, "es", "Cuba"),
          'Helsinki': ( 60.167,  24.933, "fi", "Finland"),
         'Islamabad': ( 33.700,  73.167, "ur", "Pakistan"),
           'Jakarta': ( -6.167, 106.817, "ms", "Indonesia"),
         'Jerusalem': ( 31.767,  35.233, "he", "Israel"),
              'Juba': (  4.850,  31.617, "en", "Sudan"),
             'Kabul': ( 34.517,  69.183, "fa", "Afghanistan"),
           'Kampala': (  0.317,  32.417, "en", "Uganda"),
         'Kathmandu': ( 27.717,  85.317, "ne", "Nepal"),
          'Khartoum': ( 15.600,  32.533, "ar", "Sudan"),
              'Kiev': ( 50.433,  30.517, "rw", "Ukraine"),
            'Kigali': ( -1.950,  30.067, "en", "Rwanda"),
          'Kingston': ( 18.000, -76.800, "fr", "Jamaica"),
          'Kinshasa': ( -4.317,  15.300, "ms", "Congo"),
      'Kuala Lumpur': (  3.167, 101.700, "ar", "Malaysia"),
       'Kuwait City': ( 29.367,  47.967, "uk", "Kuwait"),
            'La Paz': (-16.500, -68.150, "es", "Bolivia"),
              'Lima': (-12.050, -77.050, "es", "Peru"),
            'Lisbon': ( 38.717,  -9.133, "pt", "Portugal"),
         'Ljubljana': ( 46.050,  14.517, "sl", "Slovenia"),
              'Lome': (  6.133,   1.217, "fr", "Togo"),
            'London': ( 51.500,  -0.167, "en", "United Kingdom"),
            'Luanda': ( -8.833,  13.233, "pt", "Angola"),
            'Lusaka': (-15.417,  28.283, "en", "Zambia"),
        'Luxembourg': ( 49.600,   6.117, "cd", "Luxembourg"),
            'Madrid': ( 40.400,  -3.683, "es", "Spain"),
           'Managua': ( 12.150, -86.283, "es", "Nicaragua"),
            'Manila': ( 14.583, 121.000, "tl", "Philippines"),
            'Maputo': (-25.950,  32.583, "pt", "Mozambique"),
       'Mexico City': ( 19.433, -99.133, "es", "Mexico"),
             'Minsk': ( 53.900,  27.567, "be", "Belarus"),
         'Mogadishu': (  2.067,  45.367, "so", "Somalia"),
            'Monaco': ( 43.733,   7.417, "fr", "Monaco"),
          'Monrovia': (  6.300, -10.800, "en", "Liberia"),
        'Montevideo': (-34.883, -56.183, "es", "Uruguay"),
            'Moscow': ( 55.750,  37.583, "ru", "Russia"),
            'Muscat': ( 23.617,  58.583, "ar", "Oman"),
           'Nairobi': ( -1.283,  36.817, "en", "Kenya"),
            'Nassau': ( 25.083, -77.350, "en", "Bahamas"),
         'New Delhi': ( 28.600,  77.200, "hi", "India"),
          'New York': ( 40.756, -73.987, "en", "United States"),
            'Niamey': ( 13.517,   2.117, "fr", "Niger"),
              'Oslo': ( 59.917,  10.750, "no", "Norway"),
            'Ottawa': ( 45.417, -75.700, "en", "Canada"),
       'Panama City': (  8.967, -79.533, "es", "Panama"),
             'Paris': ( 48.867,   2.333, "fr", "France"),
       'Philipsburg': ( 18.017, -63.033, "en", "Sint Maarten"),
        'Phnom Penh': ( 11.550, 104.917, "km", "Cambodia"),
        'Port Louis': (-20.150,  57.483, "en", "Mauritius"),
    'Port-au-Prince': ( 18.533, -72.333, "fr", "Haiti"),
        'Porto-Novo': (  6.483,   2.617, "fr", "Benin"),
            'Prague': ( 50.083,  14.467, "cs", "Czech Republic"),
          'Pretoria': (-25.700,  28.217, "xh", "South Africa"),
         'Pyongyang': ( 39.017, 125.750, "ko", "North Korea"),
             'Quito': ( -0.217, -78.500, "es", "Ecuador"),
             'Rabat': ( 34.017,  -6.817, "ar", "Morocco"),
           'Rangoon': ( 16.800,  96.150, "my", "Myanmar"),
         'Reykjavik': ( 64.150, -21.950, "is", "Iceland"),
              'Riga': ( 56.950,  24.100, "lv", "Latvia"),
            'Riyadh': ( 24.633,  46.717, "ar", "Saudi Arabia"),
              'Rome': ( 41.900,  12.483, "it", "Italy"),
            'Saipan': ( 15.200, 145.750, "en", "Saipan"),
          'San Jose': (  9.933, -84.083, "es", "Costa Rica"),
          'San Juan': ( 18.467, -66.117, "es", "Puerto Rico"),
        'San Marino': ( 43.933,  12.417, "it", "San Marino"),
      'San Salvador': ( 13.700, -89.200, "es", "El Salvador"),
             'Sanaa': ( 15.350,  44.200, "ar", "Yemen"),
          'Santiago': (-33.450, -70.667, "es", "Chile"),
     'Santo Domingo': ( 18.467, -69.900, "es", "Domenican Republic"),
          'Sarajevo': ( 43.867,  18.417, "bo", "Bosnia and Herzegovina"),
             'Seoul': ( 37.550, 126.983, "ko", "South Korea"),
         'Singapore': (  1.283, 103.850, "en", "Singapore"),
            'Skopje': ( 42.000,  21.433, "mk", "Macedonia"),
             'Sofia': ( 42.683,  23.317, "bg", "Bulgaria"),
         'Stockholm': ( 59.333,  18.050, "sv", "Sweden"),
            'Taipei': ( 25.050, 121.500, "zh", "China"),
           'Tallinn': ( 59.433,  24.717, "et", "Estonia"),
          'Tashkent': ( 41.333,  69.300, "uz", "Uzbekistan"),
       'Tegucigalpa': ( 14.100, -87.217, "es", "Honduras"),
            'Tehran': ( 35.667,  51.417, "fa", "Iran"),
            'Tirana': ( 41.317,  19.817, "sq", "Albania"),
             'Tokyo': ( 35.683, 139.750, "ja", "Japan"),
          'Torshavn': ( 62.017,  -6.767, "fo", "Faroe Islands"),
           'Tripoli': ( 32.883,  13.167, "ar", "Libya"),
             'Tunis': ( 36.800,  10.183, "ar", "Tunis"),
             'Vaduz': ( 47.133,   9.517, "de", "Liechtenstein"),
      'Vatican City': ( 41.900,  12.450, "it", "Vatican City"),
            'Vienna': ( 48.200,  16.367, "de", "Austria"),
         'Vientiane': ( 17.967, 102.600, "lo", "Laos"),
           'Vilnius': ( 54.683,  25.317, "lt", "Lithuania"),
            'Warsaw': ( 52.250,  21.000, "pl", "Poland"),
       'Washington.': ( 38.883, -77.033, "en", "United States"),
        'Wellington': (-41.467, 174.850, "en", "New Zealand"),
      'Yamoussoukro': (  6.817,  -5.283, "fr", "Côte d'Ivoire"),
           'Yaounde': (  3.867,  11.517, "en", "Cameroon"),
            'Zagreb': ( 45.800,  16.000, "hr", "Croatia")
}


def geocode(location):
    """ Returns a (latitude, longitude, language code, region)-tuple 
        for the given city (mostly capitals).
    """
    if location in GEOCODE:
        return GEOCODE[location]
    for k, v in GEOCODE.items():
        if location.lower() == k.lower():
            return v
