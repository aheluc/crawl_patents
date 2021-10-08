import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sqlite3

with open('./config.json', encoding='utf-8') as file:
    config = json.load(file)

login_url = 'https://cprs.patentstar.com.cn/Account/LoginOut'

chrome_options = Options()
if not config['browser_visible']:
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=chrome_options)

patent_count = 0

def click_and_wait(element):
    element.click()
    driver.implicitly_wait(0.01)
    WebDriverWait(driver,10).until_not(EC.presence_of_element_located((By.XPATH,'//div[@class="layui-layer-shade"]')))

# 登录
def login():
    driver.get(login_url)
    username = driver.find_elements_by_xpath("//input[@type='text']")[0]
    username.send_keys(config['username'])
    password = driver.find_elements_by_xpath("//input[@type='password']")[0]
    password.send_keys(config['password'])
    login_button = driver.find_elements_by_xpath("//button[@type='submit']")[0]
    click_and_wait(login_button)
    driver.implicitly_wait(2)

def visit_current_page(conn, cursor):
    patent_abstracts = driver.find_elements_by_xpath("//div[@class='patent-content']//div[@class='p3']//span")
    patent_abstracts = [abstract.text for abstract in patent_abstracts]
    links = driver.find_elements_by_xpath("//div[@class='patent']//label[@class='title-color']")
    patent_ids = []
    patent_contents = []
    SQL = 'INSERT INTO CRAWLED_PATENTS(PATENT_ID, ARTICLE, ABSTRACT) VALUES(?, ?, ?)'
    for link in links:
        click_and_wait(link)
        windows = driver.window_handles
        driver.switch_to.window(windows[-1])
        patent_id = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='item-content fl']//span")))
        patent_ids.append(patent_id.text.strip())
        intro = driver.find_elements_by_xpath("//p[@class='fmxx' and @data-name='itemIntro']")[0]
        click_and_wait(intro)
        driver.implicitly_wait(0.1)
        content = driver.find_elements_by_xpath("//disclosure//p")
        content = ''.join([block.text for block in content[1:]])
        patent_contents.append(content)
        driver.close()
        driver.implicitly_wait(0.1)
        windows = driver.window_handles
        driver.switch_to.window(windows[-1])
    cursor.executemany(SQL, list(zip(patent_ids, patent_contents, patent_abstracts)))
    conn.commit()
    next_page = driver.find_elements_by_xpath("//a[@class='nextPage']")[0]
    click_and_wait(next_page)

def visit_current_genre(conn, cursor, patent_count):
    max_page = driver.find_elements_by_xpath("//span[@class='allcountlab']")[0]
    max_page = int(int(max_page.text) / 15) - 1
    max_check_page = min(config['max_check_pages'], max_page)
    for i in range(max_check_page):
        visit_current_page(conn, cursor)
        patent_count += 15
        print('{} data has been saved'.format(patent_count))
    return patent_count

def visit(conn, cursor, patent_count):
    patent_count = visit_current_genre(conn, cursor, patent_count)
    for genre in config['genres'][1:]:
        search_bar = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="searchtext"]')))
        search_bar.clear()
        search_bar.send_keys(genre)
        re_search = driver.find_elements_by_xpath("//a[@id='searchbtn']")[0]
        click_and_wait(re_search)
        patent_count = visit_current_genre(conn, cursor, patent_count)

login()

search_bar = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//input[@name="patent_search"]')))
search_bar.send_keys(config['genres'][0])
search_button = driver.find_elements_by_xpath("//a[@class='search_btn']")[0]
search_button.click()

patent_type = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//ul[@id="patent-type"]')))
patent_type.find_elements_by_xpath("//li[@data-type='one']")[0].click()

patent_state = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//ul[@id="patent-lg"]')))
patent_state.find_elements_by_xpath("//li[@data-type='one' and @data-name='US']")[0].click()

filter_button = WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,'//p[@id="filterbtn"]')))
click_and_wait(filter_button)

count_filter = driver.find_elements_by_xpath('//div[@id="filter-box2"]//div[@class="filter-text"]')[0]
count_filter.click()
page_15 = driver.find_elements_by_xpath('//li[@data-value="15"]//a')[0]
click_and_wait(page_15)

with sqlite3.connect('Patents.db') as conn:
    cursor = conn.cursor()
    visit(conn, cursor, patent_count)


