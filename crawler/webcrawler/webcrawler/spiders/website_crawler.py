from scrapy.spiders import Spider
from scrapy.linkextractors import LinkExtractor
import re
import json

class UniWebCrawler(Spider):
    name = "project_crawler_ollama"
    allowed_domains = ["brighton.ac.uk", "research.brighton.ac.uk"]
    start_urls = ["https://www.brighton.ac.uk/courses/study/computer-science-with-cyber-security-bsc-hons.aspx"]

  

    custom_settings = {
        'DOWNLOAD_DELAY': 2, # leaves 2 seconds between requests to webpage
        'CONCURRENT_REQUESTS': 1, # ensures only 1 request happens at a time
        'ROBOTSTXT_OBEY': True, # ensures crawler respects robots.txt
        'USER_AGENT': 'UniversityOfBrightonFinalProject/1.0 (Final Year Project; c.deretuerto1@uni.brighton.ac.uk)' # declares bot purpose and origin to site
    }

    

    def parse(self, response):

        import ollama #integration of ollama framework to find information from any course page
        import json

        team_section = response.css('div.sys_span8')

        if not team_section:
            team_section = response.css('main')

        page_text = ' '.join(team_section.css('*::text').getall())
        cleaned_page_text = ' '.join(page_text.split())[:3000]

        profile_links = team_section.css('a::attr(href)').getall()

        correct_links = []
        for link in profile_links:
            full_url = response.urljoin(link)

            if "persons" in full_url or "research.brighton.ac.uk" in full_url:
                correct_links.append(full_url)

        correct_links = list(set(correct_links))

        try:
            result = ollama.chat(
            model = 'llama3.2:1b',
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a data extractor. Return ONLY valid JSON.'
                },
                {
                    'role': 'user',
                    'content': f"Extract staff names from this HTML text and return as JSON with keys 'course_title' and 'staff_names' (array):\n\n{cleaned_page_text}"
                }

            ],
            options={'temperature': 0}
            )
            

            raw_content = result['message']['content']

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

        yield course_information

    def parse_staff_profile(self, response): #method to extract profile information

        import ollama


        page_text = ' '.join(response.css('body *::text').getall())
        page_text = ' '.join(page_text.split())[:4000]


        try:
            result = ollama.chat(
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

            extracted_info = json.loads(response_info.strip())
            extracted_info['type'] = 'staff_profile'
            extracted_info['url'] = response.url

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

        all_links = response.css('a::attr(href)').getall()
        for link in all_links:
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