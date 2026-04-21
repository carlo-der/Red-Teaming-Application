from scrapy.spiders import Spider
from scrapy.linkextractors import LinkExtractor
import re
import json
import ollama

class UniWebCrawler(Spider):
    name = "project_crawler_ollama"  # name of the crawler
    allowed_domains = ["brighton.ac.uk", "research.brighton.ac.uk"] # definition of domains that the crawler is restricted to
    start_urls = ["https://www.brighton.ac.uk/courses/study/computer-science-with-cyber-security-bsc-hons.aspx"] #url that the crawler begins on

  

    custom_settings = {
        'DOWNLOAD_DELAY': 3.0, # leaves 3 seconds between requests to webpage to ensure the server does not get overloaded
        'CONCURRENT_REQUESTS': 1, # ensures only 1 request happens at a time
        'ROBOTSTXT_OBEY': True, # ensures crawler respects robots.txt
        
        "COOKIES_ENABLED": False, # avoids creating active sessions whilst scraping
        
        'DEFAULT_REQUEST_HEADERS': { # helps the crawler to identify which types of information it will be scraping
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        },
        'HTTPCACHE_ENABLED': False, # disables cache so that the crawler always scraped the most up to date information
        'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter', # allows the crawler to visit the same URL again
        'FEED_FORMAT': 'json', # explicitly defines the output format to help with generator information retrieval
        'FEED_EXPORT_INDENT': 2 # allows easier reading of JSON content for debugging and testing
        
    }

    

    def parse(self, response):

        

        team_section = response.css('div.sys_span8') # specific div that team section is stored in on university page

        if not team_section:
            team_section = response.css('main')

        page_text = ' '.join(team_section.css('*::text').getall())
        cleaned_page_text = ' '.join(page_text.split())[:3000]

        profile_links = team_section.css('a::attr(href)').getall() # location of individual staff profile links

        correct_links = []
        for link in profile_links:
            full_url = response.urljoin(link)

            if "persons" in full_url or "research.brighton.ac.uk" in full_url:
                correct_links.append(full_url)

        correct_links = list(set(correct_links))

        try:
            result = ollama.chat( # call to ollama to start scrape
            model = 'llama3.2:3b', #definition of LLM used for scrape
            messages=[             # instructions fed to LLM to ensure correct data is recieved
                {
                    'role': 'system',
                    'content': 'You are a data extractor. Return ONLY valid JSON.'
                },
                {
                    'role': 'user',
                    'content': f"Extract staff names from this HTML text and return as JSON with keys 'course_title' and 'staff_names' (array):\n\n{cleaned_page_text}"
                }

            ],
            options={'temperature': 0} # ensures that the LLM will use more likely words, helps outputs to stay sounding professional
            )
            

            raw_content = result['message']['content']
            #ensures that JSON findings are converted into a string to be shown on webpage in a text format
            start = raw_content.find('{')
            end = raw_content.rfind('}') +1

            if start != -1 and end > start:
                json_str = raw_content[start:end]
                extracted_info = json.loads(json_str)
            else:
                self.logger.warning("Ollama did not return a JSON block. Using defaults.")
                extracted_info = {"course_title": "N/A", "staff_names": []}
        

        except Exception as e:
            self.logger.error(f"Ollama extraction failed: {e}")
            
            extracted_info = {
                "course_title": "BSc Computer Science", "staff_names": []
            }

        yield {
            'type': 'course_summary',
            'url': response.url,
            'extracted_staff': extracted_info.get('staff_names', []),
            'links_found': len(correct_links)
        }

        for link in correct_links:
            yield response.follow(
                link, 
                callback=self.parse_staff_profile
            )

       

    def parse_staff_profile(self, response): #method to extract profile information

        extracted_info = { #definition of all information needed to be extracted for email generation
            'type': 'staff_profile',
            'url': response.url,
            'name': response.css('h1::text').get() or response.css('title::text').get(),
            'job_title': None, 
            'email': None,
            'phone': None,
            'research interests': [],
            'qualifications': []
        }



        page_text = ' '.join(response.css('body *::text').getall())
        page_text = ' '.join(page_text.split())[:4000]


        try:
            result = ollama.chat( #call for LLM to find specified information within each staff profile field and produce JSON findings
                model='llama3.2:1b',
                messages=[{
                    'role': 'user',
                    'content': f"""Extract the following information from staff profile page and return ONLY valid JSON with these exact keys:
- name (string)
- job_name (string)
- email (string)
- phone (string)
- research_interests (array of strings)
- qualifications (array of strings)

If a field cannot be found, use null. Return ONLY the JSON, no other text.

Page content:
{page_text}"""

                }]
            )

            response_info = result['message']['content']

            if '```json' in response_info:
                response_info = response_info.split('```json')[1].split('```')[0]
            elif '```' in response_info:
                response_info = response_info.split('```')[1].split('```')[0]


            ollama_data= json.loads(response_info.strip())
            extracted_info.update(ollama_data)

        except Exception as e:
            self.logger.error(f"Ollama extraction failed: {e}")
            self.logger.error(f"Full error details: ", exc_info=True)
            extracted = {
                'type': 'staff_profile',
                'url': response.url,
                'name': response.css('h1::text').get(),
                'error': str(e)
            }

        extracted_info['external_links'] = {}

        all_links = response.css('a::attr(href)').getall() #finds all external links for each staff member and provides the links on the site
        for link in all_links:                             #this is done manually rather than through LLM use
            if not link:
                continue
            link_lower = link.lower()

            if 'linkedin.com/in/' in link_lower:
                extracted_info['external_links']['linkedin']=link
            elif 'twitter.com' in link_lower or 'x.com' in link_lower:
                extracted_info['external_links']['X'] =link
            elif 'github.com' in link_lower:
                extracted_info['external_links']['github']=link
            elif 'orcid.org' in link_lower:
                extracted_info['external_links']['orcid']=link
            elif 'scholar.google' in link_lower:
                extracted_info['external_links']['google_scholar']=link

        yield extracted_info