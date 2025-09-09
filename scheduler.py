from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
import time
import pytz

from utility import get_logger

logger = get_logger(__file__, logging.DEBUG)

class Scheduler:
    def __init__(self):
        # Initialize the scheduler
        self.scheduler = BackgroundScheduler()
        
    def start(self):
        # Start the scheduler
        self.scheduler.start()

    def stop(self):
        # Shutdown the scheduler
        self.scheduler.shutdown()

    def add_periodic_job(self, func, params, job_id):
        # Add a job with static day_of_week and timezone, rest from params
        cron_params = {k: v for k, v in params.items() if v is not None}
        cron_params['day_of_week'] = 'mon-fri'
        cron_params['timezone'] = pytz.timezone('Asia/Kolkata')
        self.scheduler.add_job(
            func,
            trigger=CronTrigger(**cron_params),
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Job '{job_id}' added with cron params: {cron_params}")

    def remove_job(self, job_id):
        # Remove a job by id
        self.scheduler.remove_job(job_id)
        # logger.info(f"Job '{job_id}' removed.")


# Usage example
if __name__ == '__main__':
    # Example job function
    def example_job():
        print("hello")
        logger.info(f"Job executed at {datetime.now()}")
    # Instantiate the scheduler
    my_scheduler = Scheduler()
    
    # Start the scheduler
    my_scheduler.start()
    
    # Add a periodic job to run every 10 seconds
    my_scheduler.add_periodic_job(example_job, 10, 'example_job_id')

    try:
        # Keep the script running
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        # Stop the scheduler on exit
        my_scheduler.stop()