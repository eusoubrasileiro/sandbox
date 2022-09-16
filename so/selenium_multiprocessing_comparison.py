import time
from bs4 import BeautifulSoup
from selenium import webdriver
import threading, multiprocessing 

links = ["https://www.amazon.com", "https://www.google.com", "https://www.youtube.com/", "https://www.facebook.com/", "https://www.wikipedia.org/", 
"https://us.yahoo.com/?p=us", "https://www.instagram.com/", "https://www.globo.com/", "https://outlook.live.com/owa/"]

def create_driver():
  """returns a chrome webdriver headless"""
  chromeOptions = webdriver.ChromeOptions()
  chromeOptions.add_argument("--headless") # make it not visible
  return webdriver.Chrome(options=chromeOptions)  

def try_click_random_link(driver):
  """try to click on a random link on the opened page"""
  try:     
    elements = driver.find_elements_by_tag_name('a:link')  
    element = elements[len(elements)//3] # try being more deterministic for threads/process
    element.click()
  except:
    pass

def print_title(driver, url):
  driver.get(url)
  #[ try_click_random_link(driver) for i in range(8) ] # try to click-walk through 8 pages on random found links
  soup = BeautifulSoup(driver.page_source,"lxml")
  item = soup.find('title')
  print(item.string.strip())   

def get_title(url, webdriver=None):  
  """get the url html title using BeautifulSoup 
  if driver is None uses a new chrome-driver and quit() after
  otherwise uses the driver provided and don't quit() after
  """
  if webdriver:
    print_title(webdriver, url)  
  else: 
    webdriver = create_driver()
    print_title(webdriver, url)   
    webdriver.quit()

def main_sequentially():
  start_time = time.time()
  driver = create_driver()

  for link in links: # simulation clicks 
    get_title(link, driver)  

  driver.quit()
  return (time.time() - start_time)

def main_threads():
  start_time = time.time() 

  threads = [] 
  for link in links: # each thread a new 'click' 
      th = threading.Thread(target=get_title, args=(link,))    
      th.start() # could sleep 1 between 'clicks' with `time.sleep(1)``
      threads.append(th)        
  for th in threads:
      th.join() # Main thread wait for threads finish

  return (time.time() - start_time)

def main_multiprocessing():
  start_time = time.time() 

  processes = [] 
  for link in links: # each thread a new 'click' 
      ps = multiprocessing.Process(target=get_title, args=(link,))    
      ps.start() # could sleep 1 between 'clicks' with `time.sleep(1)``
      processes.append(ps)        
  for ps in processes:
      ps.join() # Main wait for processes finish

  return (time.time() - start_time)

def run_nget_times():
  """only for statistical measuraments - using this as a module"""
  return main_sequentially(), main_threads(), main_multiprocessing()


from concurrent import futures

def main_poolthreads(): 

  start_time = time.time() 
 
  # default number of threads is optimized for cpu cores 
  # but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
  with futures.ThreadPoolExecutor() as executor: # Pool of threads
    # store the url for each thread as a dict, so we can know which thread (if it fails)
    future_results = { executor.submit(get_title, link)  : link for link in links }
    for future, url in future_results.items(): 
      try:        
        future.result() # can use `timeout` to wait max seconds for each thread               
      except Exception as exc: # can give a exception in some thread
        print('url {:0} generated an exception: {:1}'.format(url, exc))
  
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

  def print_title(driver, url):
    driver.get(url)
    #[ try_click_random_link(driver) for i in range(8) ] # try to click-walk through 8 pages on random found links
    soup = BeautifulSoup(driver.page_source,"lxml")
    item = soup.find('title')
    print(item.string.strip())  

  start_time = time.time() 

  def get_title_pool(url):
    webdriver = get_driver()
    print_title(webdriver, url)   
    #return webdriver # driver will remain open, will be killed auto after 

  # default number of threads is optimized for cpu cores 
  # but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
  with futures.ThreadPoolExecutor() as executor: # Pool of 6 threads
    # store the url for each thread as a dict, so we can know which thread fails
    future_results = { executor.submit(get_title_pool, link)  : link for link in links }
    for future, url in future_results.items(): 
      try:        
        future.result() # can use `timeout` to wait max seconds for each thread               
      except Exception as exc: # can give a exception in some thread
        print('url {:0} generated an exception: {:1}'.format(url, exc))
  
  return (time.time() - start_time)

if __name__ == '__main__':

  seq_time = main_sequentially()  
  th_time = main_threads()
  #ps_time = main_multiprocessing()  
  pe_time = main_poolthreads()
  
  print("sequential {:0} seconds ---".format(seq_time))
  print("multithreads(12) {:0} seconds ---".format(th_time))
  #print("multiprocessing(12) {:0} seconds ---".format(ps_time))
  print("poolthreads(6) {:1} seconds ---".format(pe_time))

