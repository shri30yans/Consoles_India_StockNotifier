#coding=utf-8                                                                                                                                                                              
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = webdriver.ChromeOptions()
options.headless = True
driver = webdriver.Chrome(options=options)
driver.set_window_size(1800,900)
print("now")
URL = "https://www.amazon.in/dp/B08FV5GC28"

driver.get(URL)

driver.get_screenshot_as_file("ss.png")

driver.quit()
