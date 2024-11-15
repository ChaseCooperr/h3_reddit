import json
import time, csv, os, sys, logging
from alive_progress import alive_bar
from client import Reddit_Client
from config import config
from auth import auth
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def gather_subreddit_data() -> None:
    logger.info(f'init gather subbreddit data')   

    reddit_client = Reddit_Client(auth['REDDIT_USER'],auth['REDDIT_PASS'], auth['REDDIT_CLIENT_ID'] , auth['REDDIT_CLIENT_SECRET'] )
    for subreddit in config['SUBS_TO_PROCESS']:
        logger.info(f'processing {subreddit} subreddit')

        new_subreddit_posts = []
        subreddit_posts     = []

        for post_sort in config['POST_TO_GATHER']:
            match post_sort:
                case 'default':
                    try:
                        logger.info(f'gathering posts - default')
                        subreddit_posts += reddit_client.get_subreddit_posts(subreddit, limit=1000)
                    except:
                        logger.critical('error gathering posts - default')
                case 'controversial':    
                    try:
                        logger.info(f'gathering posts - controversial')
                        subreddit_posts += reddit_client.get_subreddit_posts_controversial(subreddit, limit=1000)
                    except:
                        logger.critical('error gathering posts - controversial')
                case 'top':  
                    try:
                        logger.info(f'gathering posts - top')
                        subreddit_posts += reddit_client.get_subreddit_posts_top(subreddit, limit=1000)
                    except:
                        logger.critical('error gathering posts - top')
                case 'new': 
                    try:
                        logger.info(f'gathering posts - new')
                        subreddit_posts += reddit_client.get_subreddit_posts_new(subreddit, limit=1000)
                    except:
                        logger.critical('error gathering posts - new')
                case 'hot':
                    try:
                        logger.info(f'gathering posts - hot')
                        subreddit_posts += reddit_client.get_subreddit_posts_hot(subreddit, limit=1000)
                    except:
                        logger.critical('error gathering posts - hot')

        logger.info(f'processesing posts - remove duplicte author entries')
        for post in subreddit_posts:
            new_subreddit_posts.append({
                'id':       post['data']['id'] , 
                'author':   post['data']['author'], 
                'title' :   post['data']['title'] 
                })
        new_subreddit_posts = list({author['author']:author for author in new_subreddit_posts}.values())
    
        csv_subreddit_posts = []
        if os.path.isfile(f"reports/{subreddit}_posts.csv"):    
            logger.info('subreddit data file exists')
            with open(f"reports/{subreddit}_posts.csv", newline='') as csvfile:
                reader              = csv.DictReader(csvfile)
                csv_subreddit_posts = list(reader)
        
        if csv_subreddit_posts:    
            subreddit_posts_to_add  = [post for post in new_subreddit_posts if post not in csv_subreddit_posts] 
        else:
            logger.info('subreddit data file not found - creating new')
            subreddit_posts_to_add = new_subreddit_posts

        if not subreddit_posts_to_add:
            logger.info(f'no new posts found on {subreddit} subreddit')    
        else:
            logger.info(f'{len(subreddit_posts_to_add)} new posts found on {subreddit} subreddit - adding to data file')
            with open(f"reports/{subreddit}_posts.csv", 'a') as csvfile:
                    
                    fieldnames  = ['id', 'author', 'title']
                    writer      = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    if os.path.getsize(f"reports/{subreddit}_posts.csv") == 0:
                        writer.writeheader()
                    
                    for post in subreddit_posts_to_add:
                        writer.writerow({
                            'id':       post['id'], 
                            'author':   post['author'],                 
                            'title' :   post['title']
                            })

def count_user_interactions(subreddit:str) -> None:
    logger.info(f'init count user impressions') 
    report = {
        'success'   : 0,
        'fail'      : 0
    }

    csv_subreddit_posts = []
    if os.path.isfile(f"reports/{subreddit}_posts.csv"):
        with open(f"reports/{subreddit}_posts.csv", newline='') as csvfile:
            reader              = csv.DictReader(csvfile)
            csv_subreddit_posts = list(reader)
    else:
        logger.error('no subreddit post data file found')
        return
    
    subreddit_counter   = {}
    reddit_client       = Reddit_Client(auth['REDDIT_USER'],auth['REDDIT_PASS'], auth['REDDIT_CLIENT_ID'] , auth['REDDIT_CLIENT_SECRET'] )
    with alive_bar(len(csv_subreddit_posts), bar='brackets', unknown='classic',) as bar:
        raw_interaction_data = ""

        for post in csv_subreddit_posts:
            with open(f"reports/{subreddit}_impressions.csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                for interaction in config['INTERACTIONS_TO_COUNT']:
                    time.sleep(1)
                    try:
                        match interaction:
                            case "comments":
                                user_interactions = reddit_client.get_user_comments(post['author']).json() 
                            case "submitted":
                                user_interactions = reddit_client.get_user_submitted(post['author']).json()

                        raw_interaction_data += json.dumps(user_interactions)

                        for interaction in user_interactions['data']['children']:
                            subreddit = interaction['data']['subreddit']
                            if subreddit not in subreddit_counter:
                                subreddit_counter[subreddit] = 0
                            subreddit_counter[subreddit] += 1

                        report['success'] += 1
                    except:
                        report['fail'] += 1
                        time.sleep(2)
                        
                sorted_subreddit_counter = dict(sorted(subreddit_counter.items(), key=lambda item: item[1]))
                for key, val in sorted_subreddit_counter.items():
                    writer.writerow([key, val])
            
            report_total    = report['success'] + report['fail']
            fail_rate       = report['fail'] / report_total * 100 if report_total > 0 else 0
            report.update({
                'fail_rate' : "{:3.2f}%".format(fail_rate) 
            })
            logger.info(report)
            bar()
        with open(f"reports/raw_{subreddit}.txt", "w") as text_file:
            text_file.write(raw_interaction_data)
         
if __name__ == "__main__":
    task        = str(sys.argv[1])
    #subreddit   = str(sys.argv[2])
    match task:
        case 'get':
            gather_subreddit_data() 
        # case 'count': 
        #     count_user_interactions(subreddit)