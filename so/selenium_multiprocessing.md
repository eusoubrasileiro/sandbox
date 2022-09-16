https://stackoverflow.com/questions/42732958/python-parallel-execution-with-selenium?noredirect=1&lq=1

1. **[Python Parallel Wd][1]** seams to be dead from its github (last commit 9 years ago). Also it implements an [obsolete protocol][2] for selenium. Still I haven't tested it I wouldn't recommend.

## Selenium Performance Boost ([concurrent.futures][3])

### Short Answer

 - **Both `threads` and `processes` will give you a *considerable speed up* on your *selenium code*.** 

Short examples are given bellow. The selenium work is done by `selenium_title` function that return the page title. They don't deal with exceptions happenning during each thread/process execution. For that look at *Long Answer* - *Dealing with exceptions*.

1.  Pool of thread workers [`concurrent.futures.ThreadPoolExecutor`][4]. 

```
from selenium import webdriver  
from concurrent import futures

def selenium_title(url):  
  wdriver = webdriver.Chrome() # chrome webdriver
  wdriver.get(url)  
  title = wdriver.title  
  wdriver.quit()
  return title

links = ["https://www.amazon.com", "https://www.google.com"]

with futures.ThreadPoolExecutor() as executor: # default/optimized number of threads
  titles = list(executor.map(selenium_title, links))
```

 2. Pool of processes workers  [`concurrent.futures.ProcessPoolExecutor`][5]. Just need to replace `ThreadPoolExecuter` by `ProcessPoolExecutor` in the code above. They are both derived from the `Executor`base class. Also you **must** protect the *main*, like below.

 ```
 if __name__ == '__main__':
  with futures.ProcessPoolExecutor() as executor: # default/optimized number of processes
    titles = list(executor.map(selenium_title, links))
 ```

### Long Answer

#### Why `Threads` with Python GIL works?

Even tough Python has limitations on threads due the Python GIL and even though threads will be context switched. Performance gain will come due to implementation details of Selenium. Selenium works by sending commands like `POST`, `GET` (`HTTP requests`). Those are sent to the browser driver server. Consequently you might already know I/O bound tasks (`HTTP requests`) releases the GIL, so the performance gain. 

#### Dealing with exceptions

We can make small modifications on the example above to deal with `Exceptions` on the threads spawned. Instead of using `executor.map` we use `executor.submit`. That will return the title wrapped on `Future` instances. 

To access the returned title we can use `future_titles[index].result` where index size `len(links)`, or simple use a `for` like bellow.

```
with futures.ThreadPoolExecutor() as executor:
  future_titles = [ executor.submit(selenium_title, link) for link in links ]
  for future_title, link in zip(future_titles, links): 
    try:        
      title = future_title.result() # can use `timeout` to wait max seconds for each thread               
    except Exception as exc: # this thread migh have had an exception
      print('url {:0} generated an exception: {:1}'.format(link, exc))
```

Note that besides iteration over `future_titles` we iterate over `links` so in case an `Exception` in some thread  we know which url(link) was responsible for it.

The `futures.Future` class are cool because they give you control on the results received from each thread. Like if it completed correctly or there was an exception and others, more about [here][6]. 

Also important to mention is that [`futures.as_completed`][7] is better if you don´t care which order the threads return itens. But since the syntax to control exceptions with that is a little ugly so I omitted it here.

#### Performance gain and Threads

First why I've been allways using threads for speeding up my selenium code:
  - On I/O bound tasks my experience with selenium shows that there's [minimal or no diference][8] between using a pool of Processes (`Process`) or Threads (`Threads`). [Here][9] also reach similar conclusions about Python threads vs processes on I/O bound tasks. 
  - We also know that processes use their own memory space. That means more memmory usage with more processes. Also processes are a little slower to be spawned than threads.
  
**Sequential approach**

Let's exemplify comparing both to the sequential approach.

 Sorry, for long code bellow. I tried but couldn't make it smaller. 

The code bellows **simple saying** **does some** work with selenium **(`selenium_work`)** from a list of url's. For that it uses a pool 6 worker threads each has its own web-driver instance. More detailed bellow:

 - For each url on a list called `links` it calls `selenium_work` function. 
 - `selenium_work` creates a chrome-webdriver calling `create_driver`. 
 - With the created `webdriver` it opens the given `url`.
 - On that it 'tries' (`try: block`) to click-walk on 2 random links (`try_click_nrandom_links`). That is first it finds a link click on it and on the next page opened it does the same.  

```
links = ["https://www.amazon.com", "https://www.google.com", "https://www.youtube.com/", "https://www.facebook.com/", "https://www.wikipedia.org/", 
"https://us.yahoo.com/?p=us", "https://www.instagram.com/", "https://www.globo.com/", "https://outlook.live.com/owa/"]

def create_driver():
  """returns a chrome webdriver headless"""
  chromeOptions = webdriver.ChromeOptions()
  chromeOptions.add_argument("--headless") # make it not visible
  return webdriver.Chrome(options=chromeOptions)  

def print_title(driver, url):
  driver.get(url)
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
```


```
from selenium import webdriver  
from concurrent import futures

def selenium_work(url):  
  webdriver = create_driver() # your function to create an instance of your webdriver
  webdriver.get(url)
  # <your selenium code work here>

# default number of threads is optimized for cpu cores 
# but you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=...)`
with futures.ThreadPoolExecutor() as executor: # Pool of threads
  # store the url for each thread as a dict, so we can know which thread (if it fails)
  future_results = { executor.submit(selenium_work, link)  : link for link in links }
  for future, url in future_results.items(): 
    try:        
      future.result() # can use `timeout` to wait max seconds for each thread               
    except Exception as exc: # can give a exception in some thread
      print('url {} generated an exception: {}'.format(url, exc))
```

Also worth to mention that the default number of threads is optimized on cpu cores. But you can set with `max_workers` like `futures.ThreadPoolExecutor(max_workers=4)`


  

  [1]: https://github.com/OniOni/python-parallel-wd
  [2]: https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol
  [3]: https://docs.python.org/3/library/concurrent.futures.html
  [4]: https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
  [5]: https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor  
  [6]: https://docs.python.org/3/library/concurrent.futures.html#future-objects
  [7]: https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.as_completed
  [8]: https://stackoverflow.com/a/68997963/1207193
  [9]: https://stackoverflow.com/a/55319297/1207193
  
  
  
  