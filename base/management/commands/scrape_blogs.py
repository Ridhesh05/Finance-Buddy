# your_app/management/commands/scrape_blogs.py

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from ...models import Blog

class Command(BaseCommand):
    help = 'Scrape blog data from the website'

    def handle(self, *args, **kwargs):
        url = 'https://1finance.co.in/blog/'
        response = requests.get(url)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            titles = soup.find_all(class_='card-title')
            links = soup.find_all(class_='blog-link')
            
            if titles and links:
                for title, link in zip(titles, links):
                    blog_title = title.get_text(strip=True)
                    blog_link = link.get('href')
                    
                    Blog.objects.create(title=blog_title, link=blog_link)
                    self.stdout.write(self.style.SUCCESS(f'Added blog: {blog_title}'))
            else:
                self.stdout.write(self.style.WARNING('No titles or links found.'))
        else:
            self.stdout.write(self.style.ERROR('Failed to retrieve the webpage.'))
