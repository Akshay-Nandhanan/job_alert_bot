import os, re, json, schedule, time, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()
EMAIL = os.getenv("GMAIL_EMAIL")
PASS = os.getenv("GMAIL_PASSWORD")
TO = os.getenv("RECEIVER_EMAIL")

def scrape_internshala():
    url = "https://internshala.com/internships/data%20science-internship"
    jobs=[]
    soup = BeautifulSoup(requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
    for div in soup.select("div.internship_meta")[:5]:
        a=div.find_previous("a")
        if a and a.get("href"):
            jobs.append(f"{a.text.strip()}\nhttps://internshala.com{a['href']}")
    return jobs

def scrape_naukri():
    roles=["data+science+fresher","machine+learning+fresher","ai+developer+fresher","computer+vision+fresher","business+intelligence+analyst+fresher"]
    jobs=[]
    for r in roles:
        url=f"https://www.naukri.com/{r}-jobs?k={r}"
        soup=BeautifulSoup(requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text,"html.parser")
        for c in soup.select("article.jobTuple")[:5]:
            t=c.find("a",class_="title")
            if t and t.get("href"):
                jobs.append(f"{t.text.strip()} ({r.replace('+',' ')})\n{t['href']}")
    return jobs

def scrape_indeed():
    url="https://www.indeed.com/jobs?q=data+science+fresher&l="
    html=requests.get(url,headers={"User-Agent":"Mozilla/5.0"}).text
    m=re.search(r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', html)
    if not m: return []
    data=json.loads(m.group(1))
    res=data.get("metaData",{}).get("mosaicProviderJobCardsModel",{}).get("results",[])[:5]
    return [f"{r['titleText']}\nhttps://www.indeed.com/viewjob?jk={r['jobKey']}" for r in res]

def format_jobs(source,jobs):
    if not jobs: return f"No results from {source}\n\n"
    txt=f"🔹 {source} jobs:\n"
    for i,j in enumerate(jobs,1): txt+=f"{i}. {j}\n\n"
    return txt

def job_alert():
    body=""
    body+=format_jobs("Internshala",scrape_internshala())
    body+=format_jobs("Naukri",scrape_naukri())
    body+=format_jobs("Indeed",scrape_indeed())
    body+="🔸 Apna jobs: Automation needs Selenium or API\n\n"
    body+="🔸 LinkedIn jobs: Automation requires Selenium or ScraperAPI\n\n"
    send_email("🔥 Daily Fresher Job Alerts (AI/ML/Data)",body)

def send_email(subject,body):
    msg=MIMEMultipart(); msg["From"]=EMAIL; msg["To"]=TO; msg["Subject"]=subject
    msg.attach(MIMEText(body,"plain"))
    ctx=ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com",587) as s:
        s.starttls(context=ctx)
        s.login(EMAIL,PASS)
        s.sendmail(EMAIL,TO,msg.as_string())
    print("✅ Email sent")

schedule.every().day.at("19:00").do(job_alert)
print("⏱️ Scheduled: every day at 7 PM")
while True:
    schedule.run_pending()
    time.sleep(60)
