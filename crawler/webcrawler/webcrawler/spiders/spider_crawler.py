from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import re



class UniWebCrawler(CrawlSpider):
    name = "project_crawler"
    allowed_domains = ["brighton.ac.uk", "research.brighton.ac.uk"]
    start_urls = ["https://www.brighton.ac.uk/courses/study/computer-science-with-cyber-security-bsc-hons.aspx"]

    def __init__(self, start_url=None, *args **kwargs):
        super().__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]

    custom_settings = {
        'DOWNLOAD_DELAY': 2, # leaves 2 seconds between requests to webpage
        'CONCURRENT_REQUESTS': 1, # ensures only 1 request happens at a time
        'ROBOTSTXT_OBEY': True, # ensures crawler respects robots.txt
        'USER_AGENT': 'UniversityOfBrightonFinalProject/1.0 (Final Year Project; c.deretuerto1@uni.brighton.ac.uk)' # declares bot purpose and origin to site
    }

    rules = (
        # rule to follow links to find staff profiles
        Rule(LinkExtractor(allow=r"/about/us/contact-us/staff-profiles/", deny=(r"/_design/", r"/_backup", r"/_dev", r"/_forms", r"/_proxy")), callback="parse_staff_profile", follow=True),

        Rule(LinkExtractor(allow=r"/staff/",), callback="parse_staff_profile", follow=True),
    )

    def parse_start_url(self,response):
        """Parse the inital course page"""
        # Retrieve and scrape the course information
        course_information = {
            'url': response.url,
            'course_title': response.css('h1::text').get(),
            'staff_names': [],
            "staff_external_links": [],
            "staff_email_addresses": []
        }


       

        team_locator = response.css('div.sys_span8')

        leader = team_locator.css('p > strong > a.sys_16::text').get()
        if leader:
            leader = leader.replace(',', ''). strip()

        members = team_locator.css('ul >li>a.sys_16::text').getall()
        members =[name.strip() for name in members]

        all_names = []
        if leader:
            all_names.append(leader)
        all_names.extend(members)
        
        # remove duplicate results from scrape
        seen = set()
        unique_names =[]
        for name in all_names:
            if name not in seen:
                seen.add(name)
                unique_names.append(name)

        course_information['staff_names'] = unique_names



        #Find links to staff profiles on site

        

        leader_link = team_locator.css('p > strong > a.sys_16::attr(href)').get()
        team_member_links = team_locator.css('ul>li>a.sys_16::attr(href)').getall()

        all_links =[]
        if leader_link:
            all_links.append(leader_link)
        all_links.extend(team_member_links)

        course_information['staff_links']= all_links

        # Find any linked email addresses available on the page

        email_locator = r'\b[A-Za-z0-9._%+-]+@brighton\.ac\.uk\b'
        email = re.findall(email_locator, response.text)
        course_information['staff_emails'] = list(set(email))

        for links in all_links:
            yield response.follow(
                link,
                callback=self.parse_staff_profiles
            )

        yield course_information