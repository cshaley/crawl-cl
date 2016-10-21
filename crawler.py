from bs4 import BeautifulSoup as bs
import requests

def get_links_by_state():
    """ This function pulls all of the US State craigslist website cities from craigslist
    and returns them as a dictionary
    
    Returns
    -------
    states (dictionary): dictionary of cities for which craigslist has a website in the format
        {'state1':['city1', 'city2', ...], 'state2':['city3', 'city4', ...], ...}
    """
    
    # Get site
    q = "https://www.craigslist.org/about/sites#US"
    html = requests.get(q).text
    
    # Make beautifulsoup object
    soup = bs(html, 'html.parser')
    
    # find divs on page
    div_list = soup.find_all('div')
    
    # cut div_list only to the correct class of div and split out unnecessary data
    hrefs = [p for p in div_list if p.get('class') == [u'colmask']]
    hrefs = str(hrefs[0]).split('<h4>')
    hrefs2 = []
    for h in hrefs:
        hrefs2.append(h.split('</h4>'))
    
    # Create states dictionary in the format {'state1':['city1_url', 'city2_url', ...], ...}
    states = {}
    for html_split in hrefs2:
        if len(html_split) == 2:
            states[html_split[0].lower()] = html_split[1]
    
    # Parse city urls so that the states dictionary transforms to
    # {'state1':['city1', 'city2', ...], 'state2':['city3', 'city4', ...], ...}
    for state in states.keys():
        soup = bs(states[state], 'html.parser')
        links = soup.find_all('a')
        states[state] = [get_city_from_url(a.get("href")) for a in links]
    return states

def get_car_links(url):
    """ Gets item links from craigslist search results page
    Runs recursively for queries with more than 1 page of results
    
    Parameters
    ----------
    url (string): URL to craigslist search query page
    
    Returns
    -------
    test_list (list of strings): List of titles of pages
    href_list (list of strings): List of links to pages
    """
    
    city = get_city_from_url(url)
    
    # Load page
    html = requests.get(url).text
    
    # Create beautiful soup parser
    soup = bs(html, 'html.parser')
    
    # find all links on page
    link_list = soup.find_all('a') 
    
    # Find all car links 
    car_list = [a for a in link_list 
                 if str(a.get('class')) == "[u'hdrlnk']"]
                 #if any(x in str(a) for x in search_strings)]
    
    # Parse the page to get the title of and link to each item on the search results page
    text_list, href_list = [], []
    for l in car_list:
        if l.contents:
            text_list.append(unicode(l.contents[0]))
            href = l.get('href')
            if href.startswith("//"):
                href = "http:{0}".format(href)
            elif href.startswith("http"):
                pass
            else:
                href = "http://{0}.craigslist.org{1}".format(city, href)
            href_list.append(href)
    
    # Find all link tags in page - in order to move to the next page
    link_rels = soup.find_all('link')
    
    # If there is a next page, then set the next_page variable and call this function (recursively) to get the next page
    # Else return the title list and link list
    try:
        next_page = [a.get('href') for a in link_rels if a.get('rel')[0] == u'next'][0]
    except IndexError:
        return text_list, href_list
    tl, hl = get_car_links(next_page)
    
    # Aggregate and return title list and link list
    text_list+= tl
    href_list += hl
    return text_list, href_list

def get_city_from_url(url):
    """ Parse craigslist url to only return the city 
    
    Parameters
    ----------
    url (string): Any craigslist URL
    
    Returns
    -------
    city (string): The city from the subdomain of the URL
    None if no city was detected
    """
    assert type(url) == str, "URL must be a string"
    assert len(url) > 7, "string provided is too short to be a URL"
    
    end = 0
    for i, letter in enumerate(url):
        if letter == '.':
            end = i
            break
    
    if end == 0:
        return None
    return url[7:end]

def get_attrs(lnk):
    """ Get attributes of an object that is for sale on craigslist from the link 
    
    Parameters
    ----------
    lnk (string): Link to an item for sale on craigslist
    
    Returns
    -------
    d (dictionary): Dictionary of attributes of the item for sale on craigslist
    """
    
    # load webpage
    html = requests.get(lnk).text
    
    # Create beautifulsoup parser to parse page
    soup = bs(html, 'html.parser')
    
    # find all paragraphs and spans on page
    p_list = soup.find_all('p')
    spans = soup.find_all('span')
    
    # Set the price of the item from the attribute.
    # If price is not listed, set it to NaN.
    try:
        price = [s for s in spans if s.get('class') == [u'price']][0].contents[0]
    except:
        price = np.NaN
    
    # Get a list of the rest of the attributes of the item
    attrs = [p for p in p_list if p.get('class') == [u"attrgroup"]]
    attr_list = attrs[1].find_all('span')
    
    # Create a dictionary of the attributes of the item in the format {'attribute': 'value', ...}
    d = {}
    d['Price'] = price
    for attr in attr_list:
        try:
            d[attr.contents[0]] = attr.contents[1].contents[0]
        except IndexError:
            # If the attribute is listed but has no value, then ignore it
            pass
    return d
