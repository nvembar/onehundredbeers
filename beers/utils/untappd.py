
from bs4 import BeautifulSoup, Tag
import datetime
import logging
import re
from urllib.request import urlopen, Request
from urllib.parse import urljoin
from django.utils import timezone
from beers.models import Unvalidated_Checkin, Beer, Brewery

logger = logging.getLogger(__name__)

RE_RATING = re.compile('r[0-9]{3}')
HEADERS= {'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:66.0) Gecko/20100101 Firefox/66.0'}

class UntappdParseException(Exception):
    pass

def parse_checkin(url):
    """
    Takes in a URL and parses the result into a Unvalidated_Checkin object 
    with the following attributes, all optional:

    """
    with urlopen(Request(url, headers=HEADERS)) as response:
        soup = BeautifulSoup(response, "html.parser")
        result = Unvalidated_Checkin()
        # Get title
        title = soup.find('title')
        result.untappd_title = title.string.strip()

        # Get beer info and error if it's not there
        checkinInfo = soup.find("div", class_="beer")
        if checkinInfo is None:
            raise UntappdParseException(
                    "Unable to find beer information on checkin page")
        links = checkinInfo.find_all("a")
        for link in links:
            if 'href' not in link.attrs:
                continue
            if link['href'].startswith('/b/'):
                result.beer = link.string.strip()
                result.beer_url = urljoin(response.geturl(), link['href'])
            elif link['href'].startswith('/brewery/'):
                result.brewery = link.string.strip()
                result.brewery_url = urljoin(response.geturl(), link['href'])

        if result.beer is None or result.beer_url is None:
            raise UntappdParseException(
                    "Unable to find beer information link on page")

        timeP = soup.find('p', class_='time')
        if timeP is not None:
            result.untappd_checkin_date = datetime.datetime.strptime(
                    timeP.string.strip(), 
                    '%a, %d %b %Y %H:%M:%S %z')

        result.untappd_checkin = response.geturl()

        # Optional photo information
        photoDiv = soup.find("div", class_="photo")
        if photoDiv is not None:
            photoLink = photoDiv.find("a")
            result.photo_url = photoLink['data-image']

        # Optional rating
        ratingSpan = soup.find('span', class_='rating')
        if ratingSpan is not None:
            for cls in ratingSpan['class']:
                # These look like 'r200' for a 2 star rating
                if RE_RATING.match(cls):
                    result.rating = int(cls[1:])
        return result

def parse_beer(url, followBrewery=True):
    with urlopen(Request(url, headers=HEADERS)) as response:
        soup = BeautifulSoup(response, "html.parser")
        result = Beer()
        divs = soup.find_all('div', class_='name')
        if len(divs) == 0:
            raise UntappdParseException("Expected Beer URL at {}".format(url))
        breweryUrl = None
        result.untappd_url = response.geturl()
        for div in divs:
            header = div.find('h1')
            if header is not None:
                # We're in the right title block
                result.name = header.string.strip()
                breweryLink = div.find('a')
                if breweryLink is None:
                    raise UntappdParseException(
                            'Could not find expected brewery link in {}'.format(url))
                result.brewery = breweryLink.string.strip()
                breweryUrl  = urljoin(response.geturl(), breweryLink['href'])
                styleP = div.find('p', class_='style')
                if styleP is not None:
                    result.style = styleP.string.strip()
                break
        if followBrewery:       
            brewery = parse_brewery(breweryUrl)
            result.brewery_url = brewery.untappd_url
        else:
            result.brewery_url = breweryUrl
        return result

def parse_brewery(url):
    with urlopen(Request(url, headers=HEADERS)) as response:
        soup = BeautifulSoup(response, "html.parser")
        result = Brewery()
        result.untappd_url = response.geturl()
        divs = soup.find_all('div', class_='name')
        if len(divs) == 0:
            raise UntappdParseException("Expected Brewery URL at {}".format(url))
        for div in divs:
            header = div.find('h1')
            if header is not None:
                result.name = header.string.strip()
                locationP = div.find('p', class_='brewery')
                if locationP is not None:
                    result.location = locationP.string.strip()
            break
        return result

def parse_user(stream):
    pass
