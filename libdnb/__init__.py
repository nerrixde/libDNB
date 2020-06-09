import requests, json, re
from lxml import etree
from lxml.etree import tostring
from bs4 import BeautifulSoup
import datetime
class Metadata(object):
    pass
class LibDNB:
    def __init__(self, token):
        self.token = token
    def removeSortingCharacters(self, text):
        if text is not None:
            return ''.join([c for c in text if ord(c) != 152 and ord(c) != 156])
        else:
            return None
    def cleanUpTitle(self, title):
        if title is not None:
            match = re.search(
                '^(.+) [/:] [Aa]us dem .+? von(\s\w+)+$', self.removeSortingCharacters(title))
            if match:
                title = match.group(1)
        return title
    def cleanUpSeries(self, series, publisher_name):
        if series is not None:
            match = re.search('[\w\d]', series)
            if not match:
                return None
            series = ''.join(
                [c for c in series if ord(c) != 152 and ord(c) != 156])
            if publisher_name is not None:
                if publisher_name == series:
                    return None
                match = re.search(
                    '^(\w\w\w\w+)', self.removeSortingCharacters(publisher_name))
                if match:
                    pubcompany = match.group(1)
                    if re.search('^'+pubcompany, series, flags=re.IGNORECASE):
                        return None
            for i in [
                '^\[Ariadne\]$', '^Ariadne$', '^atb$', '^BvT$', '^Bastei L', '^bb$', '^Beck Paperback', '^Beck\-.*berater', '^Beck\'sche Reihe', '^Bibliothek Suhrkamp$', '^BLT$',
                '^DLV-Taschenbuch$', '^Edition Suhrkamp$', '^Edition Lingen Stiftung$', '^Edition C', '^Edition Metzgenstein$', '^ETB$', '^dtv', '^Ein Goldmann',
                '^Oettinger-Taschenbuch$', '^Haymon-Taschenbuch$', '^Mira Taschenbuch$', '^Suhrkamp-Taschenbuch$', '^Bastei-L', '^Hey$', '^btb$', '^bt-Kinder', '^Ravensburger',
                '^Sammlung Luchterhand$', '^blanvalet$', '^KiWi$', '^Piper$', '^C.H. Beck', '^Rororo', '^Goldmann$', '^Moewig$', '^Fischer Klassik$', '^hey! shorties$', '^Ullstein',
                '^Unionsverlag', '^Ariadne-Krimi', '^C.-Bertelsmann', '^Phantastische Bibliothek$', '^Beck Paperback$', '^Beck\'sche Reihe$', '^Knaur', '^Volk-und-Welt',
                    '^Allgemeine', '^Horror-Bibliothek$']:
                if re.search(i, series, flags=re.IGNORECASE):
                    return None
        return series
    def lookup(self, isbn):
        try:
            result = self._lookup(isbn)
            if not result:
                return None
            return result.__dict__
        except:
            return None
    def _lookup(self, isbn):
        if not isbn:
            return {}
        requesturl = f"https://services.dnb.de/sru/dnb?version=1.1&operation=searchRetrieve&accessToken={self.token}&query={isbn}&recordSchema=MARC21-xml&maximumRecords=10"
        respData = requests.get(requesturl).text.encode()
        root = etree.XML(respData)
        total_records = root.find('{http://www.loc.gov/zing/srw/}numberOfRecords').text
        if int(total_records) == 0:
            return {}
        nms = {'marc21': 'http://www.loc.gov/MARC21/slim'}
        records = root.xpath(".//marc21:record", namespaces=nms)

        record = records[0]

        series = None
        series_index = None
        publisher = None
        pubdate = None
        languages = []
        title = None
        title_sort = None
        authors = []
        author_sort = None
        edition = None
        comments = None
        idn = None
        urn = None
        isbn = None
        ddc = []
        subjects_gnd = []
        subjects_non_gnd = []
        publisher_name = None
        publisher_location = None
        fields = record.xpath(".//marc21:datafield[@tag='264']/marc21:subfield[@code='b' and string-length(text())>0]/../marc21:subfield[@code='a' and string-length(text())>0]/..", namespaces=nms)
        if len(fields) > 0:
            publisher_name = fields[0].xpath(".//marc21:subfield[@code='b' and string-length(text())>0]", namespaces=nms)[0].text.strip()
            publisher_location = fields[0].xpath(".//marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms)[0].text.strip()
        else:
            fields = record.xpath(".//marc21:datafield[@tag='264']/marc21:subfield[@code='b' and string-length(text())>0]/../..", namespaces=nms)
            if len(fields) > 0:
                publisher_name = fields[0].xpath(".//marc21:subfield[@code='b' and string-length(text())>0]", namespaces=nms)[0].text.strip()
            else:
                fields = record.xpath(".//marc21:datafield[@tag='264']/marc21:subfield[@code='a' and string-length(text())>0]/../..", namespaces=nms)
                if len(fields) > 0:
                    publisher_location = fields[0].xpath(".//marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms)[0].text.strip()
        for i in record.xpath(".//marc21:datafield[@tag='264']/marc21:subfield[@code='c' and string-length(text())>=4]", namespaces=nms):
            match = re.search("(\d{4})", i.text.strip())
            if match is not None:
                year = match.group(1)
                pubdate = datetime.datetime(int(year), 1, 1, 12, 30, 0)
                break
        title_parts = []
        for i in record.xpath(".//marc21:datafield[@tag='245']/marc21:subfield[@code='a' and string-length(text())>0]/..", namespaces=nms):
            code_a = []
            code_n = []
            code_p = []
            for j in i.xpath(".//marc21:subfield[@code='a']", namespaces=nms):
                code_a.append(j.text.strip())
            for j in i.xpath(".//marc21:subfield[@code='n']", namespaces=nms):
                match = re.search("(\d+([,\.]\d+)?)", j.text.strip())
                if match:
                    code_n.append(match.group(1))
                else:
                    code_n.append("0")
            for j in i.xpath(".//marc21:subfield[@code='p']", namespaces=nms):
                code_p.append(j.text.strip())
            title_parts = code_a
            if len(code_a) > 0 and len(code_n) > 0:
                if len(code_p) > 0:
                    title_parts = [code_p[-1]]
                series_parts = [code_a[0]]
                for i in range(0, min(len(code_p), len(code_n))-1):
                    series_parts.append(code_p[i])

                if len(series_parts) > 1:
                    for i in range(0, min(len(series_parts), len(code_n)-1)):
                        series_parts[i] += ' ' + code_n[i]

                series = ' - '.join(series_parts)
                series_index = 0
                if len(code_n) > 0:
                    series_index = code_n[-1]
        for i in record.xpath(".//marc21:datafield[@tag='245']/marc21:subfield[@code='b' and string-length(text())>0]", namespaces=nms):
            title_parts.append(i.text.strip())
            break
        title = title_parts[0]
        subtitle = ""
        if len(title_parts) > 1:
            subtitle = title_parts[1]
        if series is not None:
            series = self.cleanUpSeries(series, publisher_name)
        if title is not None:
            title = self.cleanUpTitle(title)
        if len(title_parts) > 0:
            title_sort_parts = list(title_parts)
            title_sort_regex = re.match('^(.*?)('+chr(152)+'.*'+chr(156)+')?(.*?)$', title_parts[0])
            sortword = title_sort_regex.group(2)
            if sortword:
                title_sort_parts[0] = ''.join(filter(None, [title_sort_regex.group(1).strip(), title_sort_regex.group(3).strip(), ", "+sortword]))
            title_sort = " : ".join(title_sort_parts)

        for i in record.xpath(".//marc21:datafield[@tag='100']/marc21:subfield[@code='4' and text()='aut']/../marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            name = re.sub(" \[.*\]$", "", i.text.strip())
            authors.append(name)
        for i in record.xpath(".//marc21:datafield[@tag='700']/marc21:subfield[@code='4' and text()='aut']/../marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            name = re.sub(" \[.*\]$", "", i.text.strip())
            authors.append(name)
        if len(authors) == 0:  # if no "real" autor was found take all persons involved
            # secondary authors
            for i in record.xpath(".//marc21:datafield[@tag='700']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
                name = re.sub(" \[.*\]$", "", i.text.strip())
                authors.append(name)
        if len(authors) > 0:
            author_sort = authors[0]
        for i in record.xpath(".//marc21:datafield[@tag='856']/marc21:subfield[@code='u' and string-length(text())>0]", namespaces=nms):
            if i.text.startswith("http://deposit.dnb.de/"):
                try:
                    comments = requests.get(i.text).text
                    comments = re.sub(
                        b'(\s|<br>|<p>|\n)*Angaben aus der Verlagsmeldung(\s|<br>|<p>|\n)*(<h3>.*?</h3>)*(\s|<br>|<p>|\n)*', b'', comments, flags=re.IGNORECASE)
                    comments = sanitize_comments_html(comments)
                    break
                except:
                    pass
        for i in record.xpath(".//marc21:datafield[@tag='016']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            idn = i.text.strip()
            break
        for i in record.xpath(".//marc21:datafield[@tag='024']/marc21:subfield[@code='2' and text()='urn']/../marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            urn = i.text.strip()
            break
        for i in record.xpath(".//marc21:datafield[@tag='020']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            isbn_regex = "(?:ISBN(?:-1[03])?:? )?(?=[-0-9 ]{17}|[-0-9X ]{13}|[0-9X]{10})(?:97[89][- ]?)?[0-9]{1,5}[- ]?(?:[0-9]+[- ]?){2}[0-9X]"
            match = re.search(isbn_regex, i.text.strip())
            isbn = match.group()
            isbn = isbn.replace('-', '')
            break

        # # When doing an exact search for a given ISBN skip books with wrong ISBNs
        # if isbn is not None and "isbn" in exact_search:
        #     if isbn != exact_search["isbn"]:
        #         continue

        ##### Field 82 #####
        # ID: Sachgruppe (DDC)
        for i in record.xpath(".//marc21:datafield[@tag='082']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            ddc.append(i.text.strip())
        ##### Field 490 #####
        # In theory this field is not used for "real" book series, use field 830 instead. But it is used.
        # Series and Series_Index
        if series is None or (series is not None and series_index == "0"):
            for i in record.xpath(".//marc21:datafield[@tag='490']/marc21:subfield[@code='v' and string-length(text())>0]/../marc21:subfield[@code='a' and string-length(text())>0]/..", namespaces=nms):

                attr_v = i.xpath(
                    ".//marc21:subfield[@code='v']", namespaces=nms)[0].text.strip()
                parts = re.split(" : ", attr_v)
                if len(parts) == 2:
                    if bool(re.search("\d", parts[0])) != bool(re.search("\d", parts[1])):
                        # figure out which part contains the index
                        if bool(re.search("\d", parts[0])):
                            indexpart = parts[0]
                            textpart = parts[1]
                        else:
                            indexpart = parts[1]
                            textpart = parts[0]

                        match = re.search("(\d+[,\.\d+]?)", indexpart)
                        if match is not None:
                            series_index = match.group(1)
                            series = textpart.strip()
                else:
                    match = re.search("(\d+[,\.\d+]?)", attr_v)
                    if match is not None:
                        series_index = match.group(1)
                    else:
                        series_index = "0"

                if series_index is not None:
                    series_index = series_index.replace(',', '.')

                # Use Series Name from attribute "a" if not already found in attribute "v"
                if series is None:
                    series = i.xpath(
                        ".//marc21:subfield[@code='a']", namespaces=nms)[0].text.strip()


                if series is not None:
                    series = self.cleanUpSeries(series, publisher_name)
                if series is not None:
                    break
        ##### Field 246 #####
        # Series and Series_Index
        if series is None or (series is not None and series_index == "0"):
            for i in record.xpath(".//marc21:datafield[@tag='246']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
                match = re.search(
                    "^(.+?) ; (\d+[,\.\d+]?)$", i.text.strip())
                if match is not None:
                    series = match.group(1)
                    series_index = match.group(2)
                    if series is not None:
                        series = self.cleanUpSeries(series, publisher_name)
                    if series is not None:
                        break
        ##### Field 800 #####
        # Series and Series_Index
        if series is None or (series is not None and series_index == "0"):
            for i in record.xpath(".//marc21:datafield[@tag='800']/marc21:subfield[@code='v' and string-length(text())>0]/../marc21:subfield[@code='t' and string-length(text())>0]/..", namespaces=nms):
                # Series Index
                series_index = i.xpath(
                    ".//marc21:subfield[@code='v']", namespaces=nms)[0].text.strip()
                match = re.search("(\d+[,\.\d+]?)", series_index)
                if match is not None:
                    series_index = match.group(1)
                else:
                    series_index = "0"
                series_index = series_index.replace(',', '.')
                # Series
                series = i.xpath(
                    ".//marc21:subfield[@code='t']", namespaces=nms)[0].text.strip()
                if series is not None:
                    series = self.cleanUpSeries(series, publisher_name)
                if series is not None:
                    break

        ##### Field 830 #####
        # Series and Series_Index
        if series is None or (series is not None and series_index == "0"):
            for i in record.xpath(".//marc21:datafield[@tag='830']/marc21:subfield[@code='v' and string-length(text())>0]/../marc21:subfield[@code='a' and string-length(text())>0]/..", namespaces=nms):
                # Series Index
                series_index = i.xpath(
                    ".//marc21:subfield[@code='v']", namespaces=nms)[0].text.strip()
                match = re.search("(\d+[,\.\d+]?)", series_index)
                if match is not None:
                    series_index = match.group(1)
                else:
                    series_index = "0"
                series_index = series_index.replace(',', '.')
                # Series
                series = i.xpath(
                    ".//marc21:subfield[@code='a']", namespaces=nms)[0].text.strip()
                if series is not None:
                    series = self.cleanUpSeries(series, publisher_name)
                if series is not None:
                    break

        ##### Field 689 #####
        # GND Subjects
        for i in record.xpath(".//marc21:datafield[@tag='689']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            subjects_gnd.append(i.text.strip())
        for f in range(600, 656):
            for i in record.xpath(".//marc21:datafield[@tag='"+str(f)+"']/marc21:subfield[@code='2' and text()='gnd']/../marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
                if i.text.startswith("("):
                    continue
                subjects_gnd.append(i.text)
        ##### Fields 600-655 #####
        # TODO: Remove sorting characters
        # Non-GND subjects
        for f in range(600, 656):
            for i in record.xpath(".//marc21:datafield[@tag='"+str(f)+"']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
                # ignore entries starting with "(":
                if i.text.startswith("("):
                    continue
                subjects_non_gnd.extend(re.split(',|;', i.text))
        # remove one-character subjects:
        for i in subjects_non_gnd:
            if len(i) < 2:
                subjects_non_gnd.remove(i)

        ##### Field 250 #####
        # Edition
        for i in record.xpath(".//marc21:datafield[@tag='250']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            edition = i.text.strip()
            break
        ##### Field 41 #####
        # Languages
        for i in record.xpath(".//marc21:datafield[@tag='041']/marc21:subfield[@code='a' and string-length(text())>0]", namespaces=nms):
            languages.append(i.text.strip())
        # if idn is not None and "idn" in exact_search:
        #     if idn != exact_search["idn"]:
        #         continue
        mi = Metadata()
        mi.title = self.removeSortingCharacters(title)
        mi.author_sort = list(map(lambda i: self.removeSortingCharacters(i), authors))
        #mi.title_sort = self.removeSortingCharacters(title_sort)
        mi.authors = self.removeSortingCharacters(author_sort)
        mi.languages = languages
        mi.pubdate = pubdate
    #    mi.publisher = " ; ".join(filter(
    #        None, [publisher_location, self.removeSortingCharacters(publisher_name)]))
        mi.publisher_location = publisher_location
        mi.publisher_name = publisher_name
        if series_index is not None and float(series_index) < 3000:
            mi.series = self.removeSortingCharacters(series)
            mi.series_index = series_index
        if comments:
            soup = BeautifulSoup(comments, 'lxml')
            mi.comments = soup.find("p").text
        else:
            mi.comments = ""
        mi.isbn = isbn
        mi.urn = urn if urn else ""
        mi.idn = idn if idn else ""
        mi.ddc = ",".join(ddc) if ddc else ""
        mi.subtitle = subtitle if subtitle else ""
        if len(subjects_gnd) > 0:
            mi.tags = subjects_gnd
        else:
            mi.tags = subjects_non_gnd if subjects_non_gnd else []
        if mi.tags:
            mi.tags = list(dict.fromkeys(mi.tags))
        return mi
