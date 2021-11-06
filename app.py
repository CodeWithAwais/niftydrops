import os
import json
import schedule
import aiohttp
import asyncio
import discord
from discord.webhook import AsyncWebhookAdapter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from scrapy.selector import Selector
from tqdm import tqdm
from time import sleep


global upcoming_links_list
global all_links
upcoming_links_list = []
all_links = []
def scraper():
    # setting-up browser profile
    firefox_profile = webdriver.FirefoxProfile()
    firefox_profile.set_preference("browser.privatebrowsing.autostart", True)

    # setting-up browser options
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("prefs", {
        "profile.default_conent_settings_values.notifications": 1
    })

    # executing chrome-driver
    driver = webdriver.Chrome(executable_path=r'chromedriver', options=options, service_args=["--log-path=log.txt"])

    def write_to_json(file_name, json_data):
        json_file = open(file_name, 'w')
        json_file.write(json.dumps(json_data, indent=2))
        json_file.close()

    async def send_webhook():
        upcoming_links_list.clear()
        print(upcoming_links_list)
        driver.get('https://niftydrops.io/upcoming')

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "/drop/")]'))
        )

        resp = Selector(text=driver.page_source)
        upcoming = resp.xpath('//a[contains(@href, "/drop/")]')
        for each in upcoming:
            link = each.xpath('.//@href').get()
            if link in all_links:
                print('Already scraped, moving to the next one...')
                continue
            upcoming_links_list.append(link)
            all_links.append(link)

        print(upcoming_links_list)
        if upcoming_links_list == []:
            print('There are no new links...')
        for each_link in tqdm(upcoming_links_list[:3]):
            driver.get(f'https://niftydrops.io{each_link}')
            unique_file_name = driver.current_url.split('/drop/')[-1]
            
            try:
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="titles"]'))
                )
            except Exception:
                driver.refresh()
            
            response = Selector(text=driver.page_source)
            
            title = response.xpath('//div[@class="titles"]/h2/text()').get()
            description = response.xpath('normalize-space(//div[@class="content-text"]/p)').get()
            author_name = response.xpath('normalize-space(//div[@class="titles"]/h5)').get()
            image_url = response.xpath('//div[@class="image-container"]/img/@src').get()
            blockchain_value = response.xpath('normalize-space(//strong[contains(text(), "Blockchain:")]/following-sibling::text())').get()
            total_supply_value = response.xpath('normalize-space(//strong[contains(text(), "Total supply:")]/following-sibling::text())').get()
            mint_price = response.xpath('normalize-space(//strong[contains(text(), "Mint price:")]/following-sibling::text())').get()
            discord_ = response.xpath('//div[@class="social-links"]/a[contains(@href, "discord")]/@href').get()
            twitter = response.xpath('//div[@class="social-links"]/a[contains(@href, "twitter")]/@href').get()
            
            data = {
                "content": "",
                "embeds": [
                    {
                        "title": title,
                        "color": 15810082,
                        "description": description,
                        "timestamp": "",
                        "author": {
                            "name": author_name,
                        },
                        "image": {
                            "url": image_url,
                        },
                        "thumbnail": {
                            "profile_url": f'{twitter}/photo'
                        },
                        "footer": {
                            "text": "Nifty NFTs | #1Discord NFT Information Provider",
                            "icon_url": "https://media.discordapp.net/attachments/896526829152776222/896526902783791104/Nifty_Logo.png?width=676&height=676"
                        },
                        "fields": [
                            {
                            "name": "**BLOCKCHAIN**",
                            "value": blockchain_value,
                            "inline": True
                            },
                            {
                            "name": "**TOTAL SUPPLY**",
                            "value": total_supply_value,
                            "inline": True
                            },
                            {
                            "name": "**MINT PRICE**",
                            "value": mint_price,
                            "inline": True
                            },
                            {
                            "name": "More Information",
                            "value": f'''[Discord]({discord_}) | [Twitter]({twitter})'''
                            }
                        ],
                    },
                ],
                "components": []
            }
            
            if data.get('embeds')[0].get('fields')[2].get('value') == '':
                del data.get('embeds')[0].get('fields')[2]
            if data.get('embeds')[0].get('fields')[1].get('value') == '':
                del data.get('embeds')[0].get('fields')[1]
            if data.get('embeds')[0].get('fields')[0].get('value') == '':
                del data.get('embeds')[0].get('fields')[0]
            
            write_to_json(os.path.join('json_files', f'{unique_file_name}.json'), data)
            print(data)
                
            try:
                embed_date = data.get('embeds')[0].get('author').get('name')
            except:
                embed_date = 'N/A'
            try:
                embed_title = data.get('embeds')[0].get('title')
            except:
                embed_title = 'N/A'
            try:
                embed_description = data.get('embeds')[0].get('description')
            except:
                embed_description = 'N/A'
            try:
                embed_footer_text = data.get('embeds')[0].get('footer').get('text')
            except:
                embed_footer_text = 'N/A'
            try:
                embed_footer_icon_url = data.get('embeds')[0].get('footer').get('icon_url')
            except:
                embed_footer_icon_url = 'N/A'
            try:
                embed_main_image = data.get('embeds')[0].get('image').get('url')
            except:
                embed_main_image = 'N/A'
            try:
                embed_field_1_name = data.get('embeds')[0].get('fields')[0].get('name')
            except:
                embed_field_1_name = 'N/A'
            try:
                embed_field_1_value = data.get('embeds')[0].get('fields')[0].get('value')
            except:
                embed_field_1_value = 'N/A'
            try:
                embed_field_2_name = data.get('embeds')[0].get('fields')[1].get('name')
            except:
                embed_field_2_name = 'N/A'
            try:
                embed_field_2_value = data.get('embeds')[0].get('fields')[1].get('value')
            except:
                embed_field_2_value = 'N/A'
            try:
                embed_field_3_name = data.get('embeds')[0].get('fields')[2].get('name')
            except:
                embed_field_3_name = 'N/A'
            try:
                embed_field_3_value = data.get('embeds')[0].get('fields')[2].get('value')
            except:
                embed_field_3_value = 'N/A'
            try:
                embed_social_name = data.get('embeds')[0].get('fields')[3].get('name')
            except:
                embed_social_name = 'N/A'
            try:
                embed_social_value = data.get('embeds')[0].get('fields')[3].get('value')
            except:
                embed_social_value = 'N/A'


            webhook_url = 'https://discord.com/api/webhooks/897668619121590323/OrH8o_E5Sfapk4j7-EZ0Byi9Fp-YDVT9gUMY-ppYs6MXuENGi19mGDF2enxyqswcSds0'
            
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                f"{webhook_url}", adapter=AsyncWebhookAdapter(session))
                
                embed = discord.Embed(
                    title = embed_title,
                    description = embed_description,
                    colour = discord.Colour.blue(),
                )
                embed.set_footer(text=embed_footer_text, icon_url=embed_footer_icon_url)
                embed.set_image(url=embed_main_image)
                embed.set_author(name=embed_date)
                embed.add_field(name=embed_field_1_name, value=embed_field_1_value, inline=True)
                embed.add_field(name=embed_field_2_name, value=embed_field_2_value, inline=True)
                embed.add_field(name=embed_field_3_name, value=embed_field_3_value, inline=True)
                embed.add_field(name=embed_social_name, value=embed_social_value, inline=False) 

                await webhook.send(embed=embed)

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(send_webhook())
            
    driver.close()
    
    
# schedule.every().day.at("05:00").do(scraper)
schedule.every(5).minutes.do(scraper)

while True:
    schedule.run_pending()
    sleep(1)