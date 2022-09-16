from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
import time
import threading
from concurrent import futures
import sys

links = ["https://www.amazon.com", "https://www.google.com", "https://www.youtube.com/", "https://www.facebook.com/", "https://www.wikipedia.org/", 
"https://us.yahoo.com/?p=us", "https://www.instagram.com/", "https://www.globo.com/", "https://outlook.live.com/owa/"]

def create_driver():
  """returns a chrome webdriver headless"""
  coptions = webdriver.ChromeOptions()
  coptions.add_argument("log-level=3")
  coptions.add_argument("--headless") # make it not visible
  return webdriver.Chrome(options=coptions)  

def try_click_nrandom_links(driver, nclick=2, maxlinks=10):
  """'try' to click-walk on `n` 'random' link on the opened page"""  
  if nclick:        
    elements = wait(driver, 3).until(EC.presence_of_all_elements_located(
      (By.XPATH, "//a[starts-with(@href,'http')]")))        
    for element in elements[:maxlinks]: # to avoid long lists of links
        try:                
            element.click()                            
        except: # not a link, try next 
            continue 
        else: # found a clickable link stop
            break        
    time.sleep(1)
    print('url is :', driver.current_url, file=sys.stderr)        
    try_click_nrandom_links(driver, nclick-1)
  
def selenium_work(url):  
  """get the url than 'try' click-walk for n 
  links starting from this page and getting its title 
  """
  webdriver = create_driver()
  webdriver.get(url)
  try_click_nrandom_links(webdriver) # try to click-walk through pages from 'random' links
  time.sleep(1)
  webdriver.quit()

def main_poolthreads(): 

  start_time = time.time() 
 
  # default number of threads is optimized for cpu cores 
  # but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
  with futures.ThreadPoolExecutor(max_workers=6) as executor: # Pool of threads
    # store the url for each thread as a dict, so we can know which thread (if it fails)
    future_results = { executor.submit(selenium_work, link)  : link for link in links }
    for future, url in future_results.items(): 
      try:        
        future.result() # can use `timeout` to wait max seconds for each thread               
      except Exception as exc: # can give a exception in some thread
        print('url {} generated an exception: {}'.format(url, exc))
  
  return (time.time() - start_time)

def main_poolprocesses(): 

  start_time = time.time() 
 
  # default number of threads is optimized for cpu cores 
  # but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
  with futures.ProcessPoolExecutor(max_workers=6) as executor: # Pool of threads
    # store the url for each thread as a dict, so we can know which thread (if it fails)
    future_results = { executor.submit(selenium_work, link)  : link for link in links }
    for future, url in future_results.items(): 
      try:        
        future.result() # can use `timeout` to wait max seconds for each thread               
      except Exception as exc: # can give a exception in some thread
        print('url {} generated an exception: {}'.format(url, exc))
  
  return (time.time() - start_time)


def main_poolthreads_local(): 
 
  # threadPool with local chrome-driver already initialized
  threadLocal = threading.local()

  def get_driver():
    """usage with ThreadPoolExecutor 
    using thread local data storage to save an initialized webdriver
    faster than initialize a webdriver each new time"""
    driver = getattr(threadLocal, 'driver', None)
    if driver is None: # first time create the driver
        driver = create_driver()
        threadLocal.driver = driver
    return driver

  def selenium_work(url):  
    """get the url than 'try' click-walk for n 
  links starting from this page and getting its title 
    """
    webdriver = get_driver()
    webdriver.get(url)
    try_click_nrandom_links(webdriver) # try to click-walk through pages from 'random' links
    time.sleep(1)
    #webdriver.quit() # will be killed after

  start_time = time.time() 
 
  # default number of threads is optimized for cpu cores 
  # but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
  with futures.ThreadPoolExecutor(max_workers=6) as executor: # Pool of threads
    # store the url for each thread as a dict, so we can know which thread fails
    future_results = { executor.submit(selenium_work, link)  : link for link in links }
    for future, url in future_results.items(): 
      try:        
        future.result() # can use `timeout` to wait max seconds for each thread               
      except Exception as exc: # can give a exception in some thread
        print('url {} generated an exception: {}'.format(url, exc))
  
  return (time.time() - start_time)


def main_sequentially():

  start_time = time.time()  
  webdriver = create_driver()

  def selenium_work(url):  
    """get the url than 'try': click-walk for n 'random'
    links getting the title for each page"""
    webdriver.get(url)
    try_click_nrandom_links(webdriver) # try to click-walk through pages from 'random' links
    time.sleep(1)

  for link in links: # simulation clicks 
    selenium_work(link)  

  webdriver.quit()
  return (time.time() - start_time)


if __name__ == '__main__':

  #links = links

  seq_time = main_sequentially()
  pproc_time = main_poolprocesses()
  pot_time = main_poolthreads()
  potl_time = main_poolthreads_local()  

  print("sequential {:0} seconds ---".format(seq_time))
  print("poolprocesses {:0} seconds ---".format(pproc_time))
  print("poolthreads {:0} seconds ---".format(pot_time))
  print("poolthreads_local {:0} seconds ---".format(potl_time))  




