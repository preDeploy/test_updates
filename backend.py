from fastapi import FastAPI, Request, HTTPException, Depends
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime
import os
import time
import asyncio
import csv
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base
# from sqlalchemy.ext.declarative import 
# from models import User
import stripe

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, primary_key=True, nullable=False)
    subscription_type = Column(String, default='basic', nullable=False)

class Dolores():
    def __init__(self):
        self.OPENAI_API_KEY = ""
        self.OPENAI_ASSISTANT_ID = "asst_1l9QjbTLtJnMI3fEbZyf4Tc6"
        self.context = {
            "user": '',
            "assistant": ''
        }
        self.user_input = ''
        self.bot_response = ''
        self.location = './context/'

    def getFileName(self, user):
        if user=='unknown':
            contextFile = os.listdir('./context/unknown/')
            now = int(time.time())
            if len(contextFile)>0:
                if now - int(contextFile[0][:-5]) > 1800 and contextFile[0][-4:] == 'json':
                    os.remove(f'./context/unknown/{contextFile[0]}')
                else:
                    now = contextFile[0][:-5]
            else:
                pass
            return now
        return int(datetime.today().strftime('%Y%m%d'))

    def assistant(self, user_input):
        client = OpenAI(api_key=self.OPENAI_API_KEY)
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"This is the previous context:\n\nuser:{self.context['user']}\nassistant:{self.context['assistant']}. And this is the current prompt: {user_input}. Respond in plain string format, no special formatting",
                }
            ]
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.OPENAI_ASSISTANT_ID
        )
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        return messages.data[0].content[0].text.value

    def generateContext(self, input, role):
        summarizing_client = OpenAI(api_key=self.OPENAI_API_KEY)
        response = summarizing_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You'll be given a transcript of one of the person in the chat. this transcript is from the {role}. The transcript will have 2 paragraphs, first paragraph will have all the summarized info from previous message sent by the {role} and current message sent by the {role}. You have to summarize both these messages and create a paragraph that will have all the important information from the transcripts. Return summary in this format: 'Previous Context: [summary]'"
                },
                {
                    "role": "user",
                    "content": f"{input}"
                }
            ],
            temperature=0.7,
            top_p=1
        )
        return response.choices[0].message.content

    def openJSON(self, user):
        filename = self.getFileName(user)
        if not os.path.isdir(f"./context/{user}"):
            os.makedirs(f"./context/{user}")
        self.location = f"./context/{user}/{filename}.json"
        try:
            with open(self.location, 'r') as cFile:
                self.context = json.load(cFile)
        except:
            pass

    def saveJSON(self):
        with open(self.location, 'w') as cFile:
            json.dump(self.context, cFile)

    async def chat(self, user_input, user):
        self.user_input = user_input
        self.openJSON(user)
        response = self.assistant(user_input).replace("\n", "<br>")
        self.bot_response = response
        return response
    
    async def updateContext(self):       
        self.context['user'] = self.generateContext(f"{self.context['user']}\n\n{self.user_input}", "user")
        self.context['assistant'] = self.generateContext(f"{self.context['assistant']}\n\n{self.bot_response}", "assistant")
        self.saveJSON()

class Database():
    def __init__(self):
        self.database_url = 'postgresql://dolores:JustiGuide!UserInfo2024@user-details.cf2y80iom48x.us-west-1.rds.amazonaws.com:5432/user_details'
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def add_user(self, details, db):
        new_user = User(first_name=details['firstName'], last_name=details['lastName'], email=details['email'])
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    def update_subscription(self, email, tier, db):
        user = db.query(User).filter(User.email==email).first()        
        if user:
            user.subscription_type=tier
            db.commit()
            db.refresh(user)


class Stripe():
    def __init__(self) -> None:
        self.publishableKey = 'pk_live_51PDwGXP6cNlgDSsmbpqe2mJUE2oYznCtT4AWzvNewWy2s1senClvQdBpGo7vhnnEmitiAIDHEqMszvg5bBPt7wEN00sHnbYPnG'
        self.secretKey = ''
        stripe.api_key=self.secretKey
        self.priceID = {
            'basic': {'monthly': 'price_1PEJ4lP6cNlgDSsmuwNOrTna', 'yearly': 'price_1PEJ0GP6cNlgDSsmNmInXFzC'},
            'plus': {'monthly': 'price_1PEJ41P6cNlgDSsmHHD7FBIc', 'yearly': 'price_1PGkUUP6cNlgDSsmW0DG8cYh'},
            'premium': {'monthly': 'price_1PGkXdP6cNlgDSsmedxP1cEU', 'yearly':'price_1PGkYCP6cNlgDSsmJfN7djSg'}
        }
        # self.priceID = {
        #     'pro': {'monthly': 'price_1PEabFP6cNlgDSsmwo4VLXmn', 'yearly': 'price_1PEabFP6cNlgDSsmwo4VLXmn'},
        #     'plus': {'monthly': 'price_1PEabFP6cNlgDSsmwo4VLXmn', 'yearly': 'price_1PEabFP6cNlgDSsmwo4VLXmn'}
        # }
        self.tier='basic'
        self.email='none'
        self.transaction_id = 'none'
        self.sessID = 'none'
    
    def checkOutSess(self, tier, duration, email):
        self.tier=tier
        self.email=email
        checkoutSess = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': self.priceID[tier][duration],
                    'quantity': 1,
                },
            ],
            subscription_data={                
                "trial_settings": {"end_behavior": {"missing_payment_method": "pause"}},
                "trial_period_days": 1,
            },
            mode='subscription',
            success_url='http://127.0.0.1:5500/success.html',
            cancel_url='http://127.0.0.1:5500/error.html',
        )
        return checkoutSess.id
    
    def getTier(self):
        return self.tier
    
    def getEmail(self):
        return self.email


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot_responses = Dolores()
sql_db = Database()
stripeObj = Stripe()

@app.post("/get_response/")
async def get_bot_response(request: Request):
    data = await request.json()
    user_message = data["user_message"]
    user = data["user"]
    bot_response = await bot_responses.chat(user_message, user)
    response = {"bot_response": bot_response}
    asyncio.create_task(bot_responses.updateContext())
    return response

@app.post('/new_user/')
async def new_user(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    user = db.query(User).filter(User.email == data['email']).first()
    if not user:
        sql_db.add_user(data, db)


@app.post('/create_checkoutsess/')
async def create_checkoutSessID(request: Request):
    data = await request.json()
    coSess_ID = stripeObj.checkOutSess(data['tier'], data['duration'], data['email'])
    # stripeObj.assignCID(coSess_ID)
    return {'id': coSess_ID}

@app.post('/stripe-webhook/')
def handle_stripeWebhook(request, db: Session=Depends(sql_db.get_db)):
    signature = request.headers.get('Stripe-Signature')
    try:
        event=stripe.Webhook.construct_event(
            payload=request.get_data(as_text=True),
            sig_header=signature,
            secret=stripe.api_key
        )
    except ValueError as e:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError as e:
        return 'Invalid Signature', 400

@app.get("/update_subscription/")
async def userUpdate(db: Session=Depends(sql_db.get_db)):
    email = stripeObj.getEmail()
    tier = stripeObj.getTier()
    sql_db.update_subscription(email, tier, db)

@app.post('/user_sub/')
async def update_userPage(request: Request, db: Session = Depends(sql_db.get_db)):
    data = await request.json()
    email = data['email']
    user = db.query(User).filter(User.email == email).first()
    if user:
        subscription_tier = user.subscription_type
        return {'subscription': subscription_tier.capitalize()}


@app.get('/test/')
async def test_func():
    return {'test': 'successful'}

if __name__ == "__main__":
    uvicorn.run("backend:app", reload=True)
    

