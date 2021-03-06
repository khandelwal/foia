import os
from unittest import TestCase

from bs4 import BeautifulSoup
from mock import Mock, patch
import yaml

import keywords_from_fr as fr
import layer_with_csv as layer
import scraper
import layer_with_usa_contacts as usa_layer

import average_time_scraper


class ScraperTests(TestCase):

    def test_populate_parent(self):
        agency_data = {
            'name': 'Best agency',
            'description': "The most important agency.",
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': "I don't know which office",
                    'emails': ['hq@agency.gov'],
                    'phone': '202-555-5555',
                    'office_url': 'http://office.url',
                    'person_name': 'Joe Bureaucrat'
                }
            ]
        }
        populated = scraper.populate_parent(agency_data)
        self.assertEqual(len(populated['departments']), 1)
        self.assertEqual(populated['name'], 'Best agency')
        self.assertEqual(populated['phone'], '202-555-5555')
        self.assertEqual(populated['person_name'], 'Joe Bureaucrat')
        self.assertEqual(populated['emails'], ['hq@agency.gov'])
        self.assertEqual(populated['office_url'], 'http://office.url')

    def test_all_but_unknown(self):
        agency_data = {
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': "I don't know which office",
                    'emails': ['hq@agency.gov']
                }
            ]
        }
        departments = scraper.all_but_unknown(agency_data)
        self.assertEqual(len(departments), 1)
        self.assertEqual(departments[0]['name'], 'department one')

    def test_get_unknown_office_details(self):
        agency_data = {
            'emails': ['foia@agency.gov'],
            'common_requests': ['spaceship plans'],
            'keywords': ['purchase card use', 'government forms'],
            'name': 'Best agency',
            'description': "The most important agency.",
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': "I don't know which office",
                    'emails': ['hq@agency.gov']
                }
            ]
        }
        unknown = scraper.get_unknown_office_details(agency_data)
        self.assertEqual(
            unknown,
            {
                'name': "I don't know which office",
                'emails': ['hq@agency.gov']})

    def test_update_list_in_dict(self):
        original = {'keywords': ['accounting', 'estates']}
        scraper.update_list_in_dict(
            original, 'keywords', ['accounting', 'employment', 'courts'])

        self.assertEqual(
            original['keywords'],
            ['accounting', 'courts', 'employment', 'estates'])

        original = {}
        scraper.update_list_in_dict(original, 'emails', ['email@agency.gov'])
        self.assertEqual(original['emails'], ['email@agency.gov'])

    def test_actual_apply(self):
        agency_data = {
            'emails': ['foia@agency.gov'],
            'common_requests': ['spaceship plans'],
            'keywords': ['purchase card use', 'government forms'],
            'name': 'Best agency',
            'description': "The most important agency.",
            'departments': [
                {
                    'name': 'department one',
                    'emails': ['department.one@agency.gov'],
                    'keywords': ['department one things'],
                },
                {
                    'name': 'department two',
                    'emails': ['department.two@agency.gov']
                }
            ]
        }

        manual_data = {
            'no_records_about': ['aliens'],
            'emails': ['public.liaison@agency.gov'],
            'description': 'One of the most important agencies',
            'common_requests': ['travel data'],
            'keywords': ['election data', 'courts'],
            'departments': [
                {
                    'name': 'department one',
                    'top_level': True,
                    'emails': ['onefoia@agency.gov'],
                    'keywords': ['first things']}
            ]
        }

        applied = scraper.actual_apply(agency_data, manual_data)

        self.assertEqual(
            applied['emails'],
            ['foia@agency.gov', 'public.liaison@agency.gov'])
        self.assertEqual(
            applied['keywords'],
            [
                'courts', 'election data',
                'government forms', 'purchase card use'])
        self.assertEqual(
            applied['common_requests'],
            ['spaceship plans', 'travel data'])

        self.assertEqual(applied['no_records_about'], ['aliens'])
        self.assertEqual(
            applied['description'],
            'One of the most important agencies')

        department_names = [d['name'] for d in applied['departments']]
        self.assertEqual(
            department_names, ['department one', 'department two'])

        for d in applied['departments']:
            if d['name'] == 'department one':
                self.assertEqual(
                    d['emails'],
                    ['department.one@agency.gov', 'onefoia@agency.gov'])

                self.assertEqual(
                    d['keywords'],
                    ['department one things', 'first things'])

                self.assertTrue(d['top_level'])

            if d['name'] == 'department two':
                self.assertEqual({
                    'name': 'department two',
                    'emails': ['department.two@agency.gov']}, d)

    def test_read_manual_data(self):
        scraper.save_agency_data(
            'TEST', {'name': 'Test Agency'}, data_directory='/tmp/test/')
        data = scraper.read_manual_data('TEST', manual_data_dir='/tmp/test')
        self.assertEqual({'name': 'Test Agency'}, data)

    def test_agency_yaml_filename(self):
        filename = scraper.agency_yaml_filename('/tmp', 'TEST')
        self.assertEqual('/tmp/TEST.yaml', filename)

    def test_save_agency_data(self):
        scraper.save_agency_data(
            'TEST', {'name': 'Test Agency'}, data_directory='/tmp/test/')
        self.assertTrue(os.path.isfile('/tmp/test/TEST.yaml'))
        test_data = yaml.load(open('/tmp/test/TEST.yaml', 'r'))
        self.assertEqual({'name': 'Test Agency'}, test_data)

    def test_agency_description(self):
        """Description should be pulled out and BRs should be converted"""
        html = """
            <h1>An Agency</h1>
            <h2>Blah blah</h2>
            <div id='0'>Default</div>
            <div id='1'>Description of office 1</div>
            <h2>About</h2>Line 1<br>Line 2<br><br>
            Line 3<br />
            Last Line
        """
        doc = BeautifulSoup(html)
        description = scraper.agency_description(doc)
        self.assertEqual(description, "Line 1\nLine 2\nLine 3\nLast Line")

    def test_clean_paragraphs(self):
        """Paragraphs should be pulled out and converted to text, disregarding
        empty/whitespace paragraphs"""
        doc = BeautifulSoup("""
            <div>
                <h1>Title</h1>
                <p>Content 1</p>
                <p />
                <p> &nbsp;</p>
                <p>\n\t</p>
                <p>Content 2
                <p><img />Content 3
            </div>""")
        lines, ps = scraper.clean_paragraphs(doc)
        self.assertEqual(lines, ['Content 1', 'Content 2', 'Content 3'])

    def test_phone(self):
        """Test various phone formats and make sure bad formats produce
        errors"""
        for line in ("+4 123-456-7890", "4-(123) 456 7890", "41234567890"):
            self.assertEqual("+4 123-456-7890", scraper.phone(line))
        for line in ("  123-456-7890", "(123) 456 7890", "1234567890"):
            self.assertEqual("123-456-7890", scraper.phone(line))
        for line in ("Other", "123-4567", "1234-5679-0"):
            self.assertRaises(Exception, scraper.phone, line)

    def test_split_address_from(self):
        """Address should be separated as soon as we encounter "service
        center", "fax", etc."""
        lines = ["Line 1", "Line 2", "1234567890 serVice CenTer", "Line 3"]
        addy, rest = scraper.split_address_from(lines)
        self.assertEqual(lines[:2], addy)
        self.assertEqual(lines[2:], rest)

        lines = ["Line 1\n\rLine 2\nfax", "fax 1234567890"]
        addy, rest = scraper.split_address_from(lines)
        self.assertEqual(["Line 1", "Line 2", "fax"], addy)
        self.assertEqual(lines[1:], rest)

    def test_find_emails(self):
        """Verify that email addresses can be pulled out (and split, if
        appropriate) from paragraphs"""
        lines = ["Line 1", "Some email: ", "Then e-mails:", "Line 4"]
        ps = ["<p>Line 1</p>",
              "<p>Some email: <a href='mailto:a@b.com'>click</a></p>",
              "<p>Then e-mails:<a href='mailto:c@d.com;e@f.info;   g@h.io'>"
              + "email</a></p>",
              "<p>Line 4</p>"]
        ps = [BeautifulSoup(p) for p in ps]
        emails = scraper.find_emails(lines, ps)
        self.assertEqual(["a@b.com", "c@d.com", "e@f.info", "g@h.io"],
                         emails)

        emails = scraper.find_emails(lines[:1], ps[:1])
        self.assertEqual([], emails)

        lines = ["Off hand reference to email"]
        ps = [BeautifulSoup("<p>Off hand reference to email</p>")]
        self.assertRaises(Exception, scraper.find_emails, lines, ps)

    def test_find_bold_fields(self):
        """Three types of bold fields, simple key-value pairs (like 'notes'),
        url values (e.g. website, request form), and 'misc' -- everything
        else. Account for empty urls"""
        ps = [
            "<p>Intro <strong>Some Key:</strong> Some Value</p>",
            "<p><strong>Notes</strong> Some notes here</p>",
            "<p><strong>Website:</strong><a href='example.com'>here</a></p>",
            "<p><strong>Request Form: </strong><a href=''></a></p>",
            "<p><strong>FOIA Contact</strong> is John</p>"]
        ps = [BeautifulSoup(p) for p in ps]
        results = list(scraper.find_bold_fields(ps))
        self.assertEqual(results, [("misc", ("Some Key", "Some Value")),
                                   ("notes", "Some notes here"),
                                   ("website", "example.com"),
                                   ("request_form", "")])

    def test_parse_department_integration(self):
        """Integration test for the department div. Make sure that, given a
        blob of html, correct fields are pulled out. Use a mix of properly
        closed <p>s and not (this mixtures matches the live data)"""
        html = BeautifulSoup("""<div><blockquote>
            <p><strong>FOIA Contact:</strong> send to:</p>
            <p>Jane Smith</p>
            <p>Awesome Person</p>
            <p></p>
            <p>A Federal Agency</p>
            <p>Washington, DC 20505</p>
            <p>(555) 111-2222 (Telephone)</p>
            <p>(555) 222-3333 (Fax)</p>
            <p><a href="mailto:foia@example.gov;other@example.com">
                foia@example.gov</a> (Request via Email)</p>
            <hr />
            <p><strong>FOIA Requester Service Center:</strong>
                Phone: (555) 333-4444
            <p><strong>FOIA Public Liaison:</strong>
                Mark Someone, (555) 444-5555
            <p><strong>Program Manager:</strong>
                Someone Else, Phone: (555) 555-6666
            <p><strong>Website: </strong>
                <a href="http://www.foia.example.gov/">
                    http://www.foia.example.gov/</a>
            </p></blockquote></div>""")
        result = scraper.parse_department(html, "Agency X")
        self.assertEqual(result['name'], "Agency X")
        self.assertEqual(result['address'],
                         ["Jane Smith", "Awesome Person", "A Federal Agency",
                          "Washington, DC 20505"])
        self.assertEqual(result['phone'], "555-111-2222")
        self.assertEqual(result['fax'], "555-222-3333")
        self.assertEqual(result['emails'],
                         ["foia@example.gov", "other@example.com"])
        self.assertEqual(result['service_center'], "Phone: (555) 333-4444")
        self.assertEqual(result['public_liaison'],
                         "Mark Someone, (555) 444-5555")
        self.assertEqual(result['misc']['Program Manager'],
                         "Someone Else, Phone: (555) 555-6666")
        self.assertEqual(result['website'], "http://www.foia.example.gov/")

    @patch('scraper.parse_department')
    def test_parse_agency(self, parse_department):
        """Verify that the agency-specific fields (abbreviation, name,
        description) are pulled out, and that we are calling the
        parse_department function on the appropriate div. Include some messy
        HTML (e.g. empty link tag in the title, "Return to Top", etc. etc.)"""
        html = """<div><div><a><img />Print Selected Office</a></div></div>
                  <h1><a></a>An Agency</h1>
                  <div><img />
                    <p>Chief FOIA Officer: Some One, Officer</p>
                    <p><a><img />What do these FOIA terms mean?</a></p>
                  </div>
                  <h2><label for="ComponentsList">I want to:</label></h2>
                  <select id="ComponentsList">
                    <option value="0">Select an Office</option>
                    <option value="1">Headquarters</option>
                    <option value="2">Chicago Branch</option>
                  </select>
                  <div id="0">Div Zero</div>
                  <div id="1">Div One</div>
                  <div id="2">Div Two</div>
                  <p>&nbsp;</p>
                  <div class="lineshadow"></div>
                  <h2>About the this agency</h2>Some Description
                  <p align="right"><a href="#top">Return to Top</a></p>"""
        result = scraper.parse_agency("AAA", BeautifulSoup(html))
        self.assertEqual(result['abbreviation'], "AAA")
        self.assertEqual(result['name'], "An Agency")
        self.assertEqual(result['description'], 'Some Description')
        self.assertEqual(2, len(result['departments']))
        hq_call, chicago_call = parse_department.call_args_list
        self.assertEqual(hq_call[0][0]['id'], "1")
        self.assertEqual(hq_call[0][1], "Headquarters")
        self.assertEqual(chicago_call[0][0]['id'], "2")
        self.assertEqual(chicago_call[0][1], "Chicago Branch")

    def test_agency_url(self):
        """Verify that agency abbreviations are getting converted into a URL"""
        self.assertTrue("agency=ABCDEF" in scraper.agency_url("ABCDEF"))
        self.assertTrue("agency=A+B+C+D" in scraper.agency_url("A B C D"))


class LayerTests(TestCase):
    def test_address_lines(self):
        """Add lines for room number, street addy is present. Only add
        city/state/zip if all three are present."""
        row = {"Room Number": "", "Street Address": "", "City": "",
               "State": "", "Zip Code": ""}
        row["City"] = "Boston"
        self.assertEqual([], layer.address_lines(row))
        row["Zip Code"] = 90210
        self.assertEqual([], layer.address_lines(row))
        row["Street Address"] = "123 Maywood Dr"
        self.assertEqual(["123 Maywood Dr"], layer.address_lines(row))
        row["Room Number"] = "Apt B"
        self.assertEqual(["Apt B", "123 Maywood Dr"],
                         layer.address_lines(row))
        row["State"] = "XY"
        self.assertEqual(["Apt B", "123 Maywood Dr", "Boston, XY 90210"],
                         layer.address_lines(row))

    def test_contact_string(self):
        """Format name and phone information; check each combination"""
        row = {"Name": "", "Telephone": ""}
        self.assertEqual("", layer.contact_string(row))
        row["Name"] = "Bob Bobberson"
        self.assertEqual("Bob Bobberson", layer.contact_string(row))
        row["Telephone"] = "(111) 222-3333"
        self.assertEqual("Bob Bobberson, Phone: (111) 222-3333",
                         layer.contact_string(row))
        row["Name"] = ""
        self.assertEqual("Phone: (111) 222-3333", layer.contact_string(row))

    def test_patch_dict(self):
        """Verify fields are added, nothing gets overwritten, and misc fields
        are merged"""
        old_dict = {"a": 1, "b": 2, "misc": {"z": 100}}
        new_dict = {"b": 4, "c": 3, "misc": {"z": 999, "y": 99}}
        result = layer.patch_dict(old_dict, new_dict)
        self.assertEqual(result, {
            "a": 1, "b": 2, "c": 3, "misc": {"z": 100, "y": 99}})

    def test_patch_dict_noop(self):
        """If there are no new field, None is returned"""
        old_dict = {"a": 1, "b": 2}
        new_dict = {"b": 100}
        self.assertEqual(None, layer.patch_dict(old_dict, old_dict))
        self.assertEqual(None, layer.patch_dict(old_dict, new_dict))

    def empty_row(self):
        return {"Agency": "", "Department": "", "Name": "", "Title": "",
                "Room Number": "", "Street Address": "", "City": "",
                "State": "", "Zip Code": "", "Telephone": "", "Fax": "",
                "Email Address": "", "Website": "", "Online Request Form": "",
                "Notes": ""}

    def test_add_contact_info_agency(self):
        """Agency & Office should be added to `contact` dictionary if not
        present"""
        row = self.empty_row()
        row["Department"] = "ACRONYM"
        row["Agency"] = "Sewage Treatment"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        #   Adding again has no affect
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        #   Adding another agency
        row["Agency"] = "Road Maintenance"
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        self.assertTrue("Road Maintenance" in contact_dict["ACRONYM"])
        #   Adding another agency with leading and trailing spaces
        row["Agency"] = "  Economic Development   "
        layer.add_contact_info(contact_dict, row)
        self.assertTrue("ACRONYM" in contact_dict)
        self.assertTrue("Sewage Treatment" in contact_dict["ACRONYM"])
        self.assertTrue("Road Maintenance" in contact_dict["ACRONYM"])
        self.assertTrue("Economic Development" in contact_dict["ACRONYM"])

    def test_add_contact_info_website(self):
        """Website field gets cleaned up -- verify it's not added unless it's
        in the right form"""
        row = self.empty_row()
        row["Department"] = "A"
        row["Agency"] = "B"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("website" in contact_dict["A"]["B"])

        row["Website"] = "http://"
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("website" in contact_dict["A"]["B"])

        row["Website"] = "http://example.gov"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual("http://example.gov",
                         contact_dict["A"]["B"]["website"])

    def test_add_contact_info_emails(self):
        """Each row that contains an email address should get added to the
        list"""
        row = self.empty_row()
        row["Department"] = "A"
        row["Agency"] = "B"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["emails"], [])

        row["Email Address"] = "a@b.com"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["emails"], ["a@b.com"])

        row["Email Address"] = "c@d.gov"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["emails"],
                         ["a@b.com", "c@d.gov"])

    def test_add_contact_info_people(self):
        """Verify that the title of a row indicates which field it should be
        placed in"""
        row = self.empty_row()
        row["Department"] = "A"
        row["Agency"] = "B"
        row["Name"] = "Ada"
        contact_dict = {}
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("service_center" in contact_dict["A"]["B"])
        self.assertEqual(contact_dict["A"]["B"]["misc"], {})

        row["Title"] = "Awesome Person"
        layer.add_contact_info(contact_dict, row)
        self.assertFalse("service_center" in contact_dict["A"]["B"])
        self.assertEqual(contact_dict["A"]["B"]["misc"],
                         {"Awesome Person": "Ada"})

        row["Name"] = "Bob"
        row["Title"] = "FOIA Service Center Technician"
        layer.add_contact_info(contact_dict, row)
        self.assertEqual(contact_dict["A"]["B"]["service_center"], "Bob")
        self.assertEqual(contact_dict["A"]["B"]["misc"],
                         {"Awesome Person": "Ada"})


class FRTests(TestCase):
    """Tests keywords_from_fr"""
    def test_normalize_name(self):
        for old, new in (
            ('United States African Development Foundation',
                'AFRICAN DEVELOPMENT FOUNDATION'),
            ('Administration for Children and Families',
                'CHILDREN FAMILIES'),
            ('Export-Import Bank of the U.S.', 'EXPORTIMPORT BANK'),
            ('Department of the Army - Main Office', 'ARMY'),
            ('Centers for Disease Control', 'CENTER DISEASE CONTROL'),
                ):
            self.assertEqual(fr.normalize_name(old), new)

    def test_fetch_page_dates(self):
        """Should compute the min and max day of each month"""
        client = Mock()
        fr.fetch_page(2003, 2, 1, client)
        self.assertTrue('2003-02-01' in str(client.get.call_args))
        self.assertTrue('2003-02-28' in str(client.get.call_args))
        self.assertFalse('2003-02-29' in str(client.get.call_args))
        fr.fetch_page(2004, 2, 1, client)
        self.assertTrue('2004-02-01' in str(client.get.call_args))
        self.assertFalse('2004-02-28' in str(client.get.call_args))
        self.assertTrue('2004-02-29' in str(client.get.call_args))

    def test_fetch_page_errors(self):
        """Should handle bad JSON and 500s"""
        client = Mock()
        response = Mock()
        client.get.return_value = response
        response.status_code = 500
        self.assertEqual({'results': []}, fr.fetch_page(2003, 2, 1, client))

        response.status_code = 200
        response.json.side_effect = ValueError
        self.assertEqual({'results': []}, fr.fetch_page(2003, 2, 1, client))

    def test_last_day_in_month(self):
        """Verify leap years, etc."""
        self.assertEqual(28, fr.last_day_in_month(2003, 2))
        self.assertEqual(29, fr.last_day_in_month(2004, 2))
        self.assertEqual(31, fr.last_day_in_month(2011, 1))

    def test_normalize_and_map(self):
        """should normalize keys w/ loosing data"""
        test_dict = {'A': {'datum1'}, 'B': {'datum2'}, 'a': {'datum3'}}
        expected_dict = {'A': {'datum1', 'datum3'}, 'B': {'datum2'}}
        self.assertEqual(expected_dict, fr.normalize_and_map(test_dict))


class USALayerTests(TestCase):
    def test_float_to_int_str(self):
        """should convert input to int (floor) then string when possible"""
        self.assertEqual('32', usa_layer.float_to_int_str(32.32))
        self.assertEqual('32', usa_layer.float_to_int_str(32.99))
        self.assertEqual(None, usa_layer.float_to_int_str(None))
        self.assertEqual('23', usa_layer.float_to_int_str("23.2"))
        self.assertEqual('23.2x', usa_layer.float_to_int_str("23.2x"))

    def test_extract_acronym(self):
        """extract one acroym, if it has two return 'massive error'"""

        self.assertEqual(
            "DOS", usa_layer.extract_acronym('Department of State (DOS)'))
        self.assertEqual(
            "", usa_layer.extract_acronym("Random Office"))
        self.assertEqual(
            "Massive Error",
            usa_layer.extract_acronym("Random Office (RO) (RO)"))


class AverageTimeScaperTests(TestCase):
    def test_parse_table(self):
        '''parses data tables from foia.gov'''
        expected_data = {
            'Federal Retirement Thrift Investment Board_2012_FRTIB': {
                'Complex-Lowest No. of Days': 'NA',
                'Complex-Average No. of Days': 'NA',
                'Expedited Processing-Highest No. of Days': 'NA',
                'Component': 'FRTIB',
                'Expedited Processing-Lowest No. of Days': 'NA',
                'Simple-Lowest No. of Days': '1',
                'Simple-Highest No. of Days': '57',
                'Simple-Median No. of Days': '20', 'Agency': 'FRTIB',
                'Complex-Highest No. of Days': 'NA',
                'Simple-Average No. of Days': '27',
                'Expedited Processing-Average No. of Days': 'NA',
                'Expedited Processing-Median No. of Days': 'NA',
                'Complex-Median No. of Days': 'NA', 'Year': '2012'}}

        testurl = 'http://www.foia.gov/foia/Services/DataProcessTime.jsp?'
        params = {"advanceSearch": "71001.gt.-999999"}
        params['requestYear'] = '2012'
        params['agencyName'] = 'FRTIB'
        data = average_time_scraper.parse_table(testurl, params, {})
        self.assertEqual(expected_data, data)

        # Won't break with empty tables
        params['requestYear'] = '2008'
        params['agencyName'] = 'RATB'
        data = average_time_scraper.parse_table(testurl, params, {})
        self.assertEqual({}, data)

    def test_zip_and_clean(self):
        '''returns a zipped dictionary with 0s coded as NAs'''

        test_header = ['header 1', 'header 2', 'header 3']
        test_row = ['2.23', '0', 'NA']
        exp_data = {'header 1': '2.23', 'header 2': 'NA', 'header 3': 'NA'}
        result = average_time_scraper.zip_and_clean(test_header, test_row)
        self.assertEqual(exp_data, result)

    def test_get_agency(self):
        '''returns a string in format _%s where %s is the agency name'''

        test_data = {'Agency': "DOS", "other_data": "text blob"}
        expected_data = '_DOS'
        result = average_time_scraper.get_agency(test_data)
        self.assertEqual(expected_data, result)

    def test_append_time_stats(self):
        '''appends time stats data to dictionary'''

        test_yaml = {'name': "DOS", "other_data": "text blob"}
        test_data = {
            'DOS_2013DOS': {
                'Simple-Mean No. of Days': '22', 'Agency': 'DOS',
                'Year': '2013', 'Component': 'DOS'}}
        expected_data = {
            'name': "DOS", "other_data": "text blob",
            'request_time_stats': {
                '2013': {'Simple-Mean No. of Days': '22'}}}
        result = average_time_scraper.append_time_stats(
            test_yaml, test_data, "_2013", "DOS")
        self.assertEqual(expected_data, result)

    def test_update_dict(self):
        '''updates the new dictionary with ids, abbreviation, description
        and forms, but will not overwrite any descriptions'''

        new_data = {
            'Deparment A': {'usa_id': '1', 'acronym': 'A'},
            'Deparment B': {
                'usa_id': '2', 'acronym': 'B',
                'description': 'next des.'}}

        old_data = {'name': 'Deparment A', 'description': "old desc."}
        old_data_expected = {
            'name': 'Deparment A', 'description': "old desc.",
            'usa_id': '1', 'abbreviation': 'A'}
        old_data, new_data = usa_layer.update_dict(old_data, new_data)
        self.assertEqual(old_data_expected, old_data)

        old_data = {'name': 'Deparment B'}
        old_data_expected = {
            'name': 'Deparment B', 'description': "next des.",
            'usa_id': '2', 'abbreviation': 'B'}
        old_data, new_data = usa_layer.update_dict(old_data, new_data)
        self.assertEqual(old_data_expected, old_data)
