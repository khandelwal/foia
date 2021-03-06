## Agency FOIA contact info

Downloading agency contact information for FOIA, from FOIA.gov.

This is a three step process:

1. Scraping the [FOIA.gov request form](http://www.foia.gov/report-makerequest.html) for contact data. This automatically adds in some additional manually curated data, stored in `manual_data/`.
2. Filling in missing data using a CSV rendition of an [Excel spreadsheet](http://www.foia.gov/full-foia-contacts.xls) hosted on FOIA.gov.
3. Downloading keywords for agencies from the Federal Register.

It scrapes/parses the contact details out of these sources, and makes YAML files in the `data/` directory (versioned).

## Using

First, install all of the Python dependencies:

```bash
pip install -r requirements.txt
```

Then run the three relevant scripts, in this order:

```bash
python scraper.py
python layer_with_csv.py
python layer_with_usa_contacts.py
python average_time_scraper.py
python keywords_from_fr.py
```

If an agency's HTML has already been downloaded, it will not be downloaded
again. To re-download, delete the `html/` directory and run again. Similarly,
the XLS file is stored locally in the `xls/` directory. JSON responses pulled
from the Federal Register for keywords are logged in an SQLite DB.

### scraper.py

scraper.py operates in two modes. Without any command line arguments it will
re-process the data for all agencies. You can however provide an agency
abbreviation as a parameter, and it will only process the data for that agency.

Agency abbreviations are currently listed
[here.](https://github.com/18F/foia/blob/master/contacts/scraper.py#L21)

### average_time_scraper.py

average_time_scraper.py crawls through request processing time reports
on foia.gov and updates the yaml files. Additionally, it creates
"request_time_data.csv", which contains all data available on request
processing times on foia.gov

## Data

_**(Work-in-progress)**_

There are 99 agencies listed on FOIA.gov, and they each have 1 or more departments. Departments have addresses and phone numbers, and can also have fax numbers and email addresses.

They may have a website, or a request form, or both.

Data for an agency looks like this:

```yaml
---
abbreviation: GSA
name: Headquarters
description: GSA's mission is to use expertise to provide innovative solutions for
  our customers in support of their missions and by so doing, foster an effective,
  sustainable, and transparent government for the American people.
departments:
- name: Headquarters
  address:
  - FOIA Contact
  - FOIA Requester Service Center (H1C)
  - Room 7308
  - 1800 F. Street, NW
  - Washington, DC 20405
  phone: 855-675-3642
  fax: 202-501-2727
  emails:
  - gsa.foia@gsa.gov
  service_center: 'Phone: (855) 675-3642'
  misc:
    Program Manager: 'Travis Lewis, Phone: (202) 219-3078'
  public_liaison: 'Audrey Corbett Brooks, Phone: (202) 205-5912'
  website: http://www.gsa.gov/portal/category/21416

```

## usa.gov Agency Data

*Warning* - Integration between usa.gov data and the above scraper is not
complete. For now, we only download the JSON data files

To run, execute

```
python usagov.py
```

The files below are located in the usagov-data directory:

| File name      | Description   |
| -------------  |:-------------:|
| all_data.json      | Data pull from http://www.usa.gov/api/USAGovAPI/contacts.json/contacts |
| sample_data.json      | sample data from all_data.json |
| federal-offices.csv | data dump from SQL in https://github.com/GSA/project-open-data-dashboard#installation |


### Sample json from records

```
{'Alt_Language': [{'Id': '50101',
                   'Language': 'es',
                   'Name': 'Administración de Asuntos de Niños y Familias',
                   'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/50101'}],
 'Child': [{'Id': '49064',
            'Name': 'Administration for Native Americans',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49064'},
           {'Id': '49066',
            'Name': 'Administration on Developmental Disabilities',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49066'},
           {'Id': '49588',
            'Name': 'Office of Refugee Resettlement',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49588'}],
 'City': 'Washington',
 'Contact_Url': [{'Description': 'Contact the Administration for Children '
                                 'and Families (ACF)',
                  'Language': 'en',
                  'Url': 'http://www.acf.hhs.gov/about'},
                 {'Description': 'Child Support',
                  'Language': 'en',
                  'Url': 'http://www.acf.hhs.gov/programs/css/resource/state-and-tribal-child-support-agency-contacts'},
                 {'Description': 'Temporary Assistance for Needy Families '
                                 '(Welfare)',
                  'Language': 'en',
                  'Url': 'http://www.acf.hhs.gov/programs/ofa/help'},
                 {'Description': 'Report Child Abuse and Neglect',
                  'Language': 'en',
                  'Url': 'http://www.childwelfare.gov/pubs/reslist/rl_dsp.cfm?rs_id=5&rate_chno=11-11172'},
                 {'Description': 'Low Income Home Energy Assistance '
                                 'Program (LIHEAP)',
                  'Language': 'en',
                  'Url': 'http://1.usa.gov/n0kIxZ'}],
 'Description': 'The ACF funds state, territory, local, and tribal '
                'organizations to provide family assistance (welfare), child '
                'support, child care, Head Start, child welfare, and other '
                'programs relating to children and families.',
 'Id': '47994',
 'In_Person_Url': [{'Description': 'Head Start Program Locator',
                    'Language': 'en',
                    'Url': 'http://eclkc.ohs.acf.hhs.gov/hslc/HeadStartOffices'},
                   {'Description': 'Child Support Enforcement in Your State',
                    'Language': 'en',
                    'Url': 'http://www.acf.hhs.gov/programs/cse/extinf.html'},
                   {'Description': 'Contact Regional Offices',
                    'Language': 'en',
                    'Url': 'http://www.acf.hhs.gov/programs/oro'}],
 'Language': 'en',
 'Name': 'Administration for Children and Families (ACF)',
 'Parent': {'Id': '49021',
            'Name': 'U.S. Department of Health and Human Services (HHS)',
            'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/49021'},
 'Phone': ['(202) 401-9200'],
 'Source_Url': 'http://www.usa.gov/directory/federal/administration-for-children--families.shtml',
 'StateTer': 'DC',
 'Street1': "370 L'Enfant Promenade, SW",
 'Tollfree': ['(888) 289-8442 (Fraud Alert Hotline)'],
 'URI': 'http://www.usa.gov/api/USAGovAPI/contacts.json/contact/47994',
 'Web_Url': [{'Description': 'Administration for Children and Families '
                             '(ACF)',
              'Language': 'en',
              'Url': 'http://www.acf.hhs.gov/'}],
 'Zip': '20447'}
 ```

## Running the tests

Make sure you've installed the scraper's requirements, then run the tests
with:

```bash
nosetests
```
