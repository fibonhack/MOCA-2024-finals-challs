from crontab import CronTab
from pathlib import Path

def minutes_to_cron_schedule(minutes):
    cron_schedule = f"*/{minutes} * * * *"
    return cron_schedule

def remove_all_cronjobs():
    try:
        cron = CronTab(user=True)
        cron.remove_all()  
        cron.write()  
        return True
    except Exception as e:
        return f"Failed to delete cron job: {str(e)}"
        return False

def create_cronjob(data):    
    try:
        remove_all_cronjobs()
        cron = CronTab(user=True)
        job = cron.new(command=data['cmd'])
        job.setall(minutes_to_cron_schedule(data['minutes']))
        cron.write()
        return True
    except Exception as e:
        return f"Failed to create cron job: {str(e)}"
        return False