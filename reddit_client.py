import time,requests, time
from urllib.parse   import urljoin
from requests.auth  import HTTPBasicAuth
from multimethod    import multimethod
from alive_progress import alive_bar 

class Reddit_Client(requests.Session):
    def __init__(self, username:str, password:str, client_ID:str, client_secret:str ) -> None:
        super().__init__()
        self.base_url       = 'https://ssl.reddit.com/api/v1/'
        self.username       = username
        self.password       = password
        self.client_secret  = client_secret
        self.client_ID      = client_ID
        self.access_token   = self.post(
            'access_token',
            data = {
                'grant_type': 'password',
                'username': self.username ,
                'password': self.password
            },
            auth = HTTPBasicAuth(
                self.client_ID, 
                self.client_secret
            )).json()['access_token']
        self.headers = ({
            'Authorization' : f'bearer {self.access_token}'
        })
        if self.access_token :
            self.base_url = 'https://oauth.reddit.com/'
    
        def rate_hook(r, *args, **kwargs):
            if("x-ratelimit-remaining" in r.headers):
                if float(r.headers['x-ratelimit-remaining']) < 100 : 
                    print("rate limit: ", r.headers["x-ratelimit-remaining"], " - " , r.status_code ) 
                elif float(r.headers['x-ratelimit-remaining']) <= 0 :
                    print(f"{r.headers['x-ratelimit-reset']}")
                    time.sleep(int(float(r.headers["x-ratelimit-reset"]))) 
            if(r.status_code == 429):
                print("TOO-MANY-REQUESTS")   
                time.sleep(1)     
    
        self.hooks["response"].append(rate_hook)
        
    def request(self, method, endpoint, *args, **kwargs):
        return super().request(method, urljoin(self.base_url, endpoint), *args, **kwargs)
    
    def get_me(self) -> str:
        endpoint = "api/v1/me"
        return self.get(endpoint)
    
    def get_user_overview(self, username:str) -> str:
        endpoint    = f"user/{username}/overview?limit=100"
        result      = self.get(endpoint)
        return result
    
    @multimethod
    def get_user_comments(self, username:str) -> str:
        endpoint    = f"user/{username}/comments?limit=50"
        result      = self.get(endpoint)
        return result
    @multimethod
    def get_user_comments(self, username:str, limit:int) -> str:
        endpoint    = f"user/{username}/comments?limit=100" if limit >= 100 else f"user/{username}/comments?limit={limit}"
        results     = []
        results     += self.get(endpoint).json()['data']['children'] 
        remaining_limit   = limit - len(results) 
        with alive_bar(bar='brackets', unknown='classic') as bar:
            while remaining_limit > 0 :
                if remaining_limit > 100:
                    remaining_limit = limit - len(results) 
                    results         += self.get(f"user/{username}/comments?limit=100&after=t1_{results[-1]['data']['id']}").json()['data']['children']  
                    if remaining_limit == limit - len(results) : 
                        break  
                else:
                    results += self.get(f"user/{username}/comments?limit={remaining_limit}&after=t1_{results[-1]['data']['id']}").json()['data']['children']  
                    bar()
                    break
                bar()   
        return results
    
    def get_user_submitted(self, username:str) -> str:
        endpoint    = f"user/{username}/submitted?limit=50"
        result      = self.get(endpoint)
        return result
    
    def get_subreddit_post(function):
        def get_subreddit_posts_base(self, subreddit:str, limit:int):
            endpoint        = function(subreddit, limit)
            results         = []
            results         += self.get(endpoint).json()['data']['children']    
            remaining_limit = limit - len(results) 
            with alive_bar(bar='brackets', unknown='classic') as bar:
                while remaining_limit > 0 :
                    # rate limits
                    time.sleep(1) 
                    if remaining_limit > 100:
                        remaining_limit = limit - len(results) 
                        results         += self.get(f"{endpoint}&after=t3_{results[-1]['data']['id']}").json()['data']['children']  
                        # check if results changed after call - reached limit
                        if remaining_limit == limit - len(results) : 
                            bar()
                            break     
                    else:
                        results += self.get(f"{endpoint}&after=t3_{results[-1]['data']['id']}").json()['data']['children']  
                        bar() 
                        break
                    bar()
            return results
        return get_subreddit_posts_base
        
    @get_subreddit_post
    def get_subreddit_posts(subreddit:str, limit:int):
        return f"r/{subreddit}?limit=100" if limit >= 100 else f"r/{subreddit}?limit={limit}"
    
    @get_subreddit_post
    def get_subreddit_posts_controversial(subreddit:str, limit:int):
        return f"r/{subreddit}/controversial?limit=100" if limit >= 100 else f"r/{subreddit}/controversial?limit={limit}"
    
    @get_subreddit_post
    def get_subreddit_posts_top(subreddit:str, limit:int):
        return f"r/{subreddit}/top?limit=100" if limit >= 100 else f"r/{subreddit}/top?limit={limit}"
    
    @get_subreddit_post
    def get_subreddit_posts_new(subreddit:str, limit:int):
        return f"r/{subreddit}/new?limit=100" if limit >= 100 else f"r/{subreddit}/new?limit={limit}"
    
    @get_subreddit_post
    def get_subreddit_posts_hot(subreddit:str, limit:int):
        return f"r/{subreddit}/hot?limit=100" if limit >= 100 else f"r/{subreddit}/hot?limit={limit}"

        
            
