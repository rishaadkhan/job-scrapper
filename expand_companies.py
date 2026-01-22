"""Script to expand company database - Add more companies here"""
import json

# Additional companies to add (expand this list to reach 1000+)
ADDITIONAL_COMPANIES = [
    # More Tier-1 GCCs
    {"name": "Stripe India", "type": "Tier-1 GCC", "career_url": "https://stripe.com/jobs/search?location=India"},
    {"name": "Snowflake India", "type": "Tier-1 GCC", "career_url": "https://careers.snowflake.com/us/en/search-results?location=India"},
    {"name": "Databricks India", "type": "Tier-1 GCC", "career_url": "https://www.databricks.com/company/careers/open-positions?location=India"},
    {"name": "Confluent India", "type": "Tier-1 GCC", "career_url": "https://www.confluent.io/careers/?location=India"},
    {"name": "MongoDB India", "type": "Tier-1 GCC", "career_url": "https://www.mongodb.com/careers/jobs?location=India"},
    {"name": "Elastic India", "type": "Tier-1 GCC", "career_url": "https://www.elastic.co/careers/jobs?location=India"},
    {"name": "HashiCorp India", "type": "Tier-1 GCC", "career_url": "https://www.hashicorp.com/jobs?location=India"},
    {"name": "Twilio India", "type": "Tier-1 GCC", "career_url": "https://www.twilio.com/company/jobs?location=India"},
    {"name": "Okta India", "type": "Tier-1 GCC", "career_url": "https://www.okta.com/company/careers/?location=India"},
    {"name": "Palo Alto Networks India", "type": "Tier-1 GCC", "career_url": "https://jobs.paloaltonetworks.com/en/jobs/?location=India"},
    
    # More Unicorns & Series B-D
    {"name": "Dream11", "type": "Unicorn", "career_url": "https://www.dream11.com/careers"},
    {"name": "MPL", "type": "Series B-D", "career_url": "https://www.mpl.live/careers"},
    {"name": "Games24x7", "type": "Series B-D", "career_url": "https://www.games24x7.com/careers"},
    {"name": "Hike", "type": "Series B-D", "career_url": "https://hike.in/careers"},
    {"name": "Glance", "type": "Unicorn", "career_url": "https://www.glance.com/careers"},
    {"name": "InMobi", "type": "Unicorn", "career_url": "https://www.inmobi.com/company/careers"},
    {"name": "Dailyhunt", "type": "Series B-D", "career_url": "https://www.dailyhunt.in/careers"},
    {"name": "Koo", "type": "Series B-D", "career_url": "https://www.kooapp.com/careers"},
    {"name": "Josh", "type": "Series B-D", "career_url": "https://www.josh.in/careers"},
    {"name": "Moj", "type": "Series B-D", "career_url": "https://mojapp.in/careers"},
    {"name": "Chingari", "type": "Series B-D", "career_url": "https://chingari.io/careers"},
    {"name": "Roposo", "type": "Series B-D", "career_url": "https://www.roposo.com/careers"},
    {"name": "Trell", "type": "Series B-D", "career_url": "https://trell.co/careers"},
    {"name": "Bulbul", "type": "Series B-D", "career_url": "https://bulbul.tv/careers"},
    {"name": "Mitron", "type": "Series B-D", "career_url": "https://www.mitron.tv/careers"},
    
    # Fintech
    {"name": "Paytm Money", "type": "Series B-D", "career_url": "https://www.paytmmoney.com/careers"},
    {"name": "Paytm Insider", "type": "Series B-D", "career_url": "https://insider.in/careers"},
    {"name": "MobiKwik", "type": "Series B-D", "career_url": "https://www.mobikwik.com/careers"},
    {"name": "Freecharge", "type": "Series B-D", "career_url": "https://www.freecharge.in/careers"},
    {"name": "Simpl", "type": "Series B-D", "career_url": "https://getsimpl.com/careers/"},
    {"name": "LazyPay", "type": "Series B-D", "career_url": "https://www.lazypay.in/careers"},
    {"name": "ZestMoney", "type": "Series B-D", "career_url": "https://www.zestmoney.in/careers"},
    {"name": "KreditBee", "type": "Series B-D", "career_url": "https://www.kreditbee.in/careers"},
    {"name": "MoneyTap", "type": "Series B-D", "career_url": "https://www.moneytap.com/careers"},
    {"name": "EarlySalary", "type": "Series B-D", "career_url": "https://www.earlysalary.com/careers"},
    
    # Edtech
    {"name": "BYJU'S", "type": "Unicorn", "career_url": "https://byjus.com/careers/"},
    {"name": "upGrad", "type": "Unicorn", "career_url": "https://www.upgrad.com/careers/"},
    {"name": "Eruditus", "type": "Unicorn", "career_url": "https://www.eruditus.com/careers/"},
    {"name": "Simplilearn", "type": "Series B-D", "career_url": "https://www.simplilearn.com/careers"},
    {"name": "Toppr", "type": "Series B-D", "career_url": "https://www.toppr.com/careers/"},
    {"name": "Doubtnut", "type": "Series B-D", "career_url": "https://doubtnut.com/careers"},
    {"name": "Classplus", "type": "Series B-D", "career_url": "https://classplusapp.com/careers/"},
    {"name": "Teachmint", "type": "Series B-D", "career_url": "https://www.teachmint.com/careers"},
    {"name": "Leverage Edu", "type": "Series B-D", "career_url": "https://leverageedu.com/careers/"},
    {"name": "Scaler", "type": "Series B-D", "career_url": "https://www.scaler.com/careers/"},
    
    # E-commerce
    {"name": "Myntra", "type": "Unicorn", "career_url": "https://www.myntra.com/careers"},
    {"name": "Ajio", "type": "Series B-D", "career_url": "https://www.ajio.com/careers"},
    {"name": "FirstCry", "type": "Unicorn", "career_url": "https://www.firstcry.com/careers"},
    {"name": "BigBasket", "type": "Series B-D", "career_url": "https://www.bigbasket.com/careers/"},
    {"name": "Grofers (Blinkit)", "type": "Series B-D", "career_url": "https://blinkit.com/careers"},
    {"name": "Zepto", "type": "Series B-D", "career_url": "https://www.zeptonow.com/careers"},
    {"name": "Instamart", "type": "Series B-D", "career_url": "https://www.swiggy.com/instamart-careers"},
    {"name": "JioMart", "type": "Series B-D", "career_url": "https://www.jiomart.com/careers"},
    {"name": "Snapdeal", "type": "Series B-D", "career_url": "https://www.snapdeal.com/careers"},
    {"name": "ShopClues", "type": "Series B-D", "career_url": "https://www.shopclues.com/careers"},
]

def expand_companies():
    # Load existing companies
    with open('companies.json', 'r') as f:
        companies = json.load(f)
    
    print(f"Current companies: {len(companies)}")
    
    # Add new companies (avoid duplicates)
    existing_names = {c['name'] for c in companies}
    new_companies = [c for c in ADDITIONAL_COMPANIES if c['name'] not in existing_names]
    
    companies.extend(new_companies)
    
    # Save updated list
    with open('companies.json', 'w') as f:
        json.dump(companies, f, indent=2)
    
    print(f"Added {len(new_companies)} new companies")
    print(f"Total companies: {len(companies)}")

if __name__ == '__main__':
    expand_companies()
