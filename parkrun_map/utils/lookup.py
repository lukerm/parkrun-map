import os

DOMAIN_EXT_LOOKUP = {
    'Australia': '.com.au',
    'Canada': '.ca',
    'Denmark': '.dk',
    'Finland': '.fi',
    'France': '.fr',
    'Germany': '.com.de',
    'Ireland': '.ie',
    'Italy': '.it',
    'Japan': '.jp',
    'Malaysia': '.my',
    'Netherlands': '.co.nl',
    'New Zealand': '.co.nz',
    'Norway': '.no',
    'Poland': '.pl',
    'Russia': '.ru',
    'Singapore': '.sg',
    'South Africa': '.co.za',
    'Sweden': '.se',
    'UK': '.org.uk',
    'USA': '.us',
}

COUNTRY_LOOKUP = {ext: country for country, ext in DOMAIN_EXT_LOOKUP.items()}