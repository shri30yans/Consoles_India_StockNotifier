from selenium import webdriver
import time
import sys

print( 'Without Headless')
_start = time.time()
br = webdriver.PhantomJS()
br.get('https://www.amazon.in/dp/B08FV5GC28')
br.save_screenshot('screenshot-phantom.png')
br.quit
_end = time.time()
print ('Total time for non-headless {}'.format(_end - _start))