from selenium import webdriver  
from concurrent import futures

def selenium_title(url):  
  wdriver = webdriver.Chrome() # chrome webdriver
  wdriver.get(url)  
  title = wdriver.title  
  wdriver.quit()
  return title

links = ["https://www.amazon.com", "https://www.google.com"]

if __name__ == '__main__':
  with futures.ProcessPoolExecutor() as executor: # default/optimized number of threads
    titles = list(executor.map(selenium_title, links))
  print(titles)